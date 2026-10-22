"""E1 — Eficiencia: UCS vs A* em labirintos aleatorios de varios tamanhos.

Execucao:
    python -m experimentos.e1_eficiencia
"""
import csv
import math
import os
import time

TAMANHOS = [21, 41, 81, 161]
NUM_SEEDS = 20
NUM_REPETICOES = 3  # media de N execucoes para tempo
LAMBDA_RISCO = 5.0
RAIO = 4
FANTASMAS_POR_TAMANHO = {21: 2, 41: 4, 81: 8, 161: 16}


def rodar_e1():
    from src.gerador import gerar_labirinto
    from src.busca import busca_custo_uniforme, a_estrela

    os.makedirs("resultados", exist_ok=True)
    linhas_csv = []

    print(f"{'Tam':>5} {'Seed':>4} {'UCS_exp':>9} {'A*_exp':>9} "
          f"{'Reduc%':>7} {'UCS_ms':>8} {'A*_ms':>8} {'OK':>3}")
    print("-" * 65)

    for tamanho in TAMANHOS:
        for seed in range(NUM_SEEDS):
            lab = gerar_labirinto(
                tamanho, tamanho,
                seed=seed,
                num_fantasmas=FANTASMAS_POR_TAMANHO[tamanho],
                lambda_risco=LAMBDA_RISCO,
                raio=RAIO,
            )

            # Multiplas execucoes para medir tempo (sem registrar_ordem para nao distorcer)
            tempos_ucs, tempos_astar = [], []
            for _ in range(NUM_REPETICOES):
                t0 = time.perf_counter()
                res_ucs = busca_custo_uniforme(lab, registrar_ordem=False)
                tempos_ucs.append((time.perf_counter() - t0) * 1000)

                t0 = time.perf_counter()
                res_astar = a_estrela(lab, registrar_ordem=False)
                tempos_astar.append((time.perf_counter() - t0) * 1000)

            ok = (
                res_ucs.encontrado == res_astar.encontrado
                and (not res_ucs.encontrado or
                     math.isclose(res_ucs.custo_total, res_astar.custo_total, rel_tol=1e-9))
            )
            if not ok:
                raise AssertionError(
                    f"Otimalidade violada: tamanho={tamanho} seed={seed} "
                    f"UCS={res_ucs.custo_total:.4f} A*={res_astar.custo_total:.4f}"
                )

            reducao = (
                (res_ucs.nos_expandidos - res_astar.nos_expandidos) / res_ucs.nos_expandidos * 100
                if res_ucs.nos_expandidos > 0 else 0.0
            )
            ms_ucs = sum(tempos_ucs) / len(tempos_ucs)
            ms_astar = sum(tempos_astar) / len(tempos_astar)

            print(
                f"{tamanho:>5} {seed:>4} {res_ucs.nos_expandidos:>9} "
                f"{res_astar.nos_expandidos:>9} {reducao:>7.1f}% "
                f"{ms_ucs:>8.2f} {ms_astar:>8.2f} {'OK' if ok else 'FAIL':>3}"
            )

            linhas_csv.append({
                "tamanho": tamanho, "seed": seed,
                "ucs_expandidos": res_ucs.nos_expandidos,
                "astar_expandidos": res_astar.nos_expandidos,
                "reducao_pct": round(reducao, 2),
                "ucs_gerados": res_ucs.nos_gerados,
                "astar_gerados": res_astar.nos_gerados,
                "ucs_fronteira_max": res_ucs.fronteira_maxima,
                "astar_fronteira_max": res_astar.fronteira_maxima,
                "ucs_ms": round(ms_ucs, 3),
                "astar_ms": round(ms_astar, 3),
                "custo_otimo": round(res_ucs.custo_total, 4),
                "encontrado": res_ucs.encontrado,
            })

    # Salva CSV
    campos = list(linhas_csv[0].keys())
    with open("resultados/e1_eficiencia.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas_csv)
    print("\nResultados salvos em resultados/e1_eficiencia.csv")

    _gerar_grafico(linhas_csv)


def _gerar_grafico(dados):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import collections

    # Agrupa por tamanho
    por_tamanho: dict = collections.defaultdict(lambda: {"ucs": [], "astar": [], "red": []})
    for row in dados:
        t = row["tamanho"]
        por_tamanho[t]["ucs"].append(row["ucs_expandidos"])
        por_tamanho[t]["astar"].append(row["astar_expandidos"])
        por_tamanho[t]["red"].append(row["reducao_pct"])

    tamanhos = sorted(por_tamanho)
    med_ucs = [sum(por_tamanho[t]["ucs"]) / len(por_tamanho[t]["ucs"]) for t in tamanhos]
    med_astar = [sum(por_tamanho[t]["astar"]) / len(por_tamanho[t]["astar"]) for t in tamanhos]
    med_red = [sum(por_tamanho[t]["red"]) / len(por_tamanho[t]["red"]) for t in tamanhos]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    labels = [str(t) for t in tamanhos]
    x = range(len(tamanhos))
    w = 0.35

    ax1.bar([i - w/2 for i in x], med_ucs, w, label="UCS", color="steelblue")
    ax1.bar([i + w/2 for i in x], med_astar, w, label="A*", color="darkorange")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels)
    ax1.set_xlabel("Tamanho do labirinto")
    ax1.set_ylabel("Nos expandidos (media)")
    ax1.set_title("E1: Nos expandidos — UCS vs A*")
    ax1.legend()

    ax2.plot(labels, med_red, "o-", color="green", linewidth=2)
    ax2.set_xlabel("Tamanho do labirinto")
    ax2.set_ylabel("Reducao percentual (%)")
    ax2.set_title("E1: Reducao de nos expandidos pelo A*")
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("resultados/e1_grafico.png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("Grafico salvo em resultados/e1_grafico.png")


if __name__ == "__main__":
    rodar_e1()
