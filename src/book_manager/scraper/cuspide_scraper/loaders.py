import re
from decimal import Decimal, InvalidOperation
from typing import Optional
from itemloaders.processors import Join, MapCompose, TakeFirst
from scrapy.loader import ItemLoader
from cuspide_scraper.items import CuspideBook


def limpiar_espacios(valor: Optional[str]) -> str:
    """Colapsa los espacios y saltos de línea de un texto.

    Args:
        valor: Texto extraído del HTML.

    Returns:
        El texto sin espacios repetidos, o una cadena vacía.
    """
    if not valor:
        return ""
    return re.sub(r"\s+", " ", valor).strip()


def normalizar_precio(valor: Optional[str]) -> str:
    """Convierte un precio con formato argentino en un decimal con punto.

    Args:
        valor: Texto del precio, por ejemplo ``$ 32.999,00``.

    Returns:
        El precio normalizado, por ejemplo ``32999.00``, o una cadena vacía.
    """
    if not valor:
        return ""
    limpio = re.sub(r"[^0-9,.]", "", valor)
    if not limpio:
        return ""
    limpio = limpio.replace(".", "").replace(",", ".")
    try:
        return str(Decimal(limpio).quantize(Decimal("0.01")))
    except InvalidOperation:
        return ""


def normalizar_isbn(valor: Optional[str]) -> str:
    """Deja únicamente los dígitos de un ISBN.

    Args:
        valor: Texto que contiene el ISBN.

    Returns:
        El ISBN sin guiones ni espacios.
    """
    if not valor:
        return ""
    return re.sub(r"[^0-9Xx]", "", valor).upper()


def normalizar_url(valor: Optional[str]) -> str:
    """Completa una URL relativa con el dominio del sitio.

    Args:
        valor: URL absoluta o relativa.

    Returns:
        La URL absoluta, o una cadena vacía.
    """
    if not valor:
        return ""
    valor = valor.strip()
    if valor.startswith("//"):
        return f"https:{valor}"
    if valor.startswith("/"):
        return f"https://cuspide.com{valor}"
    return valor

class CuspideBookLoader(ItemLoader):
    """Loader que normaliza los campos de :class:`CuspideBook`."""

    default_item_class = CuspideBook
    default_output_processor = TakeFirst()

    titulo_in = MapCompose(limpiar_espacios)
    autor_in = MapCompose(limpiar_espacios)
    isbn_in = MapCompose(normalizar_isbn)
    url_in = MapCompose(normalizar_url)
    precio_in = MapCompose(normalizar_precio)
    moneda_in = MapCompose(limpiar_espacios)
    precio_usd_in = MapCompose(normalizar_precio)
    imagen_url_in = MapCompose(normalizar_url)
    descripcion_in = MapCompose(limpiar_espacios)
    disponible_in = MapCompose(limpiar_espacios)
    consultado_in = MapCompose(limpiar_espacios)

    formas_pago_out = Join(" | ")
