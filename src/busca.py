"""Algoritmos de busca: BFS, UCS, A*, Gulosa e A* ponderado.

Todos retornam ResultadoBusca. A implementacao generica busca_melhor_primeiro
garante comparacao justa (mesmas estruturas, mesma ordem de vizinhos,
mesmo criterio de expansao).

Regras obrigatorias:
- Teste de objetivo na EXPANSAO (remocao da fila), nunca na geracao.
- Remocao preguicosa: estados obsoletos sao ignorados ao desempilhar.
- Nos expandidos conta apenas expansoes validas (sem obsoletos).
"""

from __future__ import annotations
import heapq
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ResultadoBusca:
    algoritmo: str
    encontrado: bool
    caminho: list[tuple[int, int]]
    custo_total: float
    passos: int                          # len(caminho) - 1
    nos_expandidos: int
    nos_gerados: int
    fronteira_maxima: int
    tempo_ms: float
    exposicao_risco: float
    dist_min_fantasma: int | None
    ordem_expansao: list[tuple[int, int]]
    fronteira_por_passo: list[set] | None = None


def _reconstruir_caminho(
    pai: dict[tuple[int, int], tuple[int, int] | None],
    objetivo: tuple[int, int],
) -> list[tuple[int, int]]:
    caminho = []
    atual = objetivo
    while atual is not None:
        caminho.append(atual)
        atual = pai[atual]
    caminho.reverse()
    return caminho


def busca_melhor_primeiro(
    lab,
    funcao_prioridade: Callable[[tuple[int, int], float], tuple],
    nome: str = "busca",
    registrar_ordem: bool = True,
) -> ResultadoBusca:
    """Busca melhor-primeiro generica.

    funcao_prioridade(pos, g) -> (prioridade_principal, desempate)
    Para UCS: (g, 0)
    Para A*:  (g + h, h)   — em empate de f, expande quem esta mais perto do objetivo
    Para Gulosa: (h, 0)
    """
    inicio = lab.inicio
    objetivo = lab.objetivo

    # (prioridade, desempate, contador, pos)
    contador = 0
    heap = [(0.0, 0.0, contador, inicio)]
    heapq.heapify(heap)

    pai: dict[tuple[int, int], tuple[int, int] | None] = {inicio: None}
    melhor_g: dict[tuple[int, int], float] = {inicio: 0.0}
    fechados: set[tuple[int, int]] = set()

    nos_expandidos = 0
    nos_gerados = 1
    fronteira_atual = {inicio}
    fronteira_maxima = 1
    ordem_expansao: list[tuple[int, int]] = []

    t0 = time.perf_counter()

    while heap:
        fronteira_maxima = max(fronteira_maxima, len(fronteira_atual))
        prio, desempate, _, pos = heapq.heappop(heap)

        if pos in fechados:
            continue  # remocao preguicosa
        fronteira_atual.discard(pos)
        fechados.add(pos)
        nos_expandidos += 1

        if registrar_ordem:
            ordem_expansao.append(pos)

        # Teste de objetivo na expansao
        if pos == objetivo:
            caminho = _reconstruir_caminho(pai, objetivo)
            tempo_ms = (time.perf_counter() - t0) * 1000.0

            from src.metricas import exposicao_risco as calc_exp, distancia_minima_fantasma
            exp = calc_exp(caminho, lab)
            dist_fan = distancia_minima_fantasma(caminho, lab)

            return ResultadoBusca(
                algoritmo=nome,
                encontrado=True,
                caminho=caminho,
                custo_total=melhor_g[objetivo],
                passos=len(caminho) - 1,
                nos_expandidos=nos_expandidos,
                nos_gerados=nos_gerados,
                fronteira_maxima=fronteira_maxima,
                tempo_ms=tempo_ms,
                exposicao_risco=exp,
                dist_min_fantasma=dist_fan,
                ordem_expansao=ordem_expansao,
            )

        g_atual = melhor_g[pos]

        for viz in lab.vizinhos(pos):
            novo_g = g_atual + lab.custo(viz)
            if novo_g < melhor_g.get(viz, float("inf")):
                melhor_g[viz] = novo_g
                pai[viz] = pos
                prio_nova, desempate_novo = funcao_prioridade(viz, novo_g)
                contador += 1
                heapq.heappush(heap, (prio_nova, desempate_novo, contador, viz))
                fronteira_atual.add(viz)
                nos_gerados += 1

    tempo_ms = (time.perf_counter() - t0) * 1000.0
    return ResultadoBusca(
        algoritmo=nome,
        encontrado=False,
        caminho=[],
        custo_total=float("inf"),
        passos=0,
        nos_expandidos=nos_expandidos,
        nos_gerados=nos_gerados,
        fronteira_maxima=fronteira_maxima,
        tempo_ms=tempo_ms,
        exposicao_risco=0.0,
        dist_min_fantasma=None,
        ordem_expansao=ordem_expansao,
    )


# ---------------------------------------------------------------------------
# Funcoes publicas
# ---------------------------------------------------------------------------

def busca_custo_uniforme(lab, registrar_ordem: bool = True) -> ResultadoBusca:
    """UCS: f(n) = g(n). Baseline otimo sem heuristica."""
    def prioridade(pos, g):
        return (g, 0.0)
    return busca_melhor_primeiro(lab, prioridade, nome="UCS", registrar_ordem=registrar_ordem)


def a_estrela(
    lab,
    heuristica=None,
    registrar_ordem: bool = True,
) -> ResultadoBusca:
    """A*: f(n) = g(n) + h(n). Usa manhattan por padrao."""
    from src.heuristicas import manhattan
    if heuristica is None:
        heuristica = manhattan

    objetivo = lab.objetivo

    def prioridade(pos, g):
        h = heuristica(pos, objetivo, lab)
        return (g + h, h)  # desempate: menor h expande primeiro

    nome = f"A*({getattr(heuristica, '__name__', 'h')})"
    return busca_melhor_primeiro(lab, prioridade, nome=nome, registrar_ordem=registrar_ordem)


def busca_gulosa(lab, heuristica=None, registrar_ordem: bool = True) -> ResultadoBusca:
    """Gulosa: f(n) = h(n). Rapida, mas nao garante otimalidade."""
    from src.heuristicas import manhattan
    if heuristica is None:
        heuristica = manhattan

    objetivo = lab.objetivo

    def prioridade(pos, g):
        h = heuristica(pos, objetivo, lab)
        return (h, 0.0)

    return busca_melhor_primeiro(lab, prioridade, nome="Gulosa", registrar_ordem=registrar_ordem)


def a_estrela_ponderado(lab, w: float = 2.0, registrar_ordem: bool = True) -> ResultadoBusca:
    """A* ponderado: f(n) = g(n) + w*h(n). Para w > 1, heuristica nao e admissivel."""
    from src.heuristicas import ponderada
    h = ponderada(w)
    objetivo = lab.objetivo

    def prioridade(pos, g):
        hv = h(pos, objetivo, lab)
        return (g + hv, hv)

    return busca_melhor_primeiro(lab, prioridade, nome=f"A*_pond_{w}", registrar_ordem=registrar_ordem)


def bfs(lab, registrar_ordem: bool = True) -> ResultadoBusca:
    """BFS: ignora custos, encontra o caminho de menor numero de passos."""
    inicio = lab.inicio
    objetivo = lab.objetivo

    fila: deque[tuple[int, int]] = deque([inicio])
    pai: dict[tuple[int, int], tuple[int, int] | None] = {inicio: None}
    visitados: set[tuple[int, int]] = {inicio}

    nos_expandidos = 0
    nos_gerados = 1
    fronteira_maxima = 1
    ordem_expansao: list[tuple[int, int]] = []

    t0 = time.perf_counter()

    while fila:
        fronteira_maxima = max(fronteira_maxima, len(fila))
        pos = fila.popleft()
        nos_expandidos += 1
        if registrar_ordem:
            ordem_expansao.append(pos)

        if pos == objetivo:
            caminho = _reconstruir_caminho(pai, objetivo)
            tempo_ms = (time.perf_counter() - t0) * 1000.0
            # Custo do caminho BFS (recalculado para comparacao)
            custo = sum(lab.custo(p) for p in caminho[1:])

            from src.metricas import exposicao_risco as calc_exp, distancia_minima_fantasma
            exp = calc_exp(caminho, lab)
            dist_fan = distancia_minima_fantasma(caminho, lab)

            return ResultadoBusca(
                algoritmo="BFS",
                encontrado=True,
                caminho=caminho,
                custo_total=custo,
                passos=len(caminho) - 1,
                nos_expandidos=nos_expandidos,
                nos_gerados=nos_gerados,
                fronteira_maxima=fronteira_maxima,
                tempo_ms=tempo_ms,
                exposicao_risco=exp,
                dist_min_fantasma=dist_fan,
                ordem_expansao=ordem_expansao,
            )

        for viz in lab.vizinhos(pos):
            if viz not in visitados:
                visitados.add(viz)
                pai[viz] = pos
                fila.append(viz)
                nos_gerados += 1

    tempo_ms = (time.perf_counter() - t0) * 1000.0
    return ResultadoBusca(
        algoritmo="BFS",
        encontrado=False,
        caminho=[],
        custo_total=float("inf"),
        passos=0,
        nos_expandidos=nos_expandidos,
        nos_gerados=nos_gerados,
        fronteira_maxima=fronteira_maxima,
        tempo_ms=tempo_ms,
        exposicao_risco=0.0,
        dist_min_fantasma=None,
        ordem_expansao=ordem_expansao,
    )
