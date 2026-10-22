"""Carga, validacao e consulta do labirinto."""

from __future__ import annotations
from dataclasses import dataclass, field
from src.config import CFG, custo_base


@dataclass
class Labirinto:
    grade: list[list[str]]             # grade[linha][coluna]
    linhas: int
    colunas: int
    inicio: tuple[int, int]            # (linha, coluna) de P
    objetivo: tuple[int, int]          # (linha, coluna) de O
    # custo_celula[l][c] = custo base + lambda * risco (preenchido por risco.py)
    custo_celula: list[list[float]] = field(default_factory=list)

    # Ordem fixa de vizinhos: cima, direita, baixo, esquerda
    _DIRECOES: tuple[tuple[int, int], ...] = field(
        default=((-1, 0), (0, 1), (1, 0), (0, -1)), init=False, repr=False
    )

    def eh_valida(self, linha: int, coluna: int) -> bool:
        """Verifica se a posicao esta dentro dos limites e e transitavel."""
        if not (0 <= linha < self.linhas and 0 <= coluna < self.colunas):
            return False
        s = self.grade[linha][coluna]
        return s not in (CFG.simbolo_parede, CFG.simbolo_fantasma)

    def vizinhos(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        """Retorna vizinhos validos em ordem fixa (cima, direita, baixo, esquerda)."""
        l, c = pos
        resultado = []
        for dl, dc in self._DIRECOES:
            nl, nc = l + dl, c + dc
            if self.eh_valida(nl, nc):
                resultado.append((nl, nc))
        return resultado

    def custo(self, pos: tuple[int, int]) -> float:
        """Custo de entrar na celula pos (ja inclui risco * lambda)."""
        l, c = pos
        if self.custo_celula:
            return self.custo_celula[l][c]
        cb = custo_base(self.grade[l][c])
        return cb if cb is not None else float("inf")

    def simbolo(self, pos: tuple[int, int]) -> str:
        return self.grade[pos[0]][pos[1]]

    def posicoes_transitaveis(self) -> list[tuple[int, int]]:
        """Retorna todas as posicoes transitaveis do labirinto."""
        resultado = []
        for l in range(self.linhas):
            for c in range(self.colunas):
                if self.eh_valida(l, c):
                    resultado.append((l, c))
        return resultado

    def posicoes_fantasmas(self) -> list[tuple[int, int]]:
        """Retorna as posicoes de todos os fantasmas."""
        resultado = []
        for l in range(self.linhas):
            for c in range(self.colunas):
                if self.grade[l][c] == CFG.simbolo_fantasma:
                    resultado.append((l, c))
        return resultado


def carregar_labirinto(caminho: str, lambda_risco: float | None = None) -> Labirinto:
    """Le um arquivo .txt e retorna um Labirinto validado.

    lambda_risco sobrescreve CFG.lambda_risco se fornecido.
    O campo de risco e preenchido aqui via risco.py.
    """
    from src.risco import calcular_custos

    if lambda_risco is None:
        lambda_risco = CFG.lambda_risco

    try:
        with open(caminho, encoding="utf-8") as f:
            linhas_texto = f.read().splitlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo nao encontrado: {caminho}")

    # Remove linhas completamente vazias no inicio/fim
    while linhas_texto and not linhas_texto[0].strip():
        linhas_texto.pop(0)
    while linhas_texto and not linhas_texto[-1].strip():
        linhas_texto.pop()

    if not linhas_texto:
        raise ValueError(f"{caminho}: arquivo vazio.")

    # Normaliza para o mesmo numero de colunas (preenche com espaco)
    num_cols = max(len(l) for l in linhas_texto)
    grade = [list(l.ljust(num_cols)) for l in linhas_texto]

    num_linhas = len(grade)
    simbolos_validos = {
        CFG.simbolo_parede, CFG.simbolo_corredor, CFG.simbolo_espaco,
        CFG.simbolo_lento, CFG.simbolo_risco_fixo,
        CFG.simbolo_fantasma, CFG.simbolo_inicio, CFG.simbolo_objetivo,
    }

    inicio = None
    objetivo = None

    for li, linha in enumerate(grade):
        for ci, s in enumerate(linha):
            if s not in simbolos_validos:
                raise ValueError(
                    f"{caminho} linha {li+1} coluna {ci+1}: simbolo desconhecido '{s}'."
                )
            if s == CFG.simbolo_inicio:
                if inicio is not None:
                    raise ValueError(f"{caminho}: mais de um 'P' encontrado.")
                inicio = (li, ci)
            if s == CFG.simbolo_objetivo:
                if objetivo is not None:
                    raise ValueError(f"{caminho}: mais de um 'O' encontrado.")
                objetivo = (li, ci)

    if inicio is None:
        raise ValueError(f"{caminho}: 'P' (inicio) nao encontrado.")
    if objetivo is None:
        raise ValueError(f"{caminho}: 'O' (objetivo) nao encontrado.")

    lab = Labirinto(
        grade=grade,
        linhas=num_linhas,
        colunas=num_cols,
        inicio=inicio,
        objetivo=objetivo,
    )

    lab.custo_celula = calcular_custos(lab, lambda_risco)

    # Valida invariante: custo >= 1 para todas as celulas transitaveis
    for l in range(num_linhas):
        for c in range(num_cols):
            if lab.eh_valida(l, c):
                custo = lab.custo_celula[l][c]
                if custo < 1.0:
                    raise ValueError(
                        f"{caminho} ({l},{c}): custo={custo:.3f} < 1. "
                        "A heuristica admissivel depende de custo_min >= 1."
                    )

    return lab


def labirinto_para_str(lab: Labirinto, caminho: list[tuple[int, int]] | None = None) -> str:
    """Retorna representacao ASCII do labirinto, marcando o caminho com '*'."""
    nos_caminho = set(caminho) if caminho else set()
    linhas = []
    for li in range(lab.linhas):
        linha = []
        for ci in range(lab.colunas):
            pos = (li, ci)
            s = lab.grade[li][ci]
            if pos in nos_caminho and s not in (CFG.simbolo_inicio, CFG.simbolo_objetivo):
                linha.append("*")
            else:
                linha.append(s)
        linhas.append("".join(linha))
    return "\n".join(linhas)
