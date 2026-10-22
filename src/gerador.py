"""Gerador de labirintos aleatorios com seed deterministica.

Algoritmo:
1. Backtracker DFS iterativo em grid de dimensoes impares -> labirinto perfeito.
2. Remove fracao das paredes internas para criar ciclos.
3. Coloca P e O em cantos opostos, fantasmas em posicoes aleatorias.
4. Opcionalmente adiciona manchas de ~ e !.
5. Garante caminho P -> O via BFS; regera se nao houver.
"""

from __future__ import annotations
import random
from collections import deque
from src.config import CFG


def _tem_caminho(grade: list[list[str]], linhas: int, colunas: int,
                  inicio: tuple[int, int], objetivo: tuple[int, int]) -> bool:
    """BFS simples para checar conectividade."""
    visitados = {inicio}
    fila = deque([inicio])
    while fila:
        l, c = fila.popleft()
        if (l, c) == objetivo:
            return True
        for dl, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            nl, nc = l + dl, c + dc
            if 0 <= nl < linhas and 0 <= nc < colunas:
                if (nl, nc) not in visitados:
                    s = grade[nl][nc]
                    if s not in (CFG.simbolo_parede, CFG.simbolo_fantasma):
                        visitados.add((nl, nc))
                        fila.append((nl, nc))
    return False


def gerar_labirinto(
    linhas: int = 21,
    colunas: int = 21,
    seed: int = 42,
    num_fantasmas: int = 2,
    fracao_remocao: float = 0.15,
    fracao_lento: float = 0.05,
    fracao_risco_fixo: float = 0.03,
    lambda_risco: float | None = None,
    raio: int | None = None,
) -> object:  # retorna Labirinto
    """Gera e retorna um Labirinto aleatorio com seed deterministica."""
    from src.labirinto import Labirinto
    from src.risco import calcular_custos

    if lambda_risco is None:
        lambda_risco = CFG.lambda_risco
    if raio is None:
        raio = CFG.raio_fantasma

    # Dimensoes impares para o backtracker funcionar
    if linhas % 2 == 0:
        linhas += 1
    if colunas % 2 == 0:
        colunas += 1

    rng = random.Random(seed)

    def _gerar_grade():
        # Inicializa tudo com paredes
        grade = [[CFG.simbolo_parede] * colunas for _ in range(linhas)]

        # Celulas visitaveis: indices impares
        visitados: set[tuple[int, int]] = set()
        li_ini, ci_ini = 1, 1
        visitados.add((li_ini, ci_ini))
        grade[li_ini][ci_ini] = CFG.simbolo_corredor
        pilha = [(li_ini, ci_ini)]

        while pilha:
            l, c = pilha[-1]
            vizinhos_disponiveis = []
            for dl, dc in [(-2, 0), (0, 2), (2, 0), (0, -2)]:
                nl, nc = l + dl, c + dc
                if 1 <= nl < linhas - 1 and 1 <= nc < colunas - 1:
                    if (nl, nc) not in visitados:
                        vizinhos_disponiveis.append((nl, nc, l + dl // 2, c + dc // 2))
            if vizinhos_disponiveis:
                nl, nc, ml, mc = rng.choice(vizinhos_disponiveis)
                grade[ml][mc] = CFG.simbolo_corredor
                grade[nl][nc] = CFG.simbolo_corredor
                visitados.add((nl, nc))
                pilha.append((nl, nc))
            else:
                pilha.pop()

        # Remove fracao das paredes internas para criar ciclos
        paredes_internas = [
            (l, c)
            for l in range(1, linhas - 1)
            for c in range(1, colunas - 1)
            if grade[l][c] == CFG.simbolo_parede
        ]
        n_remover = int(len(paredes_internas) * fracao_remocao)
        remover = rng.sample(paredes_internas, min(n_remover, len(paredes_internas)))
        for l, c in remover:
            grade[l][c] = CFG.simbolo_corredor

        return grade

    # P e O em cantos opostos (primeiro corredor disponivel em cada canto)
    def _encontrar_canto_livre(grade, preferencias):
        for l, c in preferencias:
            if grade[l][c] != CFG.simbolo_parede:
                return l, c
        # fallback: primeiro corredor
        for l in range(linhas):
            for c in range(colunas):
                if grade[l][c] == CFG.simbolo_corredor:
                    return l, c
        return 1, 1

    for tentativa in range(20):
        grade = _gerar_grade()

        inicio = _encontrar_canto_livre(grade, [(1, 1), (1, 3), (3, 1)])
        objetivo = _encontrar_canto_livre(
            grade,
            [(linhas - 2, colunas - 2), (linhas - 2, colunas - 4), (linhas - 4, colunas - 2)],
        )
        if inicio == objetivo:
            objetivo = (linhas - 2, colunas - 2)

        if not _tem_caminho(grade, linhas, colunas, inicio, objetivo):
            continue

        grade[inicio[0]][inicio[1]] = CFG.simbolo_inicio
        grade[objetivo[0]][objetivo[1]] = CFG.simbolo_objetivo

        # Posicoes livres (corredores) para fantasmas, ~, !
        livres = [
            (l, c)
            for l in range(linhas)
            for c in range(colunas)
            if grade[l][c] == CFG.simbolo_corredor
        ]
        rng.shuffle(livres)

        # Fantasmas
        fantasmas_colocados = 0
        pos_livres_restantes = []
        for pos in livres:
            if fantasmas_colocados < num_fantasmas:
                grade[pos[0]][pos[1]] = CFG.simbolo_fantasma
                fantasmas_colocados += 1
            else:
                pos_livres_restantes.append(pos)

        # Zonas lentas ~
        n_lento = int(len(pos_livres_restantes) * fracao_lento)
        for pos in pos_livres_restantes[:n_lento]:
            grade[pos[0]][pos[1]] = CFG.simbolo_lento

        # Zonas de risco fixo !
        n_risco = int(len(pos_livres_restantes) * fracao_risco_fixo)
        for pos in pos_livres_restantes[n_lento:n_lento + n_risco]:
            grade[pos[0]][pos[1]] = CFG.simbolo_risco_fixo

        lab = Labirinto(
            grade=grade,
            linhas=linhas,
            colunas=colunas,
            inicio=inicio,
            objetivo=objetivo,
        )
        lab.custo_celula = calcular_custos(lab, lambda_risco, raio)

        # Valida invariante custo >= 1
        valido = True
        for l in range(linhas):
            for c in range(colunas):
                if lab.eh_valida(l, c) and lab.custo_celula[l][c] < 1.0:
                    valido = False
                    break

        if valido:
            return lab

    raise RuntimeError(
        f"Nao foi possivel gerar labirinto {linhas}x{colunas} seed={seed} "
        "com caminho valido apos 20 tentativas."
    )
