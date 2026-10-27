import functools
import os
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from book_manager.utilities.utilities import PrinterUtil


RUTA_AUDITORIA_POR_DEFECTO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs", "auditoria.log"
)

LONGITUD_MAXIMA_DETALLE = 200


def ruta_auditoria() -> str:
    """Devuelve la ruta del archivo de auditoría configurada en ``.env``.

    Returns:
        El valor de ``AUDITORIA_PATH`` o, si no está definido,
        ``utilities/logs/auditoria.log``.
    """
    load_dotenv()
    return os.getenv("AUDITORIA_PATH") or RUTA_AUDITORIA_POR_DEFECTO


def log(accion: str, detalle: str = "", resultado: str = "OK", ruta: Optional[str] = None) -> None:
    """Escribe una operación en el archivo de auditoría.

    Cada operación ocupa una línea con tres columnas separadas por `` | ``:
    ``acción | fecha y hora | detalle``. El detalle comienza con el resultado
    (``OK`` o ``ERROR``) y sigue con la descripción de la operación.

    Args:
        accion: Nombre de la acción ejecutada (ej. ``CREAR_LIBRO``).
        detalle: Descripción de lo que se hizo.
        resultado: Resultado de la operación (``OK`` o ``ERROR``).
        ruta: Ruta del archivo de auditoría. Si es ``None``, se usa la ruta
            configurada en ``.env``.
    """
    destino = ruta or ruta_auditoria()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    descripcion = " ".join(str(detalle).split())
    if len(descripcion) > LONGITUD_MAXIMA_DETALLE:
        descripcion = f"{descripcion[:LONGITUD_MAXIMA_DETALLE]}..."
    detalle_final = f"{resultado} {descripcion}".strip()
    linea = f"{accion} | {fecha} | {detalle_final}\n"
    try:
        carpeta = os.path.dirname(os.path.abspath(destino))
        os.makedirs(carpeta, exist_ok=True)
        with open(destino, "a", encoding="utf-8") as archivo:
            archivo.write(linea)
    except OSError as error:
        print(f"No se pudo escribir la auditoría en {destino}: {error}")


def _resumir_valor(valor: Any) -> str:
    """Resume un valor de la llamada para incluirlo en el detalle.

    Args:
        valor: Valor recibido por la función decorada.

    Returns:
        Una representación corta y legible del valor.
    """
    if isinstance(valor, BaseModel):
        return str(valor)
    if isinstance(valor, (list, tuple, set)):
        return f"[{len(valor)} elemento(s)]"
    if isinstance(valor, dict):
        return f"{{{len(valor)} clave(s)}}"
    texto = str(valor)
    return texto if len(texto) <= 80 else f"{texto[:80]}..."


def _detalle_llamada(func: Callable, args: tuple, kwargs: Dict[str, Any]) -> str:
    """Arma el detalle de la llamada a partir de sus argumentos.

    Args:
        func: Función decorada.
        args: Argumentos posicionales recibidos.
        kwargs: Argumentos con nombre recibidos.

    Returns:
        Los argumentos de la llamada en formato ``clave=valor``, sin ``self``.
    """
    import inspect

    try:
        parametros = list(inspect.signature(func).parameters)
    except (TypeError, ValueError):
        parametros = []

    partes = []
    for nombre, valor in zip(parametros, args):
        if nombre == "self":
            continue
        partes.append(f"{nombre}={_resumir_valor(valor)}")
    for nombre, valor in kwargs.items():
        partes.append(f"{nombre}={_resumir_valor(valor)}")
    return ", ".join(partes)


def auditar(accion: str, ruta: Optional[str] = None) -> Callable:
    """Decora una función para registrar cada ejecución en la auditoría.

    Args:
        accion: Nombre literal de la acción a registrar (ej. ``CREAR_LIBRO``).
        ruta: Ruta del archivo de auditoría. Si es ``None``, se usa la ruta
            configurada en ``.env``.

    Returns:
        El decorador que envuelve la función.
    """
    if not accion:
        raise ValueError("El decorador auditar necesita el nombre de la acción.")

    def decorador(func: Callable) -> Callable:
        @functools.wraps(func)
        def envoltura(*args: Any, **kwargs: Any) -> Any:
            detalle = _detalle_llamada(func, args, kwargs)
            try:
                resultado = func(*args, **kwargs)
            except Exception as error:
                log(
                    accion,
                    f"{detalle} -> {type(error).__name__}: {error}",
                    resultado="ERROR",
                    ruta=ruta,
                )
                raise
            log(accion, f"{detalle} -> {_resumir_valor(resultado)}", ruta=ruta)
            return resultado

        return envoltura

    return decorador


# Pruebas unitarias:
if __name__ == '__main__':
    import tempfile

    ruta_configurada = ruta_auditoria()
    print(f"AUDITORIA_PATH : {os.getenv('AUDITORIA_PATH')}")
    print(f"Ruta de log    : {ruta_configurada}")
   
    ruta_prueba = ruta_configurada

    # 1. Escritura directa con log()
    PrinterUtil.dibujar_separador("1. Función log()")

    log("ACCION_MANUAL", "detalle de prueba", ruta=ruta_prueba)
    with open(ruta_prueba, encoding="utf-8") as archivo:
        linea = archivo.readline().rstrip("\n")
    print(linea)

    # 2. Decorador con una función que termina bien
    PrinterUtil.dibujar_separador("2. Decorador con ejecución correcta")

    @auditar("SUMAR", ruta=ruta_prueba)
    def sumar(a: int, b: int) -> int:
        return a + b

    assert sumar(2, 3) == 5
    assert sumar.__name__ == "sumar"

    # 3. Decorador con una función que lanza una excepción
    PrinterUtil.dibujar_separador("3. Decorador con excepción")

    @auditar("DIVIDIR", ruta=ruta_prueba)
    def dividir(a: int, b: int) -> float:
        return a / b

    try:
        dividir(1, 0)
    except ZeroDivisionError as error:
        print(f"Excepción propagada: {error}")

    # 4. Entidades del proyecto y acción obligatoria
    PrinterUtil.dibujar_separador("4. Entidades y acción obligatoria")

    class EntidadPrueba(BaseModel):
        nombre: str

        def __str__(self) -> str:
            return f"EntidadPrueba({self.nombre})"

    class ServicioPrueba:
        @auditar("GUARDAR_ENTIDAD", ruta=ruta_prueba)
        def guardar(self, entidad: EntidadPrueba) -> str:
            return "guardado"

    ServicioPrueba().guardar(EntidadPrueba(nombre="Rayuela"))

    try:
        auditar("")
    except ValueError as error:
        print(f"Error esperado: {error}")

