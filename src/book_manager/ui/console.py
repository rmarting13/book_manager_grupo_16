from datetime import date, datetime, time
from decimal import Decimal
from typing import Callable, Dict, List, Optional, Tuple, overload

from pydantic import ValidationError

from book_manager.utilities.utilities import PrinterUtil
from book_manager.entities.entities import (
    CotizacionDolar, Editorial, Genero, GeneroLiterario, Libro, Moneda, Precio, Stock, TipoCotizacion,
)
from book_manager.repositories.repositories import RepositorioError
from book_manager.services.services import (
    MonedaServicio,
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioError,
    ServicioGenero,
    ServicioLibro,
    ServicioPrecio,
    ServicioStock,
)

Opcion = Tuple[str, Callable[[], None]]

CAMPO_OBLIGATORIO = 'El campo es obligatorio'

def pedir_texto(mensaje: str) -> str:
    """Pide por pantalla un texto obligatorio."""
    while True:
        valor = input(f"  {mensaje}: ").strip()
        if valor:
            return valor
        print(CAMPO_OBLIGATORIO)


def editar_texto(mensaje: str, actual: str) -> str:
    """Pide por pantalla un texto. Enter vacío conserva el valor actual."""
    sufijo = f" [{actual}]" if actual else ""
    valor = input(f"  {mensaje}{sufijo}: ").strip()
    return valor or actual


def pedir_opcional(mensaje: str) -> Optional[str]:
    """Pide por pantalla un texto opcional. Enter vacío devuelve None."""
    return input(f"  {mensaje} (opcional): ").strip() or None


def _leer_entero(mensaje: str, minimo: int) -> Optional[int]:
    while True:
        valor = input(f"  {mensaje}: ").strip()
        if not valor:
            return None
        try:
            numero = int(valor)
        except ValueError:
            print("  Ingrese un número entero.")
            continue
        if numero < minimo:
            print(f"El valor mínimo aceptable es {minimo}.")
            continue
        return numero


def pedir_entero(mensaje: str, minimo: int = 0) -> int:
    """Solicita ingresar un número entero obligatorio."""
    while True:
        numero = _leer_entero(mensaje, minimo)
        if numero is not None:
            return numero
        print(CAMPO_OBLIGATORIO)


def editar_entero(mensaje: str, actual: int, minimo: int = 0) -> int:
    """Solicita por pantalla un número entero obligatorio, el vacío restaura el actual."""
    numero = _leer_entero(f"{mensaje} [{actual}]", minimo)
    return actual if numero is None else numero


def pedir_entero_opcional(mensaje: str, actual: Optional[int] = None, minimo: int = 1) -> Optional[int]:
    """Solicita por pantalla un entero opcional. El vacío conserva el actual o None."""
    sufijo = f" [{actual}]" if actual is not None else " (opcional)"
    numero = _leer_entero(f"{mensaje}{sufijo}", minimo)
    return actual if numero is None else numero


def _leer_decimal(mensaje: str) -> Optional[Decimal]:
    while True:
        valor = input(f"  {mensaje}: ").strip().replace(",", ".")
        if not valor:
            return None
        try:
            numero = Decimal(valor)
        except ArithmeticError:
            print("Ingrese un número decimal.")
            continue
        if not numero.is_finite() or numero < 0:
            print("Ingrese un número válido no negativo.")
            continue
        return numero


def pedir_decimal(mensaje: str) -> Decimal:
    """Solicita por pantalla un decimal obligatorio no negativo."""
    while True:
        numero = _leer_decimal(mensaje)
        if numero is not None:
            return numero
        print(CAMPO_OBLIGATORIO)


@overload
def editar_decimal(mensaje: str, actual: Decimal) -> Decimal: ...
@overload
def editar_decimal(mensaje: str, actual: None) -> Optional[Decimal]: ...
def editar_decimal(mensaje: str, actual: Optional[Decimal]) -> Optional[Decimal]:
    """Solicita por pantalla un decimal, el vacío conserva el valor actual."""
    sufijo = f" [{actual:.2f}]" if actual is not None else ""
    numero = _leer_decimal(f"{mensaje}{sufijo}")
    return actual if numero is None else numero


def pedir_fecha(mensaje: str, actual: date) -> date:
    """Solicita por pantalla una fecha AAAA-MM-DD, el vacío usa la indicada."""
    while True:
        valor = input(f"  {mensaje} (AAAA-MM-DD) [{actual.isoformat()}]: ").strip()
        if not valor:
            return actual
        try:
            return date.fromisoformat(valor)
        except ValueError:
            print("Ingrese una fecha válida con formato AAAA-MM-DD.")


def confirmar(mensaje: str) -> bool:
    while True:
        r = input(f"  {mensaje} (s/n): ").strip().lower()
        if r in ("s", "si", "sí"):
            return True
        if r in ("n", "no"):
            return False
        print("Responda 's' o 'n'.")


class ConsolaInventario:
    """Menús interactivos que delegan toda la lógica en los servicios."""

    def __init__( self,servicio_libros: ServicioLibro,servicio_generos: ServicioGenero,servicio_editoriales: ServicioEditorial,
                  servicio_precios: ServicioPrecio,servicio_stock: ServicioStock,servicio_monedas: MonedaServicio,
                  servicio_cotizaciones: ServicioCotizacionDolar ) -> None:
        self._libros = servicio_libros
        self._generos = servicio_generos
        self._editoriales = servicio_editoriales
        self._precios = servicio_precios
        self._stock = servicio_stock
        self._monedas = servicio_monedas
        self._cotizaciones = servicio_cotizaciones

    def ejecutar(self) -> None:
        PrinterUtil.dibujar_separador('INVENTARIO DE LIBRERIA')
        try:
            self._menu("MENÚ PRINCIPAL", [
                ("Gestionar libros", self._menu_libros),
                ("Gestionar géneros", self._menu_generos),
                ("Gestionar editoriales", self._menu_editoriales),
                ("Gestionar precios", self._menu_precios),
                ("Gestionar stock", self._menu_stock),
                ("Cotizaciones del dólar", self._menu_cotizaciones),
            ], salir="Salir")
        except (EOFError, KeyboardInterrupt):
            print()
        print("¡Hasta luego!")

    # ----- Menús -----
    def _menu(self, titulo: str, opciones: List[Opcion], salir: str = "Volver") -> None:
        while True:
            PrinterUtil.dibujar_separador(titulo)
            for i, (texto, _) in enumerate(opciones, start=1):
                print(f"  {i}. {texto}")
            print(f"  0. {salir}")
            eleccion = input("Opción: ").strip()
            if eleccion == "0":
                return
            if not eleccion.isdigit() or not 1 <= int(eleccion) <= len(opciones):
                print("Opción inválida.")
                continue
            try:
                opciones[int(eleccion) - 1][1]()
            except ServicioError as exc:
                print(f"Error: {exc}")
            except RepositorioError as exc:
                print(f"Error de almacenamiento: {exc}")
            except ValidationError as exc:
                for error in exc.errors():
                    print(f"Error: {error['msg']}")
            except KeyboardInterrupt:
                print("\n  Operación cancelada.")

    def _menu_libros(self) -> None:
        self._menu("LIBROS", [
            ("Crear libro", self._crear_libro),
            ("Listar libros", self._listar_libros),
            ("Ver libro por ID", self._ver_libro),
            ("Buscar por título o autor", self._buscar_libros),
            ("Listar por género", self._listar_libros_por_genero),
            ("Actualizar libro", self._actualizar_libro),
            ("Eliminar libro", self._eliminar_libro),
        ])

    def _menu_generos(self) -> None:
        self._menu("GÉNEROS", [
            ("Crear género", self._crear_genero),
            ("Listar géneros", self._listar_generos),
            ("Ver género por ID", self._ver_genero),
            ("Actualizar género", self._actualizar_genero),
            ("Eliminar género", self._eliminar_genero),
        ])

    @staticmethod
    def _elegir_tipo_genero(actual: Optional[GeneroLiterario] = None) -> GeneroLiterario:
        tipos = list(GeneroLiterario)
        print("  Tipos de género:")
        for i, tipo in enumerate(tipos, start=1):
            print(f"    {i}. {tipo.value}")
        if actual is None:
            numero = pedir_entero("Número de tipo", minimo=1)
        else:
            numero = editar_entero("Número de tipo", tipos.index(actual) + 1, minimo=1)
        if numero > len(tipos):
            raise ServicioError("Tipo de género inválido.")
        return tipos[numero - 1]

    def _crear_genero(self) -> None:
        tipo = self._elegir_tipo_genero()
        personalizado = pedir_texto("Nombre del género") if tipo == GeneroLiterario.OTRO else None
        descripcion = pedir_opcional("Descripción")
        genero = self._generos.crear(
            Genero(tipo=tipo, nombre_personalizado=personalizado, descripcion=descripcion)
        )
        print(f"Género creado: [{genero.id}] {genero.nombre}")

    def _listar_generos(self) -> None:
        generos = self._generos.listar()
        if not generos:
            print("(No hay géneros cargados)")
            return
        PrinterUtil.imprimir_tabla(["ID", "Nombre"], [[str(g.id), g.nombre] for g in generos])

    def _ver_genero(self) -> None:
        g = self._generos.obtener(pedir_entero("ID del género", minimo=1))
        print(f"  ID: {g.id}\n  Nombre: {g.nombre}\n  Descripción: {g.descripcion or '-'}")

    def _actualizar_genero(self) -> None:
        actual = self._generos.obtener(pedir_entero("ID del género a actualizar", minimo=1))
        print("  (Enter para conservar el valor actual)")
        tipo = self._elegir_tipo_genero(actual.tipo)
        personalizado: Optional[str] = None
        if tipo == GeneroLiterario.OTRO:
            personalizado = editar_texto("Nombre", actual.nombre_personalizado or "")
        descripcion = editar_texto("Descripción", actual.descripcion or "") or None
        g = self._generos.actualizar(Genero(
            id=actual.id, tipo=tipo, nombre_personalizado=personalizado, descripcion=descripcion,
        ))
        print(f"Género actualizado: [{g.id}] {g.nombre}")

    def _eliminar_genero(self) -> None:
        g = self._generos.obtener(pedir_entero("ID del género a eliminar", minimo=1))
        if confirmar(f"¿Eliminar el género '{g.nombre}'?"):
            self._generos.eliminar(g.id)
            print("Género eliminado.")
        else:
            print("Operación cancelada.")

    def _elegir_genero(self, actual: Optional[Genero] = None) -> Genero:
        generos = self._generos.listar()
        if not generos:
            raise ServicioError("Debe crear al menos un género.")
        print("Géneros disponibles:")
        PrinterUtil.imprimir_tabla(["ID", "Nombre"], [[str(g.id), g.nombre] for g in generos])
        if actual is None:
            return self._generos.obtener(pedir_entero("ID del género", minimo=1))
        return self._generos.obtener(editar_entero("ID del género", actual.id, minimo=1))

    def _elegir_editorial(self, actual: Optional[Editorial] = None) -> Editorial:
        editoriales = self._editoriales.listar()
        if not editoriales:
            raise ServicioError("Debe crear al menos un editorial.")
        print("Editoriales disponibles:")
        PrinterUtil.imprimir_tabla(["ID", "Nombre", "País"], [[str(e.id), e.nombre, e.pais_origen] for e in editoriales])
        if actual is None:
            return self._editoriales.obtener(pedir_entero("ID de editorial", minimo=1))
        return self._editoriales.obtener(editar_entero("ID de editorial", actual.id, minimo=1))

    def _moneda_base(self) -> Moneda:
        moneda = self._monedas.obtener_por_codigo("ARS")
        if moneda:
            return moneda
        monedas = self._monedas.listar()
        if not monedas:
            raise ServicioError("No hay monedas cargadas.")
        return monedas[0]

    def _precios_vigentes(self) -> Dict[int, Precio]:
        moneda = self._moneda_base()
        vigentes: Dict[int, Precio] = {}
        for libro in self._libros.listar():
            precio = self._precios.obtener_vigente(libro.id, moneda.id)
            if precio:
                vigentes[libro.id] = precio
        return vigentes

    def _stock_por_libro(self) -> Dict[int, Stock]:
        return {s.libro.id: s for s in self._stock.listar()}

    @staticmethod
    def _texto_precio(precio: Optional[Precio]) -> str:
        return f"{precio.moneda.simbolo} {precio.valor:,.2f}" if precio else "-"

    def _mostrar_libros(self, libros: List[Libro]) -> None:
        if not libros:
            print("(No se encontraron libros)")
            return
        precios = self._precios_vigentes()
        stocks = self._stock_por_libro()
        PrinterUtil.imprimir_tabla(
            ["ID", "ISBN", "Título", "Autor", "Editorial", "Género", "Precio", "Stock"],
            [[str(l.id), l.isbn, l.titulo, l.autor, l.editorial.nombre, l.genero.nombre,
              self._texto_precio(precios.get(l.id)),
              str(stocks[l.id].cantidad) if l.id in stocks else "-"] for l in libros],
        )

    def _guardar_precio(self, libro: Libro, valor: Decimal) -> None:
        moneda = self._moneda_base()
        hoy = next(
            (p for p in self._precios.historial(libro.id, moneda.id) if p.fecha_vigencia == date.today()),
            None,
        )
        if hoy:
            self._precios.actualizar(hoy.model_copy(update={"libro": libro, "valor": valor}))
        else:
            self._precios.crear(Precio(libro=libro, moneda=moneda, valor=valor))

    def _guardar_stock(self, libro: Libro, cantidad: int) -> None:
        existente = self._stock_por_libro().get(libro.id)
        if existente:
            self._stock.actualizar(existente.model_copy(update={"libro": libro, "cantidad": cantidad}))
        else:
            self._stock.crear(Stock(libro=libro, cantidad=cantidad))

    def _crear_libro(self) -> None:
        isbn = pedir_texto("ISBN-13")
        titulo = pedir_texto("Título")
        autor = pedir_texto("Autor")
        editorial = self._elegir_editorial()
        genero = self._elegir_genero()
        edicion = pedir_entero("Edición", minimo=1)
        idioma = editar_texto("Idioma", "Español")
        paginas = pedir_entero_opcional("Páginas")
        libro = Libro(
            isbn=isbn, titulo=titulo, autor=autor, editorial=editorial, genero=genero,
            edicion=edicion, idioma=idioma, paginas=paginas,
        )
        precio = pedir_decimal("Precio")
        cantidad = pedir_entero("Stock", minimo=0)
        libro = self._libros.crear(libro)
        self._guardar_precio(libro, precio)
        self._guardar_stock(libro, cantidad)
        print(f"Libro creado con ID {libro.id}.")

    def _listar_libros(self) -> None:
        self._mostrar_libros(self._libros.listar())

    def _ver_libro(self) -> None:
        l = self._libros.obtener(pedir_entero("ID del libro", minimo=1))
        precio = self._precios.obtener_vigente(l.id, self._moneda_base().id)
        stock = self._stock_por_libro().get(l.id)
        print(f"ID: {l.id}\n  ISBN: {l.isbn}\n  Título: {l.titulo}\n  Autor: {l.autor}\n"
              f"Editorial: {l.editorial.nombre}\n  Género: {l.genero.nombre}\n"
              f"Edición: {l.edicion}\n  Idioma: {l.idioma}\n  Páginas: {l.paginas or '-'}\n"
              f"Precio: {self._texto_precio(precio)}\n"
              f"Stock: {stock.cantidad if stock else '-'}")

    def _buscar_libros(self) -> None:
        self._mostrar_libros(self._libros.buscar(pedir_texto("Patrón de búsqueda")))

    def _listar_libros_por_genero(self) -> None:
        genero = self._elegir_genero()
        self._mostrar_libros(self._libros.listar_por_genero(genero.id))

    def _actualizar_libro(self) -> None:
        actual = self._libros.obtener(pedir_entero("ID del libro a actualizar", minimo=1))
        isbn = editar_texto("ISBN-13", actual.isbn)
        titulo = editar_texto("Título", actual.titulo)
        autor = editar_texto("Autor", actual.autor)
        editorial = self._elegir_editorial(actual.editorial)
        genero = self._elegir_genero(actual.genero)
        edicion = editar_entero("Edición", actual.edicion, minimo=1)
        idioma = editar_texto("Idioma", actual.idioma)
        paginas = pedir_entero_opcional("Páginas", actual.paginas)
        libro = Libro(
            id=actual.id, isbn=isbn, titulo=titulo, autor=autor, editorial=editorial,
            genero=genero, edicion=edicion, idioma=idioma, paginas=paginas,
        )
        precio_actual = self._precios.obtener_vigente(actual.id, self._moneda_base().id)
        precio = editar_decimal("Precio", precio_actual.valor if precio_actual else None)
        stock_actual = self._stock_por_libro().get(actual.id)
        if stock_actual:
            cantidad: Optional[int] = editar_entero("Stock", stock_actual.cantidad, minimo=0)
        else:
            cantidad = _leer_entero("Stock (opcional)", 0)
        libro = self._libros.actualizar(libro)
        if precio is not None:
            self._guardar_precio(libro, precio)
        if cantidad is not None:
            self._guardar_stock(libro, cantidad)
        print("Libro actualizado correctamente.")

    def _eliminar_libro(self) -> None:
        l = self._libros.obtener(pedir_entero("ID del libro a eliminar", minimo=1))
        if not confirmar(f"¿Eliminar '{l.titulo}' de {l.autor}?"):
            print("Operación cancelada por el usuario.")
            return
        if l.id in self._stock_por_libro():
            self._stock.eliminar(l.id)
        for precio in self._precios.historial(l.id):
            self._precios.eliminar(precio.id)
        self._libros.eliminar(l.id)
        print("Libro eliminado.")


    def _menu_editoriales(self) -> None:
        self._menu("EDITORIALES", [
            ("Crear editorial", self._crear_editorial),
            ("Listar editoriales", self._listar_editoriales),
            ("Ver editorial por ID", self._ver_editorial),
            ("Actualizar editorial", self._actualizar_editorial),
            ("Eliminar editorial", self._eliminar_editorial),
        ])

    def _crear_editorial(self) -> None:
        editorial = self._editoriales.crear(Editorial(
            nombre=pedir_texto("Nombre"),
            pais_origen=pedir_texto("País de origen"),
            email=pedir_opcional("Email"),
            telefono=pedir_opcional("Teléfono (solo dígitos)"),
            sitio_web=pedir_opcional("Sitio web"),
        ))
        print(f"Editorial creada: [{editorial.id}] {editorial.nombre}")

    def _listar_editoriales(self) -> None:
        editoriales = self._editoriales.listar()
        if not editoriales:
            print("No hay editoriales cargadas.")
            return
        PrinterUtil.imprimir_tabla(
            ["ID", "Nombre", "País", "Email", "Teléfono", "Sitio web"],
            [[str(e.id), e.nombre, e.pais_origen, str(e.email or "-"),
              e.telefono or "-", str(e.sitio_web or "-")] for e in editoriales],
        )

    def _ver_editorial(self) -> None:
        e = self._editoriales.obtener(pedir_entero("ID de la editorial", minimo=1))
        print(f"  ID: {e.id}\n  Nombre: {e.nombre}\n  País: {e.pais_origen}\n"
              f"  Email: {e.email or '-'}\n  Teléfono: {e.telefono or '-'}\n  Sitio web: {e.sitio_web or '-'}")

    def _actualizar_editorial(self) -> None:
        actual = self._editoriales.obtener(pedir_entero("ID de la editorial a actualizar", minimo=1))
        editorial = self._editoriales.actualizar(Editorial(
            id=actual.id,
            nombre=editar_texto("Nombre", actual.nombre),
            pais_origen=editar_texto("País de origen", actual.pais_origen),
            email=editar_texto("Email", str(actual.email or "")) or None,
            telefono=editar_texto("Teléfono", actual.telefono or "") or None,
            sitio_web=editar_texto("Sitio web", str(actual.sitio_web or "")) or None,
        ))
        print(f"Editorial actualizada: [{editorial.id}] {editorial.nombre}")

    def _eliminar_editorial(self) -> None:
        e = self._editoriales.obtener(pedir_entero("ID de la editorial a eliminar", minimo=1))
        if confirmar(f"¿Eliminar la editorial '{e.nombre}'?"):
            self._editoriales.eliminar(e.id)
            print("Editorial eliminada.")
        else:
            print("Operación cancelada por el usuario.")



    def _menu_stock(self) -> None:
        self._menu("STOCK", [
            ("Listar stock", self._listar_stock),
            ("Ver stock de un libro", self._ver_stock),
            ("Agregar unidades", self._agregar_stock),
            ("Reducir unidades", self._reducir_stock),
            ("Definir cantidad y mínimo", self._definir_stock),
            ("Listar libros a reponer", self._listar_a_reponer),
            ("Eliminar stock de un libro", self._eliminar_stock),
        ])

    @staticmethod
    def _mostrar_stocks(stocks: List[Stock]) -> None:
        if not stocks:
            print("No hay registros de stock.")
            return
        PrinterUtil.imprimir_tabla(
            ["Libro ID", "Título", "Cantidad", "Mínimo", "Último ingreso", "Reponer"],
            [[str(s.libro.id), s.libro.titulo, str(s.cantidad), str(s.stock_minimo),
              s.fecha_ultimo_ingreso.isoformat() if s.fecha_ultimo_ingreso else "-",
              "SI" if s.necesita_reposicion else "no"] for s in stocks],
        )

    def _listar_stock(self) -> None:
        self._mostrar_stocks(self._stock.listar())

    def _ver_stock(self) -> None:
        self._mostrar_stocks([self._stock.obtener_por_libro(pedir_entero("ID del libro", minimo=1))])

    def _agregar_stock(self) -> None:
        stock = self._stock.agregar(pedir_entero("ID del libro", minimo=1), pedir_entero("Unidades a agregar", minimo=1))
        print(f"Stock actualizado: {stock.cantidad} unidades.")

    def _reducir_stock(self) -> None:
        stock = self._stock.reducir(pedir_entero("ID del libro", minimo=1), pedir_entero("Unidades a reducir", minimo=1))
        print(f"Stock actualizado: {stock.cantidad} unidades.")

    def _definir_stock(self) -> None:
        libro = self._libros.obtener(pedir_entero("ID del libro", minimo=1))
        existente = self._stock_por_libro().get(libro.id)
        if existente:
            cantidad = editar_entero("Cantidad", existente.cantidad, minimo=0)
            minimo = editar_entero("Stock mínimo", existente.stock_minimo, minimo=0)
            self._stock.actualizar(existente.model_copy(update={"cantidad": cantidad, "stock_minimo": minimo}))
        else:
            cantidad = pedir_entero("Cantidad", minimo=0)
            minimo = editar_entero("Stock mínimo", 1, minimo=0)
            self._stock.crear(Stock(libro=libro, cantidad=cantidad, stock_minimo=minimo))
        print("Stock guardado.")

    def _listar_a_reponer(self) -> None:
        self._mostrar_stocks(self._stock.listar_a_reponer())

    def _eliminar_stock(self) -> None:
        stock = self._stock.obtener_por_libro(pedir_entero("ID del libro", minimo=1))
        if confirmar(f"¿Eliminar el stock de '{stock.libro.titulo}'?"):
            self._stock.eliminar(stock.libro.id)
            print("Stock eliminado.")
        else:
            print("Operación cancelada por el usuario.")

    def _menu_precios(self) -> None:
        self._menu("PRECIOS", [
            ("Listar todos los precios", self._listar_precios),
            ("Historial de un libro", self._historial_precios),
            ("Precio vigente de un libro", self._precio_vigente),
            ("Crear precio", self._crear_precio),
            ("Actualizar precio", self._actualizar_precio),
            ("Eliminar precio", self._eliminar_precio),
        ])

    @staticmethod
    def _mostrar_precios(precios: List[Precio]) -> None:
        if not precios:
            print("No hay precios registrados.")
            return
        PrinterUtil.imprimir_tabla(
            ["ID", "Libro ID", "Título", "Moneda", "Valor", "Vigencia"],
            [[str(p.id), str(p.libro.id), p.libro.titulo, p.moneda.codigo,
              f"{p.moneda.simbolo} {p.valor:,.2f}", p.fecha_vigencia.isoformat()] for p in precios],
        )

    def _elegir_moneda(self, actual: Optional[Moneda] = None) -> Moneda:
        monedas = self._monedas.listar()
        if not monedas:
            raise ServicioError("No hay monedas cargadas.")
        PrinterUtil.imprimir_tabla(["ID", "Código", "Nombre"], [[str(m.id), m.codigo, m.nombre] for m in monedas])
        if actual is None:
            return self._monedas.obtener(pedir_entero("ID de la moneda", minimo=1))
        return self._monedas.obtener(editar_entero("ID de la moneda", actual.id, minimo=1))

    def _listar_precios(self) -> None:
        self._mostrar_precios(self._precios.listar())

    def _historial_precios(self) -> None:
        libro = self._libros.obtener(pedir_entero("ID del libro", minimo=1))
        self._mostrar_precios(self._precios.historial(libro.id))

    def _precio_vigente(self) -> None:
        libro = self._libros.obtener(pedir_entero("ID del libro", minimo=1))
        moneda = self._elegir_moneda()
        precio = self._precios.obtener_vigente(libro.id, moneda.id)
        if precio:
            self._mostrar_precios([precio])
        else:
            print("No hay un precio vigente para ese libro y moneda.")

    def _crear_precio(self) -> None:
        libro = self._libros.obtener(pedir_entero("ID del libro", minimo=1))
        moneda = self._elegir_moneda()
        valor = pedir_decimal("Valor")
        fecha = pedir_fecha("Fecha de vigencia", date.today())
        precio = self._precios.crear(Precio(libro=libro, moneda=moneda, valor=valor, fecha_vigencia=fecha))
        print(f"Precio creado con ID {precio.id}.")

    def _actualizar_precio(self) -> None:
        actual = self._precios.obtener(pedir_entero("ID del precio a actualizar", minimo=1))
        print("  (Enter para conservar el valor actual)")
        moneda = self._elegir_moneda(actual.moneda)
        valor = editar_decimal("Valor", actual.valor)
        fecha = pedir_fecha("Fecha de vigencia", actual.fecha_vigencia)
        self._precios.actualizar(actual.model_copy(update={
            "moneda": moneda, "valor": valor, "fecha_vigencia": fecha,
        }))
        print("Precio actualizado.")

    def _eliminar_precio(self) -> None:
        precio = self._precios.obtener(pedir_entero("ID del precio a eliminar", minimo=1))
        if confirmar(f"¿Eliminar el precio {precio.id} de '{precio.libro.titulo}'?"):
            self._precios.eliminar(precio.id)
            print("Precio eliminado.")
        else:
            print("Operación cancelada por el usuario.")


    def _menu_cotizaciones(self) -> None:
        self._menu("COTIZACIONES USD", [
            ("Histórico por tipo", self._historico_cotizaciones),
            ("Última cotización por tipo", self._ultima_cotizacion),
            ("Crear cotización", self._crear_cotizacion),
            ("Actualizar cotización", self._actualizar_cotizacion),
            ("Eliminar cotización", self._eliminar_cotizacion),
            ("Convertir USD a pesos", self._convertir_usd),
        ])

    @staticmethod
    def _elegir_tipo_cotizacion() -> TipoCotizacion:
        tipos = list(TipoCotizacion)
        for i, tipo in enumerate(tipos, start=1):
            print(f"    {i}. {tipo.value}")
        numero = pedir_entero("Número de tipo", minimo=1)
        if numero > len(tipos):
            raise ServicioError("Tipo de cotización inválido.")
        return tipos[numero - 1]

    def _moneda_por_codigo(self, codigo: str) -> Moneda:
        moneda = self._monedas.obtener_por_codigo(codigo)
        if not moneda:
            raise ServicioError(f"No existe la moneda '{codigo}'.")
        return moneda

    @staticmethod
    def _mostrar_cotizaciones(cotizaciones: List[CotizacionDolar]) -> None:
        if not cotizaciones:
            print("No hay cotizaciones registradas.")
            return
        PrinterUtil.imprimir_tabla(
            ["Tipo", "Fecha", "Par", "Compra", "Venta"],
            [[c.tipo.value, c.fecha.strftime("%Y-%m-%d %H:%M"),
              f"{c.moneda_origen.codigo}/{c.moneda_destino.codigo}",
              f"{c.valor_compra:,.2f}", f"{c.valor_venta:,.2f}"] for c in cotizaciones]
        )

    def _historico_cotizaciones(self) -> None:
        self._mostrar_cotizaciones(self._cotizaciones.historico(self._elegir_tipo_cotizacion()))

    def _ultima_cotizacion(self) -> None:
        self._mostrar_cotizaciones([self._cotizaciones.obtener_ultima(self._elegir_tipo_cotizacion())])

    def _crear_cotizacion(self) -> None:
        tipo = self._elegir_tipo_cotizacion()
        compra = pedir_decimal("Compra")
        venta = pedir_decimal("Venta")
        fecha = pedir_fecha("Fecha", date.today())
        self._cotizaciones.crear(CotizacionDolar(
            tipo=tipo,
            moneda_origen=self._moneda_por_codigo("USD"),
            moneda_destino=self._moneda_por_codigo("ARS"),
            valor_compra=compra,
            valor_venta=venta,
            fecha=datetime.combine(fecha, time(12, 0))
        ))
        print("Cotización creada.")

    def _actualizar_cotizacion(self) -> None:
        tipo = self._elegir_tipo_cotizacion()
        fecha = pedir_fecha("Fecha de la cotización", date.today())
        actual = self._cotizaciones.obtener(tipo, fecha)
        compra = editar_decimal("Compra", actual.valor_compra)
        venta = editar_decimal("Venta", actual.valor_venta)
        self._cotizaciones.actualizar(CotizacionDolar(
            id=actual.id,
            tipo=actual.tipo,
            moneda_origen=actual.moneda_origen,
            moneda_destino=actual.moneda_destino,
            valor_compra=compra,
            valor_venta=venta,
            fecha=actual.fecha
        ))
        print("Cotización actualizada.")

    def _eliminar_cotizacion(self) -> None:
        tipo = self._elegir_tipo_cotizacion()
        fecha = pedir_fecha("Fecha de la cotización", date.today())
        self._cotizaciones.obtener(tipo, fecha)
        if confirmar(f"¿Eliminar la cotización {tipo.value} del {fecha.isoformat()}?"):
            self._cotizaciones.eliminar(tipo, fecha)
            print("Cotización eliminada.")
        else:
            print("Operación cancelada por el usuario.")

    def _convertir_usd(self) -> None:
        tipo = self._elegir_tipo_cotizacion()
        monto = pedir_decimal("Monto en USD")
        usar_venta = confirmar("¿Usar cotización de venta? (n = compra)")
        total = self._cotizaciones.convertir(monto, tipo, usar_venta)
        print(f"USD {monto:,.2f} = ARS {total:,.2f} (dólar {tipo.value})")
