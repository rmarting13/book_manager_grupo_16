import csv
import os
from typing import Optional, Sequence
from sqlalchemy import text
from book_manager.entities.entities import ArchivoCsv
from book_manager.database.connection import ConexionDB
from book_manager.utilities.utilities import PrinterUtil

TABLA_EDITORIALES = "editoriales"
TABLA_GENEROS = "generos"
TABLA_MONEDAS = "monedas"
TABLA_TIPOS_COTIZACION = "tipos_cotizacion"
TABLA_LIBROS = "libros"
TABLA_PRECIOS = "precios"
TABLA_STOCK = "stock"
TABLA_COTIZACIONES = "cotizaciones"


ORDEN_MIGRACION: Sequence[tuple[str, str]] = (
    (TABLA_EDITORIALES, ArchivoCsv.EDITORIAL),
    (TABLA_GENEROS, ArchivoCsv.GENERO),
    (TABLA_MONEDAS, ArchivoCsv.MONEDA),
    (TABLA_TIPOS_COTIZACION, ArchivoCsv.TIPO_COTIZACION),
    (TABLA_LIBROS, ArchivoCsv.LIBRO),
    (TABLA_PRECIOS, ArchivoCsv.PRECIO),
    (TABLA_STOCK, ArchivoCsv.STOCK),
    (TABLA_COTIZACIONES, ArchivoCsv.COTIZACION)
)

COLUMNAS_NUMERICAS: dict[str, set[str]] = {
    TABLA_EDITORIALES: {"id"},
    TABLA_GENEROS: {"id"},
    TABLA_MONEDAS: {"id"},
    TABLA_TIPOS_COTIZACION: {"id"},
    TABLA_LIBROS: {"id", "editorial_id", "genero_id", "edicion", "paginas", "peso"},
    TABLA_PRECIOS: {"id", "libro_id", "moneda_id"},
    TABLA_STOCK: {"id", "libro_id", "cantidad", "stock_minimo"},
    TABLA_COTIZACIONES: {
        "id",
        "tipo_id",
        "moneda_origen_id",
        "moneda_destino_id",
    },
}

COLUMNAS_DECIMALES: dict[str, set[str]] = {
    TABLA_PRECIOS: {"valor"},
    TABLA_COTIZACIONES: {"valor_compra", "valor_venta"},
}


def _leer_csv(ruta_csv: str) -> list[dict[str, str]]:
    """Lee un archivo CSV y devuelve sus filas como diccionarios.

    Args:
        ruta_csv: Ruta del archivo CSV a leer.

    Returns:
        Lista de filas, cada una como diccionario columna-valor.
    """
    with open(ruta_csv, encoding="utf-8", newline="") as archivo:
        return [fila for fila in csv.DictReader(archivo)]


def _literal_sql(tabla: str, columna: str, valor: Optional[str]) -> str:
    """Convierte el valor de una celda CSV en un literal SQL.

    Args:
        tabla: Nombre de la tabla a la que pertenece la columna.
        columna: Nombre de la columna.
        valor: Valor leído del CSV, o ``None`` si la celda está vacía.

    Returns:
        El literal SQL correspondiente: ``NULL``, un número sin comillas o
        una cadena entre comillas simples.
    """
    if valor is None or valor.strip() == "":
        return "NULL"
    valor = valor.strip()
    if columna in COLUMNAS_NUMERICAS.get(tabla, set()):
        return valor
    if columna in COLUMNAS_DECIMALES.get(tabla, set()):
        return valor
    return f"'{valor.replace("'", "''")}'" #Escapa las comillas simples de un valor de texto para SQL


def _sentencias_insert(tabla: str, filas: Sequence[dict[str, str]]) -> list[str]:
    """Genera las sentencias ``INSERT`` para las filas de una tabla.

    Args:
        tabla: Nombre de la tabla destino.
        filas: Filas leídas del CSV de origen.

    Returns:
        Lista con una sentencia ``INSERT`` por cada fila.
    """
    sentencias: list[str] = []
    for fila in filas:
        columnas = [columna for columna in fila.keys() if columna]
        valores = [_literal_sql(tabla, columna, fila[columna]) for columna in columnas]
        sentencias.append(
            f"INSERT INTO {tabla} ({', '.join(columnas)}) "
            f"VALUES ({', '.join(valores)});"
        )
    return sentencias


def _escribir_sql(ruta_sql: str, tabla: str, sentencias: Sequence[str]) -> None:
    """Escribe en disco el archivo ``.sql`` con las sentencias de una tabla.

    Args:
        ruta_sql: Ruta del archivo ``.sql`` a generar.
        tabla: Nombre de la tabla migrada.
        sentencias: Sentencias ``INSERT`` a guardar.
    """
    with open(ruta_sql, "w", encoding="utf-8", newline="\n") as archivo:
        archivo.write("\n".join(sentencias))
        archivo.write("\n")

def _reajustar_secuencias(conexion: ConexionDB, tablas: Sequence[str]) -> None:
    """Sincroniza las secuencias de las claves primarias tras la inserción.

    Los ``INSERT`` con ``id`` explícito desfasan la columna ``SERIAL``. 
    Esta función la reajusta al máximo valor existente en cada tabla.

    Args:
        conexion: Conexión a la base de datos.
        tablas: Tablas cuyas secuencias se deben reajustar.
    """
    for tabla in tablas:
        conexion.ejecutar_query(
            f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {tabla}), 1), "
            f"(SELECT COUNT(*) > 0 FROM {tabla}));"
        )

def migrar_datos(carpeta_csvs: str, carpeta_sqls: str) -> None:
    """Función encargada de la migración de datos de csv a sql.

    Se encarga de leer los archivos csv y crear los archivos sql
    para la inserción en la base de datos.

    Args:
        carpeta_csvs (str): Carpeta donde se encuentran los archivos csv de origen.
        carpeta_sqls (str): Carpeta donde se deben guardar los archivos sql generados.
    """
    os.makedirs(carpeta_sqls, exist_ok=True)

    tablas_migradas: list[str] = []
    total_registros = 0

    for tabla, archivo in ORDEN_MIGRACION:
        ruta_csv = os.path.join(carpeta_csvs, archivo)
        if not os.path.exists(ruta_csv):
            PrinterUtil.dibujar_separador(f"AVISO: no se encontró {archivo}, se omite")
            continue

        filas = _leer_csv(ruta_csv)
        sentencias = _sentencias_insert(tabla, filas)
        ruta_sql = os.path.join(carpeta_sqls, f"{tabla}.sql")
        _escribir_sql(ruta_sql, tabla, sentencias)

        tablas_migradas.append(tabla)
        total_registros += len(sentencias)
        print(f"{tabla}: {len(sentencias)} sentencias escritas en {ruta_sql}")

    PrinterUtil.dibujar_separador(
        f"Migración finalizada: {len(tablas_migradas)} tablas, {total_registros} registros"
    )


def cargar_datos_sql(conexion: ConexionDB, ruta_sql: str) -> int:
    """Carga en la base de datos las sentencias de un archivo ``.sql``.

    Lee el archivo indicado, ejecuta cada sentencia dentro de una única
    transacción y devuelve la cantidad de sentencias ejecutadas.

    Args:
        conexion: Conexión a la base de datos destino.
        ruta_sql: Ruta del archivo ``.sql`` con las sentencias a ejecutar.

    Returns:
        Cantidad de sentencias ejecutadas.

    Raises:
        FileNotFoundError: Si el archivo indicado no existe.
    """
    with open(ruta_sql, encoding="utf-8") as archivo_sql:
        sentencias = [linea.strip() for linea in archivo_sql if linea.strip()]

    with conexion.transaccion() as transaccion:
        for sentencia in sentencias:
            transaccion.execute(text(sentencia))

    return len(sentencias)


def ejecutar_migracion(conexion: ConexionDB, carpeta_sqls: str) -> None:
    """Migra los datos de los CSV y los inserta en la base de datos.

    Lee los archivos ``.sql`` y ejecuta sus sentencias para migrar los datos a la DB.

    Args:
        conexion: Conexión a la base de datos destino.
        carpeta_sqls: Carpeta donde se guardan los archivos sql generados.
    """
    conexion.eliminar_tablas()
    conexion.crear_tablas()

    tablas_insertadas: list[str] = []
    total_insertado = 0

    for tabla, archivo in ORDEN_MIGRACION:
        ruta_sql = os.path.join(carpeta_sqls, f"{tabla}.sql")
        if not os.path.exists(ruta_sql):
            continue

        cantidad = cargar_datos_sql(conexion, ruta_sql)

        tablas_insertadas.append(tabla)
        total_insertado += cantidad
        print(f"{tabla}: {cantidad} registros insertados")

    _reajustar_secuencias(conexion, tablas_insertadas)
    
    PrinterUtil.dibujar_separador(f"Base poblada: {len(tablas_insertadas)} tablas, {total_insertado} registros")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    RUTA_BD: str = os.getenv("SQLALCHEMY_DATABASE_URL", "")
    PASSWORD: str = os.getenv("SUPABASE_DB_PASSWORD", "")
    URL_BD: str = RUTA_BD.replace("[YOUR-PASSWORD]", PASSWORD)

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CARPETA_CSVS = os.path.join(BASE_DIR, "migrations", "csv")
    CARPETA_SQLS = os.path.join(BASE_DIR, "migrations", "sql")

    PrinterUtil.dibujar_separador("1. Migración de CSV a archivos SQL")
    migrar_datos(CARPETA_CSVS, CARPETA_SQLS)

    PrinterUtil.dibujar_separador("2. Poblado de la base de datos")
    conexion = ConexionDB(URL_BD)
    ejecutar_migracion(conexion, CARPETA_SQLS)

    PrinterUtil.dibujar_separador("3. Verificación de los datos migrados")
    for tabla, _ in ORDEN_MIGRACION:
        filas = conexion.ejecutar_query(f"SELECT COUNT(*) FROM {tabla};")
        print(f"{tabla}: {filas[0][0]} filas")

    PrinterUtil.dibujar_separador("4. Cierre de la conexión")
    conexion.cerrar()
    print("Conexión cerrada.")
