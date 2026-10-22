"""Testes de carregamento e validacao do labirinto."""
import pytest
from src.labirinto import carregar_labirinto, labirinto_para_str
from src.config import CFG


def test_carrega_aberto():
    lab = carregar_labirinto("mapas/aberto.txt", lambda_risco=0.0)
    assert lab.inicio is not None
    assert lab.objetivo is not None
    assert lab.linhas > 0 and lab.colunas > 0


def test_carrega_sem_saida():
    lab = carregar_labirinto("mapas/sem_saida.txt", lambda_risco=0.0)
    assert lab.inicio is not None
    assert lab.objetivo is not None


def test_simbolos_validos():
    lab = carregar_labirinto("mapas/atalho_perigoso.txt", lambda_risco=0.0)
    for l in range(lab.linhas):
        for c in range(lab.colunas):
            assert lab.grade[l][c] in {
                CFG.simbolo_parede, CFG.simbolo_corredor, CFG.simbolo_espaco,
                CFG.simbolo_lento, CFG.simbolo_risco_fixo,
                CFG.simbolo_fantasma, CFG.simbolo_inicio, CFG.simbolo_objetivo,
            }


def test_exatamente_um_inicio_objetivo():
    lab = carregar_labirinto("mapas/aberto.txt", lambda_risco=0.0)
    contagem_p = sum(
        1 for l in range(lab.linhas) for c in range(lab.colunas)
        if lab.grade[l][c] == CFG.simbolo_inicio
    )
    contagem_o = sum(
        1 for l in range(lab.linhas) for c in range(lab.colunas)
        if lab.grade[l][c] == CFG.simbolo_objetivo
    )
    assert contagem_p == 1
    assert contagem_o == 1


def test_custo_minimo_um():
    """Toda celula transitavel deve ter custo >= 1 (invariante da admissibilidade)."""
    for mapa in ["mapas/aberto.txt", "mapas/atalho_perigoso.txt", "mapas/pantano.txt"]:
        lab = carregar_labirinto(mapa, lambda_risco=5.0)
        for l in range(lab.linhas):
            for c in range(lab.colunas):
                if lab.eh_valida(l, c):
                    assert lab.custo((l, c)) >= 1.0, (
                        f"{mapa} ({l},{c}) custo={lab.custo((l,c)):.3f}"
                    )


def test_vizinhos_sem_paredes():
    lab = carregar_labirinto("mapas/aberto.txt", lambda_risco=0.0)
    for pos in lab.posicoes_transitaveis():
        for viz in lab.vizinhos(pos):
            assert lab.eh_valida(viz[0], viz[1])


def test_arquivo_inexistente():
    with pytest.raises(FileNotFoundError):
        carregar_labirinto("mapas/nao_existe.txt")


def test_representacao_ascii():
    lab = carregar_labirinto("mapas/aberto.txt", lambda_risco=0.0)
    s = labirinto_para_str(lab, caminho=[lab.inicio, lab.objetivo])
    assert "P" in s
    assert "O" in s


def test_parede_intransitavel():
    lab = carregar_labirinto("mapas/aberto.txt", lambda_risco=0.0)
    # A borda eh parede — nao deve ser valida
    assert not lab.eh_valida(0, 0)
