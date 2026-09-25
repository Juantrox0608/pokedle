"""
main.py — Punto de entrada del juego Pokédle

Uso:
  python main.py            → lanza el juego
  python main.py --setup    → corre el ETL pipeline antes de lanzar
"""

import argparse
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "pokedle.db")


def verificar_base_datos() -> bool:
    """Verifica que la base de datos existe y tiene datos."""
    if not os.path.exists(DB_PATH):
        return False
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM pokemon").fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Pokédle — Adivina el Pokémon")
    parser.add_argument("--setup", action="store_true",
                        help="Ejecutar el ETL pipeline (descarga datos y crea la DB)")
    parser.add_argument("--skip-extract", action="store_true",
                        help="En --setup, usar datos ya descargados")
    args = parser.parse_args()

    if args.setup:
        from data.pipeline import run_pipeline
        run_pipeline(skip_extract=args.skip_extract)

    if not verificar_base_datos():
        print("=" * 55)
        print("  Base de datos no encontrada.")
        print("  Corre primero: python main.py --setup")
        print("=" * 55)
        sys.exit(1)

    from game.interface import main as lanzar_juego
    lanzar_juego()


if __name__ == "__main__":
    main()
