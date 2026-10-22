"""E2 — O caminho mais curto e o mais seguro?

Varia lambda e compara BFS (menos passos) vs A* (menor custo).

Execucao:
    python -m experimentos.e2_curto_vs_seguro
"""
import csv
import math
import os

LAMBDAS = [0, 1, 2, 5, 10, 20, 50]
MAPAS = ["mapas/atalho_perigoso.txt", "mapas/arcade.txt"]
RAIO = 4


def rodar_e2():
    from src.labirinto import carregar_labirinto
    from src.busca import bfs, a_estrela

    os.makedirs("resultados", exist_ok=True)
    linhas_csv = []

    for mapa in MAPAS:
        print(f"\n=== {mapa} ===")
        print(
            f"{'lambda':>8} {'BFS_pass':>9} {'BFS_custo':>10} {'BFS_risco':>10} "
            f"{'A*_pass':>8} {'A*_custo':>10} {'A*_risco':>10} {'Mesma?':>7}"
        )
        print("-" * 80)

        for lam in LAMBDAS:
            lab = carregar_labirinto(mapa, lambda_risco=float(lam))
            res_bfs = bfs(lab, registrar_ordem=False)
            res_astar = a_estrela(lab, registrar_ordem=False)

            if not res_bfs.encontrado or not res_astar.encontrado:
                print(f"{lam:>8} sem caminho")
                continue

            mesma_rota = res_bfs.caminho == res_astar.caminho
            print(
                f"{lam:>8.1f} {res_bfs.passos:>9} {res_bfs.custo_total:>10.2f} "
                f"{res_bfs.exposicao_risco:>10.1f} "
                f"{res_astar.passos:>8} {res_astar.custo_total:>10.2f} "
                f"{res_astar.exposicao_risco:>10.1f} {'sim' if mesma_rota else 'nao':>7}"
            )

            linhas_csv.append({
                "mapa": os.path.basename(mapa),
                "lambda": lam,
                "bfs_passos": res_bfs.passos,
                "bfs_custo": round(res_bfs.custo_total, 4),
                "bfs_risco": round(res_bfs.exposicao_risco, 4),
                "bfs_dist_fantasma": res_bfs.dist_min_fantasma,
                "astar_passos": res_astar.passos,
                "astar_custo": round(res_astar.custo_total, 4),
                "astar_risco": round(res_astar.exposicao_risco, 4),
                "astar_dist_fantasma": res_astar.dist_min_fantasma,
                "mesma_rota": mesma_rota,
            })

            # Verificacao de otimalidade
            res_ucs_check = None
            if lam > 0:
                from src.busca import busca_custo_uniforme
                res_ucs_check = busca_custo_uniforme(lab, registrar_ordem=False)
                if res_ucs_check.encontrado and not math.isclose(
                    res_ucs_check.custo_total, res_astar.custo_total, rel_tol=1e-9
                ):
                    raise AssertionError(
                        f"Otimalidade violada: {mapa} lambda={lam} "
                        f"UCS={res_ucs_check.custo_total:.4f} A*={res_astar.custo_total:.4f}"
                    )

    campos = list(linhas_csv[0].keys())
    with open("resultados/e2_curto_vs_seguro.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas_csv)
    print("\nResultados salvos em resultados/e2_curto_vs_seguro.csv")

    _gerar_grafico(linhas_csv)
    _gerar_imagens_rotas()


def _gerar_grafico(dados):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mapas_unicos = list(dict.fromkeys(r["mapa"] for r in dados))

    for mapa_nome in mapas_unicos:
        rows = [r for r in dados if r["mapa"] == mapa_nome]
        lambdas = [r["lambda"] for r in rows]
        bfs_passos = [r["bfs_passos"] for r in rows]
        astar_passos = [r["astar_passos"] for r in rows]
        bfs_risco = [r["bfs_risco"] for r in rows]
        astar_risco = [r["astar_risco"] for r in rows]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(f"E2: {mapa_nome} — Passos e Risco em funcao de lambda", fontsize=12)

        ax1.plot(lambdas, bfs_passos, "o-", color="cyan", linewidth=2, label="BFS (passos)")
        ax1.plot(lambdas, astar_passos, "s--", color="orange", linewidth=2, label="A* (passos)")
        ax1.set_xlabel("lambda")
        ax1.set_ylabel("Numero de passos")
        ax1.set_title("Passos vs lambda")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.plot(lambdas, bfs_risco, "o-", color="cyan", linewidth=2, label="BFS (risco)")
        ax2.plot(lambdas, astar_risco, "s--", color="orange", linewidth=2, label="A* (risco)")
        ax2.set_xlabel("lambda")
        ax2.set_ylabel("Exposicao ao risco (sum risco(c))")
        ax2.set_title("Exposicao ao risco vs lambda")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        nome_arquivo = f"resultados/e2_{mapa_nome.replace('.txt', '')}_grafico.png"
        plt.savefig(nome_arquivo, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"Grafico salvo em {nome_arquivo}")


def _gerar_imagens_rotas():
    """Gera imagens PNG das rotas BFS vs A* para lambda=0 e lambda=10."""
    from src.labirinto import carregar_labirinto
    from src.busca import bfs, a_estrela
    from src.desenho import desenhar_comparacao

    for mapa in MAPAS:
        for lam in [0, 10]:
            lab = carregar_labirinto(mapa, lambda_risco=float(lam))
            res_bfs = bfs(lab, registrar_ordem=False)
            res_astar = a_estrela(lab, registrar_ordem=False)
            nome_mapa = os.path.basename(mapa).replace(".txt", "")
            nome_arquivo = f"resultados/e2_{nome_mapa}_lambda{lam}.png"
            desenhar_comparacao(
                lab, res_bfs, res_astar,
                lambda_risco=float(lam),
                titulo=f"{nome_mapa} — lambda={lam}",
                caminho_saida=nome_arquivo,
            )
            print(f"Imagem salva em {nome_arquivo}")


if __name__ == "__main__":
    rodar_e2()
