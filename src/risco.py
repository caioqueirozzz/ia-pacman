"""Campo de risco dos fantasmas e calculo dos custos finais das celulas."""

from __future__ import annotations
from collections import deque
from src.config import CFG, custo_base


def calcular_risco(
    grade: list[list[str]],
    linhas: int,
    colunas: int,
    raio: int | None = None,
) -> list[list[float]]:
    """Calcula o campo de risco de cada celula usando BFS a partir dos fantasmas.

    O risco respeita paredes (nao atravessa obstaculos).
    risco(c) = sum_fantasmas max(0, raio + 1 - d_bfs(c, fantasma))

    Retorna grade[linhas][colunas] com o valor de risco (float).
    """
    if raio is None:
        raio = CFG.raio_fantasma

    risco = [[0.0] * colunas for _ in range(linhas)]

    # Encontra fantasmas
    fantasmas = []
    for l in range(linhas):
        for c in range(colunas):
            if grade[l][c] == CFG.simbolo_fantasma:
                fantasmas.append((l, c))

    if not fantasmas:
        return risco

    direcoes = [(-1, 0), (0, 1), (1, 0), (0, -1)]

    for (fl, fc) in fantasmas:
        # BFS a partir do fantasma pelos corredores
        dist: dict[tuple[int, int], int] = {}
        fila: deque[tuple[tuple[int, int], int]] = deque()
        fila.append(((fl, fc), 0))
        dist[(fl, fc)] = 0

        while fila:
            (l, c), d = fila.popleft()
            if d >= raio:
                continue
            for dl, dc in direcoes:
                nl, nc = l + dl, c + dc
                if not (0 <= nl < linhas and 0 <= nc < colunas):
                    continue
                if grade[nl][nc] == CFG.simbolo_parede:
                    continue
                if (nl, nc) in dist:
                    continue
                dist[(nl, nc)] = d + 1
                fila.append(((nl, nc), d + 1))

        for (l, c), d in dist.items():
            if grade[l][c] == CFG.simbolo_fantasma:
                continue  # celula do fantasma e intransitavel
            contribuicao = max(0, raio + 1 - d)
            risco[l][c] += contribuicao

    return risco


def calcular_custos(
    lab,  # Labirinto (importacao tardia evita ciclo)
    lambda_risco: float | None = None,
    raio: int | None = None,
) -> list[list[float]]:
    """Calcula custo_base + lambda * risco para cada celula transitavel.

    Celulas intransiitaveis recebem float('inf').
    """
    if lambda_risco is None:
        lambda_risco = CFG.lambda_risco
    if raio is None:
        raio = CFG.raio_fantasma

    campo_risco = calcular_risco(lab.grade, lab.linhas, lab.colunas, raio)
    custos = [[float("inf")] * lab.colunas for _ in range(lab.linhas)]

    for l in range(lab.linhas):
        for c in range(lab.colunas):
            cb = custo_base(lab.grade[l][c])
            if cb is None:
                continue  # intransitavel
            custos[l][c] = cb + lambda_risco * campo_risco[l][c]

    return custos


def obter_risco_puro(lab) -> list[list[float]]:
    """Retorna o campo de risco sem lambda (para calcular exposicao_risco)."""
    return calcular_risco(lab.grade, lab.linhas, lab.colunas, CFG.raio_fantasma)
