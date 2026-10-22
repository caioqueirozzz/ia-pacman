"""Metricas de caminho: exposicao ao risco e distancia minima a fantasma."""

from __future__ import annotations
from collections import deque
from src.risco import calcular_risco
from src.config import CFG


def exposicao_risco(caminho: list[tuple[int, int]], lab) -> float:
    """Soma do risco puro (sem lambda) das celulas do caminho, excluindo a origem."""
    if len(caminho) <= 1:
        return 0.0
    campo = calcular_risco(lab.grade, lab.linhas, lab.colunas)
    return sum(campo[l][c] for (l, c) in caminho[1:])


def distancia_minima_fantasma(caminho: list[tuple[int, int]], lab) -> int | None:
    """Menor distancia BFS de qualquer celula do caminho a qualquer fantasma.

    Retorna None se nao houver fantasmas no labirinto.
    """
    fantasmas = lab.posicoes_fantasmas()
    if not fantasmas or not caminho:
        return None

    nos_caminho = set(caminho)
    direcoes = [(-1, 0), (0, 1), (1, 0), (0, -1)]

    # BFS multi-fonte a partir dos fantasmas
    dist: dict[tuple[int, int], int] = {}
    fila: deque = deque()
    for pos in fantasmas:
        dist[pos] = 0
        fila.append((pos, 0))

    while fila:
        (l, c), d = fila.popleft()
        for dl, dc in direcoes:
            nl, nc = l + dl, c + dc
            if not (0 <= nl < lab.linhas and 0 <= nc < lab.colunas):
                continue
            if lab.grade[nl][nc] == CFG.simbolo_parede:
                continue
            if (nl, nc) in dist:
                continue
            dist[(nl, nc)] = d + 1
            fila.append(((nl, nc), d + 1))

    distancias = [dist.get(pos, float("inf")) for pos in nos_caminho]
    melhor = min(distancias)
    return int(melhor) if melhor != float("inf") else None
