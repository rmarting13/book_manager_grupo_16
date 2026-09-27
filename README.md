## Objetivo

El objetivo principal de este proyecto es aplicar los conocimientos adquiridos en programación orientada a objetos, almacenamiento de datos en archivos para su persistencia.

## Introducción y Contexto del problema
### Sprint 1

Una librería con venta al público necesita modernizar su sistema de gestión de inventario de libros. Debido a la fluctuación en los costos de importación de material bibliográfico, el sistema debe gestionar precios en diferentes monedas y seguir de cerca la cotización del dólar para actualizar sus valores en tiempo real.

El objetivo es desarrollar una aplicación de consola (CLI) robusta en Python que permita gestionar el inventario de una librería, cotizar los libros en tiempo real según el valor del dólar y comparar precios automáticamente con la competencia web.

Descripción de las Entidades

Para cumplir con el requerimiento, se han identificado las siguientes entidades:

- Libro: representa cada título del catálogo de la librería (isbn, título, autor, editorial, género, etc.).
- Genero: categoría literaria a la que pertenece un libro (novela, ensayo, infantil, técnico, etc.).
- Editorial: proveedor/distribuidora que provee los libros a la librería.
- Moneda: las distintas monedas en las que se puede expresar un precio (ARS, USD, etc.).
- TipoCotizacion: los distintos tipos de cotización del dólar (Oficial, Blue, MEP, etc.).
- Precio: valor monetario asociado a un libro en una moneda determinada.
- Stock: cantidad disponible de cada libro.
- Cotizacion: registro histórico de las cotizaciones por tipo y fecha.
