"""
logic.py — Motor del juego Pokédle

Separa COMPLETAMENTE la lógica del juego de la interfaz visual.
Esto es arquitectura Model-View: si mañana cambias pygame por web,
solo reescribes la interfaz, no la lógica.

Lógica de comparación:
  GREEN   → coincide exactamente
  RED     → no coincide
  YELLOW  → para numéricos: valor del guess está CERCA (±10%)
  UP ↑    → el objetivo tiene un valor MAYOR que el guess
  DOWN ↓  → el objetivo tiene un valor MENOR que el guess
  (UP/DOWN solo para altura, peso, etapa, generación)
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.load import (
    get_connection, obtener_todos_los_pokemon,
    obtener_pokemon_por_nombre, buscar_por_prefijo,
    crear_partida, registrar_intento, finalizar_partida
)

# Columnas que se comparan y sus tipos
COLUMNAS_EXACTAS  = ["tipo_1", "tipo_2", "categoria", "habilidad_1", "habilidad_2"]
COLUMNAS_NUMERICAS = ["altura_m", "peso_kg", "etapa_evolucion", "generacion"]
TODAS_COLUMNAS    = COLUMNAS_EXACTAS + COLUMNAS_NUMERICAS

# Tolerancia para YELLOW en valores numéricos (10% del valor objetivo)
TOLERANCIA = 0.10

# Etiquetas de resultado
GREEN  = "GREEN"
RED    = "RED"
YELLOW = "YELLOW"
UP     = "UP"      # el objetivo es mayor → subir
DOWN   = "DOWN"    # el objetivo es menor → bajar


class Resultado:
    """
    Resultado de comparar un atributo del guess contra el objetivo.

    Atributos:
      columna   — qué atributo se comparó
      valor_guess   — valor del pokémon adivinado
      valor_obj     — valor del pokémon objetivo (no se muestra en pantalla)
      estado        — GREEN / RED / YELLOW / UP / DOWN
    """
    __slots__ = ("columna", "valor_guess", "valor_obj", "estado")

    def __init__(self, columna, valor_guess, valor_obj, estado):
        self.columna     = columna
        self.valor_guess = valor_guess
        self.valor_obj   = valor_obj
        self.estado      = estado

    def __repr__(self):
        return f"Resultado({self.columna}: {self.valor_guess!r} → {self.estado})"


def comparar_columna_exacta(valor_guess, valor_obj) -> str:
    """Compara dos strings: GREEN si iguales, RED si no."""
    if str(valor_guess).lower().strip() == str(valor_obj).lower().strip():
        return GREEN
    return RED


def comparar_columna_numerica(valor_guess, valor_obj) -> str:
    """
    Compara dos valores numéricos con indicación de dirección:
      GREEN  → igual
      YELLOW → dentro del ±10% del objetivo
      UP     → el objetivo es mayor (debes adivinar algo más grande)
      DOWN   → el objetivo es menor
    """
    try:
        vg = float(valor_guess)
        vo = float(valor_obj)
    except (ValueError, TypeError):
        return RED

    if vg == vo:
        return GREEN

    tolerancia_abs = abs(vo) * TOLERANCIA
    if abs(vg - vo) <= tolerancia_abs:
        return YELLOW

    return UP if vo > vg else DOWN


def comparar_tipos(valor_guess, col_guess, objetivo: pd.Series) -> str:
    """
    Compara un tipo del guess contra ambos tipos del objetivo:
      GREEN  → coincide en la misma posición
      YELLOW → el tipo existe pero en la otra posición
      RED    → el tipo no aparece en ninguno de los dos tipos del objetivo
    """
    vg = str(valor_guess).lower().strip()
    t1 = str(objetivo["tipo_1"]).lower().strip()
    t2 = str(objetivo["tipo_2"]).lower().strip()
    val_mismo = t1 if col_guess == "tipo_1" else t2
    val_otro  = t2 if col_guess == "tipo_1" else t1

    if vg == val_mismo:
        return GREEN
    if vg == val_otro:
        return YELLOW
    return RED


def comparar_pokemon(guess: pd.Series, objetivo: pd.Series) -> dict[str, Resultado]:
    """
    Compara todos los atributos del guess contra el objetivo.
    Retorna un dict {columna: Resultado}.

    Para tipos: GREEN=posición correcta, YELLOW=tipo existe en la otra posición, RED=no existe.
    """
    resultados = {}

    # Tipos con lógica especial
    for col in ("tipo_1", "tipo_2"):
        estado = comparar_tipos(guess[col], col, objetivo)
        resultados[col] = Resultado(col, guess[col], objetivo[col], estado)

    # Resto de columnas exactas
    for col in COLUMNAS_EXACTAS:
        if col in ("tipo_1", "tipo_2"):
            continue
        estado = comparar_columna_exacta(guess[col], objetivo[col])
        resultados[col] = Resultado(col, guess[col], objetivo[col], estado)

    for col in COLUMNAS_NUMERICAS:
        estado = comparar_columna_numerica(guess[col], objetivo[col])
        resultados[col] = Resultado(col, guess[col], objetivo[col], estado)

    return resultados


def es_correcto(resultados: dict[str, Resultado]) -> bool:
    """Retorna True si todos los atributos son GREEN."""
    return all(r.estado == GREEN for r in resultados.values())


def resultados_a_dict(resultados: dict[str, Resultado]) -> dict[str, str]:
    """Convierte el dict de Resultado a dict simple {columna: estado} para guardar en DB."""
    return {col: r.estado for col, r in resultados.items()}


# ─────────────────────────────────────────────
# Estado del juego
# ─────────────────────────────────────────────

class EstadoJuego:
    """
    Mantiene el estado completo de una partida en curso.
    El interfaz solo lee de aquí; no maneja lógica directamente.

    Separación de responsabilidades:
      EstadoJuego sabe QUÉ pasó en el juego.
      La interfaz sabe CÓMO mostrarlo.
    """

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "..", "data", "pokedle.db")
        self.db_path     = db_path
        self.conn        = get_connection(db_path)
        self.df_pokemon  = obtener_todos_los_pokemon(self.conn)
        self.objetivo    = None
        self.id_partida  = None
        self.historial   = []      # lista de dicts: {guess, resultados}
        self.ganado      = False
        self.terminado   = False
        self.max_intentos = 15

    def nueva_partida(self) -> None:
        """Selecciona un pokémon aleatorio y registra la partida en la DB."""
        self.objetivo   = self.df_pokemon.sample(1).iloc[0]
        self.id_partida = crear_partida(self.conn, int(self.objetivo["id"]))
        self.historial  = []
        self.ganado     = False
        self.terminado  = False

    def intentos_restantes(self) -> int:
        return self.max_intentos - len(self.historial)

    def buscar_sugerencias(self, prefijo: str) -> "list[str]":
        """Retorna pokémones que empiezan con el prefijo, para el autocomplete."""
        if len(prefijo) < 1:
            return []
        return buscar_por_prefijo(self.conn, prefijo)

    def adivinar(self, nombre_pokemon: str) -> dict | None:
        """
        Procesa un intento del usuario.
        Retorna el dict de resultados, o None si el pokémon no existe.
        """
        if self.terminado:
            return None

        # Verificar que el pokémon existe
        guess = obtener_pokemon_por_nombre(self.conn, nombre_pokemon)
        if guess is None:
            return None

        # Comparar
        resultados = comparar_pokemon(guess, self.objetivo)
        correcto   = es_correcto(resultados)

        # Guardar en historial (en memoria)
        entrada = {
            "numero":    len(self.historial) + 1,
            "pokemon":   guess,
            "resultados": resultados,
            "correcto":  correcto,
        }
        self.historial.append(entrada)

        # Guardar en base de datos
        registrar_intento(
            self.conn,
            self.id_partida,
            int(guess["id"]),
            entrada["numero"],
            resultados_a_dict(resultados),
            correcto
        )

        # Verificar condición de fin
        if correcto:
            self.ganado    = True
            self.terminado = True
            finalizar_partida(self.conn, self.id_partida, ganada=True)
        elif len(self.historial) >= self.max_intentos:
            self.terminado = True
            finalizar_partida(self.conn, self.id_partida, ganada=False)

        return resultados

    def __del__(self):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
