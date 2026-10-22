"""Testes do campo de risco dos fantasmas."""
import pytest
from src.risco import calcular_risco
from src.labirinto import carregar_labirinto
from src.config import CFG


def _grade_simples(conteudo: list[str]) -> tuple:
    """Constroi grade, linhas, colunas a partir de lista de strings."""
    linhas = len(conteudo)
    colunas = max(len(l) for l in conteudo)
    grade = [list(l.ljust(colunas)) for l in conteudo]
    return grade, linhas, colunas


def test_sem_fantasmas_risco_zero():
    grade, l, c = _grade_simples(["###", "#.#", "###"])
    risco = calcular_risco(grade, l, c)
    for li in range(l):
        for ci in range(c):
            assert risco[li][ci] == 0.0


def test_fantasma_cria_risco():
    grade, l, c = _grade_simples([
        "#######",
        "#.....#",
        "#..F..#",
        "#.....#",
        "#######",
    ])
    risco = calcular_risco(grade, l, c, raio=4)
    # F esta em (2,3); celulas adjacentes (distancia 1) tem risco = raio = 4
    assert risco[2][2] == pytest.approx(4.0)  # esquerda do F
    assert risco[2][4] == pytest.approx(4.0)  # direita do F
    assert risco[1][3] == pytest.approx(4.0)  # acima do F
    assert risco[3][3] == pytest.approx(4.0)  # abaixo do F


def test_parede_bloqueia_risco():
    """Risco nao deve atravessar paredes."""
    grade, l, c = _grade_simples([
        "#######",
        "#.#.F.#",
        "#.#...#",
        "#######",
    ])
    risco = calcular_risco(grade, l, c, raio=4)
    # (1,1) esta separado de F por uma parede na coluna 2 — nao deve ter risco por F
    # A BFS nao atravessa paredes, entao (1,1) so recebe risco se F estiver acessivel por corridores
    # Caminho F(1,4)->down nao existe (parede em baixo nao, mas a esquerda sim via (1,5)->(1,4) ok)
    # Caminho de F ate (1,1): F(1,4) -> precisaria passar pela parede (1,2) = impossivel
    assert risco[1][1] == 0.0


def test_risco_decai_com_distancia():
    grade, l, c = _grade_simples([
        "#########",
        "#.......#",
        "#...F...#",
        "#.......#",
        "#########",
    ])
    risco = calcular_risco(grade, l, c, raio=4)
    # Distancias a partir de F(2,4): (2,3)=1, (2,2)=2, (2,1)=3
    assert risco[2][3] > risco[2][2] > risco[2][1]


def test_risco_borda_raio_zero():
    """Celulas exatamente no raio de distancia tem risco = 1; alem do raio, risco = 0."""
    grade, l, c = _grade_simples([
        "###########",
        "#.........#",
        "#....F....#",
        "#.........#",
        "###########",
    ])
    risco = calcular_risco(grade, l, c, raio=4)
    # Distancia 4 de F(2,5): (2,1) = dist 4 -> risco = max(0, 4+1-4) = 1
    assert risco[2][1] == pytest.approx(1.0)
    # Distancia 5: (2,0) = parede, mas se houvesse corredor teria risco=0
    # Verificar que parede nao tem risco (irrelevante pois intransitavel)


def test_custo_com_lambda():
    lab = carregar_labirinto("mapas/atalho_perigoso.txt", lambda_risco=5.0)
    # A celula junto ao fantasma deve ter custo > custo_base
    fl, fc = lab.posicoes_fantasmas()[0]
    # Vizinho do fantasma (se existir e for corredor)
    for dl, dc in [(-1, 0), (0, -1), (0, 1), (1, 0)]:
        nl, nc = fl + dl, fc + dc
        if lab.eh_valida(nl, nc):
            assert lab.custo((nl, nc)) > 1.0
            break
