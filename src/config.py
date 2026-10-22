"""Configuracoes centralizadas do projeto — custos, raio, lambda e cores."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    # Custos base por tipo de celula
    custo_corredor: float = 1.0
    custo_lento: float = 3.0
    custo_risco_fixo: float = 8.0

    # Parametros do campo de risco dos fantasmas
    raio_fantasma: int = 4
    lambda_risco: float = 5.0  # peso do risco no custo final

    # Simbolos do mapa
    simbolo_parede: str = "#"
    simbolo_corredor: str = "."
    simbolo_espaco: str = " "
    simbolo_lento: str = "~"
    simbolo_risco_fixo: str = "!"
    simbolo_fantasma: str = "F"
    simbolo_inicio: str = "P"
    simbolo_objetivo: str = "O"

    # Cores pygame (R, G, B)
    cor_parede: tuple = (20, 20, 120)
    cor_corredor: tuple = (0, 0, 0)
    cor_lento: tuple = (101, 67, 33)
    cor_risco_fixo: tuple = (200, 100, 0)
    cor_fantasma: tuple = (220, 50, 220)
    cor_inicio: tuple = (255, 255, 0)
    cor_objetivo: tuple = (0, 230, 0)
    cor_caminho: tuple = (255, 255, 0)
    cor_fronteira: tuple = (0, 150, 255)
    cor_fechado: tuple = (80, 80, 80)
    cor_risco_overlay: tuple = (255, 0, 0)  # alfa aplicado por codigo

    # Dimensoes da janela (pygame)
    largura_janela: int = 1280
    altura_janela: int = 720


# Instancia global — importar desta constante
CFG = Config()


def custo_base(simbolo: str) -> float | None:
    """Custo base de entrar numa celula pelo simbolo.

    Retorna None para celulas intransiitaveis (parede, fantasma).
    """
    if simbolo in (CFG.simbolo_parede, CFG.simbolo_fantasma):
        return None
    tabela = {
        CFG.simbolo_corredor: CFG.custo_corredor,
        CFG.simbolo_espaco:   CFG.custo_corredor,
        CFG.simbolo_inicio:   CFG.custo_corredor,
        CFG.simbolo_objetivo: CFG.custo_corredor,
        CFG.simbolo_lento:    CFG.custo_lento,
        CFG.simbolo_risco_fixo: CFG.custo_risco_fixo,
    }
    return tabela.get(simbolo, CFG.custo_corredor)
