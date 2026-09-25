"""
interface.py — Interfaz gráfica del Pokédle con Pygame

Responsabilidades de esta capa (solo presentación):
  - Dibujar el estado actual del juego
  - Capturar eventos del usuario (teclado, mouse)
  - Llamar a EstadoJuego para procesar la lógica
  - NO contiene reglas del juego

Diseño de pantalla:
  ┌──────────────────────────────────────────┐
  │         ADIVINA EL POKÉMON               │  título
  │  [__Charmander___________]  [ADIVINAR]   │  input + botón
  │  ┌────────────────────────────────────┐  │
  │  │ #  Pokémon │T1│T2│Alt│Pes│Evo│Cat│...│  │  cabecera tabla
  │  │ 1  Pikachu │🟢│🔴│↑  │🟡 │🟢 │🔴│...│  │  filas de intentos
  │  └────────────────────────────────────┘  │
  │  Sugerencias: Charmander Charmeleon...   │  autocomplete
  └──────────────────────────────────────────┘
"""

import pygame
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from game.logic import EstadoJuego, GREEN, RED, YELLOW, UP, DOWN, TODAS_COLUMNAS

# ─────────────────────────────────────────────
# Constantes de pantalla
# ─────────────────────────────────────────────

ANCHO, ALTO = 0, 0   # se sobreescribe al iniciar con el tamaño real del monitor
FPS = 60

# Paleta de colores
C_FONDO      = (15, 15, 35)        # azul noche muy oscuro
C_HEADER     = (25, 25, 55)        # azul oscuro para headers
C_TEXTO      = (230, 230, 240)     # blanco suave
C_TEXTO_DIM  = (130, 130, 160)     # gris para texto secundario
C_INPUT_BG   = (30, 30, 60)        # fondo del input
C_INPUT_BOR  = (80, 80, 150)       # borde del input
C_INPUT_ACT  = (100, 100, 220)     # borde activo del input
C_BOTON      = (60, 60, 160)       # botón normal
C_BOTON_HOV  = (80, 80, 200)       # botón hover
C_SUGERENCIA = (35, 35, 75)        # fondo sugerencias
C_SUG_HOV    = (50, 50, 100)       # hover sugerencia

# Colores de resultado
C_GREEN  = (76,  175,  80)         # verde
C_RED    = (229,  57,  53)         # rojo
C_YELLOW = (251, 192,  45)         # amarillo
C_UP     = (100, 181, 246)         # azul claro → más alto
C_DOWN   = (255, 138,  10)         # naranja → más bajo
C_CORRECTO = (156,  39, 176)       # morado → ¡correcto!

COLOR_ESTADO = {
    GREEN:  C_GREEN,
    RED:    C_RED,
    YELLOW: C_YELLOW,
    UP:     C_UP,
    DOWN:   C_DOWN,
}

ICONO_ESTADO = {
    GREEN:  "✓",
    RED:    "✗",
    YELLOW: "~",
    UP:     "↑",
    DOWN:   "↓",
}

# Nombres cortos para cabecera de tabla
NOMBRES_COLUMNA = {
    "tipo_1":         "Tipo 1",
    "tipo_2":         "Tipo 2",
    "altura_m":       "Alt (m)",
    "peso_kg":        "Peso kg",
    "etapa_evolucion":"Evo",
    "categoria":      "Categoría",
    "habilidad_1":    "Hab 1",
    "habilidad_2":    "Hab 2",
    "generacion":     "Gen",
}

# Layout de la tabla de intentos
TABLA_X        = 30
TABLA_Y        = 175
FILA_ALTO      = 48
CABECERA_ALTO  = 44
COL_NOMBRE_W   = 160

# Ancho de cada columna ajustado a su contenido real
COL_ANCHOS = {
    "tipo_1":          120,
    "tipo_2":          120,
    "altura_m":         85,
    "peso_kg":          95,
    "etapa_evolucion":  65,
    "categoria":       230,  # texto más largo, columna generosa
    "habilidad_1":     210,
    "habilidad_2":     210,
    "generacion":       65,
}
PADDING        = 10

# Input
INPUT_X, INPUT_Y = 30, 100
INPUT_W, INPUT_H = 620, 52

# Botón
BOTON_X = INPUT_X + INPUT_W + 16
BOTON_Y = INPUT_Y
BOTON_W, BOTON_H = 160, 52

# Sugerencias
SUG_X   = INPUT_X
SUG_W   = INPUT_W
SUG_H   = 44
MAX_SUG = 6

# Área de victoria/derrota
OVERLAY_ALPHA = 200


# ─────────────────────────────────────────────
# Helpers de dibujo
# ─────────────────────────────────────────────

def dibujar_rect_redondeado(surface, color, rect, radio=8, borde=0, borde_color=None):
    pygame.draw.rect(surface, color, rect, border_radius=radio)
    if borde and borde_color:
        pygame.draw.rect(surface, borde_color, rect, borde, border_radius=radio)


def dibujar_texto_centrado(surface, texto, fuente, color, rect):
    texto_surf = fuente.render(str(texto), True, color)
    texto_rect = texto_surf.get_rect(center=(rect[0] + rect[2]//2, rect[1] + rect[3]//2))
    surface.blit(texto_surf, texto_rect)


def truncar(texto: str, max_chars: int) -> str:
    return texto if len(texto) <= max_chars else texto[:max_chars - 1] + "…"


# ─────────────────────────────────────────────
# Clase principal de la interfaz
# ─────────────────────────────────────────────

class InterfazPokedle:

    def __init__(self):
        pygame.init()
        self.ventana = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        global ANCHO, ALTO
        ANCHO, ALTO = self.ventana.get_size()
        pygame.display.set_caption("Pokédle")
        self.clock = pygame.time.Clock()

        # Fuentes
        self.f_titulo    = pygame.font.SysFont("segoeui", 48, bold=True)
        self.f_subtitulo = pygame.font.SysFont("segoeui", 28, bold=True)
        self.f_texto     = pygame.font.SysFont("segoeui", 22)
        self.f_pequeña   = pygame.font.SysFont("segoeui", 19)
        self.f_icono     = pygame.font.SysFont("segoeuisymbol", 24, bold=True)

        # Estado del juego
        self.estado_juego = EstadoJuego()
        self.estado_juego.nueva_partida()

        # UI state
        self.entrada_texto  = ""
        self.sugerencias    = []
        self.sug_selec      = -1     # índice de sugerencia resaltada
        self.scroll_tabla   = 0      # desplazamiento vertical de la tabla
        self.input_activo   = True

        # Carga imagen de fondo pokébola (si existe)
        self.img_fondo = None
        ruta_fondo = os.path.join(os.path.dirname(__file__), "..", "assets", "fondo.jpg")
        if os.path.exists(ruta_fondo):
            img = pygame.image.load(ruta_fondo).convert_alpha()
            img.set_alpha(18)
            self.img_fondo = pygame.transform.scale(img, (ANCHO, ALTO))

        # Directorio de imágenes de cartas
        self.cartas_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "cartas")
        # Índice case-insensitive de todas las imágenes disponibles
        self._cartas_index = {
            f.lower(): f
            for f in os.listdir(self.cartas_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        }
        self.img_pokemon_fin = None   # imagen del pokémon al terminar la partida

    # ── Bucle principal ───────────────────────

    def run(self):
        while True:
            self.clock.tick(FPS)
            self._procesar_eventos()
            self._dibujar()
            pygame.display.flip()

    # ── Eventos ──────────────────────────────

    def _procesar_eventos(self):
        mouse_pos = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN:
                self._handle_keydown(evento)

            if evento.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(mouse_pos)

            if evento.type == pygame.MOUSEWHEEL:
                self.scroll_tabla = max(0, self.scroll_tabla - evento.y * FILA_ALTO)

        # Actualizar sugerencias mientras escribe
        self.sugerencias = self.estado_juego.buscar_sugerencias(self.entrada_texto)[:MAX_SUG]

    def _handle_keydown(self, evento):
        if evento.key == pygame.K_ESCAPE:
            if self.sugerencias:
                self.sugerencias = []
                self.sug_selec   = -1
            else:
                pygame.quit()
                sys.exit()

        elif evento.key == pygame.K_BACKSPACE:
            self.entrada_texto = self.entrada_texto[:-1]
            self.sug_selec     = -1

        elif evento.key == pygame.K_RETURN:
            if self.sug_selec >= 0 and self.sug_selec < len(self.sugerencias):
                self._confirmar_guess(self.sugerencias[self.sug_selec])
            elif self.sugerencias:
                self._confirmar_guess(self.sugerencias[0])
            else:
                self._confirmar_guess(self.entrada_texto)

        elif evento.key == pygame.K_DOWN:
            self.sug_selec = min(self.sug_selec + 1, len(self.sugerencias) - 1)

        elif evento.key == pygame.K_UP:
            self.sug_selec = max(self.sug_selec - 1, -1)

        elif evento.key == pygame.K_r and self.estado_juego.terminado:
            self.estado_juego.nueva_partida()
            self.entrada_texto   = ""
            self.sugerencias     = []
            self.scroll_tabla    = 0
            self.img_pokemon_fin = None

        else:
            if evento.unicode.isalpha() or evento.unicode in (" ", "-", "'", "."):
                self.entrada_texto += evento.unicode
                self.sug_selec      = -1

    def _handle_click(self, pos):
        x, y = pos

        # Clic en botón "Adivinar"
        if BOTON_X <= x <= BOTON_X + BOTON_W and BOTON_Y <= y <= BOTON_Y + BOTON_H:
            nombre = (self.sugerencias[0] if self.sugerencias else self.entrada_texto)
            self._confirmar_guess(nombre)
            return

        # Clic en sugerencia
        if self.sugerencias:
            for i, sug in enumerate(self.sugerencias):
                sy = INPUT_Y + INPUT_H + 4 + i * SUG_H
                if SUG_X <= x <= SUG_X + SUG_W and sy <= y <= sy + SUG_H:
                    self._confirmar_guess(sug)
                    return

    def _buscar_imagen_pokemon(self, nombre: str):
        """
        Busca la imagen del pokémon en assets/cartas/ de forma case-insensitive.
        Todos los archivos siguen la convención: Nombre.capitalize() + '.png'
        """
        candidatos = [
            nombre + ".png",
            nombre.capitalize() + ".png",
            nombre.lower() + ".png",
        ]
        for candidato in candidatos:
            archivo = self._cartas_index.get(candidato.lower())
            if archivo:
                ruta = os.path.join(self.cartas_dir, archivo)
                try:
                    return pygame.image.load(ruta).convert_alpha()
                except Exception:
                    pass
        return None

    def _confirmar_guess(self, nombre: str):
        nombre = nombre.strip()
        if not nombre or self.estado_juego.terminado:
            return

        resultado = self.estado_juego.adivinar(nombre)
        if resultado is None:
            return  # pokémon no encontrado, no hacer nada

        self.entrada_texto = ""
        self.sugerencias   = []
        self.sug_selec     = -1
        # Hacer scroll hacia abajo para ver el último intento
        total_filas = len(self.estado_juego.historial)
        area_visible = (ALTO - TABLA_Y - CABECERA_ALTO - 80) // FILA_ALTO
        if total_filas > area_visible:
            self.scroll_tabla = (total_filas - area_visible) * FILA_ALTO

        # Si terminó la partida, cargar imagen del objetivo
        if self.estado_juego.terminado:
            nombre_obj = self.estado_juego.objetivo["nombre"]
            self.img_pokemon_fin = self._buscar_imagen_pokemon(nombre_obj)

    # ── Dibujo ───────────────────────────────

    def _dibujar(self):
        self.ventana.fill(C_FONDO)
        if self.img_fondo:
            self.ventana.blit(self.img_fondo, (0, 0))

        self._dibujar_titulo()
        self._dibujar_input()
        self._dibujar_tabla()
        # Sugerencias al final para que queden ENCIMA de la tabla
        self._dibujar_sugerencias()

        if self.estado_juego.terminado:
            self._dibujar_overlay_fin()

    def _dibujar_titulo(self):
        titulo = self.f_titulo.render("POKÉDLE", True, C_TEXTO)
        self.ventana.blit(titulo, (20, 20))

        total = len(self.estado_juego.df_pokemon)
        subtitulo = self.f_texto.render(
            f"Gen 1–9  •  {total} pokémones  •  Intentos: {len(self.estado_juego.historial)}/{self.estado_juego.max_intentos}",
            True, C_TEXTO_DIM
        )
        self.ventana.blit(subtitulo, (20, 62))

    def _dibujar_input(self):
        mouse_pos = pygame.mouse.get_pos()
        borde = C_INPUT_ACT if self.input_activo else C_INPUT_BOR

        dibujar_rect_redondeado(self.ventana, C_INPUT_BG, (INPUT_X, INPUT_Y, INPUT_W, INPUT_H), borde=2, borde_color=borde)

        # Texto de placeholder
        mostrar = self.entrada_texto if self.entrada_texto else "Escribe el nombre de un pokémon..."
        color   = C_TEXTO if self.entrada_texto else C_TEXTO_DIM
        texto_s = self.f_texto.render(mostrar, True, color)
        self.ventana.blit(texto_s, (INPUT_X + 12, INPUT_Y + 13))

        # Cursor parpadeante
        if self.input_activo and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = INPUT_X + 12 + texto_s.get_width() + 2 if self.entrada_texto else INPUT_X + 12
            pygame.draw.line(self.ventana, C_TEXTO, (cursor_x, INPUT_Y + 8), (cursor_x, INPUT_Y + INPUT_H - 8), 2)

        # Botón adivinar
        hover = (BOTON_X <= mouse_pos[0] <= BOTON_X + BOTON_W and BOTON_Y <= mouse_pos[1] <= BOTON_Y + BOTON_H)
        color_btn = C_BOTON_HOV if hover else C_BOTON
        dibujar_rect_redondeado(self.ventana, color_btn, (BOTON_X, BOTON_Y, BOTON_W, BOTON_H))
        dibujar_texto_centrado(self.ventana, "ADIVINAR", self.f_subtitulo, C_TEXTO, (BOTON_X, BOTON_Y, BOTON_W, BOTON_H))

    def _dibujar_sugerencias(self):
        if not self.sugerencias:
            return

        mouse_pos = pygame.mouse.get_pos()
        for i, sug in enumerate(self.sugerencias):
            sy    = INPUT_Y + INPUT_H + 4 + i * SUG_H
            hover = (SUG_X <= mouse_pos[0] <= SUG_X + SUG_W and sy <= mouse_pos[1] <= sy + SUG_H)
            selec = (i == self.sug_selec)

            color_bg = C_SUG_HOV if (hover or selec) else C_SUGERENCIA
            dibujar_rect_redondeado(self.ventana, color_bg, (SUG_X, sy, SUG_W, SUG_H - 2), radio=4)
            texto = self.f_texto.render(sug, True, C_TEXTO)
            self.ventana.blit(texto, (SUG_X + 12, sy + 10))

    def _dibujar_tabla(self):
        if not self.estado_juego.historial:
            msg = self.f_texto.render("Escribe el nombre de un pokémon para empezar...", True, C_TEXTO_DIM)
            self.ventana.blit(msg, (TABLA_X, TABLA_Y + 10))
            return

        # Calcular posiciones y anchos de columnas según contenido
        COLS_ANCHAS = {"categoria", "habilidad_1", "habilidad_2"}
        cols = list(TODAS_COLUMNAS)
        col_anchos = [COL_ANCHOS.get(c, 110) for c in cols]

        # Posición X de cada columna (acumulativa)
        col_x = []
        x_acum = TABLA_X + COL_NOMBRE_W
        for w in col_anchos:
            col_x.append(x_acum)
            x_acum += w
        tabla_w = x_acum - TABLA_X

        # Cabecera
        dibujar_rect_redondeado(
            self.ventana, C_HEADER,
            (TABLA_X, TABLA_Y, tabla_w, CABECERA_ALTO), radio=6
        )
        # "Pokémon"
        txt = self.f_pequeña.render("Pokémon", True, C_TEXTO_DIM)
        self.ventana.blit(txt, (TABLA_X + PADDING, TABLA_Y + 10))

        for i, col in enumerate(cols):
            nombre_corto = NOMBRES_COLUMNA.get(col, col)
            txt = self.f_pequeña.render(nombre_corto, True, C_TEXTO_DIM)
            txt_rect = txt.get_rect(center=(col_x[i] + col_anchos[i] // 2, TABLA_Y + CABECERA_ALTO // 2))
            self.ventana.blit(txt, txt_rect)

        # Clip para scroll de filas
        area_tabla = pygame.Rect(TABLA_X, TABLA_Y + CABECERA_ALTO, tabla_w, ALTO - TABLA_Y - CABECERA_ALTO - 20)
        self.ventana.set_clip(area_tabla)

        # Filas de intentos
        for idx, entrada in enumerate(self.estado_juego.historial):
            fy_base = TABLA_Y + CABECERA_ALTO + idx * FILA_ALTO - self.scroll_tabla
            if fy_base + FILA_ALTO < area_tabla.top or fy_base > area_tabla.bottom:
                continue

            # Fondo de fila
            color_fila = (20, 40, 20) if entrada["correcto"] else (25, 25, 50)
            dibujar_rect_redondeado(
                self.ventana, color_fila,
                (TABLA_X, fy_base, tabla_w, FILA_ALTO - 2), radio=4
            )

            # Nombre del pokémon
            nombre = truncar(entrada["pokemon"]["nombre"], 16)
            txt = self.f_texto.render(nombre, True, C_TEXTO)
            self.ventana.blit(txt, (TABLA_X + PADDING, fy_base + (FILA_ALTO - txt.get_height()) // 2))

            # Celdas de atributos
            resultados = entrada["resultados"]
            for i, col in enumerate(cols):
                res = resultados.get(col)
                if res is None:
                    continue
                cx = col_x[i]
                w  = col_anchos[i]
                celda = (cx + 2, fy_base + 3, w - 4, FILA_ALTO - 6)

                color_celda = COLOR_ESTADO.get(res.estado, C_FONDO)
                dibujar_rect_redondeado(self.ventana, color_celda, celda, radio=5)

                # Truncado proporcional al ancho de la columna (aprox 9px por carácter)
                max_chars = max(3, (col_anchos[i] - 30) // 9)
                valor_str = truncar(str(res.valor_guess), max_chars)
                icono     = ICONO_ESTADO.get(res.estado, "")
                linea     = f"{valor_str} {icono}" if icono else valor_str

                dibujar_texto_centrado(self.ventana, linea, self.f_pequeña, (10, 10, 20), celda)

        self.ventana.set_clip(None)

        # Leyenda de colores
        self._dibujar_leyenda()

    def _dibujar_leyenda(self):
        leyenda_y = ALTO - 28
        items = [
            (C_GREEN,  "✓ Correcto"),
            (C_RED,    "✗ Incorrecto"),
            (C_YELLOW, "~ Cerca"),
            (C_UP,     "↑ El objetivo es mayor"),
            (C_DOWN,   "↓ El objetivo es menor"),
        ]
        x = 20
        for color, texto in items:
            pygame.draw.rect(self.ventana, color, (x, leyenda_y + 4, 14, 14), border_radius=3)
            txt = self.f_pequeña.render(texto, True, C_TEXTO_DIM)
            self.ventana.blit(txt, (x + 18, leyenda_y + 3))
            x += txt.get_width() + 34

    def _dibujar_overlay_fin(self):
        """Overlay con imagen del pokémon al ganar o perder."""
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, OVERLAY_ALPHA))
        self.ventana.blit(overlay, (0, 0))

        nombre_obj = self.estado_juego.objetivo["nombre"]

        # ── Imagen del pokémon ───────────────────
        IMG_SIZE = 260
        IMG_X    = ANCHO // 2 - IMG_SIZE // 2
        IMG_Y    = 60

        if self.img_pokemon_fin:
            img_scaled = pygame.transform.smoothscale(self.img_pokemon_fin, (IMG_SIZE, IMG_SIZE))
            # Marco redondeado detrás de la imagen
            color_marco = C_GREEN if self.estado_juego.ganado else C_RED
            dibujar_rect_redondeado(
                self.ventana, (30, 30, 60),
                (IMG_X - 10, IMG_Y - 10, IMG_SIZE + 20, IMG_SIZE + 20),
                radio=16, borde=3, borde_color=color_marco
            )
            self.ventana.blit(img_scaled, (IMG_X, IMG_Y))
        else:
            # Sin imagen: mostrar cuadrado con el nombre
            dibujar_rect_redondeado(
                self.ventana, (30, 30, 60),
                (IMG_X, IMG_Y, IMG_SIZE, IMG_SIZE), radio=16
            )
            txt = self.f_titulo.render("?", True, C_TEXTO_DIM)
            self.ventana.blit(txt, txt.get_rect(center=(ANCHO // 2, IMG_Y + IMG_SIZE // 2)))

        # ── Textos debajo de la imagen ───────────
        cy = IMG_Y + IMG_SIZE + 24

        if self.estado_juego.ganado:
            intentos = len(self.estado_juego.historial)
            lineas = [
                ("¡Lo lograste!", self.f_titulo, C_GREEN),
                (f"Era: {nombre_obj}", self.f_subtitulo, C_YELLOW),
                (f"Adivinaste en {intentos} intento{'s' if intentos > 1 else ''}.", self.f_texto, C_TEXTO),
            ]
        else:
            lineas = [
                ("¡Se acabaron los intentos!", self.f_titulo, C_RED),
                (f"Era: {nombre_obj}", self.f_subtitulo, C_YELLOW),
            ]

        lineas.append(("Presiona R para jugar de nuevo", self.f_texto, C_TEXTO_DIM))

        for texto, fuente, color in lineas:
            surf = fuente.render(texto, True, color)
            rect = surf.get_rect(centerx=ANCHO // 2, y=cy)
            self.ventana.blit(surf, rect)
            cy += surf.get_height() + 14


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    interfaz = InterfazPokedle()
    interfaz.run()


if __name__ == "__main__":
    main()
