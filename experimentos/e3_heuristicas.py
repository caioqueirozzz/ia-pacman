"""E3 (opcional) — Qualidade da heuristica: comparacao de heuristicas.

Execucao:
    python -m experimentos.e3_heuristicas
"""
import csv
import math
import os

MAPA = "mapas/arcade.txt"
LAMBDA_RISCO = 5.0


def rodar_e3():
    from src.labirinto import carregar_labirinto
    from src.busca import busca_custo_uniforme, a_estrela, busca_gulosa
    from src.heuristicas import zero, euclidiana, manhattan, ponderada

    os.makedirs("resultados", exist_ok=True)
    lab = carregar_labirinto(MAPA, lambda_risco=LAMBDA_RISCO)

    heuristicas = [
        ("h=0 (UCS)", zero),
        ("Euclidiana", euclidiana),
        ("Manhattan", manhattan),
        ("Manhattan x2", ponderada(2.0)),
        ("Manhattan x5", ponderada(5.0)),
        ("Gulosa", None),  # caso especial
    ]

    res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
    custo_otimo = res_ucs.custo_total

    print(f"{'Heuristica':<18} {'Admissivel':>10} {'Expandidos':>11} "
          f"{'Custo':>10} {'Otimo?':>7}")
    print("-" * 60)

    linhas_csv = []
    for nome, h in heuristicas:
        if h is None:
            res = busca_gulosa(lab, registrar_ordem=False)
        elif nome.startswith("h=0"):
            res = a_estrela(lab, heuristica=h, registrar_ordem=False)
        else:
            res = a_estrela(lab, heuristica=h, registrar_ordem=False)

        admissivel = "sim" if nome not in ("Manhattan x2", "Manhattan x5", "Gulosa") else "nao"
        otimo = "sim" if (res.encontrado and math.isclose(
            res.custo_total, custo_otimo, rel_tol=1e-3)) else "nao"

        print(
            f"{nome:<18} {admissivel:>10} {res.nos_expandidos:>11} "
            f"{res.custo_total:>10.2f} {otimo:>7}"
        )
        linhas_csv.append({
            "heuristica": nome,
            "admissivel": admissivel,
            "nos_expandidos": res.nos_expandidos,
            "custo": round(res.custo_total, 4),
            "otimo": otimo,
        })

    with open("resultados/e3_heuristicas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas_csv[0].keys()))
        w.writeheader()
        w.writerows(linhas_csv)
    print("\nResultados salvos em resultados/e3_heuristicas.csv")

    _gerar_grafico(linhas_csv, custo_otimo)


def _gerar_grafico(dados, custo_otimo):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    nomes = [r["heuristica"] for r in dados]
    expandidos = [r["nos_expandidos"] for r in dados]
    custos = [r["custo"] for r in dados]
    cores = ["green" if r["otimo"] == "sim" else "red" for r in dados]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    barras = ax1.barh(nomes, expandidos, color=cores, alpha=0.8)
    ax1.set_xlabel("Nos expandidos")
    ax1.set_title("E3: Nos expandidos por heuristica\n(verde=otimo, vermelho=sub-otimo)")
    ax1.axvline(expandidos[0], color="gray", linestyle="--", linewidth=1, label="h=0 (UCS)")

    barras2 = ax2.barh(nomes, custos, color=cores, alpha=0.8)
    ax2.axvline(custo_otimo, color="blue", linestyle="--", linewidth=2, label=f"Custo otimo={custo_otimo:.1f}")
    ax2.set_xlabel("Custo encontrado")
    ax2.set_title("E3: Custo da solucao por heuristica")
    ax2.legend()

    plt.tight_layout()
    plt.savefig("resultados/e3_grafico.png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("Grafico salvo em resultados/e3_grafico.png")


if __name__ == "__main__":
    rodar_e3()
