from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import CheckConstraint,Date,DateTime,ForeignKey,Integer,Numeric,String,UniqueConstraint
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

Base = declarative_base()

class Moneda(Base):
    """Tabla de monedas en las que se expresan precios y cotizaciones."""

    __tablename__ = "monedas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(3), nullable=False, unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    simbolo: Mapped[str] = mapped_column(String(10), nullable=False)

    precios: Mapped[List["Precio"]] = relationship(back_populates="moneda")
    cotizaciones_origen: Mapped[List["CotizacionDolar"]] = relationship(
        back_populates="moneda_origen",
        foreign_keys="CotizacionDolar.moneda_origen_id",
    )
    cotizaciones_destino: Mapped[List["CotizacionDolar"]] = relationship(
        back_populates="moneda_destino",
        foreign_keys="CotizacionDolar.moneda_destino_id",
    )

    def __repr__(self) -> str:
        return f"Moneda(id={self.id}, codigo='{self.codigo}')"


class Genero(Base):
    """Tabla de géneros literarios."""

    __tablename__ = "generos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    nombre_personalizado: Mapped[Optional[str]] = mapped_column(String(80))
    descripcion: Mapped[Optional[str]] = mapped_column(String(255))

    libros: Mapped[List["Libro"]] = relationship(back_populates="genero")

    @property
    def nombre(self) -> str:
        """Nombre efectivo del género."""
        if self.tipo == "Otro" and self.nombre_personalizado:
            return self.nombre_personalizado
        return self.tipo

    def __repr__(self) -> str:
        return f"Genero(id={self.id}, nombre='{self.nombre}')"


class Editorial(Base):
    """Tabla de editoriales proveedoras de libros."""

    __tablename__ = "editoriales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    pais_origen: Mapped[str] = mapped_column(String(60), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(120))
    telefono: Mapped[Optional[str]] = mapped_column(String(30))
    sitio_web: Mapped[Optional[str]] = mapped_column(String(200))

    libros: Mapped[List["Libro"]] = relationship(back_populates="editorial")

    def __repr__(self) -> str:
        return f"Editorial(id={self.id}, nombre='{self.nombre}')"


class Libro(Base):
    """Tabla de libros del catálogo."""

    __tablename__ = "libros"
    __table_args__ = (
        CheckConstraint("edicion >= 1", name="ck_libros_edicion"),
        CheckConstraint("paginas IS NULL OR paginas > 0", name="ck_libros_paginas"),
        CheckConstraint("peso IS NULL OR peso > 0", name="ck_libros_peso"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    isbn: Mapped[str] = mapped_column(String(13), nullable=False, unique=True, index=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    autor: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    editorial_id: Mapped[int] = mapped_column(
        ForeignKey("editoriales.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    edicion: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    idioma: Mapped[str] = mapped_column(String(40), nullable=False, default="Español", server_default="Español")
    paginas: Mapped[Optional[int]] = mapped_column(Integer)
    fecha_publicacion: Mapped[Optional[date]] = mapped_column(Date)
    peso: Mapped[Optional[int]] = mapped_column(Integer)

    editorial: Mapped["Editorial"] = relationship(back_populates="libros")
    genero: Mapped["Genero"] = relationship(back_populates="libros")
    precios: Mapped[List["Precio"]] = relationship(
        back_populates="libro", cascade="all, delete-orphan"
    )
    stock: Mapped[Optional["Stock"]] = relationship(
        back_populates="libro", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"Libro(id={self.id}, isbn='{self.isbn}', titulo='{self.titulo}')"


class Precio(Base):
    """Tabla de precios de libros por moneda y fecha de vigencia."""

    __tablename__ = "precios"
    __table_args__ = (
        UniqueConstraint("libro_id", "moneda_id", "fecha_vigencia", name="uq_precios_libro_moneda_fecha"),
        CheckConstraint("valor >= 0", name="ck_precios_valor"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id", ondelete="CASCADE"), nullable=False, index=True
    )
    moneda_id: Mapped[int] = mapped_column(
        ForeignKey("monedas.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha_vigencia: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    libro: Mapped["Libro"] = relationship(back_populates="precios")
    moneda: Mapped["Moneda"] = relationship(back_populates="precios")

    def __repr__(self) -> str:
        return f"Precio(id={self.id}, libro_id={self.libro_id}, valor={self.valor})"


class Stock(Base):
    """Tabla de existencias por libro (una fila por libro)."""

    __tablename__ = "stock"
    __table_args__ = (
        CheckConstraint("cantidad >= 0", name="ck_stock_cantidad"),
        CheckConstraint("stock_minimo >= 0", name="ck_stock_minimo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    stock_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    fecha_ultimo_ingreso: Mapped[Optional[date]] = mapped_column(Date)

    libro: Mapped["Libro"] = relationship(back_populates="stock")

    @property
    def necesita_reposicion(self) -> bool:
        """Indica si la cantidad está en o por debajo del mínimo."""
        return self.cantidad <= self.stock_minimo

    def __repr__(self) -> str:
        return f"Stock(id={self.id}, libro_id={self.libro_id}, cantidad={self.cantidad})"


class TipoCotizacion(Base):
    """Tabla de tipos o mercados de cotización del dólar."""

    __tablename__ = "tipos_cotizacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255))

    cotizaciones: Mapped[List["CotizacionDolar"]] = relationship(back_populates="tipo")

    def __repr__(self) -> str:
        return f"TipoCotizacion(id={self.id}, nombre='{self.nombre}')"


class CotizacionDolar(Base):
    """Tabla histórica de cotizaciones por tipo, par de monedas y fecha."""

    __tablename__ = "cotizaciones"
    __table_args__ = (
        UniqueConstraint("tipo_id", "fecha", name="uq_cotizaciones_tipo_fecha"),
        CheckConstraint("valor_compra > 0", name="ck_cotizaciones_compra"),
        CheckConstraint("valor_venta > 0", name="ck_cotizaciones_venta"),
        CheckConstraint("valor_venta >= valor_compra", name="ck_cotizaciones_spread"),
        CheckConstraint("moneda_origen_id <> moneda_destino_id", name="ck_cotizaciones_monedas"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_cotizacion.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    moneda_origen_id: Mapped[int] = mapped_column(
        ForeignKey("monedas.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    moneda_destino_id: Mapped[int] = mapped_column(
        ForeignKey("monedas.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    valor_compra: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    valor_venta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, index=True)

    tipo: Mapped["TipoCotizacion"] = relationship(back_populates="cotizaciones")
    moneda_origen: Mapped["Moneda"] = relationship(
        back_populates="cotizaciones_origen", foreign_keys=[moneda_origen_id]
    )
    moneda_destino: Mapped["Moneda"] = relationship(
        back_populates="cotizaciones_destino", foreign_keys=[moneda_destino_id]
    )

    @property
    def spread(self) -> Decimal:
        """Diferencia entre el valor de venta y el de compra."""
        return self.valor_venta - self.valor_compra

    def __repr__(self) -> str:
        return (
            f"CotizacionDolar(id={self.id}, tipo_id={self.tipo_id}, "
            f"fecha='{self.fecha:%Y-%m-%d}')"
        )
