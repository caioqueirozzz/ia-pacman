"""Testes de admissibilidade e consistencia das heuristicas."""
import math
import heapq
import pytest
from src.labirinto import carregar_labirinto
from src.heuristicas import manhattan, euclidiana, zero, ponderada
from src.config import CFG


def dijkstra_reverso(lab) -> dict[tuple[int, int], float]:
    """Calcula h*(n) para todas as celulas via Dijkstra a partir do objetivo."""
    objetivo = lab.objetivo
    dist = {objetivo: 0.0}
    heap = [(0.0, objetivo)]
    while heap:
        d, pos = heapq.heappop(heap)
        if d > dist.get(pos, float("inf")):
            continue
        for viz in lab.vizinhos(pos):
            nd = d + lab.custo(pos)  # custo de entrar em pos (reversao: custo de sair de viz para pos)
            if nd < dist.get(viz, float("inf")):
                dist[viz] = nd
                heapq.heappush(heap, (nd, viz))
    return dist


def _verificar_admissibilidade(lab, heuristica):
    h_star = dijkstra_reverso(lab)
    objetivo = lab.objetivo
    for pos in lab.posicoes_transitaveis():
        h = heuristica(pos, objetivo, lab)
        h_opt = h_star.get(pos, float("inf"))
        assert h <= h_opt + 1e-9, (
            f"Admissibilidade violada em {pos}: h={h:.3f} > h*={h_opt:.3f}"
        )


def _verificar_consistencia(lab, heuristica):
    objetivo = lab.objetivo
    for pos in lab.posicoes_transitaveis():
        h_pos = heuristica(pos, objetivo, lab)
        for viz in lab.vizinhos(pos):
            h_viz = heuristica(viz, objetivo, lab)
            custo_aresta = lab.custo(viz)
            assert h_pos <= custo_aresta + h_viz + 1e-9, (
                f"Consistencia violada: {pos}->{viz}: h={h_pos:.3f}, "
                f"c={custo_aresta:.3f}, h_viz={h_viz:.3f}"
            )


MAPAS = ["mapas/aberto.txt", "mapas/atalho_perigoso.txt", "mapas/pantano.txt"]


@pytest.mark.parametrize("mapa", MAPAS)
def test_manhattan_admissivel(mapa):
    lab = carregar_labirinto(mapa, lambda_risco=5.0)
    _verificar_admissibilidade(lab, manhattan)


@pytest.mark.parametrize("mapa", MAPAS)
def test_manhattan_consistente(mapa):
    lab = carregar_labirinto(mapa, lambda_risco=5.0)
    _verificar_consistencia(lab, manhattan)


@pytest.mark.parametrize("mapa", MAPAS)
def test_euclidiana_admissivel(mapa):
    lab = carregar_labirinto(mapa, lambda_risco=5.0)
    _verificar_admissibilidade(lab, euclidiana)


@pytest.mark.parametrize("mapa", MAPAS)
def test_zero_admissivel(mapa):
    lab = carregar_labirinto(mapa, lambda_risco=5.0)
    _verificar_admissibilidade(lab, zero)


def test_manhattan_gerador():
    """Admissibilidade em mapas aleatorios com seeds variadas."""
    from src.gerador import gerar_labirinto
    for seed in range(10):
        lab = gerar_labirinto(21, 21, seed=seed, lambda_risco=5.0)
        _verificar_admissibilidade(lab, manhattan)
        _verificar_consistencia(lab, manhattan)


def test_euclidiana_le_manhattan():
    """Euclidiana e sempre <= Manhattan (menos informada)."""
    lab = carregar_labirinto("mapas/aberto.txt", lambda_risco=0.0)
    objetivo = lab.objetivo
    for pos in lab.posicoes_transitaveis():
        h_m = manhattan(pos, objetivo, lab)
        h_e = euclidiana(pos, objetivo, lab)
        assert h_e <= h_m + 1e-9
