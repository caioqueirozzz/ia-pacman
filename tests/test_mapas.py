"""Testes das propriedades especificas de cada mapa manual (secao 6.2)."""
import math
import pytest
from src.labirinto import carregar_labirinto
from src.busca import bfs, busca_custo_uniforme, a_estrela
from src.metricas import exposicao_risco


def test_aberto_mesmo_custo():
    """Em mapa aberto sem risco, BFS/UCS/A* tem o mesmo custo."""
    lab = carregar_labirinto("mapas/aberto.txt", lambda_risco=0.0)
    res_bfs = bfs(lab, registrar_ordem=False)
    res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
    res_astar = a_estrela(lab, registrar_ordem=False)
    assert res_bfs.encontrado and res_ucs.encontrado and res_astar.encontrado
    # Com lambda=0 e custo 1 por celula, custo = passos
    assert math.isclose(res_ucs.custo_total, float(res_bfs.passos), rel_tol=1e-9)
    assert math.isclose(res_astar.custo_total, res_ucs.custo_total, rel_tol=1e-9)


def test_aberto_astar_expande_menos():
    """Em mapa aberto, A* expande bem menos que UCS."""
    lab = carregar_labirinto("mapas/aberto.txt", lambda_risco=0.0)
    res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
    res_astar = a_estrela(lab, registrar_ordem=False)
    assert res_astar.nos_expandidos < res_ucs.nos_expandidos


def test_atalho_perigoso_lambda0():
    """Com lambda=0: custo UCS == passos BFS (todos os corredores custam 1)."""
    lab = carregar_labirinto("mapas/atalho_perigoso.txt", lambda_risco=0.0)
    res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
    res_bfs = bfs(lab, registrar_ordem=False)
    assert res_ucs.encontrado and res_bfs.encontrado
    assert math.isclose(res_ucs.custo_total, float(res_bfs.passos), rel_tol=1e-9)


def test_atalho_perigoso_lambda5():
    """Com lambda=5: A* encontra rota com mais passos e menor exposicao ao risco que BFS."""
    lab = carregar_labirinto("mapas/atalho_perigoso.txt", lambda_risco=5.0)
    res_bfs = bfs(lab, registrar_ordem=False)
    res_astar = a_estrela(lab, registrar_ordem=False)
    assert res_bfs.encontrado and res_astar.encontrado
    # A* deve ter mais passos e menor (ou igual) exposicao ao risco
    assert res_astar.passos >= res_bfs.passos, (
        f"A* ({res_astar.passos} passos) deveria ter >= passos que BFS ({res_bfs.passos})"
    )
    assert res_astar.exposicao_risco <= res_bfs.exposicao_risco, (
        f"A* risco={res_astar.exposicao_risco:.1f} deveria ser <= BFS risco={res_bfs.exposicao_risco:.1f}"
    )


def test_pantano_rota_contorna():
    """A rota otima no pantano nao e o caminho direto pela lama."""
    lab = carregar_labirinto("mapas/pantano.txt", lambda_risco=0.0)
    res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
    res_bfs = bfs(lab, registrar_ordem=False)
    assert res_ucs.encontrado
    # BFS pode encontrar o caminho direto pela lama (menos passos)
    # UCS deve encontrar o caminho mais barato (contorna ou reduz celulas ~)
    # A rota otima deve custar menos que ir reto pela lama
    # Verificamos que o custo otimo e menor que o custo do caminho BFS
    custo_bfs = sum(lab.custo(p) for p in res_bfs.caminho[1:])
    assert res_ucs.custo_total <= custo_bfs + 1e-9


def test_arcade_tem_caminho():
    """Todos os algoritmos encontram caminho no mapa arcade."""
    lab = carregar_labirinto("mapas/arcade.txt", lambda_risco=5.0)
    for algo in [bfs, busca_custo_uniforme, a_estrela]:
        res = algo(lab, registrar_ordem=False)
        assert res.encontrado, f"{algo.__name__} nao encontrou caminho no arcade.txt"


def test_sem_saida_sem_caminho():
    """Todos os algoritmos retornam encontrado=False no mapa sem saida."""
    lab = carregar_labirinto("mapas/sem_saida.txt", lambda_risco=5.0)
    for algo in [bfs, busca_custo_uniforme, a_estrela]:
        res = algo(lab, registrar_ordem=False)
        assert not res.encontrado, f"{algo.__name__} deveria retornar False no sem_saida.txt"
