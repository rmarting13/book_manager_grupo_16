import json
import logging
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from cuspide_scraper.items import CuspideBook

LOGGER = logging.getLogger(__name__)


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
    """Descarta los libros repetidos, conservando el primero de cada ISBN."""

    def __init__(self) -> None:
        """Inicializa el conjunto de claves ya vistas."""
        self._vistos: set[str] = set()

    def process_item(self, item: CuspideBook) -> CuspideBook:
        """Descarta el item si su ISBN ya fue procesado.

        Args:
            item: Libro extraído del sitio.

        Returns:
            El item si es la primera aparición.

        Raises:
            DropItem: Si el ISBN ya fue procesado.
        """
        adapter = ItemAdapter(item)
        clave = adapter.get("isbn") or adapter.get("url")
        if not clave:
            raise DropItem(f"Sin ISBN ni URL: {adapter.get('titulo')!r}")
        if clave in self._vistos:
            raise DropItem(f"Duplicado: {adapter.get('titulo')!r}")
        self._vistos.add(str(clave))
        return item


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
        self._items.append(dict(ItemAdapter(item)))
        return item

    def close_spider(self) -> None:
        """Escribe los items acumulados en el archivo JSON."""
        carpeta = os.path.dirname(os.path.abspath(self._ruta))
        os.makedirs(carpeta, exist_ok=True)
        with open(self._ruta, "w", encoding="utf-8") as archivo:
            json.dump(self._items, archivo, indent=4, ensure_ascii=False)
        LOGGER.info("Se guardaron %s libros en %s", len(self._items), self._ruta)
