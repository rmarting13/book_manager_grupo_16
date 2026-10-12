import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.row import Row
from sqlalchemy.sql import text
from book_manager.utilities.utilities import PrinterUtil


class ConexionDB:
    """Administra la conexión a la base de datos y la ejecución de consultas.

    Attrs:
        url: URL de conexión utilizada por el engine.
    """

    def __init__(self, url: str) -> None:
        """Crea el engine a partir de la URL de conexión.

        Args:
            url: URL de conexión, por ejemplo ``sqlite:///base.db``.
        """
        self._url = url
        self._engine: Engine = create_engine(self._url, echo=True)

    @property
    def url(self) -> str:
        """URL de conexión utilizada por el engine."""
        return self._url

    @property
    def engine(self) -> Engine:
        """Engine de SQLAlchemy asociado a la conexión."""
        return self._engine

    def ejecutar_query(self, query: str) -> list[Row]:
        """Ejecuta una sentencia SQL dentro de una transacción.

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
        connection = self.engine.connect()
        transaction = connection.begin()
        try:
            resultado = connection.execute(text(query))
            filas: list[Row] = list(resultado.fetchall()) if resultado.returns_rows else []
            transaction.commit()
            return filas
        except Exception:
            transaction.rollback()
            raise
        finally:
            transaction.close()
            connection.close()

    def cerrar(self) -> None:
        """Libera el pool de conexiones del engine."""
        self._engine.dispose()

    def __repr__(self) -> str:
        return f"ConexionDB(url='{self.url}')"


if __name__ == "__main__":
    # Pruebas unitarias
    import tempfile

    RUTA_BD = os.path.join(tempfile.mkdtemp(), "prueba.db")
    conexion = ConexionDB(f"sqlite:///{RUTA_BD}")

    PrinterUtil.dibujar_separador("1. Creación de la tabla")
    conexion.ejecutar_query("""
        CREATE TABLE libros (
            id INTEGER NOT NULL,
            isbn VARCHAR NOT NULL,
            titulo VARCHAR NOT NULL,
            autor VARCHAR NOT NULL,
            editorial VARCHAR NOT NULL,
            genero VARCHAR NOT NULL,
            idioma VARCHAR NOT NULL,
            paginas INTEGER,
            edicion INTEGER NOT NULL,
            fecha_publicacion DATE,
            peso INTEGER,
            PRIMARY KEY (id));
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

    PrinterUtil.dibujar_separador("5. Cierre de la conexión")
    conexion.cerrar()
    print("Conexión cerrada.")
