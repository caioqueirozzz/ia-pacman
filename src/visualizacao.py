"""Interface grafica pygame com modo Exploracao e modo Rotas.

Controles:
    Espaco       Play/pause da animacao
    ->           Avanca um passo
    R            Reinicia
    Tab          Alterna Exploracao / Rotas
    + / -        Aumenta/diminui lambda (recalcula custos e rotas)
    N            Proximo mapa
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


# Paleta de cores pygame
COR_PAREDE = (20, 20, 120)
COR_CORREDOR = (10, 10, 10)
COR_LENTO = (101, 67, 33)
COR_RISCO_FIXO = (180, 90, 0)
COR_FANTASMA = (220, 50, 220)
COR_INICIO = (255, 220, 0)
COR_OBJETIVO = (0, 220, 0)
COR_FRONTEIRA_UCS = (0, 120, 220)
COR_FRONTEIRA_ASTAR = (0, 200, 150)
COR_FECHADO_UCS = (40, 40, 80)
COR_FECHADO_ASTAR = (20, 60, 50)
COR_CAMINHO = (255, 220, 0)
COR_CAMINHO_BFS = (0, 220, 220)
COR_FUNDO_UI = (20, 20, 30)
COR_TEXTO = (220, 220, 220)


def _tamanho_celula(linhas: int, colunas: int, largura: int, altura: int) -> int:
    """Calcula o tamanho de celula que cabe na janela."""
    return max(4, min(largura // colunas, (altura - 120) // linhas))


def _cor_celula_pygame(lab, l: int, c: int, campo_risco, lambda_risco: float):
    from src.config import CFG
    s = lab.grade[l][c]
    if s == CFG.simbolo_parede:
        return COR_PAREDE
    if s == CFG.simbolo_fantasma:
        return COR_FANTASMA
    if s == CFG.simbolo_inicio:
        return COR_INICIO
    if s == CFG.simbolo_objetivo:
        return COR_OBJETIVO

    risco_val = campo_risco[l][c]
    r_norm = min(1.0, risco_val * lambda_risco / 50.0) if lambda_risco > 0 else 0.0

    if s == CFG.simbolo_lento:
        base = COR_LENTO
    elif s == CFG.simbolo_risco_fixo:
        base = COR_RISCO_FIXO
    else:
        base = COR_CORREDOR

    return (
        int(base[0] + r_norm * (200 - base[0])),
        int(base[1] * (1 - r_norm)),
        int(base[2] * (1 - r_norm)),
    )


class EstadoGUI:
    """Estado mutavel da interface."""

    MODO_EXPLORACAO = 0
    MODO_ROTAS = 1

    def __init__(self, lab, lambda_risco: float = 5.0):
        self.lambda_risco = lambda_risco
        self._recarregar(lab)

    def _recarregar(self, lab):
        from src.risco import calcular_risco, calcular_custos
        from src.busca import bfs, busca_custo_uniforme, a_estrela
        from src.config import CFG

        self.lab = lab
        self.campo_risco = calcular_risco(lab.grade, lab.linhas, lab.colunas)
        # Recalcula custos com lambda atual
        lab.custo_celula = calcular_custos(lab, self.lambda_risco)

        self.res_bfs = bfs(lab)
        self.res_ucs = busca_custo_uniforme(lab)
        self.res_astar = a_estrela(lab)

        self.passo = 0
        self.rodando = False
        self.modo = self.MODO_EXPLORACAO
        self.seed_aleatorio = 42

    def trocar_lambda(self, delta: float):
        self.lambda_risco = max(0.0, self.lambda_risco + delta)
        self._recarregar(self.lab)
        self.passo = 0
        self.rodando = False

    def proximo_passo(self):
        max_passo = max(
            len(self.res_ucs.ordem_expansao),
            len(self.res_astar.ordem_expansao),
        )
        if self.passo < max_passo:
            self.passo += 1

    def reiniciar(self):
        self.passo = 0
        self.rodando = False

    def alternar_modo(self):
        self.modo = 1 - self.modo
        self.reiniciar()

    def carregar_mapa(self, caminho: str):
        from src.labirinto import carregar_labirinto
        lab = carregar_labirinto(caminho, lambda_risco=self.lambda_risco)
        self._recarregar(lab)

    def gerar_aleatorio(self, tamanho: int = 21):
        from src.gerador import gerar_labirinto
        self.seed_aleatorio += 1
        lab = gerar_labirinto(tamanho, tamanho, seed=self.seed_aleatorio,
                               lambda_risco=self.lambda_risco)
        self._recarregar(lab)


def _renderizar_grade(surface, lab, campo_risco, lambda_risco, tc, offset_x, offset_y,
                       fechados_ucs=None, fronteira_ucs=None,
                       fechados_astar=None, fronteira_astar=None,
                       caminho=None, caminho_bfs=None, modo=0):
    """Renderiza o labirinto numa surface pygame."""
    fechados_ucs = fechados_ucs or set()
    fronteira_ucs = fronteira_ucs or set()
    fechados_astar = fechados_astar or set()
    fronteira_astar = fronteira_astar or set()
    nos_caminho = set(caminho) if caminho else set()
    nos_bfs = set(caminho_bfs) if caminho_bfs else set()

    for l in range(lab.linhas):
        for c in range(lab.colunas):
            pos = (l, c)
            cor = _cor_celula_pygame(lab, l, c, campo_risco, lambda_risco)
            rect = pygame.Rect(offset_x + c * tc, offset_y + l * tc, tc - 1, tc - 1)

            if modo == EstadoGUI.MODO_EXPLORACAO:
                if pos in fronteira_ucs:
                    cor = COR_FRONTEIRA_UCS
                elif pos in fechados_ucs:
                    cor = COR_FECHADO_UCS
                elif pos in fronteira_astar:
                    cor = COR_FRONTEIRA_ASTAR
                elif pos in fechados_astar:
                    cor = COR_FECHADO_ASTAR
            else:
                if pos in nos_bfs and lab.grade[l][c] not in "PO":
                    cor = COR_CAMINHO_BFS
                if pos in nos_caminho and lab.grade[l][c] not in "PO":
                    cor = COR_CAMINHO

            pygame.draw.rect(surface, cor, rect)


def _painel_texto(screen, font, estado: EstadoGUI, largura: int, altura: int):
    """Renderiza a barra de informacoes na parte inferior."""
    y = altura - 100
    pygame.draw.rect(screen, COR_FUNDO_UI, (0, y, largura, 100))

    lab = estado.lab
    passo = estado.passo

    if estado.modo == EstadoGUI.MODO_EXPLORACAO:
        exp_ucs = estado.res_ucs.ordem_expansao[:passo]
        exp_astar = estado.res_astar.ordem_expansao[:passo]
        linhas_texto = [
            f"Modo: Exploracao  |  lambda={estado.lambda_risco:.1f}  |  "
            f"Passo {passo}/{max(len(estado.res_ucs.ordem_expansao), len(estado.res_astar.ordem_expansao))}",
            f"UCS:   expandidos={len(exp_ucs)},  custo_final={estado.res_ucs.custo_total:.1f}  |  "
            f"A*:    expandidos={len(exp_astar)},  custo_final={estado.res_astar.custo_total:.1f}",
            "Espaco=play/pause  ->  R=reiniciar  Tab=modo  +/-=lambda  G=aleatorio  S=screenshot",
        ]
    else:
        r_bfs = estado.res_bfs
        r_astar = estado.res_astar
        linhas_texto = [
            f"Modo: Rotas  |  lambda={estado.lambda_risco:.1f}",
            (f"BFS: {r_bfs.passos} passos, custo={r_bfs.custo_total:.1f}, "
             f"risco={r_bfs.exposicao_risco:.1f}  |  "
             f"A*: {r_astar.passos} passos, custo={r_astar.custo_total:.1f}, "
             f"risco={r_astar.exposicao_risco:.1f}"),
            "Espaco=play/pause  Tab=modo  +/-=lambda  G=aleatorio  S=screenshot",
        ]

    for i, linha in enumerate(linhas_texto):
        surf = font.render(linha, True, COR_TEXTO)
        screen.blit(surf, (10, y + 8 + i * 28))


def iniciar_gui(lab_inicial, lambda_risco: float = 5.0, mapas_extras: list[str] | None = None):
    """Inicia a interface pygame."""
    if not _PYGAME_OK:
        raise ImportError("pygame nao instalado. Execute: pip install pygame")

    pygame.init()
    pygame.display.set_caption("Pac-Man: Busca de Custo Uniforme vs A*")

    LARGURA, ALTURA = 1280, 720
    screen = pygame.display.set_mode((LARGURA, ALTURA))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)
    font_pequena = pygame.font.SysFont("monospace", 12)

    estado = EstadoGUI(lab_inicial, lambda_risco=lambda_risco)
    mapas_lista = mapas_extras or []
    indice_mapa = 0

    velocidade_fps = 15  # frames por segundo na animacao
    t_ultimo_passo = 0.0

    screenshot_contador = 0

    rodando = True
    while rodando:
        agora = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rodando = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    estado.rodando = not estado.rodando
                elif event.key == pygame.K_RIGHT:
                    estado.proximo_passo()
                elif event.key == pygame.K_r:
                    estado.reiniciar()
                elif event.key == pygame.K_TAB:
                    estado.alternar_modo()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    estado.trocar_lambda(1.0)
                elif event.key == pygame.K_MINUS:
                    estado.trocar_lambda(-1.0)
                elif event.key == pygame.K_n and mapas_lista:
                    indice_mapa = (indice_mapa + 1) % len(mapas_lista)
                    estado.carregar_mapa(mapas_lista[indice_mapa])
                elif event.key == pygame.K_g:
                    estado.gerar_aleatorio(21)
                elif event.key == pygame.K_s:
                    os.makedirs("resultados", exist_ok=True)
                    nome = f"resultados/screenshot_{screenshot_contador:03d}.png"
                    pygame.image.save(screen, nome)
                    screenshot_contador += 1
                    print(f"Screenshot salvo: {nome}")

        # Avanca animacao automaticamente
        if estado.rodando and (agora - t_ultimo_passo) > (1.0 / velocidade_fps):
            estado.proximo_passo()
            t_ultimo_passo = agora

        # Renderizacao
        screen.fill(COR_FUNDO_UI)
        lab = estado.lab
        tc = _tamanho_celula(lab.linhas, lab.colunas, LARGURA, ALTURA)

        passo = estado.passo

        if estado.modo == EstadoGUI.MODO_EXPLORACAO:
            # Dois paineis lado a lado
            largura_painel = LARGURA // 2 - 5
            for painel_idx, (res, cor_front, cor_fech) in enumerate([
                (estado.res_ucs, COR_FRONTEIRA_UCS, COR_FECHADO_UCS),
                (estado.res_astar, COR_FRONTEIRA_ASTAR, COR_FECHADO_ASTAR),
            ]):
                offset_x = painel_idx * (LARGURA // 2 + 5)
                expans = set(res.ordem_expansao[:passo])
                fronteira = set()  # simplificado: nao rastreamos fronteira por passo aqui

                _renderizar_grade(
                    screen, lab, estado.campo_risco, estado.lambda_risco,
                    tc, offset_x, 0,
                    fechados_ucs=expans if painel_idx == 0 else set(),
                    fechados_astar=expans if painel_idx == 1 else set(),
                    caminho=res.caminho if passo >= len(res.ordem_expansao) else None,
                    modo=EstadoGUI.MODO_EXPLORACAO,
                )

                nome_algo = "UCS" if painel_idx == 0 else "A*"
                label = font.render(
                    f"{nome_algo} — expandidos: {min(passo, res.nos_expandidos)}", True, COR_TEXTO
                )
                screen.blit(label, (offset_x + 5, 5))
        else:
            # Modo Rotas: um painel com BFS (ciano) + A* (amarelo)
            _renderizar_grade(
                screen, lab, estado.campo_risco, estado.lambda_risco,
                tc, 0, 0,
                caminho=estado.res_astar.caminho,
                caminho_bfs=estado.res_bfs.caminho,
                modo=EstadoGUI.MODO_ROTAS,
            )
            # Legenda
            leg_bfs = font.render(f"BFS (ciano): {estado.res_bfs.passos} passos", True, COR_CAMINHO_BFS)
            leg_ast = font.render(f"A* (amarelo): {estado.res_astar.passos} passos", True, COR_CAMINHO)
            screen.blit(leg_bfs, (5, 5))
            screen.blit(leg_ast, (5, 25))

        _painel_texto(screen, font_pequena, estado, LARGURA, ALTURA)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
