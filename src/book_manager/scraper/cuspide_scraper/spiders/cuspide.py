import logging
import os
from datetime import datetime
from typing import Any, AsyncIterator, Iterator, List, Optional
from urllib.parse import quote_plus
from scrapy import Request, Spider
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse
from cuspide_scraper.items import CuspideBook
from cuspide_scraper.loaders import CuspideBookLoader

LOGGER = logging.getLogger(__name__)


class CuspideSpider(Spider):
    """Busca cada libro del catálogo en Cúspide y extrae su ficha.

    Para cada título del catálogo se consulta el buscador del sitio, se toman
    los primeros ``max_resultados`` resultados y se visita cada ficha para
    extraer precio, imagen, formas de pago y descripción.

    Attributes:
        name: Nombre del spider usado por el comando ``scrapy crawl``.
        max_resultados: Cantidad máxima de resultados por búsqueda.
    """

    name = "cuspide"
    allowed_domains = ["cuspide.com"]

    custom_settings = {
        "CUSPIDE_JSON_PATH": "downloads/cuspide.json",
    }

    def __init__(   self, 
                    titulos: Optional[str] = None, 
                    max_resultados: int = 10, 
                    *args: Any, 
                    **kwargs: Any   ) -> None:
        """Inicializa el spider con los títulos a buscar.

        Args:
            titulos: Títulos separados por ``|``. Si se omite, se leen de la base.
            max_resultados: Cantidad máxima de resultados por búsqueda.
        """
        super().__init__(*args, **kwargs)
        self._titulos_argumento = titulos
        self.max_resultados = int(max_resultados)

    @property
    def titulos(self) -> List[str]:
        """Títulos del catálogo que se van a buscar."""
        if self._titulos_argumento:
            return [t.strip() for t in self._titulos_argumento.split("|") if t.strip()]
        return self._titulos_desde_base()

    @staticmethod
    def _titulos_desde_base() -> List[str]:
        """Lee los títulos del catálogo desde la base de datos."""
        from dotenv import load_dotenv
        from book_manager.database.connection import ConexionDB
        from book_manager.repositories.repositories import RepositorioLibro

        load_dotenv()
        ruta = os.getenv("SQLALCHEMY_DATABASE_URL", "")
        password = os.getenv("SUPABASE_DB_PASSWORD", "")
        conexion = ConexionDB(ruta.replace("[YOUR-PASSWORD]", password), echo=False)
        try:
            return [libro.titulo for libro in RepositorioLibro(conexion).leer_todos()]
        finally:
            conexion.cerrar()

    def start_requests(self) -> Iterator[Request]:
        """Genera una búsqueda por cada título del catálogo.

        Yields:
            Request: Petición al buscador del sitio para un título.
        """
        for titulo in self.titulos:
            url = f"https://cuspide.com/?s={quote_plus(titulo)}&post_type=product"
            yield Request(  url=url,
                            callback=self.parse_busqueda,
                            cb_kwargs={"titulo_buscado": titulo},
                            dont_filter=True )

    async def start(self) -> AsyncIterator[Request]:
        """Punto de entrada del spider en Scrapy 2.13 y posteriores.

        Yields:
            Request: Petición al buscador del sitio para un título.
        """
        for peticion in self.start_requests():
            yield peticion

    def parse_busqueda(self, response: Response, titulo_buscado: str) -> Iterator[Request]:
        """Extrae los primeros resultados de una búsqueda y pide sus fichas.

        Args:
            response: Respuesta del buscador.
            titulo_buscado: Título del catálogo que originó la búsqueda.

        Yields:
            Request: Petición a la ficha de cada resultado.
        """
        enlaces = response.css("div.product-small a[href*='/producto/']::attr(href)").getall()
        vistos: List[str] = []
        for enlace in enlaces:
            if enlace not in vistos:
                vistos.append(enlace)
        seleccionados = vistos[: self.max_resultados]
        self.logger.info(
            "Búsqueda %r: %s resultados, se visitan %s",
            titulo_buscado,
            len(vistos),
            len(seleccionados),
        )
        for enlace in seleccionados:
            yield response.follow(
                enlace,
                callback=self.parse_libro,
                cb_kwargs={"titulo_buscado": titulo_buscado},
            )

    def parse_libro(self, response: Response, titulo_buscado: str) -> Iterator[CuspideBook]:
        """Extrae los datos de la ficha de un libro.

        Args:
            response: Respuesta de la ficha del libro.
            titulo_buscado: Título del catálogo que originó la búsqueda.

        Yields:
            CuspideBook: Libro con precio, imagen, formas de pago y descripción.
        """
        if not isinstance(response, TextResponse):
            raise TypeError(f"Se esperaba una respuesta de texto, se recibió {type(response).__name__}.")
        loader = CuspideBookLoader(item=CuspideBook(), response=response)
        loader.add_value("titulo_buscado", titulo_buscado)
        loader.add_css("titulo", "h1.product-title::text")
        loader.add_css("autor", "div.product-summary span a::text")
        loader.add_css("url", "link[rel='canonical']::attr(href)")
        loader.add_css("precio", "p.price span.woocommerce-Price-amount bdi::text")
        loader.add_css("moneda", "span.woocommerce-Price-currencySymbol::text")
        loader.add_css("precio_usd", "div.product-summary span[style*='1.1em'] span::text")
        loader.add_css("imagen_url", "div.product-gallery img::attr(src)")
        loader.add_css("descripcion", "p.livriz-text-synopsis::text")
        loader.add_css("isbn", "p.livriz-code::text")
        loader.add_css("disponible", "p.stock.in-stock::text")
        loader.add_css("formas_pago", "div#contentPaymentsPopUpArg ul li::text")
        loader.add_value("consultado", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        yield loader.load_item()


# =============================================================================
# Pruebas unitarias desde la terminal
# =============================================================================
#
# Todos los comandos se ejecutan desde la carpeta del proyecto Scrapy: cd src/book_manager/scraper
#
# 1. Buscar todos los libros del catálogo (lee los títulos de la base de datos):
# scrapy crawl cuspide
#
# Requiere que el archivo .env de la raíz del proyecto tenga configuradas
# SQLALCHEMY_DATABASE_URL y SUPABASE_DB_PASSWORD.
#
# 2. Buscar títulos puntuales, sin consultar la base de datos:
# scrapy crawl cuspide -a "titulos=Maus|Rayuela"
#
# Los títulos se separan con el carácter |.
#
# 3. Cambiar la cantidad de resultados por búsqueda:
# scrapy crawl cuspide -a max_resultados=5
#
# Por defecto se visitan los primeros 10 resultados de cada búsqueda.
# Se puede combinar con -a titulos:
# scrapy crawl cuspide -a "titulos=Maus" -a max_resultados=3
#
# 4. Guardar el resultado en un archivo:
# scrapy crawl cuspide -O downloads/cuspide.json
# scrapy crawl cuspide -o prueba.csv
#
# -O sobrescribe el archivo; -o agrega al final del archivo existente.
# El pipeline JsonPipeline también escribe downloads/cuspide.json al terminar.
