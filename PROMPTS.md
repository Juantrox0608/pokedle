# Pokédle — Historial de Prompts

Registro de los prompts usados para construir este proyecto con Claude Code.
Útil para replicar el proceso, entender decisiones de diseño, o mostrar en entrevistas.

---

## 1. Análisis inicial del proyecto

```
en la carpeta c:/users/juant/documents hay una carpeta que se llama proyecto p
quiero que lo revises y mires como quedo una idea de pokedle que nunca termine
dime como mejorarla y hacer funcionar y que pueda servir como proyecto para
mostrar en una entrevista de trabajo para data engineer
```

**Resultado:** Diagnóstico del proyecto original. Identificados 6 problemas concretos
(sin historial de intentos, rutas hardcodeadas, CSV con espacios en columnas, etc.)
y propuesta de arquitectura ETL completa.

---

## 2. Construcción completa del proyecto

```
hagamos todo para que sea un juego 10/10 y pues sea bastante util como
referencia para trabajos explicame todo tambien
```

**Resultado:** Construcción completa del proyecto desde cero:
- `data/extract.py` — ETL Extract: PokéAPI con reintentos y backoff exponencial
- `data/transform.py` — ETL Transform: normalización, tidy data, 4 tablas
- `data/load.py` — ETL Load: SQLite con FK constraints, registro de partidas
- `data/pipeline.py` — Orquestador ETL con flags `--skip-extract`
- `game/logic.py` — Motor del juego: GREEN/RED/YELLOW/UP/DOWN, historial en DB
- `game/interface.py` — Interfaz pygame: tabla scrolleable, autocomplete, leyenda
- `analysis/eda.ipynb` — Notebook EDA completo
- `main.py` + `requirements.txt`

---

## 3. Correcciones de UX

```
me gusta pero toca corregir un par de cosas:
la barra de busqueda se tapa por las busquedas
hasta que generacion va si va a las 9 generaciones?
me gustaria una foto del pokemon al final de la partida si se gana o se pierde
```

**Resultado:**
- Sugerencias ahora se dibujan encima de la tabla (orden de render corregido)
- Subtítulo muestra "Gen 1 · 151 pokémones"
- Overlay de fin de partida con imagen del pokémon y marco verde/rojo

---

## 4. Expansión a 1025 pokémones

```
quitemos el limite de 151 y vamos por los 1035 pokemones
```

**Resultado:**
- `LIMITE` cambiado a 1025 (Gen 1–9 completos)
- Generación 9 añadida al cálculo (IDs 906–1025)
- Debug print eliminado de `logic.py`
- Subtítulo actualizado dinámicamente desde la DB

---

## 5. Descarga de imágenes

```
si tambien descarga las imagenes
```

**Resultado:**
- `data/download_images.py` — descarga official artwork desde PokéAPI
- Integrado al pipeline como fase 4 (con flag `--skip-images`)
- Script idempotente: salta imágenes que ya existen

---

## 6. Aumentar intentos

```
aumenta los intentos a 15
```

**Resultado:** `max_intentos = 8` → `max_intentos = 15` en `logic.py`

---

## 7. YELLOW para tipos cruzados

```
quiero que si el tipo esta en alguno de los 2 se ponga en amarillo
```

**Resultado:** Nueva función `comparar_tipos()` en `logic.py`:
- **GREEN** → tipo coincide en la misma posición
- **YELLOW** → tipo existe pero en la otra posición del objetivo
- **RED** → tipo no aparece en ninguno de los dos tipos del objetivo

---

## 8. Pantalla más grande

```
quiero que sea mas grande la pantalla para leer bien todo
```

**Resultado:** Ventana 1000×700 → 1400×860, fuentes aumentadas, columnas más anchas.

---

## 9. Anchos de columna proporcionales al contenido

```
no los dejes simetricos sino acomodalo segun el tamano del string
donde las generacion y la evolucion son mas pequenas
```

**Resultado:** `COL_ANCHOS` dict con ancho específico por columna:
- Gen / Evo: 65px
- Altura: 85px, Peso: 95px
- Tipos: 120px
- Habilidades: 210px, Categoría: 230px

---

## 10. Pantalla completa

```
sigue cortandose la categoria si quieres dejalo full screen
```

**Resultado:** `pygame.FULLSCREEN` — el juego detecta el tamaño del monitor automáticamente.
ESC cierra el juego.

---

## 11. Reemplazar cartas TCG por official artwork

```
quiero que cambies las imagenes de las 151 en vez de tarjetas por imagenes del pokemon
```

**Resultado:** Re-descarga forzada (`--forzar`) de las 151 imágenes Gen 1 con
official artwork de PokéAPI, reemplazando las cartas TCG originales.

---

## 12. Fix bug evoluciones ramificadas (Eevee)

```
POR QUE LAS EEVEEVOLUCIONES APARECEN COMO EVOLUCION 1?
```

**Root cause:** `calcular_etapa_evolucion()` retornaba `1` como default cuando
no encontraba el pokémon en un ramal. Como `if 1` es truthy, cortaba la búsqueda
antes de revisar los otros ramales de la cadena (Eevee tiene 8 evoluciones).

**Fix:** Cambiar `return 1` → `return None` y usar `if resultado is not None`
para distinguir "no encontrado" de "etapa 1 válida".

---

## Comandos para reproducir el proyecto

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Correr ETL completo (primera vez, ~15 min)
python main.py --setup

# 3. Re-correr solo transform+load (si ya tienes raw_pokemon.json)
python data/pipeline.py --skip-extract --skip-images

# 4. Lanzar el juego
python main.py
```

---

## Stack técnico demostrado

| Concepto | Dónde |
|---|---|
| ETL pipeline con 3 fases separadas | `data/extract.py`, `transform.py`, `load.py` |
| Consumo de API REST con reintentos | `extract.py` → `get_with_retry()` |
| Backoff exponencial | `extract.py` → espera `1s, 2s, 4s...` |
| Normalización de datos (2NF) | `transform.py` → 4 tablas separadas |
| Tidy data | `transform.py` → tabla `stats` en formato largo |
| SQLite con FK constraints | `load.py` → schema con integridad referencial |
| Idempotencia del pipeline | `load.py` → DELETE + append en vez de DROP |
| Arquitectura Model-View | `logic.py` (modelo) vs `interface.py` (vista) |
| Persistencia de sesiones | `load.py` → tablas `partidas` e `intentos` |
| EDA con pandas + matplotlib | `analysis/eda.ipynb` |
