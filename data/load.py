"""
load.py — Carga de datos a SQLite

¿Por qué SQLite y no solo CSV?
- Relaciones entre tablas (claves foráneas)
- Queries SQL: más expresivo que filtros de pandas para datos estructurados
- Persistencia de partidas: guardar cada intento del usuario
- SQLite no necesita servidor: el archivo .db es portable, va en el repo

Tablas que se crean:
  pokemon     — datos del juego (una fila por pokémon)
  tipos       — catálogo de tipos
  habilidades — catálogo de habilidades
  stats       — estadísticas base en formato largo
  partidas    — cada sesión de juego (quién fue el pokémon objetivo)
  intentos    — cada guess del usuario dentro de una partida
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "pokedle.db")


def get_connection(ruta: str = DB_PATH) -> sqlite3.Connection:
    """Retorna una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(ruta)
    conn.execute("PRAGMA foreign_keys = ON")   # activar integridad referencial
    return conn


def crear_schema(conn: sqlite3.Connection) -> None:
    """
    Crea todas las tablas si no existen.
    Usar IF NOT EXISTS hace que sea idempotente (safe to run multiple times).
    """
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tipos (
            id_tipo  INTEGER PRIMARY KEY,
            nombre   TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS habilidades (
            id_habilidad INTEGER PRIMARY KEY,
            nombre       TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS pokemon (
            id               INTEGER PRIMARY KEY,
            nombre           TEXT NOT NULL,
            nombre_key       TEXT NOT NULL,
            tipo_1           TEXT NOT NULL,
            tipo_2           TEXT NOT NULL DEFAULT 'ninguno',
            altura_m         REAL NOT NULL,
            peso_kg          REAL NOT NULL,
            etapa_evolucion  INTEGER NOT NULL CHECK(etapa_evolucion IN (1, 2, 3)),
            categoria        TEXT NOT NULL,
            habilidad_1      TEXT NOT NULL,
            habilidad_2      TEXT NOT NULL DEFAULT 'ninguna',
            generacion       INTEGER NOT NULL,
            imagen_url       TEXT
        );

        CREATE TABLE IF NOT EXISTS stats (
            id_pokemon  INTEGER NOT NULL REFERENCES pokemon(id),
            stat        TEXT NOT NULL,
            valor       INTEGER NOT NULL,
            PRIMARY KEY (id_pokemon, stat)
        );

        -- Registro de partidas jugadas
        CREATE TABLE IF NOT EXISTS partidas (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pokemon_obj INTEGER NOT NULL REFERENCES pokemon(id),
            fecha          TEXT NOT NULL,
            ganada         INTEGER NOT NULL DEFAULT 0,   -- 0=en curso, 1=ganada, 2=perdida
            num_intentos   INTEGER NOT NULL DEFAULT 0
        );

        -- Registro de cada intento dentro de una partida
        CREATE TABLE IF NOT EXISTS intentos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            id_partida   INTEGER NOT NULL REFERENCES partidas(id),
            id_pokemon   INTEGER NOT NULL REFERENCES pokemon(id),
            numero       INTEGER NOT NULL,   -- número de intento (1, 2, 3...)
            resultado_tipo_1      TEXT,
            resultado_tipo_2      TEXT,
            resultado_altura      TEXT,
            resultado_peso        TEXT,
            resultado_evolucion   TEXT,
            resultado_categoria   TEXT,
            resultado_habilidad_1 TEXT,
            resultado_habilidad_2 TEXT,
            resultado_generacion  TEXT,
            es_correcto  INTEGER NOT NULL DEFAULT 0
        );

        -- Índices para queries frecuentes
        CREATE INDEX IF NOT EXISTS idx_intentos_partida ON intentos(id_partida);
        CREATE INDEX IF NOT EXISTS idx_pokemon_nombre   ON pokemon(nombre_key);
    """)
    conn.commit()
    print("Schema creado/verificado.")


def cargar_tablas(conn: sqlite3.Connection, tablas: dict) -> None:
    """
    Carga los DataFrames transformados a SQLite.

    Usamos DELETE + append en lugar de if_exists='replace'
    porque 'replace' destruye la tabla y pierde las FK constraints
    definidas en el schema. Con DELETE conservamos la estructura.
    """
    # Deshabilitar FKs durante la carga para poder borrar/recargar
    # sin problemas de orden. Se vuelve a activar al finalizar.
    conn.execute("PRAGMA foreign_keys = OFF")
    orden = ["tipos", "habilidades", "pokemon", "stats"]
    for nombre in orden:
        df = tablas[nombre]
        conn.execute(f"DELETE FROM {nombre}")
        df.to_sql(nombre, conn, if_exists="append", index=False)
        print(f"  Cargada tabla '{nombre}': {len(df)} filas")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()


# ─────────────────────────────────────────────
# Funciones de lectura para el juego
# ─────────────────────────────────────────────

def obtener_todos_los_pokemon(conn: sqlite3.Connection) -> pd.DataFrame:
    """Retorna todos los pokémones como DataFrame."""
    return pd.read_sql("SELECT * FROM pokemon ORDER BY id", conn)


def obtener_pokemon_por_nombre(conn: sqlite3.Connection, nombre_key: str):
    """Busca un pokémon por nombre (insensible a mayúsculas)."""
    df = pd.read_sql(
        "SELECT * FROM pokemon WHERE nombre_key = ?",
        conn, params=(nombre_key.lower().strip(),)
    )
    if df.empty:
        return None
    return df.iloc[0]


def buscar_por_prefijo(conn: sqlite3.Connection, prefijo: str) -> list[str]:
    """Retorna nombres de pokémones que empiezan con el prefijo dado."""
    df = pd.read_sql(
        "SELECT nombre FROM pokemon WHERE nombre_key LIKE ? ORDER BY nombre",
        conn, params=(prefijo.lower().strip() + "%",)
    )
    return df["nombre"].tolist()


# ─────────────────────────────────────────────
# Funciones de escritura para el juego
# ─────────────────────────────────────────────

def crear_partida(conn: sqlite3.Connection, id_pokemon_obj: int) -> int:
    """Registra una nueva partida y retorna su ID."""
    cur = conn.execute(
        "INSERT INTO partidas (id_pokemon_obj, fecha, ganada, num_intentos) VALUES (?, ?, 0, 0)",
        (id_pokemon_obj, datetime.now().isoformat())
    )
    conn.commit()
    return cur.lastrowid


def registrar_intento(
    conn: sqlite3.Connection,
    id_partida: int,
    id_pokemon: int,
    numero: int,
    resultados: dict,
    es_correcto: bool
) -> None:
    """Guarda un intento en la base de datos."""
    conn.execute("""
        INSERT INTO intentos (
            id_partida, id_pokemon, numero,
            resultado_tipo_1, resultado_tipo_2, resultado_altura, resultado_peso,
            resultado_evolucion, resultado_categoria,
            resultado_habilidad_1, resultado_habilidad_2, resultado_generacion,
            es_correcto
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        id_partida, id_pokemon, numero,
        resultados.get("tipo_1"), resultados.get("tipo_2"),
        resultados.get("altura_m"), resultados.get("peso_kg"),
        resultados.get("etapa_evolucion"), resultados.get("categoria"),
        resultados.get("habilidad_1"), resultados.get("habilidad_2"),
        resultados.get("generacion"),
        int(es_correcto)
    ))
    conn.execute(
        "UPDATE partidas SET num_intentos = num_intentos + 1 WHERE id = ?",
        (id_partida,)
    )
    conn.commit()


def finalizar_partida(conn: sqlite3.Connection, id_partida: int, ganada: bool) -> None:
    """Marca una partida como ganada (1) o perdida (2)."""
    conn.execute(
        "UPDATE partidas SET ganada = ? WHERE id = ?",
        (1 if ganada else 2, id_partida)
    )
    conn.commit()


def resetear_tablas_datos(conn: sqlite3.Connection) -> None:
    """
    Elimina y recrea las tablas de datos (no las de partidas/intentos).
    Necesario para garantizar que las tablas tengan PRIMARY KEY correctos
    (pandas to_sql no crea PKs, solo los hace CREATE TABLE IF NOT EXISTS).
    """
    conn.execute("PRAGMA foreign_keys = OFF")
    tablas_datos = ["stats", "pokemon", "habilidades", "tipos"]
    for t in tablas_datos:
        conn.execute(f"DROP TABLE IF EXISTS {t}")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()


def cargar_todo(tablas: dict, ruta: str = DB_PATH) -> None:
    """Función principal: crea schema y carga todos los datos."""
    print("=== LOAD ===")
    conn = get_connection(ruta)
    resetear_tablas_datos(conn)   # eliminar tablas para recrear con PKs
    crear_schema(conn)             # recrear con estructura correcta
    cargar_tablas(conn, tablas)
    conn.close()
    print(f"Base de datos guardada en: {ruta}")


if __name__ == "__main__":
    # Test rápido
    conn = get_connection()
    crear_schema(conn)
    print(buscar_por_prefijo(conn, "char"))
    conn.close()
