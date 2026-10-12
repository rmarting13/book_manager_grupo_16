import traceback

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator, model_validator, EmailStr, HttpUrl, TypeAdapter
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Dict, Optional, Any
import re
from book_manager.utilities.utilities import PrinterUtil



_URL_ADAPTER = TypeAdapter(HttpUrl)

UrlWeb = Annotated[str, AfterValidator(lambda v: str(_URL_ADAPTER.validate_python(v)))]
"""URL web recibida como str y validada como HttpUrl (se guarda normalizada como str)."""

class ArchivoCsv(str, Enum):
    "Nopmbres de archivos CSV correspondientes a cada entidad"
    MONEDA = "monedas.csv"
    GENERO = "generos.csv"
    EDITORIAL = "editoriales.csv"
    LIBRO = "libros.csv"
    PRECIO = "precios.csv"
    STOCK = "stock.csv"
    COTIZACION = "cotizaciones.csv"
    TIPO_COTIZACION = "tipo_cotizacion.csv"


class GeneroLiterario(str, Enum):
    """
    Categoría literaria a la que pertenece un libro.
    """

    NOVELA = "Novela"
    ENSAYO = "Ensayo"
    POESIA = "Poesía"
    TEATRO = "Teatro"
    INFANTIL = "Infantil"
    CIENCIA_FICCION = "Ciencia Ficción"
    FANTASIA = "Fantasía"
    TERROR = "Terror"
    BIOGRAFIA = "Biografía"
    HISTORIA = "Historia"
    CIENCIA = "Ciencia"
    DERECHO = "Derecho"
    ECONOMIA = "Economía"
    FILOSOFIA = "Filosofía"
    RELIGION = "Religión"
    OTRO = "Otro"


class EntidadBase(BaseModel):
    """Clase base de todas las entidades que proporciona un identificador único (Id).
       Hereda de BaseModel para proporcionar validaciones a las clases hijas."""

    model_config = ConfigDict(validate_assignment=True)

    id: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


class Moneda(EntidadBase):
    """
    Representa una moneda en la que se pueden expresar precios.

    Attrs:
        codigo  : Código de tres letras mayúsculas (ARS, USD, EUR, ..., etc).
        nombre  : Nombre completo de la moneda.
        simbolo : Símbolo gráfico ($, US$, etc).

    Raises:
        ValueError: Si el código no respeta el formato de 3 letras mayúsculas.
    """

    codigo: str
    nombre: str
    simbolo: str

    @field_validator("codigo")
    @classmethod
    def validar_codigo(cls, input: str) -> str:
        """Normaliza el código a mayúsculas y valida que sean 3 letras."""
        codigo = input.strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", codigo):
            raise ValueError(
                f"El código de moneda debe tener exactamente 3 letras mayúsculas. "
                f"Valor: '{codigo}'"
            )
        return codigo

    @field_validator("nombre", "simbolo")
    @classmethod
    def normalizar_texto(cls, input: str) -> str:
        """Elimina espacios sobrantes de los campos de texto."""
        return input.strip()

    @property
    def descripcion_corta(self) -> str:
        """Representación abreviada de la moneda."""
        return f"{self.simbolo} ({self.codigo})"

    def __str__(self) -> str:
        return self.descripcion_corta



class Genero(EntidadBase):
    """
    Categoría literaria a la que pertenece un libro.

    Attrs:
        tipo                : Valor del enum :class:`GeneroLiterario`.
        nombre_personalizado: Nombre libre cuando ``tipo`` es ``OTRO``.
        descripcion         : Descripción opcional del género.

    Raises:
        ValueError: Si ``tipo`` es ``OTRO`` pero no se provee ``nombre_personalizado``.
    """

    tipo: GeneroLiterario
    nombre_personalizado: Optional[str] = None
    descripcion: Optional[str] = None

    @model_validator(mode="after")
    def validar_nombre_personalizado(self) -> "Genero":
        """Exige nombre personalizado cuando el tipo es OTRO."""
        if self.tipo == GeneroLiterario.OTRO and not self.nombre_personalizado:
            raise ValueError(
                "Se debe proveer 'nombre_personalizado' cuando el tipo de género es OTRO."
            )
        return self

    @property
    def nombre(self) -> str:
        """Retorna el nombre efectivo del género."""
        if self.tipo == GeneroLiterario.OTRO and self.nombre_personalizado:
            return self.nombre_personalizado
        return self.tipo.value

    def __str__(self) -> str:
        return self.nombre



class Editorial(EntidadBase):
    """
    Proveedor o distribuidora que provee libros a la librería.

    Attrs:
        id          : Identificador único interno.
        nombre      : Razón social o nombre comercial de la editorial.
        pais_origen : País de origen de la editorial.
        email       : Correo electrónico de contacto (opcional).
        telefono    : Teléfono de contacto (opcional).
        sitio_web   : URL del sitio web oficial (opcional).

    Raises:
        ValueError: Si ``id`` no es positivo o ``nombre`` / ``pais_origen`` están vacíos.
    """

    nombre: str
    pais_origen: str
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(default=None, pattern=r"^\d+$")
    sitio_web: Optional[UrlWeb] = None

    @field_validator("nombre", "pais_origen")
    @classmethod
    def no_vacio(cls, input: str, info) -> str:
        """Normaliza y valida que nombre y país no estén vacíos."""
        input = input.strip()
        if not input:
            raise ValueError(f"El campo '{info.field_name}' de la editorial no puede estar vacío.")
        return input

    def __str__(self) -> str:
        return f"{self.nombre} ({self.pais_origen})"


class Libro(EntidadBase):
    """
    Representa un título del catálogo de la librería.

    Attrs:
        isbn             : Código ISBN-13 del libro (13 dígitos, guiones opcionales).
        titulo           : Título completo del libro.
        autor            : Nombre del autor o autores.
        editorial        : Instancia de :class:`Editorial` que publica el libro.
        genero           : Instancia de :class:`Genero` al que pertenece el libro.
        idioma           : Idioma del libro (por defecto ``'Español'``).
        paginas          : Número de páginas (opcional, debe ser > 0).
        edicion          : Número de edición (por defecto 1).
        fecha_publicacion: Fecha de publicación del libro (opcional).
        peso             : Peso del libro en gramos (opcional, debe ser > 0).

    Raises:
        ValidationError: Si el ISBN es inválido, el año está fuera de rango,
                         o los campos de texto requeridos están vacíos.

    """

    isbn: str
    titulo: str
    autor: str
    editorial: Editorial
    genero: Genero
    edicion: int = Field(default=1, ge=1)
    idioma: str = "Español"
    paginas: Optional[int] = Field(default=None, gt=0)
    fecha_publicacion: Optional[date] = None
    peso: Optional[int] = Field(default=None, gt=0)

    @field_validator("isbn")
    @classmethod
    def validar_isbn(cls, input: str) -> str:
        """
        Valida el ISBN-13:
        - Elimina espacios y guiones.
        - Verifica que sean exactamente 13 dígitos.
        - Comprueba el dígito de control según el algoritmo ISBN-13.
        """
        isbn_limpio = re.sub(r"[\s\-]", "", input )
        if not re.fullmatch(r"\d{13}", isbn_limpio):
            raise ValueError(
                f"El ISBN debe contener exactamente 13 dígitos numéricos. "
            )
        digitos = [int(d) for d in isbn_limpio] #convierte el isbn en un arreglo de enteros
        suma = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digitos[:-1]))
        digito_control = (10 - (suma % 10)) % 10
        if digito_control != digitos[-1]:
            raise ValueError(
                f"Dígito de control inválido para el ISBN-13 '{isbn_limpio}'. "
                f"Se esperaba {digito_control}, se recibió {digitos[-1]}."
            )
        return isbn_limpio

    @field_validator("titulo", "autor", "idioma")
    @classmethod
    def campo_no_vacio(cls, input: str, info) -> str:
        """Normaliza y valida campos de texto requeridos no vacíos."""
        input = input.strip()
        if not input:
            raise ValueError(f"El campo '{info.field_name}' no puede estar vacío.")
        return input

    @property
    def descripcion_corta(self) -> str:
        """Título junto al autor del libro."""
        return f"'{self.titulo}' — {self.autor}"

    @property
    def peso_kg(self) -> Optional[Decimal]:
        """Peso del libro expresado en kilogramos."""
        if self.peso is None:
            return None
        return (Decimal(self.peso) / Decimal("1000")).quantize(Decimal("0.001"))

    def __str__(self) -> str:
        return (
            f"[{self.isbn}] {self.descripcion_corta} "
            f"({self.editorial.nombre})"
        )


class Precio(EntidadBase):
    """
    Valor monetario asociado a un libro en una moneda determinada.

    Attrs:
        isbn_libro      : ISBN-13 del libro al que pertenece el precio.
        moneda          : Instancia de :class:`Moneda` en que se expresa el valor.
        valor           : Monto del precio (debe ser >= 0).
        fecha_vigencia  : Fecha desde la cual rige este precio (hoy por defecto).

    Raises:
        ValidationError: Si el valor es negativo o el ISBN tiene formato inválido.
    """

    libro: Libro
    moneda: Moneda
    valor: Decimal = Field(ge=Decimal("0"))
    fecha_vigencia: date = Field(default_factory=date.today)

    # @field_validator("isbn_libro")
    # @classmethod
    # def validar_isbn_libro(cls, input: str) -> str:
    #     """Valida que el ISBN referenciado tenga el formato de 13 dígitos."""
    #     isbn_limpio = re.sub(r"[\s\-]", "", input)
    #     if not re.fullmatch(r"\d{13}", isbn_limpio):
    #         raise ValueError(
    #             f"El ISBN del libro debe tener 13 dígitos. Recibido: '{input}'"
    #         )
    #     return isbn_limpio

    @field_validator("valor", mode="before")
    @classmethod
    def convertir_a_decimal(cls, input) -> Decimal:
        """Convierte el valor recibido a clase Decimal."""
        try:
            return Decimal(str(input))
        except Exception:
            raise ValueError(f"El valor del precio no es numérico: '{input}'")

    @property
    def valor_formateado(self) -> str:
        """Valor del precio con símbolo de moneda y dos decimales."""
        return f"{self.moneda.simbolo} {self.valor:,.2f}"

    def __str__(self) -> str:
        return (
            f"Precio | Libro: {self.libro} | "
            f"{self.valor_formateado} | "
            f"Vigente desde: {self.fecha_vigencia}"
        )


class Stock(EntidadBase):
    """
    Cantidad disponible de ejemplares de un libro.

    Attributes:
        libro          : Objeto del tipo Libro.
        cantidad            : Unidades físicas disponibles (>= 0).
        stock_minimo        : Umbral mínimo de alerta de reposición (>= 0).
        fecha_ultimo_ingreso: Fecha del último ingreso de mercadería (opcional).

    Raises:
        ValidationError: Si ``cantidad`` o ``stock_minimo`` son negativos.
    """

    libro: Libro
    cantidad: int = Field(ge=0)
    stock_minimo: int = Field(default=1, ge=0)
    fecha_ultimo_ingreso: Optional[date] = None

    # @field_validator("isbn_libro")
    # @classmethod
    # def validar_isbn_libro(cls, input: str) -> str:
    #     """Valida que el ISBN referenciado tenga el formato de 13 dígitos."""
    #     isbn_limpio = re.sub(r"[\s\-]", "", input)
    #     if not re.fullmatch(r"\d{13}", isbn_limpio):
    #         raise ValueError(
    #             f"El ISBN del libro debe tener 13 dígitos."
    #         )
    #     return isbn_limpio

    @property
    def necesita_reposicion(self) -> bool:
        """Indica si el stock actual está en o por debajo del mínimo."""
        return self.cantidad <= self.stock_minimo

    def __str__(self) -> str:
        alerta = "Atención: Stock bajo" if self.necesita_reposicion else ""
        return (
            f"Stock | Libro: {self.libro} | "
            f"Cantidad: {self.cantidad} (mín: {self.stock_minimo}) | "
            f"{alerta}"
        )


class TipoCotizacion(EntidadBase):
    """
    Tipo o mercado al que corresponde una cotización del dólar.

    Attrs:
        nombre      : Nombre del tipo de cotización (Oficial, Blue, MEP, ...).
        descripcion : Descripción opcional del tipo de cotización.

    Raises:
        ValueError: Si ``nombre`` está vacío.
    """

    nombre: str
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, input: str) -> str:
        """Normaliza y valida que el nombre no esté vacío."""
        nombre = input.strip()
        if not nombre:
            raise ValueError("El nombre del tipo de cotización no puede estar vacío.")
        return nombre

    @field_validator("descripcion")
    @classmethod
    def normalizar_descripcion(cls, input: Optional[str]) -> Optional[str]:
        """Elimina espacios sobrantes de la descripción."""
        if input is None:
            return None
        return input.strip() or None

    def __str__(self) -> str:
        return self.nombre


class CotizacionDolar(EntidadBase):
    """
    Registro histórico de la cotización de moneda por tipo y fecha.

    Attrs:
        tipo           : Instancia de :class:`TipoCotizacion`.
        moneda_origen  : Moneda de origen (usualmente USD).
        moneda_destino : Moneda de destino (usualmente ARS).
        valor_compra   : Precio de compra en ``moneda_destino`` por unidad de ``moneda_origen``.
        valor_venta    : Precio de venta en ``moneda_destino`` por unidad de ``moneda_origen``.
        fecha          : Fecha y hora del registro (``datetime.now()`` por defecto).
        fuente         : URL o nombre de la fuente proveedora del dato (opcional).

    Raises:
        ValidationError: Si valor_venta < valor_compra o los valores no son numéricos.

    """

    tipo: TipoCotizacion
    moneda_origen: Moneda
    moneda_destino: Moneda
    valor_compra: Decimal = Field(gt=Decimal("0"))
    valor_venta: Decimal = Field(gt=Decimal("0"))
    fecha: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def validar_venta_mayor_o_igual_compra(self) -> "CotizacionDolar":
        """Valida que el valor de venta no sea menor al de compra."""
        if self.valor_venta < self.valor_compra:
            raise ValueError("El valor de venta no puede ser menor al valor de compra.")
        return self

    @field_validator("valor_compra", "valor_venta", mode="before")
    @classmethod
    def convertir_a_decimal(cls, input) -> Decimal:
        """Convierte el valor a la clase Decimal."""
        try:
            return Decimal(str(input))
        except Exception:
            raise ValueError(f"El valor de cotización no es numérico: '{input}'")

    @property
    def par_monedas(self) -> str:
        """Par de monedas de la cotización (origen/destino)."""
        return f"{self.moneda_origen.codigo}/{self.moneda_destino.codigo}"

    @property
    def spread(self) -> Decimal:
        """Diferencia entre el valor de venta y el de compra."""
        return self.valor_venta - self.valor_compra

    def __str__(self) -> str:
        return (
            f"Cotización {self.tipo.nombre} "
            f"[{self.fecha.strftime('%Y-%m-%d %H:%M')}] | "
            f"{self.par_monedas} | "
            f"Compra: {self.valor_compra:,.2f} — "
            f"Venta: {self.valor_venta:,.2f} "
        )

# Pruebas unitarias:
if __name__ == '__main__':


# Monedas
    PrinterUtil.dibujar_separador("1. Monedas")

    ars = Moneda(codigo="ARS", nombre="Peso Argentino", simbolo="$")
    usd = Moneda(codigo="USD", nombre="Dólar Estadounidense", simbolo="US$")

    print(ars)
    print(usd)


    # Géneros
    PrinterUtil.dibujar_separador("2. Géneros")

    novela  = Genero(tipo=GeneroLiterario.NOVELA, descripcion="Narrativa extensa de ficción")
    manga   = Genero(tipo=GeneroLiterario.OTRO, nombre_personalizado="Manga / Cómic")

    print(novela)
    print(manga)

    #Editoriales
    PrinterUtil.dibujar_separador("3. Editoriales")

    planeta   = Editorial(id=1, nombre="Planeta", pais_origen="Argentina",
                        email="info@planeta.com.ar", sitio_web='https://www.planeta.com.ar')
    elmundo = Editorial(id=2, nombre="ElMundo", pais_origen="Argentina",
                        email="info@elmundo.com.ar")
    conmemorativa = Editorial(id=2, nombre="Conmemorativa", pais_origen="Argentina")

    print(planeta)
    print(elmundo)
    print(conmemorativa)

    #Libros
    PrinterUtil.dibujar_separador("4. Libros")

    ficciones = Libro(
        isbn="9789504930419",
        titulo="Ficciones",
        autor="Jorge Luis Borges",
        editorial=planeta,
        genero=novela,
        idioma="Español",
        paginas=224,
        edicion=3,
        fecha_publicacion=date(1944, 6, 15),
        peso=280,
    )

    cien_anios_de_soledad = Libro(
        isbn="9788420471839",
        titulo="100 años de soledad",
        autor="Gabriel García Márquez",
        editorial=conmemorativa,
        genero=novela,
        idioma="Inglés",
        paginas=431,
        fecha_publicacion=date(1967, 5, 30),
        peso=520,
    )

    tasm_04_ca = Libro(
            isbn="9786075688237",
            titulo="The Amazing Spider-man 04 Carnage Absoluto",
            autor="Spencer, Ottley",
            editorial=conmemorativa,
            genero=manga,
            idioma="Inglés",
            paginas=431,
            fecha_publicacion=date(2021, 9, 14),
            peso=610,
        )

    print(ficciones)
    print(cien_anios_de_soledad)

    # 
    #Precios
    PrinterUtil.dibujar_separador("5. Precios")

    precio_ficciones_ars = Precio(
        libro=ficciones,
        moneda=ars,
        valor= Decimal('12500.00'),
        fecha_vigencia=date.today()
    )

    precio_ficciones_usd = Precio(
        libro=ficciones,
        moneda=usd,
        valor=Decimal("10.50")
    )

    print(precio_ficciones_ars)
    print(precio_ficciones_usd)


    # Stock
    PrinterUtil.dibujar_separador("6. Stock")

    stock_ficciones = Stock(
        libro=ficciones,
        cantidad=8,
        stock_minimo=3,
        fecha_ultimo_ingreso=date(2025, 1, 15),
    )

    stock_agotado = Stock(
        libro=cien_anios_de_soledad,
        cantidad=1,
        stock_minimo=2
    )

    print(stock_ficciones)
    print(f"Necesita reposición: {stock_ficciones.necesita_reposicion}")
    print(stock_agotado)
    print(f"Necesita reposición: {stock_agotado.necesita_reposicion}")


    # Tipos de cotización
    PrinterUtil.dibujar_separador("7. Tipos de cotización")

    tipo_oficial = TipoCotizacion(id=1, nombre="Oficial", descripcion="Cotización oficial del BCRA")
    tipo_blue = TipoCotizacion(id=2, nombre="Blue", descripcion="Mercado informal")

    print(tipo_oficial)
    print(tipo_blue)


    # Cotizaciones
    PrinterUtil.dibujar_separador("8. Cotizaciones")

    cotizacion_blue = CotizacionDolar(
        tipo=tipo_blue,
        moneda_origen=usd,
        moneda_destino=ars,
        valor_compra= Decimal("1180"),
        valor_venta=Decimal("1200")
    )

    cotizacion_oficial = CotizacionDolar(
        tipo=tipo_oficial,
        moneda_origen=usd,
        moneda_destino=ars,
        valor_compra= Decimal("987"),
        valor_venta = Decimal("1010"),
    )

    print(cotizacion_blue)
    print(cotizacion_oficial)


    print(tasm_04_ca.to_dict())


    # Manejo de errores de validación
    PrinterUtil.dibujar_separador("9. Validaciones")

    from pydantic import ValidationError
    
    #ISBN inválido
    try:
        Libro(isbn="0000000000000", titulo="Prueba", autor="Autor",
            editorial=planeta, genero=novela)
    except ValidationError:
        traceback.print_exc()

    # Precio negativo
    try:
        Precio(libro=ficciones, moneda=ars, valor=Decimal('-100'))
    except ValidationError:
        traceback.print_exc()

    #Stock negativo
    try:
        Stock(libro=ficciones, cantidad=-5)
    except ValidationError:
        traceback.print_exc()

    # Cotización con venta < compra
    try:
        CotizacionDolar(tipo=tipo_oficial, moneda_origen=usd, moneda_destino=ars,
                valor_compra= Decimal('1200'), valor_venta=Decimal("1100"))
    except ValidationError:
        traceback.print_exc()

    #Código de moneda inválido
    try:
        Moneda(codigo="PESO", nombre="Peso", simbolo="$")
    except ValidationError:
        traceback.print_exc()

    # Tipo de cotización sin nombre
    try:
        TipoCotizacion(nombre="   ")
    except ValidationError:
        traceback.print_exc()
