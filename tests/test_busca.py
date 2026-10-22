"""Testes dos algoritmos de busca."""
import math
import pytest
from src.labirinto import carregar_labirinto
from src.busca import bfs, busca_custo_uniforme, a_estrela, busca_gulosa
from src.heuristicas import zero, manhattan
from src.config import CFG


def _caminho_valido(resultado, lab):
    """Verifica que o caminho e valido (vizinhos adjacentes, sem paredes)."""
    if not resultado.encontrado:
        return
    cam = resultado.caminho
    assert cam[0] == lab.inicio
    assert cam[-1] == lab.objetivo
    assert resultado.passos == len(cam) - 1
    for i in range(len(cam) - 1):
        l1, c1 = cam[i]
        l2, c2 = cam[i + 1]
        assert abs(l1 - l2) + abs(c1 - c2) == 1, f"Passo nao adjacente: {cam[i]}->{cam[i+1]}"
        assert lab.eh_valida(l2, c2), f"Celula invalida no caminho: {cam[i+1]}"


def _custo_real(resultado, lab):
    """Recalcula o custo do caminho e compara com o reportado."""
    if not resultado.encontrado:
        return
    custo = sum(lab.custo(p) for p in resultado.caminho[1:])
    assert math.isclose(custo, resultado.custo_total, rel_tol=1e-9), (
        f"Custo reportado {resultado.custo_total:.4f} != recalculado {custo:.4f}"
    )


MAPAS_COMUNS = [
    "mapas/aberto.txt",
    "mapas/atalho_perigoso.txt",
    "mapas/pantano.txt",
    "mapas/arcade.txt",
]


@pytest.mark.parametrize("mapa", MAPAS_COMUNS)
def test_caminho_valido_ucs(mapa):
    lab = carregar_labirinto(mapa, lambda_risco=5.0)
    res = busca_custo_uniforme(lab, registrar_ordem=False)
    _caminho_valido(res, lab)
    _custo_real(res, lab)


@pytest.mark.parametrize("mapa", MAPAS_COMUNS)
def test_caminho_valido_astar(mapa):
    lab = carregar_labirinto(mapa, lambda_risco=5.0)
    res = a_estrela(lab, registrar_ordem=False)
    _caminho_valido(res, lab)
    _custo_real(res, lab)


@pytest.mark.parametrize("mapa", MAPAS_COMUNS)
def test_caminho_valido_bfs(mapa):
    lab = carregar_labirinto(mapa, lambda_risco=5.0)
    res = bfs(lab, registrar_ordem=False)
    _caminho_valido(res, lab)


@pytest.mark.parametrize("mapa", MAPAS_COMUNS)
def test_otimalidade_ucs_astar(mapa):
    """UCS e A* devem encontrar o mesmo custo otimo."""
    lab = carregar_labirinto(mapa, lambda_risco=5.0)
    res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
    res_astar = a_estrela(lab, registrar_ordem=False)
    assert res_ucs.encontrado == res_astar.encontrado
    if res_ucs.encontrado:
        assert math.isclose(res_ucs.custo_total, res_astar.custo_total, rel_tol=1e-9), (
            f"{mapa}: UCS={res_ucs.custo_total:.4f} != A*={res_astar.custo_total:.4f}"
        )


def test_astar_zero_igual_ucs():
    """A* com h=0 deve ter o mesmo custo e expansoes que UCS."""
    lab = carregar_labirinto("mapas/aberto.txt", lambda_risco=5.0)
    res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
    res_az = a_estrela(lab, heuristica=zero, registrar_ordem=False)
    assert math.isclose(res_ucs.custo_total, res_az.custo_total, rel_tol=1e-9)
    assert res_ucs.nos_expandidos == res_az.nos_expandidos


def test_custo_uniforme_igual_passos_bfs():
    """Em mapa sem riscos e lambda=0, custo da UCS == passos do BFS."""
    lab = carregar_labirinto("mapas/aberto.txt", lambda_risco=0.0)
    res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
    res_bfs = bfs(lab, registrar_ordem=False)
    assert res_ucs.encontrado and res_bfs.encontrado
    assert math.isclose(res_ucs.custo_total, float(res_bfs.passos), rel_tol=1e-9), (
        f"UCS custo={res_ucs.custo_total} != BFS passos={res_bfs.passos}"
    )


def test_eficiencia_astar_menor_que_ucs():
    """A* deve expandir <= nos que UCS em mapas manuais."""
    for mapa in MAPAS_COMUNS:
        lab = carregar_labirinto(mapa, lambda_risco=5.0)
        res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
        res_astar = a_estrela(lab, registrar_ordem=False)
        if res_ucs.encontrado:
            assert res_astar.nos_expandidos <= res_ucs.nos_expandidos, (
                f"{mapa}: A*={res_astar.nos_expandidos} > UCS={res_ucs.nos_expandidos}"
            )


def test_sem_saida():
    """Todos os algoritmos devem retornar encontrado=False para objetivo inacessivel."""
    lab = carregar_labirinto("mapas/sem_saida.txt", lambda_risco=5.0)
    for algo in [bfs, busca_custo_uniforme, a_estrela, busca_gulosa]:
        res = algo(lab, registrar_ordem=False)
        assert not res.encontrado, f"{algo.__name__} deveria retornar encontrado=False"


def test_otimalidade_mapas_aleatorios():
    """UCS == A* em 50 mapas aleatorios."""
    from src.gerador import gerar_labirinto
    for seed in range(50):
        lab = gerar_labirinto(21, 21, seed=seed, lambda_risco=3.0)
        res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
        res_astar = a_estrela(lab, registrar_ordem=False)
        assert res_ucs.encontrado == res_astar.encontrado, f"seed={seed}"
        if res_ucs.encontrado:
            assert math.isclose(res_ucs.custo_total, res_astar.custo_total, rel_tol=1e-9), (
                f"seed={seed}: UCS={res_ucs.custo_total:.4f} != A*={res_astar.custo_total:.4f}"
            )


def test_determinismo():
    """Mesma seed -> mesmo resultado."""
    from src.gerador import gerar_labirinto
    lab1 = gerar_labirinto(21, 21, seed=7, lambda_risco=5.0)
    lab2 = gerar_labirinto(21, 21, seed=7, lambda_risco=5.0)
    res1 = busca_custo_uniforme(lab1, registrar_ordem=False)
    res2 = busca_custo_uniforme(lab2, registrar_ordem=False)
    assert res1.caminho == res2.caminho
    assert math.isclose(res1.custo_total, res2.custo_total)
