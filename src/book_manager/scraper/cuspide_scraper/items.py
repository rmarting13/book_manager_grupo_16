from json import dumps
from scrapy import Field, Item


class CuspideBook(Item):
    """Datos de un libro publicado en el sitio de Cúspide.

    Attributes:
        titulo_buscado: Título del catálogo con el que se buscó el libro.
        titulo: Título del libro tal como lo publica el sitio.
        autor: Autor publicado en la ficha.
        isbn: ISBN-13 del libro, usado para vincularlo con el catálogo.
        url: URL de la ficha del libro.
        precio: Precio en pesos argentinos.
        moneda: Moneda del precio principal (ARS).
        precio_usd: Precio en dólares publicado en la ficha.
        imagen_url: URL de la imagen de portada.
        formas_pago: Formas de pago publicadas por el sitio.
        descripcion: Sinopsis o descripción detallada.
        disponible: Indica si el libro está en stock.
        consultado: Fecha y hora en que se extrajo el dato.
    """

    titulo_buscado = Field()
    titulo = Field()
    autor = Field()
    isbn = Field()
    url = Field()
    precio = Field()
    moneda = Field()
    precio_usd = Field()
    imagen_url = Field()
    formas_pago = Field()
    descripcion = Field()
    disponible = Field()
    consultado = Field()

    def __str__(self) -> str:
        return dumps(
            {clave: self.get(clave) for clave in sorted(self.keys())},
            indent=4,
            ensure_ascii=False,
        )
