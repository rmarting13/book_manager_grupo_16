import abc
import csv
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Generic, List, Optional, Type, TypeVar, Union

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

T = TypeVar('T', bound=EntidadBase)


def _asegurar_csv(ruta: str, columnas: List[str]) -> None:
    """Crea el directorio y el CSV con encabezado si todavía no existe."""
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    if not os.path.exists(ruta):
        _escribir_csv(ruta, columnas, [])


def _leer_csv(ruta: str) -> List[Dict[str, str]]:
    """Lee un CSV y devuelve sus filas como diccionarios."""
    with open(ruta, "r", encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def _escribir_csv(ruta: str, columnas: List[str], filas: List[Dict[str, str]]) -> None:
    """Reemplaza el contenido de un CSV con las filas indicadas."""
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)



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
  def crear(self, stock: Stock) -> Stock:
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
  def actualizar(self, stock: 'Stock') -> 'Stock':
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
  def eliminar(self, libro_id: int) -> bool:
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
  def crear(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
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
  def actualizar(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
    """Actualiza una cotización de dólar existente.

    Args:
        cotizacion (CotizacionDolar): El objeto CotizacionDolar a actualizar.

    Returns:
        CotizacionDolar: El objeto CotizacionDolar actualizado.
    """
    pass

  @abc.abstractmethod
  def eliminar(self, tipo_id: int, fecha: date) -> bool:
    """Elimina una cotización de dólar por tipo y fecha.

    Args:
        tipo_id (int): El ID del tipo de cotización.
        fecha (date): La fecha de la cotización a eliminar.

    Returns:
        bool: True si la cotización fue eliminada, False si no se encontró.
    """
    pass

class RepositorioError(ValueError):
        """
            Clase de error a nivel de persistencia de datos.
        """

class RepositorioCSV(IRepositorio[T], Generic[T]):
    """Repositorio base para entidades persistidas en formato CSV."""

    def __init__(self, ruta_archivo: str, entidad_cls: Type[T]) -> None:
        """Inicializa el repositorio con su ruta y clase de entidad."""
        self.ruta_archivo = ruta_archivo
        self.entidad_cls = entidad_cls
        self._asegurar_archivo()

    def _asegurar_archivo(self) -> None:
        """Crea el directorio y el CSV con encabezado si todavía no existe."""
        os.makedirs(os.path.dirname(self.ruta_archivo) or ".", exist_ok=True)
        if not os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, "w", encoding="utf-8", newline="") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=self._columnas())
                escritor.writeheader()

    @abc.abstractmethod
    def _columnas(self) -> List[str]:
        """Devuelve los nombres de columnas del CSV."""

    @abc.abstractmethod
    def _a_fila(self, entidad: T) -> Dict[str, str]:
        """Convierte una entidad en fila serializable para CSV."""

    @abc.abstractmethod
    def _desde_fila(self, fila: Dict[str, str]) -> T:
        """Reconstruye una entidad a partir de una fila de CSV."""

    def _leer_filas(self) -> List[Dict[str, str]]:
        """Lee todas las filas del CSV y devuelve una lista de diccionarios."""
        with open(self.ruta_archivo, "r", encoding="utf-8", newline="") as archivo:
            lector = csv.DictReader(archivo)
            return list(lector)

    def _escribir_filas(self, filas: List[Dict[str, str]]) -> None:
        """Reemplaza el contenido del CSV con las filas indicadas."""
        with open(self.ruta_archivo, "w", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=self._columnas())
            escritor.writeheader()
            escritor.writerows(filas)

    def _siguiente_id(self) -> int:
        """Obtiene el siguiente identificador disponible."""
        ids = [int(fila["id"]) for fila in self._leer_filas() if fila.get("id")]
        return (max(ids) + 1) if ids else 1

    def crear(self, entidad: T) -> T:
        """Crea una entidad, asignando ID automático cuando llega con 0."""
        filas = self._leer_filas()
        ids_existentes = {int(fila["id"]) for fila in filas if fila.get("id")}
        if entidad.id == 0:
            entidad = entidad.model_copy(update={"id": self._siguiente_id()})
        elif entidad.id in ids_existentes:
            raise RepositorioError(f"Ya existe un registro con id {entidad.id}.")

        filas.append(self._a_fila(entidad))
        self._escribir_filas(filas)
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        """Busca una entidad por su ID."""
        for fila in self._leer_filas():
            if int(fila["id"]) == id:
                return self._desde_fila(fila)
        return None

    def leer_todos(self) -> List[T]:
        """Lee y reconstruye todas las entidades del repositorio."""
        return [self._desde_fila(fila) for fila in self._leer_filas()]

    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente por ID."""
        filas = self._leer_filas()
        encontrada = False
        for indice, fila in enumerate(filas):
            if int(fila["id"]) == entidad.id:
                filas[indice] = self._a_fila(entidad)
                encontrada = True
                break
        if not encontrada:
            raise RepositorioError(f"No existe un registro con id {entidad.id} para actualizar.")
        self._escribir_filas(filas)
        return entidad

    def eliminar(self, id: int) -> bool:
        """Elimina una entidad por ID, retornando True si hubo cambios."""
        filas = self._leer_filas()
        filas_filtradas = [fila for fila in filas if int(fila["id"]) != id]
        if len(filas_filtradas) == len(filas):
            return False
        self._escribir_filas(filas_filtradas)
        return True


class RepositorioMoneda(RepositorioCSV[Moneda]):
    """Repositorio CSV de monedas."""

    def __init__(self, ruta_archivo: str) -> None:
        """Inicializa el repositorio de monedas."""
        super().__init__(ruta_archivo, Moneda)

    def _columnas(self) -> List[str]:
        """Define columnas del archivo de monedas."""
        return ["id", "codigo", "nombre", "simbolo"]

    def _a_fila(self, entidad: Moneda) -> Dict[str, str]:
        """Serializa una moneda a fila CSV."""
        return {
            "id": str(entidad.id),
            "codigo": entidad.codigo,
            "nombre": entidad.nombre,
            "simbolo": entidad.simbolo,
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Moneda:
        """Construye una moneda desde una fila CSV."""
        return Moneda(
            id=int(fila["id"]),
            codigo=fila["codigo"],
            nombre=fila["nombre"],
            simbolo=fila["simbolo"],
        )


class RepositorioGenero(RepositorioCSV[Genero]):
    """Repositorio CSV de géneros literarios."""

    def __init__(self, ruta_archivo: str) -> None:
        """Inicializa el repositorio de géneros."""
        super().__init__(ruta_archivo, Genero)

    def _columnas(self) -> List[str]:
        """Define columnas del archivo de géneros."""
        return ["id", "tipo", "nombre_personalizado", "descripcion"]

    def _a_fila(self, entidad: Genero) -> Dict[str, str]:
        """Serializa un género a fila CSV."""
        return {
            "id": str(entidad.id),
            "tipo": entidad.tipo.value,
            "nombre_personalizado": entidad.nombre_personalizado or "",
            "descripcion": entidad.descripcion or "",
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Genero:
        """Construye un género desde una fila CSV."""
        return Genero(
            id=int(fila["id"]),
            tipo=GeneroLiterario(fila["tipo"]),
            nombre_personalizado=fila["nombre_personalizado"] or None,
            descripcion=fila["descripcion"] or None,
        )


class RepositorioEditorial(RepositorioCSV[Editorial]):
    """Repositorio CSV de editoriales."""

    def __init__(self, ruta_archivo: str) -> None:
        """Inicializa el repositorio de editoriales."""
        super().__init__(ruta_archivo, Editorial)

    def _columnas(self) -> List[str]:
        """Define columnas del archivo de editoriales."""
        return ["id", "nombre", "pais_origen", "email", "telefono", "sitio_web"]

    def _a_fila(self, entidad: Editorial) -> Dict[str, str]:
        """Serializa una editorial a fila CSV."""
        return {
            "id": str(entidad.id),
            "nombre": entidad.nombre,
            "pais_origen": entidad.pais_origen,
            "email": str(entidad.email) if entidad.email else "",
            "telefono": entidad.telefono or "",
            "sitio_web": str(entidad.sitio_web) if entidad.sitio_web else "",
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Editorial:
        """Construye una editorial desde una fila CSV."""
        return Editorial(
            id=int(fila["id"]),
            nombre=fila["nombre"],
            pais_origen=fila["pais_origen"],
            email=fila["email"] or None,
            telefono=fila["telefono"] or None,
            sitio_web=fila["sitio_web"] or None,
        )


class RepositorioLibro(RepositorioCSV[Libro]):
    """Repositorio CSV de libros con relaciones a editorial y género."""

    def __init__(self, ruta_archivo: str, repo_editorial: RepositorioEditorial, repo_genero: RepositorioGenero) -> None:
        """Inicializa el repositorio con sus dependencias relacionadas."""
        self.repo_editorial = repo_editorial
        self.repo_genero = repo_genero
        super().__init__(ruta_archivo, Libro)

    def _columnas(self) -> List[str]:
        """Define columnas del archivo de libros."""
        return [
            "id",
            "isbn",
            "titulo",
            "autor",
            "editorial_id",
            "genero_id",
            "edicion",
            "anio_publicacion",
            "idioma",
            "paginas",
        ]

    def _a_fila(self, entidad: Libro) -> Dict[str, str]:
        """Serializa un libro a fila CSV."""
        return {
            "id": str(entidad.id),
            "isbn": entidad.isbn,
            "titulo": entidad.titulo,
            "autor": entidad.autor,
            "editorial_id": str(entidad.editorial.id),
            "genero_id": str(entidad.genero.id),
            "edicion": str(entidad.edicion),
            "idioma": entidad.idioma,
            "paginas": "" if entidad.paginas is None else str(entidad.paginas),
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Libro:
        """Construye un libro desde una fila CSV, resolviendo sus relaciones."""
        editorial = self.repo_editorial.leer_por_id(int(fila["editorial_id"]))
        genero = self.repo_genero.leer_por_id(int(fila["genero_id"]))
        if not editorial or not genero:
            raise RepositorioError("No se pudo reconstruir el libro por referencias inexistentes.")
        return Libro(
            id=int(fila["id"]),
            isbn=fila["isbn"],
            titulo=fila["titulo"],
            autor=fila["autor"],
            editorial=editorial,
            genero=genero,
            edicion=int(fila["edicion"]),
            idioma=fila["idioma"],
            paginas=int(fila["paginas"]) if fila["paginas"] else None,
        )


class RepositorioPrecio(RepositorioCSV[Precio]):
    """Repositorio CSV de precios con relaciones a libro y moneda."""

    def __init__(self, ruta_archivo: str, repo_libro: RepositorioLibro, repo_moneda: RepositorioMoneda) -> None:
        """Inicializa el repositorio de precios con sus dependencias."""
        self.repo_libro = repo_libro
        self.repo_moneda = repo_moneda
        super().__init__(ruta_archivo, Precio)

    def _columnas(self) -> List[str]:
        """Define columnas del archivo de precios."""
        return ["id", "libro_id", "moneda_id", "valor", "fecha_vigencia"]

    def _a_fila(self, entidad: Precio) -> Dict[str, str]:
        """Serializa un precio a fila CSV."""
        return {
            "id": str(entidad.id),
            "libro_id": str(entidad.libro.id),
            "moneda_id": str(entidad.moneda.id),
            "valor": str(entidad.valor),
            "fecha_vigencia": entidad.fecha_vigencia.isoformat(),
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Precio:
        """Construye un precio desde una fila CSV."""
        libro = self.repo_libro.leer_por_id(int(fila["libro_id"]))
        moneda = self.repo_moneda.leer_por_id(int(fila["moneda_id"]))
        if not libro or not moneda:
            raise RepositorioError("No se pudo reconstruir el precio por referencias inexistentes.")
        return Precio(
            id=int(fila["id"]),
            libro=libro,
            moneda=moneda,
            valor=Decimal(fila["valor"]),
            fecha_vigencia=date.fromisoformat(fila["fecha_vigencia"]),
        )


class RepositorioStock(IRepositorioStock):
    """Repositorio CSV de stock con unicidad por libro."""

    def __init__(self, ruta_archivo: str, repo_libro: RepositorioLibro) -> None:
        """Inicializa el repositorio de stock con acceso a libros."""
        self.ruta_archivo = ruta_archivo
        self.repo_libro = repo_libro
        _asegurar_csv(self.ruta_archivo, self._columnas())

    def _columnas(self) -> List[str]:
        """Define columnas del archivo de stock."""
        return ["id", "libro_id", "cantidad", "stock_minimo", "fecha_ultimo_ingreso"]

    def _a_fila(self, entidad: Stock) -> Dict[str, str]:
        """Serializa un registro de stock a fila CSV."""
        return {
            "id": str(entidad.id),
            "libro_id": str(entidad.libro.id),
            "cantidad": str(entidad.cantidad),
            "stock_minimo": str(entidad.stock_minimo),
            "fecha_ultimo_ingreso": entidad.fecha_ultimo_ingreso.isoformat() if entidad.fecha_ultimo_ingreso else "",
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Stock:
        """Reconstruye un registro de stock desde CSV."""
        libro = self.repo_libro.leer_por_id(int(fila["libro_id"]))
        if not libro:
            raise RepositorioError("No se pudo reconstruir el stock por libro inexistente.")
        return Stock(
            id=int(fila["id"]),
            libro=libro,
            cantidad=int(fila["cantidad"]),
            stock_minimo=int(fila["stock_minimo"]),
            fecha_ultimo_ingreso=date.fromisoformat(fila["fecha_ultimo_ingreso"]) if fila["fecha_ultimo_ingreso"] else None,
        )

    def crear(self, stock: Stock) -> Stock:
        """Crea stock validando que no exista otro para el mismo libro."""
        if self.leer_por_libro(stock.libro.id):
            raise RepositorioError(f"Ya existe stock para el libro con id {stock.libro.id}.")
        filas = _leer_csv(self.ruta_archivo)
        ids_existentes = {int(fila["id"]) for fila in filas if fila.get("id")}
        if stock.id == 0:
            stock = stock.model_copy(update={"id": max(ids_existentes, default=0) + 1})
        elif stock.id in ids_existentes:
            raise RepositorioError(f"Ya existe un registro de stock con id {stock.id}.")
        filas.append(self._a_fila(stock))
        _escribir_csv(self.ruta_archivo, self._columnas(), filas)
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Obtiene el registro de stock asociado a un libro."""
        for fila in _leer_csv(self.ruta_archivo):
            if int(fila["libro_id"]) == libro_id:
                return self._desde_fila(fila)
        return None

    def leer_todos(self) -> List[Stock]:
        """Lee todos los registros de stock."""
        return [self._desde_fila(fila) for fila in _leer_csv(self.ruta_archivo)]

    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza un registro de stock existente."""
        existente = self.leer_por_libro(stock.libro.id)
        if existente and existente.id != stock.id:
            raise RepositorioError(f"Ya existe otro registro de stock para el libro con id {stock.libro.id}.")
        filas = _leer_csv(self.ruta_archivo)
        for indice, fila in enumerate(filas):
            if int(fila["id"]) == stock.id:
                filas[indice] = self._a_fila(stock)
                _escribir_csv(self.ruta_archivo, self._columnas(), filas)
                return stock
        raise RepositorioError(f"No existe un registro de stock con id {stock.id} para actualizar.")

    def eliminar(self, libro_id: int) -> bool:
        """Elimina el stock de un libro por su ID de libro."""
        filas = _leer_csv(self.ruta_archivo)
        filas_filtradas = [fila for fila in filas if int(fila["libro_id"]) != libro_id]
        if len(filas_filtradas) == len(filas):
            return False
        _escribir_csv(self.ruta_archivo, self._columnas(), filas_filtradas)
        return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Repositorio CSV de cotizaciones del dólar por tipo y fecha."""

    def __init__(self, ruta_archivo: str, repo_moneda: RepositorioMoneda) -> None:
        """Inicializa el repositorio de cotizaciones con acceso a monedas."""
        self.ruta_archivo = ruta_archivo
        self.repo_moneda = repo_moneda
        _asegurar_csv(self.ruta_archivo, self._columnas())

    def _columnas(self) -> List[str]:
        """Define columnas del archivo de cotizaciones."""
        return [
            "id",
            "tipo",
            "moneda_origen_id",
            "moneda_destino_id",
            "valor_compra",
            "valor_venta",
            "fecha",
        ]

    def _a_fila(self, entidad: CotizacionDolar) -> Dict[str, str]:
        """Serializa una cotización a fila CSV."""
        return {
            "id": str(entidad.id),
            "tipo": entidad.tipo.value,
            "moneda_origen_id": str(entidad.moneda_origen.id),
            "moneda_destino_id": str(entidad.moneda_destino.id),
            "valor_compra": str(entidad.valor_compra),
            "valor_venta": str(entidad.valor_venta),
            "fecha": entidad.fecha.isoformat(),
        }

    def _desde_fila(self, fila: Dict[str, str]) -> CotizacionDolar:
        """Reconstruye una cotización desde CSV."""
        moneda_origen = self.repo_moneda.leer_por_id(int(fila["moneda_origen_id"]))
        moneda_destino = self.repo_moneda.leer_por_id(int(fila["moneda_destino_id"]))
        if not moneda_origen or not moneda_destino:
            raise RepositorioError("No se pudo reconstruir la cotización por monedas inexistentes.")
        return CotizacionDolar(
            id=int(fila["id"]),
            tipo=TipoCotizacion(fila["tipo"]),
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            valor_compra=Decimal(fila["valor_compra"]),
            valor_venta=Decimal(fila["valor_venta"]),
            fecha=datetime.fromisoformat(fila["fecha"]),
        )

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea una cotización validando unicidad por tipo y fecha."""
        if self.leer_por_tipo_y_fecha(cotizacion.tipo, cotizacion.fecha.date()):
            raise RepositorioError("Ya existe una cotización para ese tipo y fecha.")
        filas = _leer_csv(self.ruta_archivo)
        ids_existentes = {int(fila["id"]) for fila in filas if fila.get("id")}
        if cotizacion.id == 0:
            cotizacion = cotizacion.model_copy(update={"id": max(ids_existentes, default=0) + 1})
        elif cotizacion.id in ids_existentes:
            raise RepositorioError(f"Ya existe una cotización con id {cotizacion.id}.")
        filas.append(self._a_fila(cotizacion))
        _escribir_csv(self.ruta_archivo, self._columnas(), filas)
        return cotizacion

    def leer_por_tipo_y_fecha(
        self,
        tipo_id: Union[int, TipoCotizacion, str],
        fecha: date,
    ) -> Optional[CotizacionDolar]:
        """Busca cotización por tipo y fecha (ignorando hora)."""
        tipo = self._normalizar_tipo(tipo_id)
        for fila in _leer_csv(self.ruta_archivo):
            fecha_fila = datetime.fromisoformat(fila["fecha"]).date()
            if fila["tipo"] == tipo.value and fecha_fila == fecha:
                return self._desde_fila(fila)
        return None

    def leer_historico_por_tipo(self, tipo_id: Union[int, TipoCotizacion, str]) -> List[CotizacionDolar]:
        """Lista histórico de cotizaciones para un tipo dado."""
        tipo = self._normalizar_tipo(tipo_id)
        cotizaciones = [
            self._desde_fila(fila) for fila in _leer_csv(self.ruta_archivo) if fila["tipo"] == tipo.value
        ]
        return sorted(cotizaciones, key=lambda c: c.fecha)

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza una cotización existente por ID."""
        existente = self.leer_por_tipo_y_fecha(cotizacion.tipo, cotizacion.fecha.date())
        if existente and existente.id != cotizacion.id:
            raise RepositorioError("Ya existe otra cotización para ese tipo y fecha.")
        filas = _leer_csv(self.ruta_archivo)
        for indice, fila in enumerate(filas):
            if int(fila["id"]) == cotizacion.id:
                filas[indice] = self._a_fila(cotizacion)
                _escribir_csv(self.ruta_archivo, self._columnas(), filas)
                return cotizacion
        raise RepositorioError(f"No existe una cotización con id {cotizacion.id} para actualizar.")

    def eliminar(self, tipo_id: Union[int, TipoCotizacion, str], fecha: date) -> bool:
        """Elimina una cotización por tipo y fecha."""
        tipo = self._normalizar_tipo(tipo_id)
        filas = _leer_csv(self.ruta_archivo)
        filas_filtradas = [
            fila
            for fila in filas
            if not (fila["tipo"] == tipo.value and datetime.fromisoformat(fila["fecha"]).date() == fecha)
        ]
        if len(filas_filtradas) == len(filas):
            return False
        _escribir_csv(self.ruta_archivo, self._columnas(), filas_filtradas)
        return True

    def _normalizar_tipo(self, tipo_id: Union[int, TipoCotizacion, str]) -> TipoCotizacion:
        """Normaliza el tipo de cotización recibido a enum TipoCotizacion."""
        if isinstance(tipo_id, TipoCotizacion):
            return tipo_id
        if isinstance(tipo_id, int):
            opciones = list(TipoCotizacion)
            if 0 <= tipo_id < len(opciones):
                return opciones[tipo_id]
            raise RepositorioError("Índice de tipo de cotización fuera de rango.")
        for tipo in TipoCotizacion:
            if tipo.value.lower() == str(tipo_id).strip().lower() or tipo.name.lower() == str(tipo_id).strip().lower():
                return tipo
        raise RepositorioError(f"Tipo de cotización inválido: {tipo_id}.")
