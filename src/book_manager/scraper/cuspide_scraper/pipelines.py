import csv
import json
import logging
import os
import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from cuspide_scraper.items import CuspideBook

LOGGER = logging.getLogger(__name__)

CABECERAS_ALERTAS = [
    "isbn_catalogo",
    "isbn_cuspide",
    "titulo_catalogo",
    "titulo_cuspide",
    "autor_catalogo",
    "autor_cuspide",
    "coincidencia",
    "moneda",
    "precio_catalogo",
    "precio_cuspide",
    "diferencia",
    "variacion_porcentual",
    "estado",
    "url",
]


class ValidacionPipeline:
    """Descarta los libros que no pertenecen al catálogo o están incompletos."""

    def __init__(
        self,
        titulos: Optional[List[str]] = None,
        isbns: Optional[List[str]] = None,
    ) -> None:
        """Inicializa el pipeline con los títulos e ISBN del catálogo.

        Args:
            titulos: Títulos que se aceptan. Si es ``None``, se leen de la base.
            isbns: ISBN que se aceptan. Si es ``None``, se leen de la base.
        """
        self._titulos = titulos
        self._isbns = isbns
        self._normalizados: Optional[set[str]] = None

    @classmethod
    def from_crawler(cls, crawler: Any) -> "ValidacionPipeline":
        """Construye el pipeline a partir de la configuración del crawler."""
        return cls(
            crawler.settings.getlist("CATALOGO_TITULOS") or None,
            crawler.settings.getlist("CATALOGO_ISBNS") or None,
        )

    @property
    def titulos(self) -> List[str]:
        """Títulos del catálogo aceptados por el pipeline."""
        if self._titulos is None:
            self._titulos, self._isbns = self._catalogo_desde_base()
        return self._titulos

    @property
    def isbns(self) -> List[str]:
        """ISBN del catálogo aceptados por el pipeline."""
        if self._isbns is None:
            self._titulos, self._isbns = self._catalogo_desde_base()
        return self._isbns

    @staticmethod
    def _catalogo_desde_base() -> tuple[List[str], List[str]]:
        """Lee los títulos e ISBN del catálogo desde la base de datos."""
        from dotenv import load_dotenv
        from book_manager.database.connection import ConexionDB
        from book_manager.repositories.repositories import RepositorioLibro

        load_dotenv()
        ruta = os.getenv("SQLALCHEMY_DATABASE_URL", "")
        password = os.getenv("SUPABASE_DB_PASSWORD", "")
        conexion = ConexionDB(ruta.replace("[YOUR-PASSWORD]", password), echo=False)
        try:
            libros = RepositorioLibro(conexion).leer_todos()
            return [l.titulo for l in libros], [l.isbn for l in libros]
        finally:
            conexion.cerrar()

    def process_item(self, item: CuspideBook) -> CuspideBook:
        """Valida que el libro pertenezca al catálogo y tenga datos mínimos.

        Args:
            item: Libro extraído del sitio.

        Returns:
            El item validado.

        Raises:
            DropItem: Si el libro no pertenece al catálogo o le faltan datos.
        """
        adapter = ItemAdapter(item)
        isbn = adapter.get("isbn", "")
        titulo = self._normalizar(adapter.get("titulo", ""))
        if isbn not in self.isbns and titulo not in self._titulos_normalizados:
            raise DropItem(
                f"Fuera del catálogo: {adapter.get('titulo')!r} (ISBN {isbn or 'sin ISBN'})"
            )
        if not adapter.get("precio"):
            raise DropItem(f"Sin precio: {adapter.get('titulo')!r}")
        return item

    @property
    def _titulos_normalizados(self) -> set[str]:
        """Títulos del catálogo normalizados para comparar."""
        if self._normalizados is None:
            self._normalizados = {self._normalizar(t) for t in self.titulos}
        return self._normalizados

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Normaliza un título para compararlo sin acentos ni mayúsculas.

        Args:
            texto: Título a normalizar.

        Returns:
            El título en minúsculas, sin acentos y sin signos de puntuación.
        """
        sin_acentos = unicodedata.normalize("NFKD", texto or "")
        sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9 ]", " ", sin_acentos.lower()).strip()



class DuplicadosPipeline:
    """Conserva un único libro por título y autor del catálogo.

    Un mismo título puede aparecer varias veces en el sitio (distintas
    ediciones o traducciones). Se guarda únicamente la primera aparición que
    coincide en título y autor con un libro del catálogo de la base de datos;
    el resto de los resultados se descarta.
    """

    def __init__(self, catalogo: Optional[List[Dict[str, str]]] = None) -> None:
        """Inicializa el pipeline con el catálogo de la base de datos.

        Args:
            catalogo: Libros del catálogo. Si es ``None``, se leen de la base.
        """
        self._catalogo = catalogo
        self._vistos: set[str] = set()

    @classmethod
    def from_crawler(cls, crawler: Any) -> "DuplicadosPipeline":
        """Construye el pipeline a partir de la configuración del crawler."""
        return cls()

    @property
    def catalogo(self) -> List[Dict[str, str]]:
        """Libros del catálogo con título y autor normalizados."""
        if self._catalogo is None:
            self._catalogo = self._catalogo_desde_base()
        return self._catalogo

    @staticmethod
    def _catalogo_desde_base() -> List[Dict[str, str]]:
        """Lee los títulos y autores del catálogo desde la base de datos."""
        from dotenv import load_dotenv
        from book_manager.database.connection import ConexionDB
        from book_manager.repositories.repositories import RepositorioLibro

        load_dotenv()
        ruta = os.getenv("SQLALCHEMY_DATABASE_URL", "")
        password = os.getenv("SUPABASE_DB_PASSWORD", "")
        conexion = ConexionDB(ruta.replace("[YOUR-PASSWORD]", password), echo=False)
        try:
            return [
                {
                    "titulo": libro.titulo,
                    "autor": libro.autor,
                    "titulo_norm": DuplicadosPipeline._normalizar(libro.titulo),
                    "autor_norm": DuplicadosPipeline._normalizar(libro.autor),
                }
                for libro in RepositorioLibro(conexion).leer_todos()
            ]
        finally:
            conexion.cerrar()

    def process_item(self, item: CuspideBook) -> CuspideBook:
        """Conserva el primer libro que coincide en título y autor con el catálogo.

        Args:
            item: Libro extraído del sitio.

        Returns:
            El item si es la primera aparición de un libro del catálogo.

        Raises:
            DropItem: Si el libro no coincide en título y autor con el catálogo
                o si ya se guardó otro resultado del mismo libro.
        """
        adapter = ItemAdapter(item)
        titulo = adapter.get("titulo", "")
        autor = adapter.get("autor", "")
        libro = self._buscar_en_catalogo(titulo, autor)
        if libro is None:
            raise DropItem(
                f"Sin coincidencia de título y autor en el catálogo: "
                f"{titulo!r} de {autor!r}"
            )
        clave = f"{libro['titulo_norm']}|{libro['autor_norm']}"
        if clave in self._vistos:
            raise DropItem(
                f"Duplicado: {titulo!r} de {autor!r} (ya se guardó "
                f"{libro['titulo']!r} de {libro['autor']!r})"
            )
        self._vistos.add(clave)
        return item

    def _buscar_en_catalogo(self, titulo: str, autor: str) -> Optional[Dict[str, str]]:
        """Busca en el catálogo el libro con el mismo título y autor.

        Args:
            titulo: Título del libro publicado en el sitio.
            autor: Autor del libro publicado en el sitio.

        Returns:
            El libro del catálogo, o ``None`` si no hay coincidencia exacta.
        """
        titulo_norm = self._normalizar(titulo)
        palabras_autor = set(self._normalizar(autor).split())
        if not titulo_norm or not palabras_autor:
            return None
        for libro in self.catalogo:
            if libro["titulo_norm"] != titulo_norm:
                continue
            if set(libro["autor_norm"].split()) == palabras_autor:
                return libro
        return None

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Normaliza un texto para compararlo sin acentos ni mayúsculas.

        Args:
            texto: Texto a normalizar.

        Returns:
            El texto en minúsculas, sin acentos y sin signos de puntuación.
        """
        sin_acentos = unicodedata.normalize("NFKD", texto or "")
        sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9 ]", " ", sin_acentos.lower()).strip()


class LimpiezaPipeline:
    """Completa y ordena los campos antes de persistir el item."""

    def process_item(self, item: CuspideBook) -> CuspideBook:
        """Normaliza los campos opcionales del libro.

        Args:
            item: Libro extraído del sitio.

        Returns:
            El item con los campos completos.
        """
        adapter = ItemAdapter(item)
        adapter.setdefault("moneda", "ARS")
        adapter.setdefault("precio_usd", "")
        adapter.setdefault("imagen_url", "")
        adapter.setdefault("formas_pago", "")
        adapter.setdefault("descripcion", "")
        # adapter.setdefault("especificaciones", "")
        adapter.setdefault("disponible", "")
        return item


class JsonPipeline:
    """Guarda todos los items en un único archivo JSON al finalizar."""

    def __init__(self, ruta: str) -> None:
        """Inicializa el pipeline con la ruta del archivo de salida.

        Args:
            ruta: Ruta del archivo JSON a generar.
        """
        self._ruta = ruta
        self._items: List[Dict[str, Any]] = []

    @classmethod
    def from_crawler(cls, crawler: Any) -> "JsonPipeline":
        """Construye el pipeline a partir de la configuración del crawler."""
        return cls(crawler.settings.get("CUSPIDE_JSON_PATH", "downloads/cuspide.json"))

    def open_spider(self) -> None:
        """Reinicia la lista de items al abrir el spider."""
        self._items = []

    def process_item(self, item: CuspideBook) -> CuspideBook:
        """Acumula el item para escribirlo al finalizar.

        Args:
            item: Libro extraído del sitio.

        Returns:
            El mismo item, sin modificaciones.
        """
        self._items.append(self._normalizar_item(dict(ItemAdapter(item))))
        return item

    @staticmethod
    def _normalizar_item(datos: Dict[str, Any]) -> Dict[str, Any]:
        """Asegura que el precio en dólares esté presente en el registro.

        Args:
            datos: Datos del item extraído del sitio.

        Returns:
            El registro con la clave ``precio_usd`` siempre definida.
        """
        datos.setdefault("precio_usd", "")
        datos["precio_usd"] = datos.get("precio_usd") or ""
        return datos

    def close_spider(self) -> None:
        """Escribe los items acumulados en el archivo JSON."""
        carpeta = os.path.dirname(os.path.abspath(self._ruta))
        os.makedirs(carpeta, exist_ok=True)
        with open(self._ruta, "w", encoding="utf-8") as archivo:
            json.dump(self._items, archivo, indent=4, ensure_ascii=False)
        LOGGER.info("Se guardaron %s libros en %s", len(self._items), self._ruta)


class AlertaPreciosPipeline:
    """Compara los precios del catálogo con los del sitio y genera un CSV de alertas.

    Recibe cada libro que ya pasó por :class:`JsonPipeline`, lo empareja con el
    catálogo de la base de datos y acumula una fila con la diferencia de precio
    y el estado de la alerta. El CSV se escribe al finalizar el spider.
    """

    def __init__(self, ruta: str) -> None:
        """Inicializa el pipeline con la ruta del archivo de salida.

        Args:
            ruta: Ruta del archivo CSV de alertas a generar.
        """
        self._ruta = ruta
        self._alertas: List[Dict[str, str]] = []
        self._catalogo: List[Dict[str, Any]] = []

    @classmethod
    def from_crawler(cls, crawler: Any) -> "AlertaPreciosPipeline":
        """Construye el pipeline a partir de la configuración del crawler."""
        fecha = datetime.now().strftime("%Y%m%d")
        ruta = crawler.settings.get(
            "CUSPIDE_ALERTAS_PATH", f"downloads/alertas_precios"
        )
        return cls(f"{ruta}_{fecha}.csv")

    def open_spider(self) -> None:
        """Reinicia las alertas y carga el catálogo desde la base."""
        self._alertas = []
        self._catalogo = self._cargar_catalogo()

    def process_item(self, item: CuspideBook) -> CuspideBook:
        """Compara el precio del libro con el del catálogo y acumula la alerta.

        Args:
            item: Libro extraído del sitio, ya procesado por ``JsonPipeline``.

        Returns:
            El mismo item, sin modificaciones.
        """
        self._alertas.append(self._comparar(dict(ItemAdapter(item))))
        return item

    def close_spider(self) -> None:
        """Escribe el CSV con las alertas acumuladas durante el rastreo."""
        self._escribir_csv()
        alertas = sum(1 for fila in self._alertas if fila["estado"].startswith("ALERTA"))
        LOGGER.info(
            "Se generaron %s alertas de precio (%s libros comparados) en %s",
            alertas,
            len(self._alertas),
            self._ruta,
        )

    def _comparar(self, libro: Dict[str, Any]) -> Dict[str, str]:
        """Compara un libro del sitio con su equivalente del catálogo."""
        isbn = str(libro.get("isbn") or "")
        titulo = str(libro.get("titulo") or "")
        autor = str(libro.get("autor") or "")
        precio_sitio = self._a_decimal(libro.get("precio"))
        precio_usd = self._a_decimal(libro.get("precio_usd"))

        coincidencia, catalogo = self._emparejar(titulo, autor)
        fila: Dict[str, str] = {
            "isbn_catalogo": str(catalogo.get("isbn", "")) if catalogo else "",
            "isbn_cuspide": isbn,
            "titulo_catalogo": str(catalogo.get("titulo", "")) if catalogo else "",
            "titulo_cuspide": titulo,
            "autor_catalogo": str(catalogo.get("autor", "")) if catalogo else "",
            "autor_cuspide": autor,
            "coincidencia": coincidencia,
            "moneda": str(libro.get("moneda") or "ARS"),
            "precio_cuspide": self._formatear(precio_sitio),
            "url": str(libro.get("url") or ""),
        }

        if precio_sitio is None:
            return {**fila, "estado": "SIN_PRECIO_SITIO"}

        if catalogo is None:
            return {**fila, "estado": "SIN_COINCIDENCIA_CATALOGO"}

        precio_catalogo = self._a_decimal(catalogo.get("precio"))
        if precio_catalogo is None:
            estado = "SIN_PRECIO_CATALOGO"
            if precio_usd is not None:
                estado = "SIN_PRECIO_CATALOGO_CON_USD"
            return {**fila, "estado": estado}

        diferencia = (precio_sitio - precio_catalogo).quantize(Decimal("0.01"))
        variacion = (
            (diferencia / precio_catalogo * 100).quantize(Decimal("0.01"))
            if precio_catalogo
            else Decimal("0")
        )
        if variacion > 0:
            estado = "ALERTA_SUBE"
        elif variacion < 0:
            estado = "ALERTA_BAJA"
        else:
            estado = "SIN_CAMBIOS"
        return {
            **fila,
            "precio_catalogo": self._formatear(precio_catalogo),
            "diferencia": self._formatear(diferencia),
            "variacion_porcentual": self._formatear(variacion),
            "estado": estado,
        }

    def _emparejar(
        self, titulo: str, autor: str
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """Busca el libro del catálogo por título y autor.

        Args:
            titulo: Título del libro publicado en el sitio.
            autor: Autor del libro publicado en el sitio.

        Returns:
            Una tupla con el criterio de coincidencia y el libro del catálogo.
            El criterio es ``TITULO_AUTOR`` si coinciden ambos campos,
            ``TITULO`` si solo coincide el título y ``SIN_COINCIDENCIA`` si no
            se encontró el libro.
        """
        titulo_norm = self._normalizar(titulo)
        autor_norm = self._normalizar(autor)
        if not titulo_norm:
            return "SIN_COINCIDENCIA", None

        candidatos = [l for l in self._catalogo if l["titulo_norm"] == titulo_norm]
        if not candidatos:
            return "SIN_COINCIDENCIA", None

        if autor_norm:
            for libro in candidatos:
                if libro["autor_norm"] == autor_norm:
                    return "TITULO_AUTOR", libro
            for libro in candidatos:
                if autor_norm in libro["autor_norm"] or libro["autor_norm"] in autor_norm:
                    return "TITULO_AUTOR", libro

        return "TITULO", candidatos[0]

    def _escribir_csv(self) -> None:
        """Escribe el archivo CSV con las alertas acumuladas."""
        carpeta = os.path.dirname(os.path.abspath(self._ruta))
        os.makedirs(carpeta, exist_ok=True)
        with open(self._ruta, "w", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=CABECERAS_ALERTAS)
            escritor.writeheader()
            for fila in self._alertas:
                escritor.writerow({c: fila.get(c, "") for c in CABECERAS_ALERTAS})

    def _cargar_catalogo(self) -> List[Dict[str, Any]]:
        """Carga desde la base los libros del catálogo con su precio en ARS."""
        try:
            from dotenv import load_dotenv

            from book_manager.database.connection import ConexionDB
            from book_manager.repositories.repositories import (
                RepositorioLibro,
                RepositorioMoneda,
                RepositorioPrecio,
            )
            from book_manager.services.services import ServicioPrecio

            load_dotenv()
            ruta_bd = os.getenv("SQLALCHEMY_DATABASE_URL", "")
            password = os.getenv("SUPABASE_DB_PASSWORD", "")
            conexion = ConexionDB(ruta_bd.replace("[YOUR-PASSWORD]", password), echo=False)
            try:
                repo_moneda = RepositorioMoneda(conexion)
                repo_precio = RepositorioPrecio(conexion)
                repo_libro = RepositorioLibro(conexion)
                servicio = ServicioPrecio(repo_precio, repo_libro, repo_moneda)
                monedas = {m.codigo: m for m in repo_moneda.leer_todos()}
                moneda = monedas.get("ARS") or next(iter(monedas.values()), None)
                if moneda is None:
                    LOGGER.warning("No hay monedas cargadas: no se pueden comparar precios.")
                    return []
                catalogo: List[Dict[str, Any]] = []
                for libro in repo_libro.leer_todos():
                    precio = servicio.obtener_vigente(libro.id, moneda.id)
                    catalogo.append({
                        "isbn": libro.isbn,
                        "titulo": libro.titulo,
                        "autor": libro.autor,
                        "titulo_norm": self._normalizar(libro.titulo),
                        "autor_norm": self._normalizar(libro.autor),
                        "precio": str(precio.valor) if precio else "",
                    })
                return catalogo
            finally:
                conexion.cerrar()
        except Exception as error:
            LOGGER.warning("No se pudo cargar el catálogo para comparar precios: %s", error)
            return []

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Normaliza un texto para compararlo sin acentos ni mayúsculas."""
        sin_acentos = unicodedata.normalize("NFKD", texto or "")
        sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9 ]", " ", sin_acentos.lower()).strip()

    @staticmethod
    def _a_decimal(valor: Any) -> Optional[Decimal]:
        """Convierte un precio a Decimal, o None si no es válido."""
        if valor is None or valor == "":
            return None
        try:
            return Decimal(str(valor))
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _formatear(valor: Optional[Decimal]) -> str:
        """Formatea un Decimal para el CSV, dejando vacío si no hay valor."""
        return f"{valor:.2f}" if valor is not None else ""
