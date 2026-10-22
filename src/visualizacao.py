"""Interface grafica pygame — identidade arcade neon.

Modo Exploracao: dois paineis lado a lado (UCS | A*), animando expansoes.
Modo Rotas (Tab): um painel com rota BFS (magenta tracejada) e A* (amarela).

Paleta, fontes e layout centralizados em src/config.py (NEON).

Controles:
    Espaco / ->  play/pause / avanca um passo
    R            reinicia animacao
    Tab          alterna Exploracao <-> Rotas
    + / -        aumenta / diminui lambda (recalcula custos e rotas)
    [ / ]        diminui / aumenta velocidade da animacao
    N            proximo mapa (se lista fornecida)
    G            gera labirinto aleatorio (nova seed)
    S            salva screenshot em resultados/
"""

from __future__ import annotations
import math
import os
import time
import urllib.request
import urllib.parse
import zipfile
import io

try:
    import pygame
    _PYGAME_OK = True
except ImportError:
    _PYGAME_OK = False

from src.config import NEON

# ---------------------------------------------------------------------------
# Constantes de layout
# ---------------------------------------------------------------------------
MARGIN       = 24
ALT_CARD     = 74
ALT_BARRA    = 46
ALT_RODAPE   = 94
TC_MIN       = 5
TC_MAX       = 24
MAX_W        = 1600
MAX_H        = 900

_DIR_FONTES = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "assets", "fontes")
)

# ---------------------------------------------------------------------------
# Download / carregamento de fontes
# ---------------------------------------------------------------------------

def _baixar_font_github(nome_arquivo: str, url: str) -> bool:
    dest = os.path.join(_DIR_FONTES, nome_arquivo)
    if os.path.exists(dest):
        return True
    os.makedirs(_DIR_FONTES, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=15).read()
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"[fonte] {nome_arquivo}: {e}")
    return False


def _carregar_fontes() -> dict:
    if not _PYGAME_OK:
        return {}

    _baixar_font_github(
        "PressStart2P-Regular.ttf",
        "https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf",
    )
    _baixar_font_github(
        "JetBrainsMono-Regular.ttf",
        "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf",
    )

    def _f(arq, tam):
        p = os.path.join(_DIR_FONTES, arq)
        if os.path.exists(p):
            try:
                return pygame.font.Font(p, tam)
            except Exception:
                pass
        return pygame.font.SysFont("monospace", tam)

    return {
        "titulo":  _f("PressStart2P-Regular.ttf", 10),
        "titulo_p": _f("PressStart2P-Regular.ttf",  8),
        "num_g":   _f("JetBrainsMono-Regular.ttf", 14),
        "num_p":   _f("JetBrainsMono-Regular.ttf", 12),
        "ui":      _f("JetBrainsMono-Regular.ttf", 11),
    }


# ---------------------------------------------------------------------------
# Calculo de dimensoes
# ---------------------------------------------------------------------------

def _dimensoes(linhas: int, colunas: int, modo: int) -> tuple[int, int, int]:
    """Retorna (LARGURA, ALTURA, tc) adaptados ao mapa e ao modo."""
    n_paineis = 2 if modo == 0 else 1
    alt_util = MAX_H - 2 * MARGIN - ALT_CARD - ALT_BARRA - ALT_RODAPE
    larg_pan = (MAX_W - (n_paineis + 1) * MARGIN) // n_paineis
    tc = min(larg_pan // max(colunas, 1), alt_util // max(linhas, 1), TC_MAX)
    tc = max(tc, TC_MIN)
    larg_pan_real = colunas * tc
    alt_grid      = linhas  * tc
    LARGURA = max(n_paineis * larg_pan_real + (n_paineis + 1) * MARGIN, 900)
    ALTURA  = max(alt_grid + 2 * MARGIN + ALT_CARD + ALT_BARRA + ALT_RODAPE, 600)
    return LARGURA, ALTURA, tc


# ---------------------------------------------------------------------------
# Primitivos de desenho
# ---------------------------------------------------------------------------

def _desenhar_fantasma(surf, cx: int, cy: int, r: int) -> None:
    if r < 3:
        pygame.draw.circle(surf, NEON.fantasma, (cx, cy), r)
        return
    cor = NEON.fantasma
    # Topo arredondado
    pygame.draw.circle(surf, cor, (cx, cy - r // 3), r)
    # Corpo retangular
    pygame.draw.rect(surf, cor, (cx - r, cy - r // 3, 2 * r, r + r // 2))
    # Ondas na base (3 meia-circulos cortados)
    seg = max(1, (2 * r) // 3)
    for i in range(3):
        bx = cx - r + i * seg + seg // 2
        pygame.draw.circle(surf, NEON.fundo_grid, (bx, cy + r // 2 + 1), r // 4 + 1)
    # Olhos
    if r >= 7:
        for ex in (cx - r // 3, cx + r // 3):
            pygame.draw.circle(surf, (255, 255, 255), (ex, cy - r // 3), max(2, r // 4))
            pygame.draw.circle(surf, (20,  20,  60), (ex, cy - r // 3), max(1, r // 8))


def _desenhar_fruta(surf, cx: int, cy: int, r: int) -> None:
    cor = NEON.objetivo
    pygame.draw.circle(surf, cor, (cx, cy), r)
    # Brilho interno
    if r >= 5:
        pygame.draw.circle(surf, (180, 255, 120), (cx - r // 3, cy - r // 3), max(1, r // 3))
    # Cabinho
    cabo = (0, 180, 60)
    pygame.draw.line(surf, cabo, (cx, cy - r), (cx + r // 2, cy - r - r // 2), max(1, r // 3))


def _desenhar_agente(surf, cx: int, cy: int, r: int) -> None:
    pygame.draw.circle(surf, NEON.inicio, (cx, cy), r)
    if r >= 5:
        # Olho / brilho
        pygame.draw.circle(surf, (255, 255, 200), (cx - r // 3, cy - r // 3), max(1, r // 4))


def _pellet(surf, cx: int, cy: int) -> None:
    pygame.draw.circle(surf, NEON.pellet, (cx, cy), 2)


def _linha_glow(surf, pts: list, cor: tuple, lw: int) -> None:
    """Linha com 3 camadas de glow (SRCALPHA)."""
    if len(pts) < 2:
        return
    W, H = surf.get_size()
    for extra, alpha in ((lw + 8, 22), (lw + 4, 65), (lw, 230)):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.lines(s, (*cor, alpha), False, pts, extra)
        surf.blit(s, (0, 0))


def _linha_tracejada_glow(surf, pts: list, cor: tuple, lw: int,
                           dash: int = 9, gap: int = 6) -> None:
    """Linha tracejada com glow (rota BFS)."""
    if len(pts) < 2:
        return
    W, H = surf.get_size()
    for extra, alpha in ((lw + 4, 30), (lw + 2, 75), (lw, 210)):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        acum = 0.0
        traco = True
        for i in range(len(pts) - 1):
            x1, y1 = float(pts[i][0]),   float(pts[i][1])
            x2, y2 = float(pts[i+1][0]), float(pts[i+1][1])
            dist = math.hypot(x2 - x1, y2 - y1)
            if dist < 1e-6:
                continue
            ux, uy = (x2 - x1) / dist, (y2 - y1) / dist
            pos = 0.0
            while pos < dist:
                tam = (dash if traco else gap) - acum
                restante = dist - pos
                if tam >= restante:
                    acum += restante
                    if traco:
                        ax = x1 + ux * pos;  ay = y1 + uy * pos
                        pygame.draw.line(s, (*cor, alpha),
                                         (int(ax), int(ay)),
                                         (int(x1 + ux * dist), int(y1 + uy * dist)),
                                         extra)
                    pos = dist
                else:
                    if traco:
                        ax = x1 + ux * pos;       ay = y1 + uy * pos
                        bx = x1 + ux * (pos+tam); by = y1 + uy * (pos+tam)
                        pygame.draw.line(s, (*cor, alpha),
                                         (int(ax), int(ay)), (int(bx), int(by)), extra)
                    pos  += tam
                    traco = not traco
                    acum  = 0.0
        surf.blit(s, (0, 0))


# ---------------------------------------------------------------------------
# Camadas de renderizacao
# ---------------------------------------------------------------------------

def _layer_base(surf, lab, expanded: set, tc: int, ox: int, oy: int) -> None:
    """Camada 1 — terreno, paredes com borda neon, pellets nos nao-expandidos."""
    from src.config import CFG
    # (dl, dc, bx_offset, by_offset, bw, bh)
    BORDAS = [
        (-1,  0,  0,       0,      tc,  2),   # topo
        ( 0,  1,  tc - 2,  0,       2, tc),   # direita
        ( 1,  0,  0,      tc - 2,  tc,  2),   # baixo
        ( 0, -1,  0,       0,       2, tc),   # esquerda
    ]
    INTRANS = {CFG.simbolo_parede, CFG.simbolo_fantasma}
    CORREDORES = {CFG.simbolo_corredor, CFG.simbolo_espaco,
                  CFG.simbolo_inicio,   CFG.simbolo_objetivo}

    for l in range(lab.linhas):
        for c in range(lab.colunas):
            s  = lab.grade[l][c]
            cx = ox + c * tc
            cy = oy + l * tc

            if s == CFG.simbolo_parede:
                pygame.draw.rect(surf, NEON.parede_fill, (cx, cy, tc, tc))
                for dl, dc, bx, by, bw, bh in BORDAS:
                    nl, nc = l + dl, c + dc
                    viz_parede = (
                        0 <= nl < lab.linhas and
                        0 <= nc < lab.colunas and
                        lab.grade[nl][nc] == CFG.simbolo_parede
                    )
                    if not viz_parede:
                        pygame.draw.rect(surf, NEON.parede_borda,
                                         (cx + bx, cy + by, bw, bh))

            elif s == CFG.simbolo_lento:
                pygame.draw.rect(surf, NEON.lento, (cx, cy, tc, tc))

            elif s == CFG.simbolo_risco_fixo:
                pygame.draw.rect(surf, NEON.risco_fixo, (cx, cy, tc, tc))

            else:
                pygame.draw.rect(surf, NEON.corredor, (cx, cy, tc, tc))
                pos = (l, c)
                if s in CORREDORES and pos not in expanded:
                    _pellet(surf, cx + tc // 2, cy + tc // 2)


def _layer_risco(surf, lab, campo_risco, lambda_risco: float,
                 tc: int, ox: int, oy: int) -> None:
    """Camada 2 — sobreposicao vermelha proporcional ao risco."""
    if lambda_risco <= 0:
        return
    from src.config import CFG
    ov = pygame.Surface((lab.colunas * tc, lab.linhas * tc), pygame.SRCALPHA)
    for l in range(lab.linhas):
        for c in range(lab.colunas):
            if lab.grade[l][c] == CFG.simbolo_parede:
                continue
            rv = campo_risco[l][c]
            if rv <= 0:
                continue
            alpha = min(140, int(rv * lambda_risco * 2.4))
            pygame.draw.rect(ov, (*NEON.risco, alpha), (c * tc, l * tc, tc, tc))
    surf.blit(ov, (ox, oy))


def _layer_exploracao(surf, lab, expanded: set, frontier: set,
                       tc: int, ox: int, oy: int) -> None:
    """Camada 3 — fechados (verde fill), fronteira (ciano contorno)."""
    from src.config import CFG
    INTRANS = {CFG.simbolo_parede, CFG.simbolo_fantasma}
    ov = pygame.Surface((lab.colunas * tc, lab.linhas * tc), pygame.SRCALPHA)
    for l, c in expanded:
        if lab.grade[l][c] not in INTRANS:
            pygame.draw.rect(ov, (*NEON.fechado, 72), (c * tc, l * tc, tc, tc))
    for l, c in frontier:
        if lab.grade[l][c] not in INTRANS:
            borda = max(1, tc // 5)
            pygame.draw.rect(ov, (*NEON.fronteira, 210),
                             (c * tc, l * tc, tc, tc), borda)
    surf.blit(ov, (ox, oy))


def _layer_rota(surf, caminho: list, cor: tuple, tracejado: bool,
                tc: int, ox: int, oy: int) -> None:
    """Camada 4 — rota com glow (sólida ou tracejada)."""
    if not caminho or len(caminho) < 2:
        return
    pts = [(ox + c * tc + tc // 2, oy + l * tc + tc // 2) for l, c in caminho]
    lw = max(2, tc // 3)
    if tracejado:
        _linha_tracejada_glow(surf, pts, cor, lw)
    else:
        _linha_glow(surf, pts, cor, lw)


def _layer_top(surf, lab, tc: int, ox: int, oy: int) -> None:
    """Camada 5 — P, O, F sempre visiveis no topo."""
    from src.config import CFG
    r = max(3, tc // 2 - 1)
    for l in range(lab.linhas):
        for c in range(lab.colunas):
            s  = lab.grade[l][c]
            cx = ox + c * tc + tc // 2
            cy = oy + l * tc + tc // 2
            if   s == CFG.simbolo_inicio:   _desenhar_agente(surf, cx, cy, r)
            elif s == CFG.simbolo_objetivo: _desenhar_fruta(surf, cx, cy, r)
            elif s == CFG.simbolo_fantasma: _desenhar_fantasma(surf, cx, cy, r)


def _layer_agente_animado(surf, caminho: list, t: float,
                           tc: int, ox: int, oy: int) -> None:
    """Agente percorrendo a rota (posicao interpolada)."""
    if not caminho or t < 0:
        return
    r = max(4, tc // 2)
    n = len(caminho)
    idx = int(t)
    if idx >= n - 1:
        l, c = caminho[-1]
        _desenhar_agente(surf, ox + c * tc + tc // 2, oy + l * tc + tc // 2, r)
        return
    frac = t - idx
    l1, c1 = caminho[idx]
    l2, c2 = caminho[idx + 1]
    ax = ox + int(c1 * tc + (c2 - c1) * tc * frac) + tc // 2
    ay = oy + int(l1 * tc + (l2 - l1) * tc * frac) + tc // 2
    _desenhar_agente(surf, ax, ay, r)


# ---------------------------------------------------------------------------
# Widgets de UI
# ---------------------------------------------------------------------------

def _card(surf, fontes: dict, res, nome: str, formula: str,
          x: int, y: int, w: int, passo_atual: int, concluido: bool) -> None:
    cor_borda = NEON.rota_astar if concluido else NEON.parede_borda
    pygame.draw.rect(surf, (18, 18, 40), (x, y, w, ALT_CARD), border_radius=8)
    pygame.draw.rect(surf, cor_borda, (x, y, w, ALT_CARD), 2, border_radius=8)

    ft = fontes.get("titulo") or fontes.get("ui")
    fn = fontes.get("num_p")  or fontes.get("ui")
    fp = fontes.get("titulo_p") or fontes.get("ui")

    exp_vivo = min(passo_atual, res.nos_expandidos)
    surf.blit(ft.render(nome, True, NEON.texto), (x + 10, y + 8))
    surf.blit(fn.render(formula, True, NEON.texto_sec), (x + 10, y + 30))

    if concluido:
        stats = (f"exp {exp_vivo}/{res.nos_expandidos}  "
                 f"custo {res.custo_total:.1f}  "
                 f"passos {res.passos}  "
                 f"risco {res.exposicao_risco:.1f}")
        surf.blit(fn.render(stats, True, NEON.texto_sec), (x + 10, y + 52))

    if concluido:
        txt = fp.render("CONCLUIDO", True, NEON.rota_astar)
        surf.blit(txt, (x + w - txt.get_width() - 10, y + 8))


def _barra_comparacao(surf, fontes: dict, res_ucs, res_astar,
                       x: int, y: int, largura: int) -> None:
    n_u = res_ucs.nos_expandidos
    n_a = res_astar.nos_expandidos
    mx  = max(n_u, n_a, 1)
    bw_max = int(largura * 0.52)
    bh  = 14
    fn  = fontes.get("num_p") or fontes.get("ui")
    red = (1 - n_a / max(n_u, 1)) * 100

    for i, (n, cor, label) in enumerate([
        (n_u, (90, 90, 170),  f"UCS  {n_u:,} nos"),
        (n_a, NEON.fronteira, f"A*   {n_a:,} nos  (A* expandiu −{red:.0f}%)"),
    ]):
        ry = y + i * (bh + 6)
        pygame.draw.rect(surf, (28, 28, 52), (x, ry, bw_max, bh), border_radius=4)
        bw = max(4, int((n / mx) * bw_max))
        pygame.draw.rect(surf, cor, (x, ry, bw, bh), border_radius=4)
        surf.blit(fn.render(label, True, NEON.texto), (x + bw_max + 12, ry))


def _tecla(surf, f, x: int, y: int, key: str, desc: str) -> int:
    kw = f.size(key)[0] + 10
    kh = f.get_height() + 6
    pygame.draw.rect(surf, (44, 44, 68), (x, y, kw, kh), border_radius=4)
    pygame.draw.rect(surf, (80, 80, 110), (x, y, kw, kh), 1, border_radius=4)
    surf.blit(f.render(key, True, NEON.texto), (x + 5, y + 3))
    dw = f.size(desc)[0]
    surf.blit(f.render(desc, True, NEON.texto_sec), (x + kw + 5, y + 3))
    return x + kw + dw + 18


def _amostra(surf, f, x: int, y: int, cor: tuple, label: str) -> int:
    h = f.get_height()
    pygame.draw.rect(surf, cor, (x, y + 2, 12, h - 4), border_radius=2)
    surf.blit(f.render(label, True, NEON.texto_sec), (x + 16, y))
    return x + 16 + f.size(label)[0] + 14


def _rodape(surf, fontes: dict, estado, LARGURA: int, ALTURA: int) -> None:
    y0 = ALTURA - ALT_RODAPE
    pygame.draw.rect(surf, NEON.fundo, (0, y0, LARGURA, ALT_RODAPE))
    pygame.draw.line(surf, NEON.parede_borda, (0, y0), (LARGURA, y0), 1)

    fu = fontes.get("ui") or fontes.get("num_p")
    x = MARGIN

    controles = [
        ("SPC", "play"),
        ("→",   "passo"),
        ("R",   "reset"),
        ("TAB", "modo"),
        ("+/-", "λ"),
        ("[/]", "vel"),
        ("G",   "mapa"),
        ("S",   "print"),
    ]
    y_keys = y0 + 8
    for key, desc in controles:
        if x + fu.size(key)[0] + fu.size(desc)[0] + 80 > LARGURA:
            break
        x = _tecla(surf, fu, x, y_keys, key, desc)

    # Velocidade no canto direito
    vel_txt = f"{estado.fps_anim} fps"
    surf.blit(fu.render(vel_txt, True, NEON.texto_sec),
              (LARGURA - fu.size(vel_txt)[0] - MARGIN, y_keys))

    # Legenda de cores
    y_leg = y0 + 40
    x = MARGIN
    legenda = [
        (NEON.fechado,    "fechado"),
        (NEON.fronteira,  "fronteira"),
        (NEON.rota_astar, "rota A*"),
        (NEON.rota_bfs,   "rota BFS"),
        (NEON.risco,      "risco"),
        (NEON.lento,      "lento"),
        (NEON.risco_fixo, "risco!"),
    ]
    for cor, label in legenda:
        if x + fu.size(label)[0] + 36 > LARGURA - 120:
            break
        x = _amostra(surf, fu, x, y_leg, cor, label)

    lam_txt = f"λ={estado.lambda_risco:.1f}"
    surf.blit(fu.render(lam_txt, True, NEON.texto),
              (LARGURA - fu.size(lam_txt)[0] - MARGIN, y_leg))


# ---------------------------------------------------------------------------
# Estado da GUI
# ---------------------------------------------------------------------------

class EstadoGUI:
    MODO_EXPLORACAO = 0
    MODO_ROTAS      = 1

    def __init__(self, lab, lambda_risco: float = 5.0):
        self.lambda_risco  = lambda_risco
        self.seed_aleatorio = 42
        self.modo          = self.MODO_EXPLORACAO
        self.fps_anim      = 15
        self.passo         = 0
        self.rodando       = False
        self.t_ag_ucs:   float = -1.0
        self.t_ag_astar: float = -1.0
        self._recarregar(lab)

    def _recarregar(self, lab):
        from src.risco import calcular_risco, calcular_custos
        from src.busca import bfs, busca_custo_uniforme, a_estrela
        self.lab         = lab
        self.campo_risco = calcular_risco(lab.grade, lab.linhas, lab.colunas)
        lab.custo_celula = calcular_custos(lab, self.lambda_risco)
        self.res_bfs     = bfs(lab)
        self.res_ucs     = busca_custo_uniforme(lab)
        self.res_astar   = a_estrela(lab)
        self.passo       = 0
        self.rodando     = False
        self.t_ag_ucs    = -1.0
        self.t_ag_astar  = -1.0

    def _fronteira(self, res, passo: int) -> set:
        exp = set(res.ordem_expansao[:passo])
        return {p for p, pg in res.passo_geracao_dict.items()
                if pg < passo and p not in exp}

    def proximo_passo(self) -> None:
        lim = max(len(self.res_ucs.ordem_expansao),
                  len(self.res_astar.ordem_expansao))
        if self.passo < lim:
            self.passo += 1

    def reiniciar(self) -> None:
        self.passo = 0
        self.rodando = False
        self.t_ag_ucs = self.t_ag_astar = -1.0

    def alternar_modo(self) -> None:
        self.modo = 1 - self.modo
        self.reiniciar()

    def trocar_lambda(self, delta: float) -> None:
        self.lambda_risco = max(0.0, self.lambda_risco + delta)
        modo = self.modo
        self._recarregar(self.lab)
        self.modo = modo

    def ajustar_vel(self, delta: int) -> None:
        self.fps_anim = max(1, min(60, self.fps_anim + delta))

    def carregar_mapa(self, caminho: str) -> None:
        from src.labirinto import carregar_labirinto
        self._recarregar(carregar_labirinto(caminho, lambda_risco=self.lambda_risco))

    def gerar_aleatorio(self, tam: int = 21) -> None:
        from src.gerador import gerar_labirinto
        self.seed_aleatorio += 1
        self._recarregar(
            gerar_labirinto(tam, tam, seed=self.seed_aleatorio,
                             lambda_risco=self.lambda_risco)
        )

    def tick_agente(self, dt: float) -> None:
        """Avanca a posicao do agente animado (10 celulas/s)."""
        VEL = 10.0
        if self.passo >= len(self.res_ucs.ordem_expansao):
            if self.t_ag_ucs < 0:
                self.t_ag_ucs = 0.0
            elif self.res_ucs.encontrado:
                tmax = float(len(self.res_ucs.caminho) - 1)
                self.t_ag_ucs = min(tmax, self.t_ag_ucs + dt * VEL)
        if self.passo >= len(self.res_astar.ordem_expansao):
            if self.t_ag_astar < 0:
                self.t_ag_astar = 0.0
            elif self.res_astar.encontrado:
                tmax = float(len(self.res_astar.caminho) - 1)
                self.t_ag_astar = min(tmax, self.t_ag_astar + dt * VEL)


# ---------------------------------------------------------------------------
# Renderizacao de paineis
# ---------------------------------------------------------------------------

def _painel_exploracao(surf, estado: EstadoGUI, res, t_ag: float,
                        tc: int, ox: int, oy: int) -> None:
    lab   = estado.lab
    passo = estado.passo
    exp   = set(res.ordem_expansao[:passo])
    front = estado._fronteira(res, passo)

    _layer_base(surf, lab, exp, tc, ox, oy)
    _layer_risco(surf, lab, estado.campo_risco, estado.lambda_risco, tc, ox, oy)
    _layer_exploracao(surf, lab, exp, front, tc, ox, oy)

    conc = passo >= len(res.ordem_expansao)
    if conc and res.encontrado:
        _layer_rota(surf, res.caminho, NEON.rota_astar, False, tc, ox, oy)

    _layer_top(surf, lab, tc, ox, oy)

    if conc and t_ag >= 0 and res.encontrado:
        _layer_agente_animado(surf, res.caminho, t_ag, tc, ox, oy)


def _painel_rotas(surf, estado: EstadoGUI, tc: int, ox: int, oy: int) -> None:
    lab = estado.lab
    _layer_base(surf, lab, set(), tc, ox, oy)
    _layer_risco(surf, lab, estado.campo_risco, estado.lambda_risco, tc, ox, oy)
    if estado.res_bfs.encontrado:
        _layer_rota(surf, estado.res_bfs.caminho,   NEON.rota_bfs,   True,  tc, ox, oy)
    if estado.res_astar.encontrado:
        _layer_rota(surf, estado.res_astar.caminho, NEON.rota_astar, False, tc, ox, oy)
    _layer_top(surf, lab, tc, ox, oy)


# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------

def iniciar_gui(
    lab_inicial,
    lambda_risco: float = 5.0,
    mapas_extras: list[str] | None = None,
) -> None:
    if not _PYGAME_OK:
        raise ImportError("pygame nao instalado. Execute: pip install pygame")

    pygame.init()
    fontes = _carregar_fontes()

    estado = EstadoGUI(lab_inicial, lambda_risco=lambda_risco)
    LARGURA, ALTURA, _ = _dimensoes(
        estado.lab.linhas, estado.lab.colunas, estado.modo
    )
    screen = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Pac-Man: UCS vs A*")
    clock = pygame.time.Clock()

    mapas_lista = mapas_extras or []
    indice_mapa = 0
    screenshot_n = 0
    t_ant = time.time()
    t_ult_passo = 0.0

    def _tc_atual() -> int:
        LW, LH = screen.get_size()
        alt_util = LH - 2 * MARGIN - ALT_CARD - ALT_BARRA - ALT_RODAPE
        n = 2 if estado.modo == EstadoGUI.MODO_EXPLORACAO else 1
        larg = (LW - (n + 1) * MARGIN) // n
        return max(TC_MIN, min(
            larg // max(estado.lab.colunas, 1),
            alt_util // max(estado.lab.linhas, 1),
            TC_MAX,
        ))

    def _redimensionar():
        nonlocal screen
        LW, LH, _ = _dimensoes(estado.lab.linhas, estado.lab.colunas, estado.modo)
        if (LW, LH) != screen.get_size():
            screen = pygame.display.set_mode((LW, LH))

    rodando = True
    while rodando:
        agora = time.time()
        dt    = min(agora - t_ant, 0.1)   # limita dt para evitar saltos grandes
        t_ant = agora

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                rodando = False
            elif ev.type == pygame.KEYDOWN:
                k = ev.key
                if   k == pygame.K_SPACE:
                    estado.rodando = not estado.rodando
                elif k == pygame.K_RIGHT:
                    estado.proximo_passo()
                elif k == pygame.K_r:
                    estado.reiniciar()
                elif k == pygame.K_TAB:
                    estado.alternar_modo(); _redimensionar()
                elif k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    estado.trocar_lambda(1.0)
                elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    estado.trocar_lambda(-1.0)
                elif k == pygame.K_LEFTBRACKET:
                    estado.ajustar_vel(-2)
                elif k == pygame.K_RIGHTBRACKET:
                    estado.ajustar_vel(2)
                elif k == pygame.K_n and mapas_lista:
                    indice_mapa = (indice_mapa + 1) % len(mapas_lista)
                    estado.carregar_mapa(mapas_lista[indice_mapa])
                    _redimensionar()
                elif k == pygame.K_g:
                    estado.gerar_aleatorio(21); _redimensionar()
                elif k == pygame.K_s:
                    os.makedirs("resultados", exist_ok=True)
                    nome = f"resultados/screenshot_{screenshot_n:03d}.png"
                    pygame.image.save(screen, nome)
                    screenshot_n += 1
                    print(f"Screenshot: {nome}")

        # Avanca passo de exploracao
        if estado.rodando and (agora - t_ult_passo) > (1.0 / estado.fps_anim):
            estado.proximo_passo()
            t_ult_passo = agora

        # Avanca agente
        estado.tick_agente(dt)

        # Renderizacao
        LW, LH = screen.get_size()
        screen.fill(NEON.fundo)

        tc       = _tc_atual()
        lab      = estado.lab
        alt_util = LH - 2 * MARGIN - ALT_CARD - ALT_BARRA - ALT_RODAPE
        y_card   = MARGIN
        y_grid   = MARGIN + ALT_CARD + 4
        y_barra  = y_grid + alt_util + 6

        if estado.modo == EstadoGUI.MODO_EXPLORACAO:
            n_pan   = 2
            larg_pan = (LW - (n_pan + 1) * MARGIN) // n_pan

            for idx, (res, nome, formula, t_ag) in enumerate([
                (estado.res_ucs,   "UCS", "f = g",     estado.t_ag_ucs),
                (estado.res_astar, "A*",  "f = g + h", estado.t_ag_astar),
            ]):
                ox   = MARGIN + idx * (larg_pan + MARGIN)
                conc = estado.passo >= len(res.ordem_expansao)
                cor_borda = NEON.rota_astar if conc else (40, 40, 72)

                # Fundo do painel
                pygame.draw.rect(screen, NEON.fundo_grid,
                                 (ox, y_grid, larg_pan, alt_util), border_radius=6)
                _painel_exploracao(screen, estado, res, t_ag, tc, ox, y_grid)
                pygame.draw.rect(screen, cor_borda,
                                 (ox, y_grid, larg_pan, alt_util), 2, border_radius=6)

                _card(screen, fontes, res, nome, formula,
                      ox, y_card, larg_pan, estado.passo, conc)

            ambos_concluidos = (
                estado.passo >= len(estado.res_ucs.ordem_expansao) and
                estado.passo >= len(estado.res_astar.ordem_expansao)
            )
            if ambos_concluidos:
                _barra_comparacao(screen, fontes, estado.res_ucs, estado.res_astar,
                                   MARGIN, y_barra, LW - 2 * MARGIN)

        else:  # MODO_ROTAS
            ox       = MARGIN
            larg_pan = LW - 2 * MARGIN
            pygame.draw.rect(screen, NEON.fundo_grid,
                             (ox, y_grid, larg_pan, alt_util), border_radius=6)
            _painel_rotas(screen, estado, tc, ox, y_grid)
            pygame.draw.rect(screen, (40, 40, 72),
                             (ox, y_grid, larg_pan, alt_util), 2, border_radius=6)

            # Cards BFS e A* lado a lado no topo
            w2 = (larg_pan - MARGIN) // 2
            _card(screen, fontes, estado.res_bfs, "BFS", "f = passos",
                  ox, y_card, w2, estado.res_bfs.nos_expandidos, True)
            _card(screen, fontes, estado.res_astar, "A*",  "f = g + h",
                  ox + w2 + MARGIN, y_card, w2,
                  estado.res_astar.nos_expandidos, True)
            _barra_comparacao(screen, fontes, estado.res_ucs, estado.res_astar,
                               MARGIN, y_barra, LW - 2 * MARGIN)

        _rodape(screen, fontes, estado, LW, LH)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
