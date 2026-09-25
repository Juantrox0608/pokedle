# Pokédle

> Proyecto personal de **Juan David Caicedo Cuesta**. Se puede leer, clonar y ejecutar;
> no acepta contribuciones externas. Licencia MIT: reutilizarlo exige conservar la autoría.

Juego tipo Wordle para adivinar Pokémon, construido sobre un **pipeline ETL propio** que
consume la [PokéAPI](https://pokeapi.co) y la normaliza en SQLite.

El juego es la excusa: lo que hay debajo es un pipeline de datos completo, con sus fases
separadas, su esquema relacional y su análisis exploratorio.

---

## Qué hace

**ETL (`data/`)**

| Fase | Archivo | Qué hace |
|---|---|---|
| Extract | `extract.py` | Descarga 1000+ Pokémon desde la PokéAPI y guarda la respuesta cruda en JSON |
| Transform | `transform.py` | Aplana la respuesta anidada, normaliza tipos, stats y generación |
| Load | `load.py` | Crea el esquema y carga los datos en SQLite |
| Orquestación | `pipeline.py` | Ejecuta las tres fases; permite reejecutar solo la que falló |

Se guarda el JSON crudo **antes** de transformar, así que se puede reprocesar sin volver a
golpear la API.

**Juego (`game/`)**

- `logic.py` — reglas de comparación: coincidencia exacta, numérica (mayor/menor) y parcial
  para tipos, que es el caso interesante porque un Pokémon puede tener uno o dos.
- `interface.py` — interfaz en pygame.

**Análisis (`analysis/eda.ipynb`)** — exploración de la distribución de stats, tipos y
generaciones sobre los datos ya cargados.

---

## Cómo ejecutarlo

```bash
pip install -r requirements.txt

python data/download_images.py   # descarga los sprites (no vienen en el repo)
python main.py --setup           # corre el ETL y lanza el juego
python main.py                   # si la base ya está cargada
```

Para reejecutar solo parte del pipeline:

```bash
python data/pipeline.py --skip-extract   # reusa el JSON ya descargado
```

---

## Decisiones de diseño

**SQLite y no PostgreSQL.** No necesita servidor y el archivo `.db` es portable, así que
cualquiera clona el repo y lo ejecuta. El esquema está normalizado igual; migrar a Postgres
sería cambiar la capa de conexión.

**Las tres fases van separadas.** Se podría hacer todo en un script, pero separarlas permite
reejecutar solo la que falló y sustituir el orquestador por Airflow o Prefect si creciera.

**Los sprites no están en el repo.** Son 127 MB de material con copyright de Nintendo y
Game Freak. `download_images.py` los baja desde la PokéAPI en la primera ejecución.

---

## Stack

Python · SQLite · PokéAPI · pandas · pygame · matplotlib / seaborn · Jupyter

---

## Autoría y licencia

Escrito por **Juan David Caicedo Cuesta** ([@Juantrox0608](https://github.com/Juantrox0608)).

Publicado bajo [licencia MIT](LICENSE): cualquiera puede usar, copiar o modificar el código
siempre que conserve el aviso de copyright, es decir, la autoría viaja con el código.

La rama `main` está protegida y el repositorio no acepta pull requests
(ver [CONTRIBUTING](.github/CONTRIBUTING.md)).

Pokémon y sus sprites son marcas de Nintendo, Game Freak y Creatures Inc.; este proyecto no
está afiliado a ellos y no redistribuye su material.
