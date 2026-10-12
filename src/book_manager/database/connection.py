import os
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from typing import Any, Generator, Optional, Sequence, Type, TypeVar
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, inspect, select, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.engine.row import Row
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from book_manager.utilities.utilities import PrinterUtil
from book_manager.models.models import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)

T = TypeVar("T", bound=DeclarativeBase)

class ConexionDBError(RuntimeError):
    """Error a nivel de conexión o transacción con la base de datos."""

class ConexionDB:
    """Administra el engine, las transacciones y las sesiones de SQLAlchemy.

    Ofrece dos formas de trabajo sobre la misma base:

    * Consultas crudas mediante :meth:`ejecutar_query` y
      :meth:`transaccion`, que operan sobre un :class:`Connection`.
    * Operaciones con los modelos ORM mediante :meth:`sesion`,
      :meth:`agregar`, :meth:`agregar_varios`, :meth:`obtener`,
      :meth:`listar`, :meth:`actualizar`, :meth:`eliminar` y
      :meth:`contar`, que operan sobre un :class:`Session`.

    Attrs:
        url: URL de conexión utilizada por el engine.
        echo: Indica si el engine registra el SQL emitido.
    """

    def __init__(self, url: str, echo: bool = False) -> None:
        """Crea el engine y la fábrica de sesiones a partir de la URL.

        Args:
            url: URL de conexión.
            echo: Si es ``True``, SQLAlchemy registra el SQL emitido.
        """
        self._url = url
        self._echo = echo
        self._engine: Engine = create_engine(self._url, echo=self._echo, future=True)
        self._session_maker: sessionmaker[Session] = sessionmaker(bind=self._engine, autoflush=False,expire_on_commit=False)

    @property
    def url(self) -> str:
        """URL de conexión utilizada por el engine."""
        return self._url

    @property
    def echo(self) -> bool:
        """Indica si el engine registra el SQL emitido."""
        return self._echo

    @property
    def engine(self) -> Engine:
        """Engine de SQLAlchemy asociado a la conexión."""
        return self._engine

    @property
    def session_maker(self) -> sessionmaker[Session]:
        """Fábrica de sesiones asociada al engine."""
        return self._session_maker

    # ------------------------------------------------------------------
    # Conexiones y transacciones
    # ------------------------------------------------------------------

    @contextmanager
    def transaccion(self) -> Generator[Connection, None, None]:
        """Context manager que maneja una transacción sobre la base de datos.

        Abre una conexión y una transacción, y entrega la conexión para
        ejecutar sentencias dentro del bloque ``with``. Hace ``commit`` al
        salir sin errores y ``rollback`` si se produce una excepción.

        Yields:
            Connection: Conexión con la transacción ya iniciada.

        Raises:
            Exception: La excepción original si falla alguna sentencia.
        """
        connection = self.engine.connect()
        transaction = connection.begin()
        try:
            yield connection
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise
        finally:
            transaction.close()
            connection.close()

    @contextmanager
    def sesion(self) -> Generator[Session, None, None]:
        """Context manager que entrega una sesión transaccional.

        Hace ``commit`` al salir sin errores y ``rollback`` ante cualquier
        excepción, cerrando siempre la sesión al final.

        Yields:
            Session: Sesión de SQLAlchemy lista para operar.

        Raises:
            ConexionDBError: Si falla el ``rollback`` de la transacción.
            Exception: La excepción original si falla alguna operación.
        """
        sesion = self.session_maker()
        try:
            yield sesion
            sesion.commit()
        except Exception:
            try:
                sesion.rollback()
            except SQLAlchemyError as error:
                raise ConexionDBError(
                    f"Fallo el rollback de la transacción: {error}"
                ) from error
            raise
        finally:
            sesion.close()

    def ejecutar_query(self, query: str) -> list[Row]:
        """Ejecuta una sentencia SQL cruda dentro de una transacción.

        Hace ``commit`` si la sentencia se ejecuta sin errores y ``rollback``
        si se produce una excepción.

        Args:
            query: Sentencia SQL a ejecutar.

        Returns:
            Lista con las filas devueltas por la consulta (vacía para
            sentencias que no devuelven resultados).

        Raises:
            Exception: La excepción original si la sentencia falla.
        """
        with self.transaccion() as connection:
            resultado = connection.execute(text(query))
            return list(resultado.fetchall()) if resultado.returns_rows else []

    # ------------------------------------------------------------------
    # Esquema
    # ------------------------------------------------------------------

    def crear_tablas(self, metadata: Optional[MetaData] = None) -> None:
        """Crea en la base todas las tablas registradas en la metadata.

        Args:
            metadata: Metadata a crear. Si se omite, se usa la de los modelos.

        Raises:
            ConexionDBError: Si falla la creación de las tablas.
        """
        metadata = metadata if metadata is not None else self.metadata()
        try:
            metadata.create_all(self.engine)
        except SQLAlchemyError as error:
            raise ConexionDBError(f"No se pudieron crear las tablas: {error}") from error

    def eliminar_tablas(self, metadata: Optional[MetaData] = None) -> None:
        """Elimina de la base todas las tablas registradas en la metadata.

        Args:
            metadata: Metadata a eliminar. Si se omite, se usa la de los modelos.

        Raises:
            ConexionDBError: Si falla la eliminación de las tablas.
        """
        metadata = metadata if metadata is not None else self.metadata()
        try:
            metadata.drop_all(self.engine)
        except SQLAlchemyError as error:
            raise ConexionDBError(f"No se pudieron eliminar las tablas: {error}") from error

    @staticmethod
    def metadata() -> MetaData:
        """Devuelve la metadata de los modelos ORM del proyecto."""
        from book_manager.models.models import Base

        return Base.metadata

    def tablas(self) -> list[str]:
        """Lista los nombres de las tablas existentes en la base."""
        return sorted(inspect(self.engine).get_table_names())

    def probar_conexion(self) -> bool:
        """Verifica que la base de datos responda a una consulta simple.

        Returns:
            ``True`` si la base respondió correctamente.

        Raises:
            ConexionDBError: Si no se pudo conectar con la base de datos.
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as error:
            raise ConexionDBError(
                f"No se pudo conectar a la base de datos: {error}"
            ) from error

    # ------------------------------------------------------------------
    # Operaciones con modelos ORM
    # ------------------------------------------------------------------

    def agregar(self, instancia: T) -> T:
        """Inserta una instancia de modelo en la base de datos.

        Args:
            instancia: Instancia de un modelo ORM.

        Returns:
            La misma instancia, ya persistida y con su ``id`` asignado.
        """
        with self.sesion() as sesion:
            sesion.add(instancia)
        return instancia

    def agregar_varios(self, instancias: Sequence[T]) -> list[T]:
        """Inserta varias instancias de modelo en una sola transacción.

        Args:
            instancias: Secuencia de instancias de modelos ORM.

        Returns:
            La lista de instancias persistidas.
        """
        lista = list(instancias)
        with self.sesion() as sesion:
            sesion.add_all(lista)
        return lista

    def obtener(self, modelo: Type[T], id_registro: int) -> Optional[T]:
        """Obtiene una instancia por su clave primaria.

        Args:
            modelo: Clase del modelo ORM.
            id_registro: Valor de la clave primaria.

        Returns:
            La instancia encontrada o ``None`` si no existe.
        """
        with self.sesion() as sesion:
            return sesion.get(modelo, id_registro)

    def obtener_por(self, modelo: Type[T], **filtros: Any) -> Optional[T]:
        """Obtiene la primera instancia que cumpla con los filtros.

        Args:
            modelo: Clase del modelo ORM.
            **filtros: Pares ``columna=valor`` usados como filtro.

        Returns:
            La primera instancia encontrada o ``None`` si no existe.
        """
        with self.sesion() as sesion:
            return sesion.scalars(select(modelo).filter_by(**filtros)).first()

    def listar(self, modelo: Type[T], **filtros: Any) -> list[T]:
        """Lista las instancias de un modelo, opcionalmente filtradas.

        Args:
            modelo: Clase del modelo ORM.
            **filtros: Pares ``columna=valor`` usados como filtro.

        Returns:
            Lista con las instancias encontradas.
        """
        with self.sesion() as sesion:
            return list(sesion.scalars(select(modelo).filter_by(**filtros)).all())

    def actualizar(self, modelo: Type[T], id_registro: int, **cambios: Any) -> Optional[T]:
        """Actualiza los campos indicados de una instancia existente.

        Args:
            modelo: Clase del modelo ORM.
            id_registro: Valor de la clave primaria.
            **cambios: Pares ``columna=nuevo_valor`` a modificar.

        Returns:
            La instancia actualizada o ``None`` si no existe.
        """
        with self.sesion() as sesion:
            instancia = sesion.get(modelo, id_registro)
            if instancia is None:
                return None
            for campo, valor in cambios.items():
                setattr(instancia, campo, valor)
            return instancia

    def eliminar(self, modelo: Type[T], id_registro: int) -> bool:
        """Elimina una instancia por su clave primaria.

        Args:
            modelo: Clase del modelo ORM.
            id_registro: Valor de la clave primaria.

        Returns:
            ``True`` si la instancia existía y fue eliminada, ``False`` si no.
        """
        with self.sesion() as sesion:
            instancia = sesion.get(modelo, id_registro)
            if instancia is None:
                return False
            sesion.delete(instancia)
            return True

    def contar(self, modelo: Type[T], **filtros: Any) -> int:
        """Cuenta las instancias de un modelo, opcionalmente filtradas.

        Args:
            modelo: Clase del modelo ORM.
            **filtros: Pares ``columna=valor`` usados como filtro.

        Returns:
            Cantidad de instancias que cumplen con los filtros.
        """
        with self.sesion() as sesion:
            return len(sesion.scalars(select(modelo).filter_by(**filtros)).all())

    # ------------------------------------------------------------------
    # Cierre
    # ------------------------------------------------------------------

    def cerrar(self) -> None:
        """Libera el pool de conexiones del engine."""
        self._engine.dispose()

    def __enter__(self) -> "ConexionDB":
        """Permite usar la conexión como context manager."""
        return self

    def __exit__(self, tipo_exc: Any, valor_exc: Any, traza_exc: Any) -> None:
        """Cierra el engine al salir del bloque ``with``."""
        self.cerrar()

    def __repr__(self) -> str:
        return f"ConexionDB(url='{self.url}')"


if __name__ == "__main__":
    # Pruebas unitarias
    load_dotenv()

    RUTA_BD: str = os.getenv("SQLALCHEMY_DATABASE_URL", "")
    PASSWORD: str = os.getenv("SUPABASE_DB_PASSWORD", "")
    URL_BD: str = RUTA_BD.replace("[YOUR-PASSWORD]", PASSWORD)

    conexion = ConexionDB(URL_BD)


    PrinterUtil.dibujar_separador("1. Creación de la tabla")
    conexion.ejecutar_query("DROP TABLE IF EXISTS libros CASCADE;")
    conexion.ejecutar_query("""
        CREATE TABLE libros (
            id SERIAL PRIMARY KEY,
            isbn VARCHAR(13) NOT NULL UNIQUE,
            titulo VARCHAR(200) NOT NULL,
            autor VARCHAR(120) NOT NULL,
            editorial VARCHAR(100) NOT NULL,
            genero VARCHAR(80) NOT NULL,
            idioma VARCHAR(40) NOT NULL,
            paginas INTEGER,
            edicion INTEGER NOT NULL,
            fecha_publicacion DATE,
            peso INTEGER);
        """)
    print("Tabla 'libros' creada.")

    PrinterUtil.dibujar_separador("2. Inserción de registros")
    conexion.ejecutar_query("""
        INSERT INTO libros (isbn, titulo, autor, editorial, genero, idioma,
                            paginas, edicion, fecha_publicacion, peso)
        values ('9788420633121', 'Ficciones', 'Jorge Luis Borges', 'Planeta',
                'Novela', 'Español', 224, 3, '1944-06-15', 280);
        """)
    conexion.ejecutar_query("""
        INSERT INTO libros (isbn, titulo, autor, editorial, genero, idioma,
                            paginas, edicion, fecha_publicacion, peso)
        values ('9788439732471', 'Cien años de soledad', 'Gabriel García Márquez',
                'Sudamericana', 'Novela', 'Español', 471, 1, '1967-05-30', 520);
        """)
    conexion.ejecutar_query("""
        INSERT INTO libros (isbn, titulo, autor, editorial, genero, idioma,
                            paginas, edicion, fecha_publicacion, peso)
        values ('9789504949930', 'La tregua', 'Mario Benedetti', 'Eterna Cadencia',
                'Novela', 'Español', 240, 2, '1960-04-01', 260);
        """)
    print("3 registros insertados.")

    PrinterUtil.dibujar_separador("3. Obtención de datos")
    filas = conexion.ejecutar_query("""
        SELECT isbn, titulo, autor, peso FROM libros WHERE fecha_publicacion >= '1960-01-01';
        """)
    for fila in filas:
        print(fila)
    assert len(filas) == 2, f"Se esperaban 2 filas, se obtuvieron {len(filas)}"
    assert filas[0].titulo == "Cien años de soledad"
    assert filas[0].peso == 520
    assert filas[1].titulo == "La tregua"
    print("Consulta verificada: 2 filas.")

    PrinterUtil.dibujar_separador("3b. Obtención por ISBN")
    filas = conexion.ejecutar_query("""
        SELECT titulo, autor, paginas, peso FROM libros WHERE isbn = '9788420633121';
        """)
    for fila in filas:
        print(fila)
    assert len(filas) == 1
    assert filas[0].titulo == "Ficciones"
    assert filas[0].peso == 280
    print("Consulta verificada: Ficciones (280 g).")

    PrinterUtil.dibujar_separador("4. Rollback ante error")
    try:
        conexion.ejecutar_query("""
            INSERT INTO libros (isbn, titulo, autor, editorial, genero, idioma,
                                paginas, edicion, fecha_publicacion, peso)
            values ('9780307476463', 'Pedro Páramo', 'Juan Rulfo', 'Planeta',
                    'Novela', 'Español', 132, 1, '1955-03-01', 210);
            INSERT INTO tabla_inexistente (nombre) values ('Falla');
            """)
    except Exception as error:
        print(f"Error capturado: {type(error).__name__}")
    total = conexion.ejecutar_query("SELECT COUNT(*) FROM libros;")
    assert total[0][0] == 3, f"El rollback no funcionó: hay {total[0][0]} filas"
    print("Rollback verificado: siguen habiendo 3 filas.")

    PrinterUtil.dibujar_separador("5. Context manager: commit")
    with conexion.transaccion() as conn:
        conn.execute(text("""
            INSERT INTO libros (isbn, titulo, autor, editorial, genero, idioma,
                                paginas, edicion, fecha_publicacion, peso)
            values ('9780307476463', 'Pedro Páramo', 'Juan Rulfo', 'Planeta',
                    'Novela', 'Español', 132, 1, '1955-03-01', 210);
            """))
        conn.execute(text("""
            INSERT INTO libros (isbn, titulo, autor, editorial, genero, idioma,
                                paginas, edicion, fecha_publicacion, peso)
            values ('9788499924212', 'Sapiens', 'Yuval Noah Harari', 'Debolsillo',
                    'Ensayo', 'Español', 496, 1, '2011-01-01', 530);
            """))
    total = conexion.ejecutar_query("SELECT COUNT(*) FROM libros;")
    assert total[0][0] == 5, f"El commit no funcionó: hay {total[0][0]} filas"
    print("Commit verificado: 5 filas.")

    PrinterUtil.dibujar_separador("6. Context manager: rollback")
    try:
        with conexion.transaccion() as conn:
            conn.execute(text("""
                INSERT INTO libros (isbn, titulo, autor, editorial, genero, idioma,
                                    paginas, edicion, fecha_publicacion, peso)
                values ('9788433910868', 'Los detectives salvajes', 'Roberto Bolaño',
                        'Anagrama', 'Novela', 'Español', 623, 1, '1998-11-01', 580);
                """))
            conn.execute(text("INSERT INTO tabla_inexistente (nombre) values ('Falla');"))
    except Exception as error:
        print(f"Error capturado: {type(error).__name__}")
    total = conexion.ejecutar_query("SELECT COUNT(*) FROM libros;")
    assert total[0][0] == 5, f"El rollback no funcionó: hay {total[0][0]} filas"
    print("Rollback verificado: siguen habiendo 5 filas.")

    PrinterUtil.dibujar_separador("7. Context manager: lectura")
    with conexion.transaccion() as conn:
        resultado = conn.execute(text("""
            SELECT titulo, peso FROM libros WHERE peso > 500 ORDER BY peso;
            """))
        filas = list(resultado)
        for fila in filas:
            print(fila)
        assert len(filas) == 2, f"Se esperaban 2 filas, se obtuvieron {len(filas)}"
        assert filas[0].titulo == "Cien años de soledad"
        assert filas[1].titulo == "Sapiens"
    print("Lectura dentro del context manager verificada: 2 filas.")

    PrinterUtil.dibujar_separador("8. Cierre de la conexión")
    conexion.cerrar()
    print("Conexión cerrada.")

    PrinterUtil.dibujar_separador("9. Esquema a partir de los modelos ORM")
    conexion.ejecutar_query("DROP TABLE IF EXISTS libros CASCADE;")
    conexion.eliminar_tablas()
    conexion.crear_tablas()
    tablas = conexion.tablas()
    print(f"Tablas creadas: {', '.join(tablas)}")
    assert "libros" in tablas and "precios" in tablas and "cotizaciones" in tablas
    assert conexion.probar_conexion() is True
    print("Esquema ORM verificado.")

    PrinterUtil.dibujar_separador("10. Inserción con modelos ORM")
    editorial = conexion.agregar(
        Editorial(nombre="Sudamericana", pais_origen="Argentina", email="contacto@sd.com")
    )
    genero = conexion.agregar(Genero(tipo="Novela", descripcion="Novela latinoamericana"))
    moneda = conexion.agregar(Moneda(codigo="ARS", nombre="Peso argentino", simbolo="$"))
    moneda_destino = conexion.agregar(Moneda(codigo="USD", nombre="Dólar", simbolo="US$"))
    tipo = conexion.agregar(TipoCotizacion(nombre="Blue", descripcion="Mercado paralelo"))
    libro = conexion.agregar(
        Libro(
            isbn="9788439732471",
            titulo="Cien años de soledad",
            autor="Gabriel García Márquez",
            editorial_id=editorial.id,
            genero_id=genero.id,
            edicion=1,
            idioma="Español",
            paginas=471,
            fecha_publicacion=date(1967, 5, 30),
            peso=520,
        )
    )
    assert libro.id is not None
    print(f"Libro insertado con id={libro.id}.")

    conexion.agregar_varios([
        Precio(libro_id=libro.id, moneda_id=moneda.id, valor=Decimal("15000.00")),
        Stock(libro_id=libro.id, cantidad=7, stock_minimo=3),
        CotizacionDolar(
            tipo_id=tipo.id,
            moneda_origen_id=moneda_destino.id,
            moneda_destino_id=moneda.id,
            valor_compra=Decimal("1150.00"),
            valor_venta=Decimal("1190.00"),
        ),
    ])
    print("Precio, stock y cotización insertados.")

    PrinterUtil.dibujar_separador("11. Lectura con modelos ORM")
    recuperado = conexion.obtener(Libro, libro.id)
    assert recuperado is not None and recuperado.titulo == "Cien años de soledad"
    print(f"obtener: {recuperado!r}")

    por_isbn = conexion.obtener_por(Libro, isbn="9788439732471")
    assert por_isbn is not None and por_isbn.peso == 520
    print(f"obtener_por: {por_isbn!r}")

    libros = conexion.listar(Libro)
    assert len(libros) == 1
    print(f"listar: {libros!r}")

    print(f"contar libros: {conexion.contar(Libro)}")
    print(f"contar libros con peso 520: {conexion.contar(Libro, peso=520)}")
    assert conexion.contar(Libro) == 1
    assert conexion.contar(Libro, peso=520) == 1

    PrinterUtil.dibujar_separador("12. Actualización con modelos ORM")
    actualizado = conexion.actualizar(Libro, libro.id, paginas=480, peso=530)
    assert actualizado is not None and actualizado.paginas == 480
    verificado = conexion.obtener(Libro, libro.id)
    assert verificado is not None and verificado.peso == 530
    print("Actualización verificada.")

    PrinterUtil.dibujar_separador("13. Eliminación con modelos ORM")
    assert conexion.eliminar(Libro, libro.id) is True
    assert conexion.obtener(Libro, libro.id) is None
    assert conexion.eliminar(Libro, libro.id) is False
    print("Eliminación verificada.")

    PrinterUtil.dibujar_separador("14. Rollback de la sesión ante error")
    try:
        with conexion.sesion() as sesion:
            sesion.add(Editorial(nombre="Planeta", pais_origen="España"))
            sesion.execute(text("INSERT INTO tabla_inexistente (nombre) values ('Falla');"))
    except Exception as error:
        print(f"Error capturado: {type(error).__name__}")
    assert conexion.contar(Editorial) == 1
    print("Rollback de la sesión verificado: sigue habiendo 1 editorial.")

    PrinterUtil.dibujar_separador("15. Cierre de la conexión")
    conexion.cerrar()
    print("Conexión cerrada.")
