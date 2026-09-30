from datetime import date
from decimal import Decimal
from typing import List, Optional, Union

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
)


class ServicioError(ValueError):
    """Clase de error base para validaciones."""
    pass


class MonedaServicio:
    """Servicio para operaciones con monedas."""

    def __init__( self, repo_moneda: RepositorioMoneda, repo_precio: RepositorioPrecio,repo_cotizacion: RepositorioCotizacionDolar) -> None:
        self.repo_moneda = repo_moneda
        self.repo_precio = repo_precio
        self.repo_cotizacion = repo_cotizacion

    def crear(self, moneda: Moneda) -> Moneda:
        """Crea una moneda validando que el código sea único."""

        if self.obtener_por_codigo(moneda.codigo):
            raise ServicioError(f"Ya existe una moneda con código '{moneda.codigo}'.")
        return self.repo_moneda.crear(moneda)

    def actualizar(self, moneda: Moneda) -> Moneda:
        """actualiza una moneda existente con validación de código"""
        self.obtener(moneda.id)
        otra = self.obtener_por_codigo(moneda.codigo)
        if otra and otra.id != moneda.id:
            raise ServicioError(f"Ya existe el código de moneda '{moneda.codigo}'.")
        return self.repo_moneda.actualizar(moneda)

    def eliminar(self, id: int) -> bool:
        """Elimina una moneda con validaciones de referencias de uso"""

        self.obtener(id)
        if any(p.moneda.id == id for p in self.repo_precio.leer_todos()):
            raise ServicioError("Imposible eliminar moneda: referencias de uso en precios.")
        for tipo in TipoCotizacion:
            for c in self.repo_cotizacion.leer_historico_por_tipo(tipo):
                if id in (c.moneda_origen.id, c.moneda_destino.id):
                    raise ServicioError("Imposible eliminar moneda: referencias de uso en cotizaciones.")
        return self.repo_moneda.eliminar(id)
    
    
    def obtener(self, id: int) -> Moneda:
        """Filtra moneda por id."""

        moneda = self.repo_moneda.leer_por_id(id)
        if not moneda:
            raise ServicioError(f"No se encontró moneda con {id}.")
        return moneda

    def obtener_por_codigo(self, codigo: str) -> Optional[Moneda]:
        """filtra moneda por código ISO."""

        codigo = codigo.strip().upper() #formateo
        return next((m for m in self.repo_moneda.leer_todos() if m.codigo == codigo), None)



    def listar(self) -> List[Moneda]:
        """Retorna todo el repositorio de monedas."""
        return self.repo_moneda.leer_todos()




class ServicioGenero:
    """Servicio para operaciones sobre Género."""

    def __init__(self, repo_genero: RepositorioGenero, repo_libro: RepositorioLibro) -> None:
        self.repo_genero = repo_genero
        self.repo_libro = repo_libro

    def crear(self, genero: Genero) -> Genero:
        """crea Genero con validación de nombre."""
        if self._buscar_por_nombre(genero.nombre):
            raise ServicioError(f"Ya existe el género '{genero.nombre}'.")
        return self.repo_genero.crear(genero)

    def obtener(self, id: int) -> Genero:
        """filtra Genero por id."""

        genero = self.repo_genero.leer_por_id(id)
        if not genero:
            raise ServicioError(f"No se encontró género con id {id}.")
        return genero


    def actualizar(self, genero: Genero) -> Genero:
        """Modifica un género validando existencia y duplicidad"""
        self.obtener(genero.id)
        otro = self._buscar_por_nombre(genero.nombre)
        if otro and otro.id != genero.id:
            raise ServicioError(f"Ya existe otro género '{genero.nombre}'.")
        return self.repo_genero.actualizar(genero)

    def eliminar(self, id: int) -> bool:
        """Elimina un Genero validando referencias de uso."""

        self.obtener(id)
        if any(l.genero.id == id for l in self.repo_libro.leer_todos()):
            raise ServicioError("Imposible eliminar: referencia de uso en libros.")
        return self.repo_genero.eliminar(id)

    def listar(self) -> List[Genero]:
        """Retorna el repositorio con todos los géneros"""

        return self.repo_genero.leer_todos()
    
    def _buscar_por_nombre(self, nombre: str) -> Optional[Genero]:
        nombre = nombre.strip().lower()
        return next((g for g in self.repo_genero.leer_todos() if g.nombre.lower() == nombre), None)


class ServicioEditorial:
    """Servicio para operaciones sobre Editoriales."""

    def __init__(self, repo_editorial: RepositorioEditorial, repo_libro: RepositorioLibro) -> None:
        self.repo_editorial = repo_editorial
        self.repo_libro = repo_libro

    def crear(self, editorial: Editorial) -> Editorial:
        """Crea un nuevo Editorial validando duplicidad"""
        if self._buscar_por_nombre(editorial.nombre):
            raise ServicioError(f"Ya existe un Editorial '{editorial.nombre}'.")
        return self.repo_editorial.crear(editorial)

    def obtener(self, id: int) -> Editorial:
        """Filtra un Editorial por id"""

        editorial = self.repo_editorial.leer_por_id(id)
        if not editorial:
            raise ServicioError(f"No se encontró Editorial con id {id}.")
        return editorial

    def listar(self) -> List[Editorial]:
        """retorna la lista completa del repositorio de Editoriales."""
        return self.repo_editorial.leer_todos()

    def actualizar(self, editorial: Editorial) -> Editorial:
        """Actualiza un Editorial validando existencia y duplicidad."""

        self.obtener(editorial.id)
        otro = self._buscar_por_nombre(editorial.nombre)
        if otro and otro.id != editorial.id:
            raise ServicioError(f"Ya existe un Editorial '{editorial.nombre}'.")
        return self.repo_editorial.actualizar(editorial)

    def eliminar(self, id: int) -> bool:
        """Elimina un Editorial con validación de referencias de uso."""

        self.obtener(id)
        if any(l.editorial.id == id for l in self.repo_libro.leer_todos()):
            raise ServicioError("Imposible eliminar Editorial: referencia de uso en libros.")
        return self.repo_editorial.eliminar(id)

    def _buscar_por_nombre(self, nombre: str) -> Optional[Editorial]:
        nombre = nombre.strip().lower()
        return next((e for e in self.repo_editorial.leer_todos() if e.nombre.lower() == nombre), None)


class ServicioLibro:
    """Servicio para operaciones sobre entidades de tipo Libro."""

    def __init__(self,repo_libro: RepositorioLibro,repo_editorial: RepositorioEditorial,
                repo_genero: RepositorioGenero,repo_precio: RepositorioPrecio,repo_stock: RepositorioStock) -> None:
        self.repo_libro = repo_libro
        self.repo_editorial = repo_editorial
        self.repo_genero = repo_genero
        self.repo_precio = repo_precio
        self.repo_stock = repo_stock

    def crear(self, libro: Libro) -> Libro:
        """Crea un Libro validando ISBN"""
        self._validar_referencias(libro)
        if self.obtener_por_isbn(libro.isbn):
            raise ServicioError(f"Ya existe un libro con ISBN {libro.isbn}.")
        return self.repo_libro.crear(libro)

    def actualizar(self, libro: Libro) -> Libro:
        """Modifica un Libro validando referencias de uso e ISBN"""
        self.obtener(libro.id)
        self._validar_referencias(libro)
        otro = self.obtener_por_isbn(libro.isbn)
        if otro and otro.id != libro.id:
            raise ServicioError(f"Ya existe un Libro con ISBN {libro.isbn}.")
        return self.repo_libro.actualizar(libro)

    def eliminar(self, id: int) -> bool:
        """elimina un Libro validando referencias de uso."""
        self.obtener(id)
        if any(p.libro.id == id for p in self.repo_precio.leer_todos()):
            raise ServicioError("Imposible borrar Libro: referencia de uso en Precio.")
        if self.repo_stock.leer_por_libro(id):
            raise ServicioError("Imposible borrar Libro: referencia de uso en Stock.")
        return self.repo_libro.eliminar(id)

    
    def obtener(self, id: int) -> Libro:
        """filtra un Libro por id"""
        libro = self.repo_libro.leer_por_id(id)
        if not libro:
            raise ServicioError(f"No se encontró Libro con id {id}.")
        return libro

    def obtener_por_isbn(self, isbn: str) -> Optional[Libro]:
        """filtra Libro por ISBN (ignora guiones y espacios)."""
        isbn = isbn.replace("-", "").replace(" ", "")
        return next((l for l in self.repo_libro.leer_todos() if l.isbn == isbn), None)

    def buscar(self, texto: str) -> List[Libro]:
        """filtra libros por patron de texto en titulo o autor"""
        texto = texto.strip().lower()
        return ([l for l in self.repo_libro.leer_todos() 
                if texto in l.titulo.lower() or texto in l.autor.lower()])

    
    def listar(self) -> List[Libro]:
        """Devuelve el listado completo del repositorio de Libro"""
        return self.repo_libro.leer_todos()


    def listar_por_genero(self, genero_id: int) -> List[Libro]:
        """Devuelve todos los libros de un género."""
        return [l for l in self.repo_libro.leer_todos() if l.genero.id == genero_id]

    def listar_por_editorial(self, editorial_id: int) -> List[Libro]:
        """Retorna todos los libros asociados a un Editorial"""
        return [l for l in self.repo_libro.leer_todos() if l.editorial.id == editorial_id]


    def _validar_referencias(self, libro: Libro) -> None:
        if not self.repo_editorial.leer_por_id(libro.editorial.id):
            raise ServicioError(f"No existe la editorial con id {libro.editorial.id}.")
        if not self.repo_genero.leer_por_id(libro.genero.id):
            raise ServicioError(f"No existe el género con id {libro.genero.id}.")


class ServicioPrecio:
    """Servicio para operaciones sobre entidad Precio"""

    def __init__(
        self,
        repo_precio: RepositorioPrecio,
        repo_libro: RepositorioLibro,
        repo_moneda: RepositorioMoneda,
    ) -> None:
        self.repo_precio = repo_precio
        self.repo_libro = repo_libro
        self.repo_moneda = repo_moneda

    def crear(self, precio: Precio) -> Precio:
        """"
            Crea Precio con validaciones de referencias de uso.
        """
        self._validar_referencias(precio)
        if self._existe(precio):
            raise ServicioError("Ya existe Precio vigente para Libro y Moneda especificados.")
        return self.repo_precio.crear(precio)

    def actualizar(self, precio: Precio) -> Precio:
        """Modifica un Precio existente validando referencias de uso y vigencia."""

        self.obtener(precio.id)
        self._validar_referencias(precio)
        if self._existe(precio, excluir_id=precio.id):
            raise ServicioError("Ya existe Precio vigente para Libro y Moneda especificados")
        return self.repo_precio.actualizar(precio)

    def eliminar(self, id: int) -> bool:
        """Elimina un precio existente."""
        self.obtener(id)
        return self.repo_precio.eliminar(id)

    
    def obtener(self, id: int) -> Precio:
        """filtra Percio por id"""
        precio = self.repo_precio.leer_por_id(id)
        if not precio:
            raise ServicioError(f"No se encontró Precio con id {id}.")
        return precio

    def listar(self) -> List[Precio]:
        """devuelve el repositorio completo de Precio."""
        return self.repo_precio.leer_todos()

    def historial(self, libro_id: int, moneda_id: Optional[int] = None) -> List[Precio]:
        """Retorna los precios históricos de un Libro 
            (opcionalmente en una moneda), en orden ascendente por vigencia"""
        precios = [
            p for p in self.repo_precio.leer_todos()
            if p.libro.id == libro_id and (moneda_id is None or p.moneda.id == moneda_id)
        ]
        return sorted(precios, key=lambda p: p.fecha_vigencia)

    def obtener_vigente(self, libro_id: int, moneda_id: int, fecha: Optional[date] = None) -> Optional[Precio]:
        """Devuelve el último precio cuya vigencia comenzó en o antes de la fecha (hoy por defecto)."""
        fecha = fecha or date.today()
        vigentes = [p for p in self.historial(libro_id, moneda_id) if p.fecha_vigencia <= fecha]
        return vigentes[-1] if vigentes else None


    def _validar_referencias(self, precio: Precio) -> None:
        if not self.repo_libro.leer_por_id(precio.libro.id):
            raise ServicioError(f"No existe el libro con id {precio.libro.id}.")
        if not self.repo_moneda.leer_por_id(precio.moneda.id):
            raise ServicioError(f"No existe la moneda con id {precio.moneda.id}.")

    def _existe(self, precio: Precio, excluir_id: Optional[int] = None) -> bool:
        return any(
            p.id != excluir_id
            and p.libro.id == precio.libro.id
            and p.moneda.id == precio.moneda.id
            and p.fecha_vigencia == precio.fecha_vigencia
            for p in self.repo_precio.leer_todos()
        )


class ServicioStock:
    """Servicio para operaciones sobre Stock disponible de Libro."""

    def __init__(self, repo_stock: RepositorioStock, repo_libro: RepositorioLibro) -> None:
        self.repo_stock = repo_stock
        self.repo_libro = repo_libro

    def crear(self, stock: Stock) -> Stock:
        """Crea Stock de un libro existente"""
        self._validar_libro(stock.libro.id)
        if self.repo_stock.leer_por_libro(stock.libro.id):
            raise ServicioError(f"Ya existe Stock para el libro con id {stock.libro.id}.")
        return self.repo_stock.crear(stock)

    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza un registro de stock existente."""
        self._validar_libro(stock.libro.id)
        return self.repo_stock.actualizar(stock)

    def eliminar(self, libro_id: int) -> bool:
        """Elimina el stock de un libro."""
        self.obtener_por_libro(libro_id)
        return self.repo_stock.eliminar(libro_id)
    

    def obtener_por_libro(self, libro_id: int) -> Stock:
        """Devuelve el Stock de un Libro."""
        stock = self.repo_stock.leer_por_libro(libro_id)
        if not stock:
            raise ServicioError(f"No existe Stock para el libro con id {libro_id}.")
        return stock

    def listar(self) -> List[Stock]:
        """retorna todo el repositorio de Stock."""
        return self.repo_stock.leer_todos()

    def listar_a_reponer(self) -> List[Stock]:
        """Lista el stock que necesita reposición."""
        return [s for s in self.repo_stock.leer_todos() if s.necesita_reposicion]

    def agregar(self, libro_id: int, cantidad: int) -> Stock:
        """Carga nuevas unidades al Stock y actualiza la fecha de ingreso."""

        self._validar_cantidad(cantidad)
        stock = self.obtener_por_libro(libro_id)
        actualizado = stock.model_copy(
            update={"cantidad": stock.cantidad + cantidad, "fecha_ultimo_ingreso": date.today()}
        )
        return self.repo_stock.actualizar(actualizado)

    def reducir(self, libro_id: int, cantidad: int) -> Stock:
        """Resta unidades al stock"""
        self._validar_cantidad(cantidad)
        stock = self.obtener_por_libro(libro_id)
        if cantidad > stock.cantidad:
            raise ServicioError(
                f"Stock insuficiente: disponible {stock.cantidad}, solicitado {cantidad}."
            )
        return self.repo_stock.actualizar(stock.model_copy(update={"cantidad": stock.cantidad - cantidad}))

    def _validar_libro(self, libro_id: int) -> None:
        if not self.repo_libro.leer_por_id(libro_id):
            raise ServicioError(f"No se encontró Libro con id {libro_id}.")

    @staticmethod
    def _validar_cantidad(cantidad: int) -> None:
        if cantidad <= 0:
            raise ServicioError("La cantidad no puede negativa.")


class ServicioCotizacionDolar:
    """Servicio para operaciones sobre CotizacionDolar."""

    def __init__(self, repo_cotizacion: RepositorioCotizacionDolar, repo_moneda: RepositorioMoneda) -> None:
        self.repo_cotizacion = repo_cotizacion
        self.repo_moneda = repo_moneda

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea una nueva cotización diaria"""

        self._validar_monedas(cotizacion)
        if self.repo_cotizacion.leer_por_tipo_y_fecha(cotizacion.tipo, cotizacion.fecha.date()):  # type: ignore[arg-type]
            raise ServicioError(f"Ya existe una cotización {cotizacion.tipo.value} para esa fecha.")
        return self.repo_cotizacion.crear(cotizacion)

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """actualiza una cotización existente."""

        self._validar_monedas(cotizacion)
        existente = self.repo_cotizacion.leer_por_tipo_y_fecha(cotizacion.tipo, cotizacion.fecha.date())  # type: ignore[arg-type]
        if existente and existente.id != cotizacion.id:
            raise ServicioError(f"Ya existe otra cotización {cotizacion.tipo.value} para esa fecha.")
        return self.repo_cotizacion.actualizar(cotizacion)

    

    def eliminar(self, tipo: Union[TipoCotizacion, str], fecha: date) -> bool:
        """Elimina una CotizacionDolar por tipo y fecha."""
        self.obtener(tipo, fecha)
        return self.repo_cotizacion.eliminar(tipo, fecha)  # type: ignore[arg-type]
    
    def obtener(self, tipo: Union[TipoCotizacion, str], fecha: date) -> CotizacionDolar:
        """Recupera una CotizacionDolar por tipo y fecha."""
        cotizacion = self.repo_cotizacion.leer_por_tipo_y_fecha(tipo, fecha)  # type: ignore[arg-type]
        if not cotizacion:
            raise ServicioError(f"No hay cotización {tipo} para el {fecha.isoformat()}.")
        return cotizacion

    
    def historico(self, tipo: Union[TipoCotizacion, str]) -> List[CotizacionDolar]:
        """
            retorna el histórico de un tipo de cotización ordenado por fecha
        """
        return self.repo_cotizacion.leer_historico_por_tipo(tipo)  # type: ignore[arg-type]

    def obtener_ultima(self, tipo: Union[TipoCotizacion, str]) -> CotizacionDolar:
        """retorna la CotizacionDolar más reciente de un tipo."""

        historico = self.historico(tipo)
        if not historico:
            raise ServicioError(f"No existen cotizaciones del tipo {tipo}.")
        return historico[-1]


    def convertir(self, monto_usd: Decimal, tipo: Union[TipoCotizacion, str], usar_venta: bool = True) -> Decimal:
        """
            Realiza la conversión de USD a moneda de destino con la última cotización (venta por defecto, o compra).
        """
        
        if monto_usd < 0:
            raise ServicioError("El monto no puede ser negativo.")
        cotizacion = self.obtener_ultima(tipo)
        valor = cotizacion.valor_venta if usar_venta else cotizacion.valor_compra
        return (Decimal(monto_usd) * valor).quantize(Decimal("0.01"))

    def _validar_monedas(self, cotizacion: CotizacionDolar) -> None:
        for moneda in (cotizacion.moneda_origen, cotizacion.moneda_destino):
            if not self.repo_moneda.leer_por_id(moneda.id):
                raise ServicioError(f"No existe Moneda con id {moneda.id}.")
        if cotizacion.moneda_origen.id == cotizacion.moneda_destino.id:
            raise ServicioError("Moneda de origen y destino idénticas.")
