from datetime import date, datetime, timedelta
from decimal import Decimal
import os
from typing import List

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    GeneroLiterario,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
    ArchivoCsv
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

def precargar_datos(ruta_csv: str) -> None:
    """Genera archivos CSV de datos iniciales para todas las entidades.

    Args:
        ruta_csv: Carpeta donde se crearán los CSV de persistencia.
    """

    for archivo in ArchivoCsv:
        ruta = os.path.join(ruta_csv, archivo.value)
        if os.path.exists(ruta):
            os.remove(ruta)

    repo_moneda = RepositorioMoneda(os.path.join(ruta_csv, ArchivoCsv.MONEDA.value))
    repo_genero = RepositorioGenero(os.path.join(ruta_csv, ArchivoCsv.GENERO.value))
    repo_editorial = RepositorioEditorial(os.path.join(ruta_csv, ArchivoCsv.EDITORIAL.value))
    repo_libro = RepositorioLibro(os.path.join(ruta_csv, ArchivoCsv.LIBRO.value), repo_editorial, repo_genero)
    repo_precio = RepositorioPrecio(os.path.join(ruta_csv, ArchivoCsv.PRECIO.value), repo_libro, repo_moneda)
    repo_stock = RepositorioStock(os.path.join(ruta_csv, ArchivoCsv.STOCK.value), repo_libro)
    repo_cotizacion = RepositorioCotizacionDolar(os.path.join(ruta_csv, ArchivoCsv.COTIZACION.value), repo_moneda)

    monedas = [
        Moneda(codigo="ARS", nombre="Peso argentino", simbolo="$"),
        Moneda(codigo="USD", nombre="Dólar estadounidense", simbolo="US$"),
        Moneda(codigo="EUR", nombre="Euro", simbolo="€"),
        Moneda(codigo="GBP", nombre="Libra esterlina", simbolo="£"),
        Moneda(codigo="BRL", nombre="Real brasileño", simbolo="R$"),
        Moneda(codigo="CLP", nombre="Peso chileno", simbolo="CLP$"),
        Moneda(codigo="UYU", nombre="Peso uruguayo", simbolo="$U"),
        Moneda(codigo="PYG", nombre="Guaraní paraguayo", simbolo="₲"),
        Moneda(codigo="MXN", nombre="Peso mexicano", simbolo="MX$"),
        Moneda(codigo="COP", nombre="Peso colombiano", simbolo="COL$")
    ]
    monedas = [repo_moneda.crear(moneda) for moneda in monedas]

    generos = [
        Genero(tipo=GeneroLiterario.NOVELA, descripcion="Narrativa de ficción de extensión media o larga."),
        Genero(tipo=GeneroLiterario.ENSAYO, descripcion="Obras de análisis y reflexión."),
        Genero(tipo=GeneroLiterario.POESIA, descripcion="Composición literaria en verso o prosa poética."),
        Genero(tipo=GeneroLiterario.TEATRO, descripcion="Textos dramáticos para representación escénica."),
        Genero(tipo=GeneroLiterario.INFANTIL, descripcion="Literatura orientada a lectores niños y niñas."),
        Genero(tipo=GeneroLiterario.CIENCIA_FICCION, descripcion="Relatos de ciencia y futuros posibles."),
        Genero(tipo=GeneroLiterario.FANTASIA, descripcion="Mundos y elementos imaginarios."),
        Genero(tipo=GeneroLiterario.BIOGRAFIA, descripcion="Relatos de vida de personas reales."),
        Genero(tipo=GeneroLiterario.HISTORIA, descripcion="Obras sobre procesos y hechos históricos."),
        Genero(tipo=GeneroLiterario.OTRO, nombre_personalizado="Novela gráfica", descripcion="Historias narradas con fuerte componente visual.")
    ]
    generos = [repo_genero.crear(genero) for genero in generos]

    editoriales = [
        Editorial(nombre="Planeta", pais_origen="Argentina", email="contacto@planeta.com.ar", sitio_web="https://www.planetadelibros.com.ar"),
        Editorial(nombre="Sudamericana", pais_origen="Argentina", email="info@sudamericana.com.ar", sitio_web="https://www.megustaleer.com.ar"),
        Editorial(nombre="Alfaguara", pais_origen="España", email="atencion@alfaguara.com", sitio_web="https://www.penguinlibros.com"),
        Editorial(nombre="Anagrama", pais_origen="España", email="info@anagrama-ed.es", sitio_web="https://www.anagrama-ed.es"),
        Editorial(nombre="Tusquets", pais_origen="España", email="contacto@tusquetseditores.com", sitio_web="https://www.tusquetseditores.com"),
        Editorial(nombre="Seix Barral", pais_origen="España", email="consultas@seix-barral.es", sitio_web="https://www.planetadelibros.com"),
        Editorial(nombre="Eterna Cadencia", pais_origen="Argentina", email="editorial@eternacadencia.com.ar", sitio_web="https://eternacadencia.com.ar"),
        Editorial(nombre="Siglo XXI", pais_origen="México", email="ventas@sigloxxieditores.com", sitio_web="https://www.sigloxxieditores.com"),
        Editorial(nombre="Debolsillo", pais_origen="España", email="hola@debolsillo.com", sitio_web="https://www.penguinlibros.com"),
        Editorial(nombre="Paidós", pais_origen="Argentina", email="info@paidos.com.ar", sitio_web="https://www.planetadelibros.com.ar"),
    ]
    editoriales = [repo_editorial.crear(editorial) for editorial in editoriales]

    datos_libros = [
        ('9788420633121',"Ficciones", "Jorge Luis Borges", 0, 0, 3, "Español", 224),
        ('9788439732471',"Cien años de soledad", "Gabriel García Márquez", 1, 0, 1, "Español", 471),
        ('978-84-20-41470-6',"Rayuela", "Julio Cortázar", 2, 0, 2, "Español", 736),
        ('9788466301169',"La ciudad y los perros", "Mario Vargas Llosa", 3, 0, 1, "Español", 464),
        ('9788433910868',"Los detectives salvajes", "Roberto Bolaño", 4, 0, 1, "Español", 623),
        ('978-98-77-25411-2',"Dune", "Frank Herbert", 5, 5, 1, "Español", 784),
        ('978-84-01-35279-9',"El nombre del viento", "Patrick Rothfuss", 8, 6, 1, "Español", 872),
        ('9788499924212',"Sapiens", "Yuval Noah Harari", 7, 1, 1, "Español", 496),
        ('9789504949930',"La tregua", "Mario Benedetti", 6, 0, 2, "Español", 240),
        ('978-98-73-65038-3',"Maus", "Art Spiegelman", 9, 9, 1, "Español", 296)
    ]

    libros: List[Libro] = []
    for reg in datos_libros:
        libro = Libro(
            isbn=reg[0],
            titulo=reg[1],
            autor=reg[2],
            editorial=editoriales[reg[3]],
            genero=generos[reg[4]],
            edicion=reg[5],
            idioma=reg[6],
            paginas=reg[7]
        )
        libros.append(repo_libro.crear(libro))

    hoy = date.today()
    precios: List[Precio] = []
    for indice, libro in enumerate(libros):
        moneda = monedas[0] if indice < 7 else monedas[1]
        base = Decimal("12500") + Decimal(indice * 1700)
        precio = Precio(libro=libro, moneda=moneda, valor=base, fecha_vigencia=hoy - timedelta(days=indice))
        precios.append(repo_precio.crear(precio))

    stock_datos = [
        (20, 5),
        (3, 5),
        (14, 4),
        (1, 3),
        (7, 7),
        (2, 6),
        (30, 8),
        (5, 4),
        (0, 2),
        (9, 3),
    ]
    for indice, libro in enumerate(libros):
        cantidad, minimo = stock_datos[indice]
        repo_stock.crear(
            Stock(
                libro=libro,
                cantidad=cantidad,
                stock_minimo=minimo,
                fecha_ultimo_ingreso=hoy - timedelta(days=indice * 3),
            )
        )

    usd = next(moneda for moneda in monedas if moneda.codigo == "USD")
    ars = next(moneda for moneda in monedas if moneda.codigo == "ARS")
    fecha_base = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    cotizaciones = [
        (TipoCotizacion.OFICIAL, Decimal("1120"), Decimal("1160"), 0),
        (TipoCotizacion.BLUE, Decimal("1280"), Decimal("1315"), 0),
        (TipoCotizacion.MEP, Decimal("1230"), Decimal("1258"), 0),
        (TipoCotizacion.OFICIAL, Decimal("1110"), Decimal("1148"), 1),
        (TipoCotizacion.BLUE, Decimal("1265"), Decimal("1298"), 1),
        (TipoCotizacion.MEP, Decimal("1218"), Decimal("1240"), 1),
        (TipoCotizacion.OFICIAL, Decimal("1102"), Decimal("1139"), 2),
        (TipoCotizacion.BLUE, Decimal("1257"), Decimal("1290"), 2),
        (TipoCotizacion.MEP, Decimal("1204"), Decimal("1232"), 2),
        (TipoCotizacion.OFICIAL, Decimal("1096"), Decimal("1130"), 3),
    ]
    for tipo, compra, venta, dias_atras in cotizaciones:
        repo_cotizacion.crear(
            CotizacionDolar(
                tipo=tipo,
                moneda_origen=usd,
                moneda_destino=ars,
                valor_compra=compra,
                valor_venta=venta,
                fecha=fecha_base - timedelta(days=dias_atras),
            )
        )


# Pruebas unitarias:
if __name__ == '__main__':

    def dibujar_separador(text: str) -> None:
        print(f"\n{'─' * 50}")
        print(f"  {text}")
        print(f"{'─' * 50}")

    carpeta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'migrations')
    
    dibujar_separador("1. Precarga")
    
    precargar_datos(carpeta)
    
    for archivo in ArchivoCsv:
        ruta = os.path.join(carpeta, archivo.value)
        assert os.path.exists(ruta), f"Falta {archivo.value}"
        print(f"OK {archivo.value}")

    repo_moneda = RepositorioMoneda(os.path.join(carpeta, ArchivoCsv.MONEDA.value))
    repo_genero = RepositorioGenero(os.path.join(carpeta, ArchivoCsv.GENERO.value))
    repo_editorial = RepositorioEditorial(os.path.join(carpeta, ArchivoCsv.EDITORIAL.value))
    repo_libro = RepositorioLibro(os.path.join(carpeta, ArchivoCsv.LIBRO.value), repo_editorial, repo_genero)
    repo_precio = RepositorioPrecio(os.path.join(carpeta, ArchivoCsv.PRECIO.value), repo_libro, repo_moneda)
    repo_stock = RepositorioStock(os.path.join(carpeta, ArchivoCsv.STOCK.value), repo_libro)
    repo_cotizacion = RepositorioCotizacionDolar(os.path.join(carpeta, ArchivoCsv.COTIZACION.value), repo_moneda)

    dibujar_separador("2. Cantidades cargadas")
    libros = repo_libro.leer_todos()
    cantidades = {
        "monedas": len(repo_moneda.leer_todos()),
        "generos": len(repo_genero.leer_todos()),
        "editoriales": len(repo_editorial.leer_todos()),
        "libros": len(libros),
        "precios": len(repo_precio.leer_todos()),
        "stock": len(repo_stock.leer_todos()),
    }
    for nombre, cantidad in cantidades.items():
        assert cantidad > 0, f"Sin datos de {nombre}"
        print(f"{nombre}: {cantidad}")

    dibujar_separador("3. Integridad de datos")
    isbns = [libro.isbn for libro in libros]
    assert len(isbns) == len(set(isbns)), "ISBN duplicados"
    print("ISBN únicos")
    for libro in libros:
        assert repo_stock.leer_por_libro(libro.id) is not None, f"Sin stock: {libro.titulo}"
    print("Todos los libros tienen stock")

    dibujar_separador("4. Cotizaciones")
    for tipo in TipoCotizacion:
        historico = repo_cotizacion.leer_historico_por_tipo(tipo)
        assert historico, f"Sin cotizaciones {tipo.value}"
        print(f"{tipo.value}: {len(historico)} registros")
        print(historico[0])
