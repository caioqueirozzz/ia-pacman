"""Heuristicas para busca informada.

Todas as funcoes tem assinatura:
    h(pos, objetivo, lab) -> float

onde pos e objetivo sao (linha, coluna) e lab e um Labirinto.
"""

from __future__ import annotations
import math
from src.config import CFG


_cache_custo_minimo: dict[int, float] = {}


def _custo_minimo(lab) -> float:
    """Menor custo de celula transitavel no labirinto (normalmente 1.0).

    Usa cache por id(lab) para evitar re-scan a cada chamada de h(n).
    """
    chave = id(lab)
    if chave in _cache_custo_minimo:
        return _cache_custo_minimo[chave]
    c_min = float("inf")
    for l in range(lab.linhas):
        for c in range(lab.colunas):
            if lab.eh_valida(l, c):
                custo = lab.custo_celula[l][c] if lab.custo_celula else 1.0
                c_min = min(c_min, custo)
    resultado = max(1.0, c_min)
    _cache_custo_minimo[chave] = resultado
    return resultado


def manhattan(pos: tuple[int, int], objetivo: tuple[int, int], lab) -> float:
    """h(n) = c_min * distancia_manhattan.

    Admissivel e consistente: qualquer caminho em 4-vizinhanca precisa de
    pelo menos Manhattan passos, cada um custando pelo menos c_min.
    Ignorar o risco e intencional — subestimar e permitido.
    """
    c_min = _custo_minimo(lab)
    return c_min * (abs(pos[0] - objetivo[0]) + abs(pos[1] - objetivo[1]))


def euclidiana(pos: tuple[int, int], objetivo: tuple[int, int], lab) -> float:
    """h(n) = c_min * distancia_euclidiana.

    Admissivel (sempre <= Manhattan em 4-vizinhanca), porem menos informada.
    """
    c_min = _custo_minimo(lab)
    dl = pos[0] - objetivo[0]
    dc = pos[1] - objetivo[1]
    return c_min * math.sqrt(dl * dl + dc * dc)


def zero(pos: tuple[int, int], objetivo: tuple[int, int], lab) -> float:
    """h(n) = 0. Reduz A* a UCS — usado para checar sanidade."""
    return 0.0


def ponderada(w: float):
    """Fabrica: retorna h(n) = w * manhattan. Para w > 1, nao e admissivel."""
    def _h(pos: tuple[int, int], objetivo: tuple[int, int], lab) -> float:
        c_min = _custo_minimo(lab)
        return w * c_min * (abs(pos[0] - objetivo[0]) + abs(pos[1] - objetivo[1]))
    _h.__name__ = f"ponderada_{w}"
    return _h
