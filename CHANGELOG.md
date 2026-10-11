## [Correcciones]
Se corrigieron las siguientes observaciones:
- Encapsulamiento: EntidadBase ahora usa model_config = ConfigDict(validate_assignment=True), de modo que toda asignación a un atributo vuelve a pasar por las validaciones (semántica de setter). Se agregaron properties derivadas a las clases. Debido a restricciones de Pydantic no es posible declarar los atributos como privados. Las lases no Pydantic como repositorios, servicios y consola cuentan con atributos privados y @property de solo lectura.
-  TipoCotizacion como entidad ya no es Enum, sino que es una clase con nombre y descripcion como atributos, se implementó RepositorioTipoCotizacion en repositories.py y CotizacionDolar.tipo es ahora una instancia de TipoCotizacion. Nuevo ServicioTipoCotizacion con CRUD en servicios.py.
- Los archivos csv ahora se escriben correctamente en el directorio migration/csv/ y se agregó tipo_cotizacion.csv generado por preload_data.py.
- Se agregaron Gestionar monedas y Gestionar tipos de cotización al menú del main para acceder sus CRUD correspondientes.

## [Ejercicio 07]
- Implementación de lógica en archivo main.py para ejecutar el sistema de inventario.
- Ajustes en modelos de entidades, repositorios y servicios.

## [Ejercicio 06]
- Implementación lógica para interfaz de usuario en console.py.

## [Ejercicio 05]
- Implementación lógica de importación y precarga de datos en preload_data.py + pruebas unitarias. 

## [Ejercicio 04]
- Implementación de las clases de servicios sobre operaciones cada entidad en services.py.
- Ajuste de modelos en entities.py para integración con las clases de servicios.
- Ajuste de repositorios en repositories.py para integración con clases de servicios.

## [Ejercicio 03]
- Implementación de interfaces y clases para manejar la persistencia de los datos en el archivo repositories.py.
- Ajustes en las entidades de entities.py por inconsistencias en las validaciones.
- Pruebas unitarias de instanciación y validaciones de las entidades.

## [Ejercicio 02]
- Definición de las clases/entidades involucradas.
- Validaciones de atributos con Pydantic.

## [Ejercicio 01]
- Creación de la estructura del directorio y archivos correspondientes.
- Actualización de los archivos README.md y CHANGELOG.md