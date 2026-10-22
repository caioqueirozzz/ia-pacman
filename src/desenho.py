"""Visualizacao estatica com matplotlib (modo --sem-gui ou para experimentos)."""

from __future__ import annotations
import os


def _cor_celula(lab, l: int, c: int, campo_risco, lambda_risco: float):
    """Retorna cor RGB (0-1) para matplotlib."""
    from src.config import CFG
    s = lab.grade[l][c]
    if s == CFG.simbolo_parede:
        return (0.08, 0.08, 0.47)
    if s == CFG.simbolo_fantasma:
        return (0.86, 0.2, 0.86)
    if s == CFG.simbolo_inicio:
        return (1.0, 1.0, 0.0)
    if s == CFG.simbolo_objetivo:
        return (0.0, 0.9, 0.0)

    risco = campo_risco[l][c]
    r_norm = min(1.0, risco * lambda_risco / 50.0) if lambda_risco > 0 else 0.0

    if s == CFG.simbolo_lento:
        base = (0.4, 0.26, 0.13)
    elif s == CFG.simbolo_risco_fixo:
        base = (0.78, 0.39, 0.0)
    else:
        base = (0.0, 0.0, 0.0)

    # Sobreposicao vermelha proporcional ao risco
    return (
        base[0] + r_norm * (0.9 - base[0]),
        base[1] * (1 - r_norm),
        base[2] * (1 - r_norm),
    )


def desenhar_comparacao(
    lab,
    resultado_bfs=None,
    resultado_otimo=None,
    lambda_risco: float = 5.0,
    titulo: str = "Pac-Man: comparacao de rotas",
    caminho_saida: str | None = None,
):
    """Desenha o labirinto com as rotas BFS e otima sobrepostas."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from src.risco import calcular_risco

    campo_risco = calcular_risco(lab.grade, lab.linhas, lab.colunas)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_aspect("equal")
    ax.set_xlim(0, lab.colunas)
    ax.set_ylim(0, lab.linhas)
    ax.invert_yaxis()
    ax.set_title(titulo, fontsize=13)
    ax.axis("off")

    # Grid de celulas
    for l in range(lab.linhas):
        for c in range(lab.colunas):
            cor = _cor_celula(lab, l, c, campo_risco, lambda_risco)
            rect = plt.Rectangle((c, l), 1, 1, color=cor)
            ax.add_patch(rect)

    def _desenhar_caminho(caminho, cor, lw, label, alpha=0.85):
        if not caminho or len(caminho) < 2:
            return
        xs = [c + 0.5 for _, c in caminho]
        ys = [l + 0.5 for l, _ in caminho]
        ax.plot(xs, ys, color=cor, linewidth=lw, alpha=alpha, label=label, zorder=5)

    if resultado_bfs and resultado_bfs.encontrado:
        _desenhar_caminho(resultado_bfs.caminho, "cyan", 2.5,
                          f"BFS ({resultado_bfs.passos} passos, custo={resultado_bfs.custo_total:.1f})")
    if resultado_otimo and resultado_otimo.encontrado:
        _desenhar_caminho(resultado_otimo.caminho, "yellow", 2.0,
                          f"{resultado_otimo.algoritmo} ({resultado_otimo.passos} passos, custo={resultado_otimo.custo_total:.1f})")

    ax.legend(loc="upper right", fontsize=9, framealpha=0.7)

    if caminho_saida:
        os.makedirs(os.path.dirname(caminho_saida) or ".", exist_ok=True)
        fig.savefig(caminho_saida, dpi=120, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.tight_layout()
        plt.show()
        plt.close(fig)


def desenhar_expansao(
    lab,
    resultado_ucs,
    resultado_astar,
    lambda_risco: float = 5.0,
    caminho_saida: str | None = None,
):
    """Dois paineis lado a lado mostrando a ordem de expansao de UCS e A*."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from src.risco import calcular_risco

    campo_risco = calcular_risco(lab.grade, lab.linhas, lab.colunas)

    fig, axes = plt.subplots(1, 2, figsize=(20, 8))

    for ax, resultado, nome in [
        (axes[0], resultado_ucs, "UCS"),
        (axes[1], resultado_astar, "A*"),
    ]:
        ax.set_aspect("equal")
        ax.set_xlim(0, lab.colunas)
        ax.set_ylim(0, lab.linhas)
        ax.invert_yaxis()
        ax.set_title(
            f"{nome} — {resultado.nos_expandidos} expandidos, "
            f"custo={resultado.custo_total:.1f}",
            fontsize=11,
        )
        ax.axis("off")

        for l in range(lab.linhas):
            for c in range(lab.colunas):
                cor = _cor_celula(lab, l, c, campo_risco, lambda_risco)
                rect = plt.Rectangle((c, l), 1, 1, color=cor)
                ax.add_patch(rect)

        # Mostra ordem de expansao como gradiente de cor
        if resultado.ordem_expansao:
            n = len(resultado.ordem_expansao)
            for i, (l, c) in enumerate(resultado.ordem_expansao):
                if (l, c) in {lab.inicio, lab.objetivo}:
                    continue
                frac = i / max(n - 1, 1)
                cor_exp = (0.1 + 0.5 * frac, 0.1, 0.7 - 0.5 * frac, 0.5)
                rect = plt.Rectangle((c + 0.05, l + 0.05), 0.9, 0.9, color=cor_exp)
                ax.add_patch(rect)

        # Caminho final
        if resultado.encontrado and len(resultado.caminho) > 1:
            xs = [c + 0.5 for _, c in resultado.caminho]
            ys = [l + 0.5 for l, _ in resultado.caminho]
            ax.plot(xs, ys, "yellow", linewidth=2.5, zorder=6)

    plt.suptitle(f"Modo Exploracao — lambda={lambda_risco}", fontsize=13)
    plt.tight_layout()

    if caminho_saida:
        os.makedirs(os.path.dirname(caminho_saida) or ".", exist_ok=True)
        fig.savefig(caminho_saida, dpi=120, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()
        plt.close(fig)
