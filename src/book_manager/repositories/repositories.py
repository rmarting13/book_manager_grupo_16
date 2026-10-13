import abc
from datetime import date, datetime
from typing import Any, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    EntidadBase,
    Genero,
    GeneroLiterario,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.models.models import (
    CotizacionDolar as CotizacionDolarORM,
    Editorial as EditorialORM,
    Genero as GeneroORM,
    Libro as LibroORM,
    Moneda as MonedaORM,
    Precio as PrecioORM,
    Stock as StockORM,
    TipoCotizacion as TipoCotizacionORM,
)

# import csv
# import os
# from decimal import Decimal
# from typing import Dict

T = TypeVar('T', bound=EntidadBase)

# def _asegurar_csv(ruta: str, columnas: List[str]) -> None:
#     """Crea el directorio y el CSV con encabezado si todavía no existe."""
#     os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
#     if not os.path.exists(ruta):
#         _escribir_csv(ruta, columnas, [])
#
#
# def _leer_csv(ruta: str) -> List[Dict[str, str]]:
#     """Lee un CSV y devuelve sus filas como diccionarios."""
#     with open(ruta, "r", encoding="utf-8", newline="") as archivo:
#         return list(csv.DictReader(archivo))
#
#
# def _escribir_csv(ruta: str, columnas: List[str], filas: List[Dict[str, str]]) -> None:
#     """Reemplaza el contenido de un CSV con las filas indicadas."""
#     with open(ruta, "w", encoding="utf-8", newline="") as archivo:
#         escritor = csv.DictWriter(archivo, fieldnames=columnas)
#         escritor.writeheader()
#         escritor.writerows(filas)

class IRepositorio(abc.ABC, Generic[T]):
  """Interfaz para repositorios que manejan entidades con operaciones CRUD básicas."""

  @abc.abstractmethod
  def crear(self, entidad: T) -> T:
    """Crea una nueva entidad en el repositorio.

    Args:
        entidad (T): La entidad a crear.

    Returns:
        T: La entidad creada.

    Raises:
        ValueError: Si ya existe una entidad con el mismo ID.
    """
    pass

  @abc.abstractmethod
  def leer_por_id(self, id: int) -> Optional[T]:
    """Lee una entidad del repositorio por su ID.

    Args:
        id (int): El ID de la entidad a leer.

    Returns:
        Optional[T]: La entidad si se encuentra, None en caso contrario.
    """
    pass

  @abc.abstractmethod
  def leer_todos(self) -> List[T]:
    """Lee todas las entidades del repositorio.

    Returns:
        List[T]: Una lista de todas las entidades.
    """
    pass

  @abc.abstractmethod
  def actualizar(self, entidad: T) -> T:
    """Actualiza una entidad existente en el repositorio.

    Args:
        entidad (T): La entidad a actualizar (debe tener un ID existente).

    Returns:
        T: La entidad actualizada.

    Raises:
        ValueError: Si no se encuentra la entidad para actualizar.
    """
    pass

  @abc.abstractmethod
  def eliminar(self, id: int) -> bool:
    """Elimina una entidad del repositorio por su ID.

    Args:
        id (int): El ID de la entidad a eliminar.

    Returns:
        bool: True si la entidad fue eliminada, False si no se encontró.
    """
    pass


class IRepositorioStock(abc.ABC):
  """Interfaz para repositorios del tipo Stock."""

  @abc.abstractmethod
  def crear(self, entidad: Stock) -> Stock:
    """Crea un nuevo registro de stock.

    Args:
        stock (Stock): El objeto Stock a crear.

    Returns:
        Stock: El objeto Stock creado.

    Raises:
        ValueError: Si ya existe un registro de stock para el mismo libro.
    """
    pass

  @abc.abstractmethod
  def leer_por_libro(self, libro_id: int) -> Optional['Stock']:
    """Lee un registro de stock por ID de libro.

    Args:
        libro_id (int): El ID del libro asociado al stock.

    Returns:
        Optional[Stock]: El objeto Stock si se encuentra, None en caso contrario.
    """
    pass

  @abc.abstractmethod
  def leer_todos(self) -> List['Stock']:
    """Lee todos los registros de stock.

    Returns:
        List[Stock]: Una lista con todos los registros de stock.
    """
    pass

  @abc.abstractmethod
  def actualizar(self, entidad: 'Stock') -> 'Stock':
    """Actualiza un registro de stock existente.

    Args:
        stock (Stock): El objeto Stock a actualizar (debe tener un libro_id existente).

    Returns:
        Stock: El objeto Stock actualizado.

    Raises:
        ValueError: Si no se encuentra el stock para actualizar.
    """
    pass

  @abc.abstractmethod
  def eliminar(self, id: int) -> bool:
    """Elimina un registro de stock por ID de libro.

    Args:
        libro_id (int): El ID del libro asociado al stock a eliminar.

    Returns:
        bool: True si el stock fue eliminado, False si no se encontró.
    """
    pass


class IRepositorioCotizacionDolar(abc.ABC):
  """Interfaz para repositorios del tipo RepositorioCotizacionDolar."""

  @abc.abstractmethod
  def crear(self, entidad: 'CotizacionDolar') -> 'CotizacionDolar':
    """Crea una nueva cotización de dólar.

    Args:
        cotizacion (CotizacionDolar): El objeto CotizacionDolar a crear.

    Returns:
        CotizacionDolar: El objeto CotizacionDolar creado.

    Raises:
        ValueError: Si ya existe una cotización para el mismo tipo y fecha.
    """
    pass

  @abc.abstractmethod
  def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: date) -> Optional['CotizacionDolar']:
    """Lee una cotización de dólar por tipo y fecha.

    Args:
        tipo_id (int): El ID del tipo de cotización (e.g., 'Oficial', 'Blue').
        fecha (date): La fecha de la cotización.

    Returns:
        Optional[CotizacionDolar]: La cotización si se encuentra, None en caso contrario.
    """
    pass

  @abc.abstractmethod
  def leer_historico_por_tipo(self, tipo_id: int) -> List['CotizacionDolar']:
    """Lee el histórico de cotizaciones para un tipo específico.

    Args:
        tipo_id (int): El ID del tipo de cotización.

    Returns:
        List[CotizacionDolar]: Una lista de cotizaciones históricas para el tipo dado.
    """
    pass

  @abc.abstractmethod
  def actualizar(self, entidad: 'CotizacionDolar') -> 'CotizacionDolar':
    """Actualiza una cotización de dólar existente.

    Args:
        cotizacion (CotizacionDolar): El objeto CotizacionDolar a actualizar.

    Returns:
        CotizacionDolar: El objeto CotizacionDolar actualizado.
    """
    pass

  @abc.abstractmethod
  def eliminar(self, id: int, fecha: date) -> bool:
    """Elimina una cotización de dólar por tipo y fecha.

    Args:
        tipo_id (int): El ID del tipo de cotización.
        fecha (date): La fecha de la cotización a eliminar.

    Returns:
        bool: True si la cotización fue eliminada, False si no se encontró.
    """
    pass

class RepositorioError(ValueError):
    """Clase de error a nivel de persistencia de datos."""
    
def _moneda_a_entidad(registro: MonedaORM) -> Moneda:
    """Convierte un registro ORM de moneda en su entidad."""
    return Moneda(
        id=registro.id,
        codigo=registro.codigo,
        nombre=registro.nombre,
        simbolo=registro.simbolo,
    )

def _moneda_a_modelo(entidad: Moneda) -> MonedaORM:
    """Convierte una entidad de moneda en su registro ORM."""
    return MonedaORM(
        codigo=entidad.codigo,
        nombre=entidad.nombre,
        simbolo=entidad.simbolo,
    )

def _genero_a_entidad(registro: GeneroORM) -> Genero:
    """Convierte un registro ORM de género en su entidad."""
    return Genero(
        id=registro.id,
        tipo=GeneroLiterario(registro.tipo),
        nombre_personalizado=registro.nombre_personalizado,
        descripcion=registro.descripcion,
    )

def _genero_a_modelo(entidad: Genero) -> GeneroORM:
    """Convierte una entidad de género en su registro ORM."""
    return GeneroORM(
        tipo=entidad.tipo.value,
        nombre_personalizado=entidad.nombre_personalizado,
        descripcion=entidad.descripcion,
    )

def _editorial_a_entidad(registro: EditorialORM) -> Editorial:
    """Convierte un registro ORM de editorial en su entidad."""
    return Editorial(
        id=registro.id,
        nombre=registro.nombre,
        pais_origen=registro.pais_origen,
        email=registro.email,
        telefono=registro.telefono,
        sitio_web=registro.sitio_web,
    )

def _editorial_a_modelo(entidad: Editorial) -> EditorialORM:
    """Convierte una entidad de editorial en su registro ORM."""
    return EditorialORM(
        nombre=entidad.nombre,
        pais_origen=entidad.pais_origen,
        email=str(entidad.email) if entidad.email else None,
        telefono=entidad.telefono,
        sitio_web=str(entidad.sitio_web) if entidad.sitio_web else None,
    )

def _libro_a_entidad(registro: LibroORM) -> Libro:
    """Convierte un registro ORM de libro en su entidad."""
    return Libro(
        id=registro.id,
        isbn=registro.isbn,
        titulo=registro.titulo,
        autor=registro.autor,
        editorial=_editorial_a_entidad(registro.editorial),
        genero=_genero_a_entidad(registro.genero),
        edicion=registro.edicion,
        idioma=registro.idioma,
        paginas=registro.paginas,
        fecha_publicacion=registro.fecha_publicacion,
        peso=registro.peso,
    )

def _libro_a_modelo(entidad: Libro) -> LibroORM:
    """Convierte una entidad de libro en su registro ORM."""
    return LibroORM(
        isbn=entidad.isbn,
        titulo=entidad.titulo,
        autor=entidad.autor,
        editorial_id=entidad.editorial.id,
        genero_id=entidad.genero.id,
        edicion=entidad.edicion,
        idioma=entidad.idioma,
        paginas=entidad.paginas,
        fecha_publicacion=entidad.fecha_publicacion,
        peso=entidad.peso,
    )

def _precio_a_entidad(registro: PrecioORM) -> Precio:
    """Convierte un registro ORM de precio en su entidad."""
    return Precio(
        id=registro.id,
        libro=_libro_a_entidad(registro.libro),
        moneda=_moneda_a_entidad(registro.moneda),
        valor=registro.valor,
        fecha_vigencia=registro.fecha_vigencia,
    )

def _precio_a_modelo(entidad: Precio) -> PrecioORM:
    """Convierte una entidad de precio en su registro ORM."""
    return PrecioORM(
        libro_id=entidad.libro.id,
        moneda_id=entidad.moneda.id,
        valor=entidad.valor,
        fecha_vigencia=entidad.fecha_vigencia,
    )

def _stock_a_entidad(registro: StockORM) -> Stock:
    """Convierte un registro ORM de stock en su entidad."""
    return Stock(
        id=registro.id,
        libro=_libro_a_entidad(registro.libro),
        cantidad=registro.cantidad,
        stock_minimo=registro.stock_minimo,
        fecha_ultimo_ingreso=registro.fecha_ultimo_ingreso,
    )

def _stock_a_modelo(entidad: Stock) -> StockORM:
    """Convierte una entidad de stock en su registro ORM."""
    return StockORM(
        libro_id=entidad.libro.id,
        cantidad=entidad.cantidad,
        stock_minimo=entidad.stock_minimo,
        fecha_ultimo_ingreso=entidad.fecha_ultimo_ingreso,
    )

def _tipo_cotizacion_a_entidad(registro: TipoCotizacionORM) -> TipoCotizacion:
    """Convierte un registro ORM de tipo de cotización en su entidad."""
    return TipoCotizacion(
        id=registro.id,
        nombre=registro.nombre,
        descripcion=registro.descripcion,
    )

def _tipo_cotizacion_a_modelo(entidad: TipoCotizacion) -> TipoCotizacionORM:
    """Convierte una entidad de tipo de cotización en su registro ORM."""
    return TipoCotizacionORM(
        nombre=entidad.nombre,
        descripcion=entidad.descripcion,
    )

def _cotizacion_a_entidad(registro: CotizacionDolarORM) -> CotizacionDolar:
    """Convierte un registro ORM de cotización en su entidad."""
    return CotizacionDolar(
        id=registro.id,
        tipo=_tipo_cotizacion_a_entidad(registro.tipo),
        moneda_origen=_moneda_a_entidad(registro.moneda_origen),
        moneda_destino=_moneda_a_entidad(registro.moneda_destino),
        valor_compra=registro.valor_compra,
        valor_venta=registro.valor_venta,
        fecha=registro.fecha,
    )

def _cotizacion_a_modelo(entidad: CotizacionDolar) -> CotizacionDolarORM:
    """Convierte una entidad de cotización en su registro ORM."""
    return CotizacionDolarORM(
        tipo_id=entidad.tipo.id,
        moneda_origen_id=entidad.moneda_origen.id,
        moneda_destino_id=entidad.moneda_destino.id,
        valor_compra=entidad.valor_compra,
        valor_venta=entidad.valor_venta,
        fecha=entidad.fecha,
    )

class RepositorioBD(IRepositorio[T], Generic[T]):
    """Repositorio base para entidades persistidas en la base de datos.

    Traduce entre las entidades de dominio (pydantic) y los modelos ORM,
    delegando el acceso a datos en :class:`ConexionDB`.
    """

    def __init__(self, conexion: ConexionDB, modelo: Type[Any], entidad_cls: Type[T]) -> None:
        """Inicializa el repositorio con su conexión, modelo ORM y entidad."""
        self._conexion = conexion
        self._modelo = modelo
        self._entidad_cls = entidad_cls

    @property
    def conexion(self) -> ConexionDB:
        """Conexión a la base de datos que respalda al repositorio."""
        return self._conexion

    @property
    def modelo(self) -> Type[Any]:
        """Modelo ORM que administra el repositorio."""
        return self._modelo

    @property
    def entidad_cls(self) -> Type[T]:
        """Clase de entidad que administra el repositorio."""
        return self._entidad_cls

    @abc.abstractmethod
    def _a_modelo(self, entidad: T) -> Any:
        """Convierte una entidad de dominio en un registro ORM."""

    @abc.abstractmethod
    def _a_entidad(self, registro: Any) -> T:
        """Convierte un registro ORM en una entidad de dominio."""

    def _opciones_carga(self) -> List[Any]:
        """Opciones de carga anticipada de relaciones para las consultas."""
        return []

    def crear(self, entidad: T) -> T:
        """Crea una entidad, respetando el ID cuando llega distinto de 0."""
        with self.conexion.sesion() as sesion:
            if entidad.id != 0 and sesion.get(self.modelo, entidad.id) is not None:
                raise RepositorioError(f"Ya existe un registro con id {entidad.id}.")
            registro = self._a_modelo(entidad)
            if entidad.id != 0:
                registro.id = entidad.id
            sesion.add(registro)
            sesion.flush()
            nuevo_id = registro.id
        return entidad.model_copy(update={"id": nuevo_id})

    def leer_por_id(self, id: int) -> Optional[T]:
        """Busca una entidad por su ID."""
        with self.conexion.sesion() as sesion:
            opciones = self._opciones_carga()
            if opciones:
                registro = sesion.get(self.modelo, id, options=opciones)
            else:
                registro = sesion.get(self.modelo, id)
            if registro is None:
                return None
            return self._a_entidad(registro)

    def leer_todos(self) -> List[T]:
        """Lee y reconstruye todas las entidades del repositorio."""
        with self.conexion.sesion() as sesion:
            consulta = select(self.modelo).options(*self._opciones_carga())
            return [self._a_entidad(registro) for registro in sesion.scalars(consulta).all()]

    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente por ID."""
        with self.conexion.sesion() as sesion:
            registro = sesion.get(self.modelo, entidad.id)
            if registro is None:
                raise RepositorioError(f"No existe un registro con id {entidad.id} para actualizar.")
            actualizado = self._a_modelo(entidad)
            for columna in self.modelo.__table__.columns.keys():
                if columna != "id":
                    setattr(registro, columna, getattr(actualizado, columna))
            sesion.flush()
        return entidad

    def eliminar(self, id: int) -> bool:
        """Elimina una entidad por ID, retornando True si hubo cambios."""
        with self.conexion.sesion() as sesion:
            registro = sesion.get(self.modelo, id)
            if registro is None:
                return False
            sesion.delete(registro)
            return True

class RepositorioMoneda(RepositorioBD[Moneda]):
    """Repositorio de monedas en base de datos."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Inicializa el repositorio de monedas."""
        super().__init__(conexion, MonedaORM, Moneda)

    def _a_modelo(self, entidad: Moneda) -> MonedaORM:
        """Convierte una moneda en su registro ORM."""
        return _moneda_a_modelo(entidad)

    def _a_entidad(self, registro: MonedaORM) -> Moneda:
        """Construye una moneda desde su registro ORM."""
        return _moneda_a_entidad(registro)

class RepositorioGenero(RepositorioBD[Genero]):
    """Repositorio de géneros literarios en base de datos."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Inicializa el repositorio de géneros."""
        super().__init__(conexion, GeneroORM, Genero)

    def _a_modelo(self, entidad: Genero) -> GeneroORM:
        """Convierte un género en su registro ORM."""
        return _genero_a_modelo(entidad)

    def _a_entidad(self, registro: GeneroORM) -> Genero:
        """Construye un género desde su registro ORM."""
        return _genero_a_entidad(registro)

class RepositorioEditorial(RepositorioBD[Editorial]):
    """Repositorio de editoriales en base de datos."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Inicializa el repositorio de editoriales."""
        super().__init__(conexion, EditorialORM, Editorial)

    def _a_modelo(self, entidad: Editorial) -> EditorialORM:
        """Convierte una editorial en su registro ORM."""
        return _editorial_a_modelo(entidad)

    def _a_entidad(self, registro: EditorialORM) -> Editorial:
        """Construye una editorial desde su registro ORM."""
        return _editorial_a_entidad(registro)

class RepositorioLibro(RepositorioBD[Libro]):
    """Repositorio de libros con relaciones a editorial y género."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Inicializa el repositorio de libros."""
        super().__init__(conexion, LibroORM, Libro)

    def _a_modelo(self, entidad: Libro) -> LibroORM:
        """Convierte un libro en su registro ORM."""
        return _libro_a_modelo(entidad)

    def _a_entidad(self, registro: LibroORM) -> Libro:
        """Construye un libro desde su registro ORM."""
        return _libro_a_entidad(registro)

    def _opciones_carga(self) -> List[Any]:
        """Carga anticipada de editorial y género del libro."""
        return [selectinload(LibroORM.editorial), selectinload(LibroORM.genero)]

class RepositorioPrecio(RepositorioBD[Precio]):
    """Repositorio de precios con relaciones a libro y moneda."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Inicializa el repositorio de precios."""
        super().__init__(conexion, PrecioORM, Precio)

    def _a_modelo(self, entidad: Precio) -> PrecioORM:
        """Convierte un precio en su registro ORM."""
        return _precio_a_modelo(entidad)

    def _a_entidad(self, registro: PrecioORM) -> Precio:
        """Construye un precio desde su registro ORM."""
        return _precio_a_entidad(registro)

    def _opciones_carga(self) -> List[Any]:
        """Carga anticipada del libro (con sus relaciones) y de la moneda."""
        return [ selectinload(PrecioORM.libro).selectinload(LibroORM.editorial),
                 selectinload(PrecioORM.libro).selectinload(LibroORM.genero),
                 selectinload(PrecioORM.moneda) ]


class RepositorioTipoCotizacion(RepositorioBD[TipoCotizacion]):
    """Repositorio de tipos de cotización en base de datos."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Inicializa el repositorio de tipos de cotización."""
        super().__init__(conexion, TipoCotizacionORM, TipoCotizacion)

    def _a_modelo(self, entidad: TipoCotizacion) -> TipoCotizacionORM:
        """Convierte un tipo de cotización en su registro ORM."""
        return _tipo_cotizacion_a_modelo(entidad)

    def _a_entidad(self, registro: TipoCotizacionORM) -> TipoCotizacion:
        """Construye un tipo de cotización desde su registro ORM."""
        return _tipo_cotizacion_a_entidad(registro)


class RepositorioStock(RepositorioBD[Stock], IRepositorioStock):
    """Repositorio de stock con unicidad por libro."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Inicializa el repositorio de stock."""
        super().__init__(conexion, StockORM, Stock)

    def _a_modelo(self, entidad: Stock) -> StockORM:
        """Convierte un registro de stock en su registro ORM."""
        return _stock_a_modelo(entidad)

    def _a_entidad(self, registro: StockORM) -> Stock:
        """Construye un registro de stock desde su registro ORM."""
        return _stock_a_entidad(registro)

    def _opciones_carga(self) -> List[Any]:
        """Carga anticipada del libro (con sus relaciones)."""
        return [
            selectinload(StockORM.libro).selectinload(LibroORM.editorial),
            selectinload(StockORM.libro).selectinload(LibroORM.genero),
        ]

    def crear(self, entidad: Stock) -> Stock:
        """Crea stock validando que no exista otro para el mismo libro."""
        if self.leer_por_libro(entidad.libro.id):
            raise RepositorioError(f"Ya existe stock para el libro con id {entidad.libro.id}.")
        return super().crear(entidad)

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Obtiene el registro de stock asociado a un libro."""
        with self.conexion.sesion() as sesion:
            consulta = (
                select(StockORM)
                .where(StockORM.libro_id == libro_id)
                .options(*self._opciones_carga())
            )
            registro = sesion.scalars(consulta).first()
            if registro is None:
                return None
            return self._a_entidad(registro)

    def actualizar(self, entidad: Stock) -> Stock:
        """Actualiza un registro de stock existente."""
        existente = self.leer_por_libro(entidad.libro.id)
        if existente and existente.id != entidad.id:
            raise RepositorioError(f"Ya existe otro registro de stock para el libro con id {entidad.libro.id}.")
        return super().actualizar(entidad)

    def eliminar(self, id: int) -> bool:
        """Elimina el stock de un libro, recibiendo el id del libro."""
        with self.conexion.sesion() as sesion:
            consulta = select(StockORM).where(StockORM.libro_id == id)
            registro = sesion.scalars(consulta).first()
            if registro is None:
                return False
            sesion.delete(registro)
            return True


class RepositorioCotizacionDolar(RepositorioBD[CotizacionDolar], IRepositorioCotizacionDolar):
    """Repositorio de cotizaciones del dólar por tipo y fecha."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Inicializa el repositorio de cotizaciones."""
        super().__init__(conexion, CotizacionDolarORM, CotizacionDolar)

    def _a_modelo(self, entidad: CotizacionDolar) -> CotizacionDolarORM:
        """Convierte una cotización en su registro ORM."""
        return _cotizacion_a_modelo(entidad)

    def _a_entidad(self, registro: CotizacionDolarORM) -> CotizacionDolar:
        """Construye una cotización desde su registro ORM."""
        return _cotizacion_a_entidad(registro)

    def _opciones_carga(self) -> List[Any]:
        """Carga anticipada del tipo y de las monedas de la cotización."""
        return [
            selectinload(CotizacionDolarORM.tipo),
            selectinload(CotizacionDolarORM.moneda_origen),
            selectinload(CotizacionDolarORM.moneda_destino),
        ]

    def crear(self, entidad: CotizacionDolar) -> CotizacionDolar:
        """Crea una cotización validando unicidad por tipo y fecha."""
        if self.leer_por_tipo_y_fecha(entidad.tipo, entidad.fecha.date()):
            raise RepositorioError("Ya existe una cotización para ese tipo y fecha.")
        return super().crear(entidad)

    def leer_por_tipo_y_fecha(
        self,
        tipo_id: Union[int, TipoCotizacion],
        fecha: date,
    ) -> Optional[CotizacionDolar]:
        """Busca cotización por tipo y fecha (ignorando hora)."""
        tipo = self._normalizar_tipo(tipo_id)
        with self.conexion.sesion() as sesion:
            consulta = (
                select(CotizacionDolarORM)
                .where(
                    CotizacionDolarORM.tipo_id == tipo.id,
                    func.date(CotizacionDolarORM.fecha) == fecha,
                )
                .options(*self._opciones_carga())
            )
            registro = sesion.scalars(consulta).first()
            if registro is None:
                return None
            return self._a_entidad(registro)

    def leer_historico_por_tipo(self, tipo_id: Union[int, TipoCotizacion]) -> List[CotizacionDolar]:
        """Lista histórico de cotizaciones para un tipo dado."""
        tipo = self._normalizar_tipo(tipo_id)
        with self.conexion.sesion() as sesion:
            consulta = (
                select(CotizacionDolarORM)
                .where(CotizacionDolarORM.tipo_id == tipo.id)
                .order_by(CotizacionDolarORM.fecha)
                .options(*self._opciones_carga())
            )
            return [self._a_entidad(registro) for registro in sesion.scalars(consulta).all()]

    def actualizar(self, entidad: CotizacionDolar) -> CotizacionDolar:
        """Actualiza una cotización existente por ID."""
        existente = self.leer_por_tipo_y_fecha(entidad.tipo, entidad.fecha.date())
        if existente and existente.id != entidad.id:
            raise RepositorioError("Ya existe otra cotización para ese tipo y fecha.")
        return super().actualizar(entidad)

    def eliminar(self, id: Union[int, TipoCotizacion], fecha: Optional[date] = None) -> bool:
        """Elimina una cotización por tipo y fecha."""
        if fecha is None:
            tipo = self._normalizar_tipo(id)
            cotizacion = self.leer_por_tipo_y_fecha(tipo, date.today())
            if cotizacion is None:
                return False
            return super().eliminar(cotizacion.id)
        tipo = self._normalizar_tipo(id)
        with self.conexion.sesion() as sesion:
            consulta = select(CotizacionDolarORM).where(
                CotizacionDolarORM.tipo_id == tipo.id,
                func.date(CotizacionDolarORM.fecha) == fecha,
            )
            registro = sesion.scalars(consulta).first()
            if registro is None:
                return False
            sesion.delete(registro)
            return True

    def _normalizar_tipo(self, tipo_id: Union[int, TipoCotizacion]) -> TipoCotizacion:
        """Normaliza el tipo de cotización recibido a una entidad TipoCotizacion."""
        if isinstance(tipo_id, TipoCotizacion):
            return tipo_id
        with self.conexion.sesion() as sesion:
            registro = sesion.get(TipoCotizacionORM, int(tipo_id))
            if registro is None:
                raise RepositorioError(f"No existe el tipo de cotización con id {tipo_id}.")
            return _tipo_cotizacion_a_entidad(registro)
