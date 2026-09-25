"""
pipeline.py — Orquestador del ETL completo

Ejecuta: Extract → Transform → Load

¿Por qué un orquestador separado?
- Un pipeline real tiene estas 3 fases claramente separadas
- Puedes re-ejecutar solo la fase que falló
- Fácil de reemplazar por Airflow/Prefect/Luigi si el proyecto escala

Uso:
  python pipeline.py           → corre el ETL completo
  python pipeline.py --skip-extract  → usa el JSON ya descargado (ahorra tiempo)
"""

import argparse
import os
import sys

# Agregar el directorio padre al path para imports
sys.path.insert(0, os.path.dirname(__file__))

from extract          import extraer_todos, guardar_raw, RAW_PATH
from transform        import transformar_todo
from load             import cargar_todo
from download_images  import descargar_todas


def run_pipeline(skip_extract: bool = False, skip_images: bool = False) -> None:
    print("=" * 50)
    print("  POKEDLE ETL PIPELINE")
    print("=" * 50)

    # ── EXTRACT ──────────────────────────────────
    if skip_extract:
        if not os.path.exists(RAW_PATH):
            print("ERROR: No existe raw_pokemon.json. Corre sin --skip-extract primero.")
            sys.exit(1)
        print("=== EXTRACT (skip) ===")
        print(f"  Usando datos crudos existentes: {RAW_PATH}")
    else:
        print("=== EXTRACT ===")
        datos_raw = extraer_todos()
        guardar_raw(datos_raw)

    # ── TRANSFORM ────────────────────────────────
    tablas = transformar_todo()

    # ── LOAD ─────────────────────────────────────
    cargar_todo(tablas)

    # ── IMAGES ───────────────────────────────────
    if skip_images:
        print("=== IMAGES (skip) ===")
    else:
        print("=== IMAGES ===")
        descargar_todas()

    print("=" * 50)
    print("  Pipeline completado exitosamente.")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL pipeline para Pokédle")
    parser.add_argument("--skip-extract", action="store_true",
                        help="Saltea la extracción y usa raw_pokemon.json existente")
    parser.add_argument("--skip-images", action="store_true",
                        help="Saltea la descarga de imágenes")
    args = parser.parse_args()
    run_pipeline(skip_extract=args.skip_extract, skip_images=args.skip_images)
