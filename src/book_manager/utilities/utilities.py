
from typing import Sequence

class PrinterUtil:

    @staticmethod    
    def dibujar_separador(text: str) -> None:
        print(f"\n{'─' * 50}")
        print(f"  {text}")
        print(f"{'─' * 50}")

    @staticmethod
    def imprimir_tabla(cabeceras: Sequence[str], filas: Sequence[Sequence[str]]) -> None:
        anchos = [len(c) for c in cabeceras]
        for fila in filas:
            for i, celda in enumerate(fila):
                anchos[i] = max(anchos[i], len(celda))
        linea = "  " + "-+-".join("-" * a for a in anchos)
        print("  " + " | ".join(c.ljust(a) for c, a in zip(cabeceras, anchos)))
        print(linea)
        for fila in filas:
            print("  " + " | ".join(c.ljust(a) for c, a in zip(fila, anchos)))