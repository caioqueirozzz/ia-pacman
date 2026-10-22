"""Interface grafica pygame.

Modo Exploracao: dois paineis lado a lado (UCS | A*) animando a expansao.
Modo Rotas (Tab): um painel com a rota BFS (ciano) e A* (amarelo) sobrepostas.

Controles:
    Espaco       Play/pause da animacao
    ->           Avanca um passo
    R            Reinicia
    Tab          Alterna Exploracao / Rotas
    + / -        Aumenta/diminui lambda (recalcula custos e rotas)
    N            Proximo mapa (se lista fornecida)
    G            Gera mapa aleatorio (nova seed)
    S            Salva screenshot em resultados/
"""

from __future__ import annotations
import os
import time

try:
    import pygame
    _PYGAME_OK = True
except ImportError:
    _PYGAME_OK = False

# ---------------------------------------------------------------------------
# Paleta unificada (mesma nos dois paineis)
# ---------------------------------------------------------------------------
COR_PAREDE       = (25,  25,  80)
COR_CORREDOR     = (8,   8,   8)
COR_LENTO        = (90,  55,  20)
COR_RISCO_FIXO   = (160, 80,   0)
COR_FECHADO      = (0,  160,  80)   # verde — nos ja expandidos
COR_FRONTEIRA    = (0,  200, 220)   # ciano — nos na fila
COR_CAMINHO      = (255, 220,  0)   # amarelo — rota final / rota A* no modo Rotas
COR_CAMINHO_BFS  = (0,  220, 220)   # ciano — rota BFS no modo Rotas
COR_INICIO       = (255, 220,  0)
COR_OBJETIVO     = (0,  220,  0)
COR_FANTASMA     = (220,  50, 220)
COR_FUNDO_UI     = (15,  15,  25)
COR_TEXTO        = (220, 220, 220)
COR_RISCO_OVER   = (220,  30,  30)  # vermelho translucido

ALTURA_RODAPE = 120  # pixels reservados para o rodape


def _tamanho_celula(linhas: int, colunas: int, larg_painel: int, altura_util: int) -> int:
    return max(3, min(larg_painel // colunas, altura_util // linhas))


# ---------------------------------------------------------------------------
# Camadas de renderizacao
# ---------------------------------------------------------------------------

def _desenhar_base(surface: "pygame.Surface", lab, tc: int, ox: int, oy: int) -> None:
    """Camada 1 — cor do terreno de cada celula."""
    from src.config import CFG
    corredores = {CFG.simbolo_corredor, CFG.simbolo_espaco,
                  CFG.simbolo_inicio, CFG.simbolo_objetivo, CFG.simbolo_fantasma}
    for l in range(lab.linhas):
        for c in range(lab.colunas):
            s = lab.grade[l][c]
            if s == CFG.simbolo_parede:
                cor = COR_PAREDE
            elif s == CFG.simbolo_lento:
                cor = COR_LENTO
            elif s == CFG.simbolo_risco_fixo:
                cor = COR_RISCO_FIXO
            else:
                cor = COR_CORREDOR  # corredores, inicio, objetivo, fantasma — base preta
            pygame.draw.rect(surface, cor, (ox + c * tc, oy + l * tc, tc, tc))


def _desenhar_risco_overlay(
    surface: "pygame.Surface", lab, campo_risco, lambda_risco: float,
    tc: int, ox: int, oy: int
) -> None:
    """Camada 2 — sobreposicao vermelha translucida proporcional ao risco."""
    if lambda_risco <= 0:
        return
    from src.config import CFG
    overlay = pygame.Surface(
        (lab.colunas * tc, lab.linhas * tc), pygame.SRCALPHA
    )
    for l in range(lab.linhas):
        for c in range(lab.colunas):
            if lab.grade[l][c] == CFG.simbolo_parede:
                continue
            rv = campo_risco[l][c]
            if rv <= 0:
                continue
            alpha = min(210, int(rv * lambda_risco * 2.8))
            pygame.draw.rect(overlay, (*COR_RISCO_OVER, alpha), (c * tc, l * tc, tc, tc))
    surface.blit(overlay, (ox, oy))


def _desenhar_exploracao_overlay(
    surface: "pygame.Surface", lab, expanded: set, frontier: set,
    tc: int, ox: int, oy: int
) -> None:
    """Camada 3 — nos fechados (verde) e fronteira (ciano) translucidos."""
    from src.config import CFG
    intransitiavel = {CFG.simbolo_parede, CFG.simbolo_fantasma}
    overlay = pygame.Surface(
        (lab.colunas * tc, lab.linhas * tc), pygame.SRCALPHA
    )
    for (l, c) in expanded:
        if lab.grade[l][c] not in intransitiavel:
            pygame.draw.rect(overlay, (*COR_FECHADO, 110), (c * tc, l * tc, tc, tc))
    for (l, c) in frontier:
        if lab.grade[l][c] not in intransitiavel:
            pygame.draw.rect(overlay, (*COR_FRONTEIRA, 170), (c * tc, l * tc, tc, tc))
    surface.blit(overlay, (ox, oy))


def _desenhar_linha_rota(
    surface: "pygame.Surface", caminho: list, tc: int, ox: int, oy: int, cor, espessura: int
) -> None:
    """Camada 4 — rota como linha grossa ligando o centro das celulas."""
    if not caminho or len(caminho) < 2:
        return
    pontos = [(ox + c * tc + tc // 2, oy + l * tc + tc // 2) for l, c in caminho]
    pygame.draw.lines(surface, cor, False, pontos, max(2, espessura))


def _desenhar_elementos_fixos(
    surface: "pygame.Surface", lab, tc: int, ox: int, oy: int
) -> None:
    """Camada 5 (topo) — P, O, F desenhados por cima de tudo."""
    from src.config import CFG
    r = max(2, tc // 2 - 1)
    for l in range(lab.linhas):
        for c in range(lab.colunas):
            s = lab.grade[l][c]
            cx = ox + c * tc + tc // 2
            cy = oy + l * tc + tc // 2
            if s == CFG.simbolo_inicio:
                pygame.draw.circle(surface, COR_INICIO, (cx, cy), r)
            elif s == CFG.simbolo_objetivo:
                pygame.draw.circle(surface, COR_OBJETIVO, (cx, cy), r)
                if tc >= 6:
                    pygame.draw.circle(surface, (0, 0, 0), (cx, cy), max(1, r - 2))
            elif s == CFG.simbolo_fantasma:
                pygame.draw.circle(surface, COR_FANTASMA, (cx, cy), r)
                if tc >= 8:
                    olho_r = max(1, r // 3)
                    pygame.draw.circle(surface, (255, 255, 255),
                                       (cx - r // 3, cy - r // 4), olho_r)
                    pygame.draw.circle(surface, (255, 255, 255),
                                       (cx + r // 3, cy - r // 4), olho_r)


# ---------------------------------------------------------------------------
# Estado da GUI
# ---------------------------------------------------------------------------

class EstadoGUI:
    MODO_EXPLORACAO = 0
    MODO_ROTAS = 1

    def __init__(self, lab, lambda_risco: float = 5.0):
        self.lambda_risco = lambda_risco
        self.seed_aleatorio = 42
        self.modo = self.MODO_EXPLORACAO
        self.passo = 0
        self.rodando = False
        self._recarregar(lab)

    def _recarregar(self, lab):
        from src.risco import calcular_risco, calcular_custos
        from src.busca import bfs, busca_custo_uniforme, a_estrela

        self.lab = lab
        self.campo_risco = calcular_risco(lab.grade, lab.linhas, lab.colunas)
        lab.custo_celula = calcular_custos(lab, self.lambda_risco)

        self.res_bfs   = bfs(lab)
        self.res_ucs   = busca_custo_uniforme(lab)
        self.res_astar = a_estrela(lab)

        self.passo = 0
        self.rodando = False

    def _fronteira_em(self, res, passo: int) -> set:
        """Celulas que estavam na fila (mas nao expandidas) no passo dado."""
        expanded = set(res.ordem_expansao[:passo])
        return {
            pos for pos, pg in res.passo_geracao_dict.items()
            if pg < passo and pos not in expanded
        }

    def proximo_passo(self) -> None:
        limite = max(
            len(self.res_ucs.ordem_expansao),
            len(self.res_astar.ordem_expansao),
        )
        if self.passo < limite:
            self.passo += 1

    def reiniciar(self) -> None:
        self.passo = 0
        self.rodando = False

    def alternar_modo(self) -> None:
        self.modo = 1 - self.modo
        self.reiniciar()

    def trocar_lambda(self, delta: float) -> None:
        self.lambda_risco = max(0.0, self.lambda_risco + delta)
        modo_salvo = self.modo
        self._recarregar(self.lab)
        self.modo = modo_salvo

    def carregar_mapa(self, caminho: str) -> None:
        from src.labirinto import carregar_labirinto
        lab = carregar_labirinto(caminho, lambda_risco=self.lambda_risco)
        self._recarregar(lab)

    def gerar_aleatorio(self, tamanho: int = 21) -> None:
        from src.gerador import gerar_labirinto
        self.seed_aleatorio += 1
        lab = gerar_labirinto(tamanho, tamanho, seed=self.seed_aleatorio,
                               lambda_risco=self.lambda_risco)
        self._recarregar(lab)


# ---------------------------------------------------------------------------
# Rodape
# ---------------------------------------------------------------------------

def _quadrado(surface, cor, x, y, lado=12):
    pygame.draw.rect(surface, cor, (x, y, lado, lado))


def _rodape_exploracao(
    screen, font, font_sm, estado: EstadoGUI, LARGURA: int, ALTURA: int
) -> None:
    y0 = ALTURA - ALTURA_RODAPE
    pygame.draw.rect(screen, COR_FUNDO_UI, (0, y0, LARGURA, ALTURA_RODAPE))
    pygame.draw.line(screen, (60, 60, 90), (0, y0), (LARGURA, y0), 1)

    passo = estado.passo
    res_u = estado.res_ucs
    res_a = estado.res_astar
    n_u = min(passo, len(res_u.ordem_expansao))
    n_a = min(passo, len(res_a.ordem_expansao))
    limite = max(len(res_u.ordem_expansao), len(res_a.ordem_expansao))

    # Linha 1 — progresso
    l1 = (f"Modo: Exploracao  |  lambda={estado.lambda_risco:.1f}  |  "
          f"Passo {passo}/{limite}")
    # Linha 2 — metricas
    l2 = (f"UCS:  exp={n_u},  custo={res_u.custo_total:.1f},  "
          f"passos={res_u.passos},  risco={res_u.exposicao_risco:.1f}     "
          f"A*:   exp={n_a},  custo={res_a.custo_total:.1f},  "
          f"passos={res_a.passos},  risco={res_a.exposicao_risco:.1f}")
    # Linha 3 — controles
    l3 = "Espaco=play/pause  ->  R=reiniciar  Tab=modo  +/-=lambda  G=aleatorio  S=screenshot"

    for i, txt in enumerate([l1, l2, l3]):
        surf = font_sm.render(txt, True, COR_TEXTO)
        screen.blit(surf, (10, y0 + 6 + i * 22))

    # Legenda de cores (linha 4, lado direito)
    items = [
        (COR_FECHADO,   "Fechado"),
        (COR_FRONTEIRA, "Fronteira"),
        (COR_CAMINHO,   "Rota final"),
        (COR_RISCO_OVER,"Risco"),
    ]
    lx = LARGURA - 320
    ly = y0 + 72
    for cor, label in items:
        _quadrado(screen, cor, lx, ly)
        surf = font_sm.render(label, True, COR_TEXTO)
        screen.blit(surf, (lx + 16, ly - 1))
        lx += 82


def _rodape_rotas(
    screen, font, font_sm, estado: EstadoGUI, LARGURA: int, ALTURA: int
) -> None:
    y0 = ALTURA - ALTURA_RODAPE
    pygame.draw.rect(screen, COR_FUNDO_UI, (0, y0, LARGURA, ALTURA_RODAPE))
    pygame.draw.line(screen, (60, 60, 90), (0, y0), (LARGURA, y0), 1)

    r_b = estado.res_bfs
    r_a = estado.res_astar

    l1 = f"Modo: Rotas  |  lambda={estado.lambda_risco:.1f}"
    l2 = (f"BFS:  passos={r_b.passos},  custo={r_b.custo_total:.1f},  "
          f"risco={r_b.exposicao_risco:.1f},  dist_fantasma={r_b.dist_min_fantasma}     "
          f"A*:   passos={r_a.passos},  custo={r_a.custo_total:.1f},  "
          f"risco={r_a.exposicao_risco:.1f},  dist_fantasma={r_a.dist_min_fantasma}")
    l3 = "Tab=modo  +/-=lambda  G=aleatorio  S=screenshot"

    for i, txt in enumerate([l1, l2, l3]):
        surf = font_sm.render(txt, True, COR_TEXTO)
        screen.blit(surf, (10, y0 + 6 + i * 22))

    # Legenda
    items = [
        (COR_CAMINHO_BFS, f"BFS ({r_b.passos} passos)"),
        (COR_CAMINHO,     f"A*  ({r_a.passos} passos)"),
    ]
    lx = LARGURA - 340
    ly = y0 + 72
    for cor, label in items:
        _quadrado(screen, cor, lx, ly)
        surf = font_sm.render(label, True, COR_TEXTO)
        screen.blit(surf, (lx + 16, ly - 1))
        lx += 170


# ---------------------------------------------------------------------------
# Renderizacao de painel
# ---------------------------------------------------------------------------

def _renderizar_painel_exploracao(
    screen, estado: EstadoGUI, res, tc: int, ox: int, oy: int, label: str, font
) -> None:
    lab = estado.lab
    passo = estado.passo

    expanded = set(res.ordem_expansao[:passo])
    frontier = estado._fronteira_em(res, passo)

    # 1. Terreno base
    _desenhar_base(screen, lab, tc, ox, oy)
    # 2. Risco
    _desenhar_risco_overlay(screen, lab, estado.campo_risco, estado.lambda_risco, tc, ox, oy)
    # 3. Fechados e fronteira
    _desenhar_exploracao_overlay(screen, lab, expanded, frontier, tc, ox, oy)
    # 4. Rota final — aparece assim que o algoritmo deste painel termina
    if passo >= len(res.ordem_expansao) and res.encontrado:
        esp = max(2, tc // 3)
        _desenhar_linha_rota(screen, res.caminho, tc, ox, oy, COR_CAMINHO, esp)
    # 5. Elementos fixos (topo)
    _desenhar_elementos_fixos(screen, lab, tc, ox, oy)

    # Label do painel
    surf = font.render(label, True, COR_TEXTO)
    screen.blit(surf, (ox + 4, oy + 4))


def _renderizar_painel_rotas(
    screen, estado: EstadoGUI, tc: int, ox: int, oy: int
) -> None:
    lab = estado.lab
    r_b = estado.res_bfs
    r_a = estado.res_astar

    # 1. Terreno base
    _desenhar_base(screen, lab, tc, ox, oy)
    # 2. Risco
    _desenhar_risco_overlay(screen, lab, estado.campo_risco, estado.lambda_risco, tc, ox, oy)
    # 3. Rota BFS (ciano) — primeiro, por baixo
    if r_b.encontrado:
        esp = max(2, tc // 3)
        _desenhar_linha_rota(screen, r_b.caminho, tc, ox, oy, COR_CAMINHO_BFS, esp + 1)
    # 4. Rota A* (amarelo) — por cima do BFS
    if r_a.encontrado:
        esp = max(2, tc // 3)
        _desenhar_linha_rota(screen, r_a.caminho, tc, ox, oy, COR_CAMINHO, esp)
    # 5. Elementos fixos (topo)
    _desenhar_elementos_fixos(screen, lab, tc, ox, oy)


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
    LARGURA, ALTURA = 1280, 720
    screen = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Pac-Man: UCS vs A*")
    clock = pygame.time.Clock()
    font    = pygame.font.SysFont("monospace", 15)
    font_sm = pygame.font.SysFont("monospace", 13)

    estado = EstadoGUI(lab_inicial, lambda_risco=lambda_risco)
    mapas_lista = mapas_extras or []
    indice_mapa = 0
    screenshot_n = 0

    FPS_ANIM = 15
    t_ultimo = 0.0

    rodando = True
    while rodando:
        agora = time.time()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                rodando = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    estado.rodando = not estado.rodando
                elif ev.key == pygame.K_RIGHT:
                    estado.proximo_passo()
                elif ev.key == pygame.K_r:
                    estado.reiniciar()
                elif ev.key == pygame.K_TAB:
                    estado.alternar_modo()
                elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    estado.trocar_lambda(1.0)
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    estado.trocar_lambda(-1.0)
                elif ev.key == pygame.K_n and mapas_lista:
                    indice_mapa = (indice_mapa + 1) % len(mapas_lista)
                    estado.carregar_mapa(mapas_lista[indice_mapa])
                elif ev.key == pygame.K_g:
                    estado.gerar_aleatorio(21)
                elif ev.key == pygame.K_s:
                    os.makedirs("resultados", exist_ok=True)
                    nome = f"resultados/screenshot_{screenshot_n:03d}.png"
                    pygame.image.save(screen, nome)
                    screenshot_n += 1
                    print(f"Screenshot: {nome}")

        if estado.rodando and (agora - t_ultimo) > (1.0 / FPS_ANIM):
            estado.proximo_passo()
            t_ultimo = agora

        screen.fill(COR_FUNDO_UI)
        lab = estado.lab
        altura_util = ALTURA - ALTURA_RODAPE

        if estado.modo == EstadoGUI.MODO_EXPLORACAO:
            larg_painel = LARGURA // 2 - 2
            tc = _tamanho_celula(lab.linhas, lab.colunas, larg_painel, altura_util)

            for idx, (res, nome_algo) in enumerate([
                (estado.res_ucs,   "UCS"),
                (estado.res_astar, "A*"),
            ]):
                ox = idx * (larg_painel + 4)
                passo_algo = min(estado.passo, len(res.ordem_expansao))
                _renderizar_painel_exploracao(
                    screen, estado, res, tc, ox, 0,
                    f"{nome_algo} — exp={passo_algo}/{res.nos_expandidos}",
                    font,
                )

            _rodape_exploracao(screen, font, font_sm, estado, LARGURA, ALTURA)

        else:  # MODO_ROTAS
            tc = _tamanho_celula(lab.linhas, lab.colunas, LARGURA, altura_util)
            _renderizar_painel_rotas(screen, estado, tc, 0, 0)
            _rodape_rotas(screen, font, font_sm, estado, LARGURA, ALTURA)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
