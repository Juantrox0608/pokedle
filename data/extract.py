"""
extract.py — Extracción de datos desde PokéAPI

¿Por qué esto importa para Data Engineering?
- Consume una API REST real con paginación y reintentos
- Maneja errores de red con backoff exponencial
- Separa la extracción (raw) del procesamiento (transform)
  Principio: guardar los datos crudos primero, transformar después
  Si transform.py falla, no tienes que volver a pegar la API
"""

import requests
import json
import time
import os

# Cuántos pokémones traer (151=Gen1, 251=Gen1+2, 1025=todas las gens, 1035=formas extra incluidas)
LIMITE = 1025
BASE_URL = "https://pokeapi.co/api/v2"
RAW_PATH = os.path.join(os.path.dirname(__file__), "raw_pokemon.json")


def get_with_retry(url: str, max_intentos: int = 3, espera: float = 1.0) -> dict:
    """
    GET con reintentos y backoff exponencial.

    Backoff exponencial: esperar 1s, luego 2s, luego 4s...
    Esto es buena práctica para no saturar la API.
    """
    for intento in range(max_intentos):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if intento == max_intentos - 1:
                raise
            tiempo_espera = espera * (2 ** intento)
            print(f"  Error en intento {intento + 1}: {e}. Reintentando en {tiempo_espera}s...")
            time.sleep(tiempo_espera)


def extraer_datos_pokemon(numero: int) -> dict:
    """
    Extrae todos los datos crudos de un pokémon por su número.
    Retorna un dict con los datos raw tal como los devuelve la API.
    """
    data = get_with_retry(f"{BASE_URL}/pokemon/{numero}")
    species = get_with_retry(data["species"]["url"])

    # Extraer habilidades (puede ser 1 o 2 habilidades normales, sin contar ocultas)
    habilidades = [
        h["ability"]["name"]
        for h in data["abilities"]
        if not h["is_hidden"]
    ]

    # Cadena de evolución para saber en qué etapa está (1=base, 2=medio, 3=final)
    evo_chain_data = get_with_retry(species["evolution_chain"]["url"])
    etapa_evolucion = calcular_etapa_evolucion(evo_chain_data["chain"], data["name"]) or 1

    # Categoría del pokémon (ej: "Seed Pokémon") — viene en flavors por idioma
    categoria = next(
        (g["genus"] for g in species["genera"] if g["language"]["name"] == "es"),
        next(
            (g["genus"] for g in species["genera"] if g["language"]["name"] == "en"),
            "Desconocido"
        )
    )

    return {
        "id": data["id"],
        "nombre": data["name"],
        "tipo_1": data["types"][0]["type"]["name"],
        "tipo_2": data["types"][1]["type"]["name"] if len(data["types"]) > 1 else None,
        "altura_dm": data["height"],          # en decímetros (x0.1 = metros)
        "peso_hg": data["weight"],            # en hectogramos (x0.1 = kg)
        "etapa_evolucion": etapa_evolucion,   # 1, 2 o 3
        "categoria": categoria,
        "habilidad_1": habilidades[0] if len(habilidades) > 0 else None,
        "habilidad_2": habilidades[1] if len(habilidades) > 1 else None,
        "generacion": 1 if data["id"] <= 151 else
                      2 if data["id"] <= 251 else
                      3 if data["id"] <= 386 else
                      4 if data["id"] <= 493 else
                      5 if data["id"] <= 649 else
                      6 if data["id"] <= 721 else
                      7 if data["id"] <= 809 else
                      8 if data["id"] <= 905 else 9,
        "stats": {s["stat"]["name"]: s["base_stat"] for s in data["stats"]},
        "imagen_url": data["sprites"]["other"]["official-artwork"]["front_default"],
    }


def calcular_etapa_evolucion(chain: dict, nombre: str, etapa: int = 1) -> int | None:
    """
    Recorre recursivamente la cadena de evolución para saber
    en qué etapa (1, 2 o 3) está el pokémon dado.

    Retorna None si no se encontró en este ramal (no confundir con etapa 1).
    El bug anterior usaba return 1 como default, lo que hacía que cadenas
    ramificadas (Eevee → 8 evoluciones) devolvieran 1 para cualquier
    evolución que no fuera la primera del ramal, porque if resultado
    evaluaba 1 como True y cortaba la búsqueda.
    """
    if chain["species"]["name"] == nombre:
        return etapa
    for siguiente in chain.get("evolves_to", []):
        resultado = calcular_etapa_evolucion(siguiente, nombre, etapa + 1)
        if resultado is not None:   # None = no encontrado, no confundir con etapa válida
            return resultado
    return None  # no encontrado en este ramal


def extraer_todos(limite: int = LIMITE) -> list[dict]:
    """
    Extrae los datos de los primeros `limite` pokémones.
    Muestra progreso en consola.
    """
    print(f"Extrayendo datos de {limite} pokémones desde PokéAPI...")
    todos = []

    for i in range(1, limite + 1):
        print(f"  [{i:>3}/{limite}] Extrayendo #{i}...", end="\r")
        try:
            pokemon = extraer_datos_pokemon(i)
            todos.append(pokemon)
            # Pequeña pausa para no saturar la API (rate limiting)
            time.sleep(0.1)
        except Exception as e:
            print(f"\n  Error en pokémon #{i}: {e}")

    print(f"\nExtracción completa: {len(todos)} pokémones.")
    return todos


def guardar_raw(datos: list[dict], ruta: str = RAW_PATH) -> None:
    """
    Guarda los datos crudos en JSON.
    Principio de Data Engineering: conservar siempre los datos originales
    antes de transformar, para poder re-procesar sin volver a la API.
    """
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"Datos crudos guardados en: {ruta}")


def cargar_raw(ruta: str = RAW_PATH) -> list[dict]:
    """Carga los datos crudos desde el JSON guardado."""
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    datos = extraer_todos(LIMITE)
    guardar_raw(datos)
