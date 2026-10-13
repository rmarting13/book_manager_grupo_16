import os

from dotenv import load_dotenv

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import ejecutar_migracion
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
    RepositorioTipoCotizacion,
)
from book_manager.services.services import (
    MonedaServicio,
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioPrecio,
    ServicioStock,
    ServicioTipoCotizacion,
)
from book_manager.ui.console import ConsolaInventario

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(BASE_DIR, 'migrations/csv')
RUTA_SQL = os.path.join(BASE_DIR, 'migrations/sql')


def main(import_default_data: bool = False) -> None:
    load_dotenv()

    RUTA_BD: str = os.getenv("SQLALCHEMY_DATABASE_URL", "")
    PASSWORD: str = os.getenv("SUPABASE_DB_PASSWORD", "")
    URL_BD: str = RUTA_BD.replace("[YOUR-PASSWORD]", PASSWORD)

    conexion = ConexionDB(URL_BD)
    conexion.crear_tablas()

    if import_default_data:
        ejecutar_migracion(conexion, RUTA_SQL)

    repo_moneda = RepositorioMoneda(conexion)
    repo_genero = RepositorioGenero(conexion)
    repo_editorial = RepositorioEditorial(conexion)
    repo_libro = RepositorioLibro(conexion)
    repo_precio = RepositorioPrecio(conexion)
    repo_stock = RepositorioStock(conexion)
    repo_tipo_cotizacion = RepositorioTipoCotizacion(conexion)
    repo_cotizacion = RepositorioCotizacionDolar(conexion)

    consola = ConsolaInventario(    ServicioLibro(repo_libro, repo_editorial, repo_genero, repo_precio, repo_stock),
                                    ServicioGenero(repo_genero, repo_libro),
                                    ServicioEditorial(repo_editorial, repo_libro),
                                    ServicioPrecio(repo_precio, repo_libro, repo_moneda),
                                    ServicioStock(repo_stock, repo_libro),
                                    MonedaServicio(repo_moneda, repo_precio, repo_cotizacion),
                                    ServicioCotizacionDolar(repo_cotizacion, repo_moneda, repo_tipo_cotizacion),
                                    ServicioTipoCotizacion(repo_tipo_cotizacion, repo_cotizacion) )
                                
    
    consola.ejecutar()


if __name__ == '__main__':
    main(import_default_data = False)
