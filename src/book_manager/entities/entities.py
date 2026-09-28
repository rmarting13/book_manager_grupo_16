from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr, HttpUrl
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any
from uuid import UUID, uuid4
import re



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


class TipoCotizacion(str, Enum):
    """
    Tipos de cotización del dólar en Argentina:

    Atrrs:
        OFICIAL   : Cotización oficial publicada por el BCRA.
        BLUE      : Cotización del mercado informal (dólar paralelo).
        MEP       : Dólar bolsa / Mercado Electrónico de Pagos.
    """

    OFICIAL = "Oficial"
    BLUE = "Blue"
    MEP = "MEP"


@dataclass
class Moneda:
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

    def __post_init__(self) -> None:
        self.codigo = self.codigo.strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", self.codigo):
            raise ValueError(
                f"El código de moneda debe tener exactamente 3 letras mayúsculas. "
                f"Valor: '{self.codigo}'"
            )
        self.nombre = self.nombre.strip()
        self.simbolo = self.simbolo.strip()

    def __str__(self) -> str:
        return f"{self.simbolo} ({self.codigo})"


@dataclass
class Genero:
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

    def __post_init__(self) -> None:
        if self.tipo == GeneroLiterario.OTRO and not self.nombre_personalizado:
            raise ValueError(
                "Se debe proveer 'nombre_personalizado' cuando el tipo de género es OTRO."
            )

    @property
    def nombre(self) -> str:
        """Retorna el nombre efectivo del género."""
        if self.tipo == GeneroLiterario.OTRO and self.nombre_personalizado:
            return self.nombre_personalizado
        return self.tipo.value

    def __str__(self) -> str:
        return self.nombre


@dataclass
class Editorial:
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

    id: UUID
    nombre: str
    pais_origen: str
    # email: Optional[str] = None
    # telefono: Optional[str] = None
    # sitio_web: Optional[str] = None
    email: EmailStr
    telefono: Optional[str] = None
    sitio_web: Optional[HttpUrl] = None

    def __post_init__(self) -> None:
        self.id = Field(default_factory=uuid4, frozen=True)
        self.nombre = self.nombre.strip()
        self.pais_origen = self.pais_origen.strip()
        if not self.nombre:
            raise ValueError("El nombre de la editorial no puede estar vacío.")
        if not self.pais_origen:
            raise ValueError("El país de origen de la editorial no puede estar vacío.")
        self.telefono = Field(default = None, pattern= r"^\d+$")

    def __str__(self) -> str:
        return f"{self.nombre} ({self.pais_origen})"


class Libro(BaseModel):
    """
    Representa un título del catálogo de la librería.

    Attrs:
        isbn             : Código ISBN-13 del libro (13 dígitos, guiones opcionales).
        titulo           : Título completo del libro.
        autor            : Nombre del autor o autores.
        editorial        : Instancia de :class:`Editorial` que publica el libro.
        genero           : Instancia de :class:`Genero` al que pertenece el libro.
        anio_publicacion : Año de publicación (1450 – año actual).
        idioma           : Idioma del libro (por defecto ``'Español'``).
        paginas          : Número de páginas (opcional, debe ser > 0).
        edicion          : Número de edición (por defecto 1).

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
    anio_publicacion: int
    idioma: str = "Español"
    paginas: Optional[int] = Field(default=None, gt=0)

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

    @field_validator("anio_publicacion")
    @classmethod
    def validar_anio(cls, input: int) -> int:
        """Valida que el año de publicación sea históricamente razonable."""
        anio_actual = datetime.now().year
        if not (1450 <= input <= anio_actual):
            raise ValueError(
                f"El año de publicación debe estar entre 1450 y {anio_actual}. "
                f"Recibido: {input}"
            )
        return input

    def __str__(self) -> str:
        return (
            f"[{self.isbn}] '{self.titulo}' — {self.autor} "
            f"({self.editorial.nombre}, {self.anio_publicacion})"
        )


class Precio(BaseModel):
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

    isbn_libro: str
    moneda: Moneda
    valor: Decimal = Field(ge=Decimal("0"))
    fecha_vigencia: date = Field(default_factory=date.today)

    @field_validator("isbn_libro")
    @classmethod
    def validar_isbn_libro(cls, input: str) -> str:
        """Valida que el ISBN referenciado tenga el formato de 13 dígitos."""
        isbn_limpio = re.sub(r"[\s\-]", "", input)
        if not re.fullmatch(r"\d{13}", isbn_limpio):
            raise ValueError(
                f"El ISBN del libro debe tener 13 dígitos. Recibido: '{input}'"
            )
        return isbn_limpio

    @field_validator("valor", mode="before")
    @classmethod
    def convertir_a_decimal(cls, input) -> Decimal:
        """Convierte el valor recibido a clase Decimal."""
        try:
            return Decimal(str(input))
        except Exception:
            raise ValueError(f"El valor del precio no es numérico: '{input}'")

    def __str__(self) -> str:
        return (
            f"Precio | ISBN: {self.isbn_libro} | "
            f"{self.moneda.simbolo} {self.valor:,.2f} | "
            f"Vigente desde: {self.fecha_vigencia}"
        )


class Stock(BaseModel):
    """
    Cantidad disponible de ejemplares de un libro.

    Attributes:
        isbn_libro          : ISBN-13 del libro al que corresponde el stock.
        cantidad            : Unidades físicas disponibles (>= 0).
        stock_minimo        : Umbral mínimo de alerta de reposición (>= 0).
        fecha_ultimo_ingreso: Fecha del último ingreso de mercadería (opcional).

    Raises:
        ValidationError: Si ``cantidad`` o ``stock_minimo`` son negativos,
                         o el ISBN tiene formato inválido.
    """

    isbn_libro: str
    cantidad: int = Field(ge=0)
    stock_minimo: int = Field(default=1, ge=0)
    fecha_ultimo_ingreso: Optional[date] = None

    @field_validator("isbn_libro")
    @classmethod
    def validar_isbn_libro(cls, input: str) -> str:
        """Valida que el ISBN referenciado tenga el formato de 13 dígitos."""
        isbn_limpio = re.sub(r"[\s\-]", "", input)
        if not re.fullmatch(r"\d{13}", isbn_limpio):
            raise ValueError(
                f"El ISBN del libro debe tener 13 dígitos."
            )
        return isbn_limpio

    @property
    def necesita_reposicion(self) -> bool:
        """Indica si el stock actual está en o por debajo del mínimo."""
        return self.cantidad <= self.stock_minimo

    def __str__(self) -> str:
        alerta = "Atención: Stock bajo" if self.necesita_reposicion else ""
        return (
            f"Stock | ISBN: {self.isbn_libro} | "
            f"Cantidad: {self.cantidad} (mín: {self.stock_minimo}) | "
            f"{alerta}"
        )


class CotizacionDolar(BaseModel):
    """
    Registro histórico de la cotización de moneda por tipo y fecha.

    Attrs:
        tipo           : Tipo de cotización (enum :class:`TipoCotizacion`).
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


    @field_validator("valor_compra", "valor_venta", mode="before")
    @classmethod
    def convertir_a_decimal(cls, input) -> Decimal:
        """Convierte el valor a la clase Decimal."""
        try:
            return Decimal(str(input))
        except Exception:
            raise ValueError(f"El valor de cotización no es numérico: '{input}'")

    def __str__(self) -> str:
        return (
            f"Cotización {self.tipo.value} "
            f"[{self.fecha.strftime('%Y-%m-%d %H:%M')}] | "
            f"{self.moneda_origen.codigo}/{self.moneda_destino.codigo} | "
            f"Compra: {self.valor_compra:,.2f} — "
            f"Venta: {self.valor_venta:,.2f} "
        )
