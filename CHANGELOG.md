## [Ejercicio 06]
- Implementación del decorador (función) `auditar` definido en el archivo `utilities/auditoria.py`. Esta función se implementó como decorador en todos los métodos públicos de las clases en `services.py` con los cuales el usuario tiene interacción desde la consola, registrando cada operación realizada por el usuario.
- Pruebas unitarias del decorador y su función log que escribe el archivo en `utilities/logs`.
- Actualización del archivo `CHANGELOG.md`.

## [Ejercicio 05]
- Implementación del archivo `reportes/reportes.py` que cuya clase `ReporteAlertasPrecios` se encarga de generar un reporte XLSX de libros y diferencias de precios a partir de los archivos CSV de alerta de precios generados por el scraper.
- Actualización de los archivos `CHANGELOG.md` y `requirements.txt`

## [Ejercicio 04]
- Se implementó el pipeline `AlertaPreciosPipeline`  en `cuspide_scraper` para procesar la comparación de precios entre el catálogo de la base de datos y los obtenidos del sitio web.
- Se modificó `DuplicadosPipeline` para mejorar la coincidencia con el catálogo: el libro del sitio debe coincidir en título y autor con un libro de la BD, si no coincide en ambos se descarta con `DropItem`.
- Actualización de los archivos `CHANGELOG.md`

## [Ejercicio 03]
- Implementación del scraper `cuspide_scraper` al proyecto con configuración, spider, items, loaders y pipelines. El scraper cuenta con integración con la base de datos para levantar el catálogo de libros a buscar directamente desde la BD en Supabase.
- Pruebas unitarias desde la terminal. Se generó el archivo `scraper/cuspide_scraper/downloads/cuspide.py` con los resultados.
- Actualización de los archivos `requirements.txt` y `CHANGELOG.md`

## [Ejercicio 02]
- Creación de la función `cargar_datos_sql` en el archivo `migrations.py`. La función se reutiliza en la función `ejecutar_migracion` reemplazando la lógica de lectura y ejecución de sentencias sql.
- Actualización de los archivos README.md y CHANGELOG.md

## [Ejercicio 01]
- Creación de la estructura del directorio y archivos correspondientes.
- Actualización de los archivos README.md y CHANGELOG.md