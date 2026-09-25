"""
download_images.py — Descarga imágenes oficiales de todos los pokémones

Usa las URLs de oficial-artwork que ya vienen en raw_pokemon.json.
Guarda cada imagen en assets/cartas/{Nombre}.png.
Es idempotente: si la imagen ya existe, la salta.
"""

import json
import os
import time
import requests

RAW_PATH    = os.path.join(os.path.dirname(__file__), "raw_pokemon.json")
CARTAS_DIR  = os.path.join(os.path.dirname(__file__), "..", "assets", "cartas")

# Pokémones Gen 1 con nombres de archivo especiales (ya existen con otro nombre)
# No los sobreescribimos para no perder las cartas originales
SKIP_SI_EXISTE = True


def nombre_a_archivo(nombre_raw: str) -> str:
    """
    Convierte el nombre crudo de la API al nombre de archivo PNG.
    Ej: 'nidoran-f' → 'Nidoran-f.png'
    """
    return nombre_raw.capitalize() + ".png"


def descargar_imagen(url: str, ruta_destino: str, max_intentos: int = 3) -> bool:
    """Descarga una imagen desde url y la guarda en ruta_destino."""
    for intento in range(max_intentos):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            with open(ruta_destino, "wb") as f:
                f.write(resp.content)
            return True
        except Exception as e:
            if intento == max_intentos - 1:
                return False
            time.sleep(1.5 * (intento + 1))
    return False


def descargar_todas(forzar: bool = False) -> None:
    """
    Descarga todas las imágenes del raw_pokemon.json.
    forzar=True re-descarga aunque ya existan.
    """
    os.makedirs(CARTAS_DIR, exist_ok=True)

    with open(RAW_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    total    = len(raw)
    saltados = 0
    ok       = 0
    errores  = []

    print(f"Descargando imágenes de {total} pokémones en {CARTAS_DIR}...")

    for i, p in enumerate(raw, 1):
        nombre_archivo = nombre_a_archivo(p["nombre"])
        ruta_destino   = os.path.join(CARTAS_DIR, nombre_archivo)

        print(f"  [{i:>4}/{total}] {nombre_archivo:<30}", end="\r")

        # Saltar si ya existe
        if not forzar and os.path.exists(ruta_destino):
            saltados += 1
            continue

        url = p.get("imagen_url")
        if not url:
            errores.append((p["nombre"], "sin URL"))
            continue

        exito = descargar_imagen(url, ruta_destino)
        if exito:
            ok += 1
        else:
            errores.append((p["nombre"], "error de descarga"))

        # Pausa breve para no saturar el CDN
        time.sleep(0.05)

    print(f"\nDescarga completa:")
    print(f"  Descargadas: {ok}")
    print(f"  Ya existían: {saltados}")
    if errores:
        print(f"  Errores ({len(errores)}): {[n for n,_ in errores[:10]]}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--forzar", action="store_true", help="Re-descargar aunque ya existan")
    args = parser.parse_args()
    descargar_todas(forzar=args.forzar)
