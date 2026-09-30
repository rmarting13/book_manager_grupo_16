import os

from book_manager.entities.entities import ArchivoCsv
from book_manager.preload_data.preload_data import precargar_datos
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
)
from book_manager.services.services import (
    MonedaServicio,
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioPrecio,
    ServicioStock,
)
from book_manager.ui.console import ConsolaInventario

RUTA_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')


def main(import_default_data: bool = False) -> None:
    
    if import_default_data:
        precargar_datos(RUTA_CSV)

    def ruta(archivo: ArchivoCsv) -> str:
        return os.path.join(RUTA_CSV, archivo.value)

    repo_moneda = RepositorioMoneda(ruta(ArchivoCsv.MONEDA))
    repo_genero = RepositorioGenero(ruta(ArchivoCsv.GENERO))
    repo_editorial = RepositorioEditorial(ruta(ArchivoCsv.EDITORIAL))
    repo_libro = RepositorioLibro(ruta(ArchivoCsv.LIBRO), repo_editorial, repo_genero)
    repo_precio = RepositorioPrecio(ruta(ArchivoCsv.PRECIO), repo_libro, repo_moneda)
    repo_stock = RepositorioStock(ruta(ArchivoCsv.STOCK), repo_libro)
    repo_cotizacion = RepositorioCotizacionDolar(ruta(ArchivoCsv.COTIZACION), repo_moneda)

    consola = ConsolaInventario(    ServicioLibro(repo_libro, repo_editorial, repo_genero, repo_precio, repo_stock),
                                    ServicioGenero(repo_genero, repo_libro),
                                    ServicioEditorial(repo_editorial, repo_libro),
                                    ServicioPrecio(repo_precio, repo_libro, repo_moneda),
                                    ServicioStock(repo_stock, repo_libro),
                                    MonedaServicio(repo_moneda, repo_precio, repo_cotizacion),
                                    ServicioCotizacionDolar(repo_cotizacion, repo_moneda) )
                                
    
    consola.ejecutar()


if __name__ == '__main__':
    main(import_default_data = True)
