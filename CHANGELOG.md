## [Ejercicio 08]
- Implementación de lógica en console.py para nuevas funcionalidades en menú principal:
    - Obtener las cotizaciones por api
    - Ver lista de precios bimonetaria
    - Exportar precios a CSV
- Pruebas unitarias.
- Actualización del CHANGELOG.md

## [Ejercicio 07]
- Modificación del servicio ServicioCotizacionDolar en services.py para obtener las cotizaciones desde la API dolarapi. 
- Pruebas unitarias del consumo de la API desde el servicio ServicioCotizacionDolar.
- Actualización del CHANGELOG.md

## [Ejercicio 06]
- Implementación de modificaciones en repositories.py para que el sistema utilice la base de datos y desestime la persistencia de datos mediante archivos locales. 
- Pruebas unitarias.
- Actualización del CHANGELOG.md

## [Ejercicio 05]
- Implementación de lógica en migrations.py para generar los scripts .sql a partir de las entradas en los archivos .csv de migration/csv. 
- Pruebas unitarias de ejecución de los scripts .sql para la migración a Supabase
- Actualización del CHANGELOG.md

## [Ejercicio 04]
- Implementación de lógica en models.py para crear las tablas del sistema con sus tipos de datos y relaciones. Se utilizó la librería sqlalchemy para importar tipos de datos y funciones del módulo ORM para mapear los modelos.
- Modificación de la clase ConexionDB para adaptar el uso de los modelos definidos en models.py. Se reemplazó la conexión SQLite por PosgreSQL para conectar con Supabase.
- Pruebas unitarias
- Actualización del CHANGELOG.md

## [Ejercicio 03]
- Modificación de la clase ConexionDB para implementar un context manager para manejar las transacciones a la base de datos.
- Pruebas unitarias
- Actualización del CHANGELOG.md

## [Ejercicio 02]
- Implementación de clase ConexionDB para gestionar la conexión usando SQLAlchemy.
- Pruebas unitarias de querys SQL
- Actualización de entities.py, repositorio.py, preload_data.py y console.py por atributos adicionales en la entidad Libro.
- Actualización del CHANGELOG.md

## [Ejercicio 01]
- Creación de la estructura del directorio y archivos correspondientes.
- Actualización de los archivos README.md y CHANGELOG.md