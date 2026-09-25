"""
transform.py — Transformación y limpieza de datos

¿Por qué esto importa para Data Engineering?
- Normalización: separar datos en tablas relacionadas evita redundancia
- Limpieza: datos consistentes = comparaciones correctas en el juego
- Tipos correctos: columnas numéricas como float, no como string
- Trazabilidad: cada decisión de transformación está documentada aquí

Tablas resultantes:
  pokemon       — una fila por pokémon, datos del juego
  tipos         — catálogo de tipos únicos
  habilidades   — catálogo de habilidades únicas
  stats         — estadísticas base por pokémon (HP, ATK, DEF, etc.)
"""

import pandas as pd
import json
import os

RAW_PATH = os.path.join(os.path.dirname(__file__), "raw_pokemon.json")


def cargar_raw(ruta: str = RAW_PATH) -> list[dict]:
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────
# Tabla principal: pokemon
# ─────────────────────────────────────────────

def transformar_pokemon(raw: list[dict]) -> pd.DataFrame:
    """
    Construye la tabla principal del juego.

    Transformaciones aplicadas:
    - altura: de decímetros a metros (÷10), redondeado a 1 decimal
    - peso: de hectogramos a kg (÷10), redondeado a 1 decimal
    - tipo_2: None → "ninguno" (valor explícito, más fácil de comparar)
    - habilidad_2: None → "ninguna"
    - nombre: capitalizado para mostrar en pantalla
    - todos los strings: strip() + lower() para comparaciones exactas
    """
    registros = []
    for p in raw:
        registros.append({
            "id":              p["id"],
            "nombre":          p["nombre"].capitalize(),
            "nombre_key":      p["nombre"].lower().strip(),   # para búsquedas
            "tipo_1":          p["tipo_1"].lower().strip(),
            "tipo_2":          (p["tipo_2"] or "ninguno").lower().strip(),
            "altura_m":        round(p["altura_dm"] / 10, 1),
            "peso_kg":         round(p["peso_hg"] / 10, 1),
            "etapa_evolucion": int(p["etapa_evolucion"]),
            "categoria":       p["categoria"].replace(" Pokémon", "").strip(),
            "habilidad_1":     (p["habilidad_1"] or "ninguna").lower().strip(),
            "habilidad_2":     (p["habilidad_2"] or "ninguna").lower().strip(),
            "generacion":      int(p["generacion"]),
            "imagen_url":      p.get("imagen_url"),
        })

    df = pd.DataFrame(registros)

    # Verificar que no haya IDs duplicados
    assert df["id"].nunique() == len(df), "¡IDs duplicados en la tabla pokemon!"

    # Verificar que etapa_evolucion solo tenga valores 1, 2, 3
    assert df["etapa_evolucion"].isin([1, 2, 3]).all(), "Etapas de evolución fuera de rango"

    print(f"Tabla pokemon: {len(df)} filas, {len(df.columns)} columnas")
    return df


# ─────────────────────────────────────────────
# Tabla de catálogo: tipos
# ─────────────────────────────────────────────

def transformar_tipos(df_pokemon: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el catálogo de tipos únicos.
    Une tipo_1 y tipo_2, elimina 'ninguno', y le asigna un ID.

    Útil para análisis: cuántos pokémones hay de cada tipo.
    """
    tipos_unicos = pd.concat([
        df_pokemon["tipo_1"],
        df_pokemon["tipo_2"]
    ]).dropna().unique()

    tipos_unicos = [t for t in tipos_unicos if t != "ninguno"]
    tipos_unicos = sorted(set(tipos_unicos))

    df_tipos = pd.DataFrame({
        "id_tipo": range(1, len(tipos_unicos) + 1),
        "nombre":  tipos_unicos
    })

    print(f"Tabla tipos: {len(df_tipos)} tipos únicos")
    return df_tipos


# ─────────────────────────────────────────────
# Tabla de catálogo: habilidades
# ─────────────────────────────────────────────

def transformar_habilidades(df_pokemon: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el catálogo de habilidades únicas.
    """
    habs_unicas = pd.concat([
        df_pokemon["habilidad_1"],
        df_pokemon["habilidad_2"]
    ]).dropna().unique()

    habs_unicas = [h for h in habs_unicas if h != "ninguna"]
    habs_unicas = sorted(set(habs_unicas))

    df_habs = pd.DataFrame({
        "id_habilidad": range(1, len(habs_unicas) + 1),
        "nombre":        habs_unicas
    })

    print(f"Tabla habilidades: {len(df_habs)} habilidades únicas")
    return df_habs


# ─────────────────────────────────────────────
# Tabla de stats (normalización 2NF)
# ─────────────────────────────────────────────

def transformar_stats(raw: list[dict]) -> pd.DataFrame:
    """
    Extrae las estadísticas base en formato largo (tidy data).

    Tidy data: una fila = una observación.
    Esto es mucho más flexible para análisis que tener hp_base, atk_base, etc.
    como columnas separadas.

    Resultado:
      id_pokemon | stat  | valor
      1          | hp    | 45
      1          | attack| 49
      ...
    """
    registros = []
    for p in raw:
        for nombre_stat, valor in p["stats"].items():
            registros.append({
                "id_pokemon": p["id"],
                "stat":       nombre_stat,
                "valor":      int(valor)
            })

    df = pd.DataFrame(registros)
    print(f"Tabla stats: {len(df)} filas ({len(raw)} pokémones × ~6 stats)")
    return df


# ─────────────────────────────────────────────
# Función principal
# ─────────────────────────────────────────────

def transformar_todo() -> dict[str, pd.DataFrame]:
    """
    Corre todas las transformaciones y retorna un dict de DataFrames.
    El pipeline.py llama esto y luego pasa el resultado a load.py.
    """
    print("=== TRANSFORM ===")
    raw = cargar_raw()

    df_pokemon    = transformar_pokemon(raw)
    df_tipos      = transformar_tipos(df_pokemon)
    df_habilidades = transformar_habilidades(df_pokemon)
    df_stats      = transformar_stats(raw)

    return {
        "pokemon":     df_pokemon,
        "tipos":       df_tipos,
        "habilidades": df_habilidades,
        "stats":       df_stats,
    }


if __name__ == "__main__":
    tablas = transformar_todo()
    for nombre, df in tablas.items():
        print(f"\n{nombre}:")
        print(df.head(3).to_string())
