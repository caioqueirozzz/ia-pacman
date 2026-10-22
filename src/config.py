"""Configuracoes centralizadas do projeto — custos, raio, lambda e cores."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PaletaNeon:
    """Paleta arcade neon — unica fonte de verdade para cores da GUI pygame."""
    # Fundos
    fundo:        tuple = (10,  10,  20)   # #0A0A14
    fundo_grid:   tuple = (16,  16,  30)   # #10101E

    # Paredes
    parede_fill:  tuple = (13,  18,  64)   # #0D1240
    parede_borda: tuple = (46,  75, 255)   # #2E4BFF neon blue

    # Corredor
    corredor:     tuple = (10,  10,  20)   # #0A0A14
    pellet:       tuple = (245, 215, 161)  # #F5D7A1

    # Exploracao
    fechado:      tuple = (31,  184, 154)  # #1FB89A (alpha ~70 aplicado em codigo)
    fronteira:    tuple = (79,  227, 255)  # #4FE3FF

    # Rotas
    rota_astar:   tuple = (255, 212,   0)  # #FFD400 amarelo
    rota_bfs:     tuple = (255,  79, 216)  # #FF4FD8 magenta

    # Risco
    risco:        tuple = (255,  59,  59)  # #FF3B3B (alpha 0-140)

    # Terrenos
    lento:        tuple = (107,  74,  43)  # #6B4A2B
    risco_fixo:   tuple = (255, 138,  31)  # #FF8A1F

    # Texto
    texto:        tuple = (232, 232, 240)  # #E8E8F0
    texto_sec:    tuple = (138, 138, 163)  # #8A8AA3

    # Elementos fixos
    inicio:       tuple = (255, 212,   0)  # amarelo
    objetivo:     tuple = (80,  220,  60)  # verde
    fantasma:     tuple = (220,  60, 220)  # magenta


NEON = PaletaNeon()


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
