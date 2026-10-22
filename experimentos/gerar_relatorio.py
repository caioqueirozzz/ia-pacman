"""Gera resultados/RESULTADOS.md com tabelas e links para os graficos.

Execucao:
    python -m experimentos.gerar_relatorio
"""
import csv
import os


def ler_csv(caminho: str) -> list[dict]:
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _tabela_md(colunas: list[str], linhas: list[dict]) -> str:
    cab = " | ".join(colunas)
    sep = " | ".join("---" for _ in colunas)
    rows = []
    for linha in linhas:
        rows.append(" | ".join(str(linha.get(c, "")) for c in colunas))
    return "\n".join([cab, sep] + rows)


def gerar():
    os.makedirs("resultados", exist_ok=True)

    e1 = ler_csv("resultados/e1_eficiencia.csv")
    e2 = ler_csv("resultados/e2_curto_vs_seguro.csv")
    e3 = ler_csv("resultados/e3_heuristicas.csv")

    # Resumo E1 por tamanho
    e1_resumo = {}
    for row in e1:
        t = int(row["tamanho"])
        if t not in e1_resumo:
            e1_resumo[t] = {"ucs": [], "astar": [], "red": []}
        e1_resumo[t]["ucs"].append(int(row["ucs_expandidos"]))
        e1_resumo[t]["astar"].append(int(row["astar_expandidos"]))
        e1_resumo[t]["red"].append(float(row["reducao_pct"]))

    e1_tabela = []
    for t, v in sorted(e1_resumo.items()):
        med_ucs = sum(v["ucs"]) / len(v["ucs"])
        med_astar = sum(v["astar"]) / len(v["astar"])
        med_red = sum(v["red"]) / len(v["red"])
        e1_tabela.append({
            "Tamanho": t,
            "UCS_expandidos": f"{med_ucs:.0f}",
            "A*_expandidos": f"{med_astar:.0f}",
            "Reducao_%": f"{med_red:.1f}",
        })

    linhas_md = [
        "# Resultados do Projeto Pac-Man",
        "",
        f"> Gerado automaticamente — {__import__('datetime').date.today()}",
        "",
        "## E1 — Eficiencia: UCS vs A* (media de 20 seeds)",
        "",
    ]

    if e1_tabela:
        linhas_md.append(_tabela_md(
            ["Tamanho", "UCS_expandidos", "A*_expandidos", "Reducao_%"],
            e1_tabela,
        ))
        linhas_md += ["", "![Grafico E1](e1_grafico.png)", ""]
    else:
        linhas_md += ["*Execute `python -m experimentos.e1_eficiencia` para gerar.*", ""]

    linhas_md += [
        "## E2 — O caminho mais curto e o mais seguro?",
        "",
    ]
    if e2:
        mapas_e2 = list(dict.fromkeys(r["mapa"] for r in e2))
        for mapa_nome in mapas_e2:
            rows = [r for r in e2 if r["mapa"] == mapa_nome]
            linhas_md.append(f"### {mapa_nome}")
            linhas_md.append("")
            linhas_md.append(_tabela_md(
                ["lambda", "bfs_passos", "bfs_risco", "astar_passos", "astar_risco", "mesma_rota"],
                rows,
            ))
            linhas_md += [
                "",
                f"![Grafico E2 {mapa_nome}](e2_{mapa_nome.replace('.txt','')}_grafico.png)",
                f"![Rota lambda=0](e2_{mapa_nome.replace('.txt','')}_lambda0.png)",
                f"![Rota lambda=10](e2_{mapa_nome.replace('.txt','')}_lambda10.png)",
                "",
            ]
    else:
        linhas_md += ["*Execute `python -m experimentos.e2_curto_vs_seguro` para gerar.*", ""]

    linhas_md += ["## E3 — Qualidade da heuristica (opcional)", ""]
    if e3:
        linhas_md.append(_tabela_md(
            ["heuristica", "admissivel", "nos_expandidos", "custo", "otimo"],
            e3,
        ))
        linhas_md += ["", "![Grafico E3](e3_grafico.png)", ""]
    else:
        linhas_md += ["*Execute `python -m experimentos.e3_heuristicas` para gerar.*", ""]

    linhas_md += [
        "## Conclusao",
        "",
        "A rota com menos passos (BFS) tende a **nao** ser a de menor custo/risco "
        "quando ha fantasmas no labirinto.",
        "Conforme lambda aumenta, o A* desvia da rota mais curta em favor de uma rota "
        "com mais passos, porem de menor exposicao ao perigo.",
        "",
        "UCS e A* encontram sempre o mesmo custo otimo, mas o A* expande significativamente "
        "menos nos gracas a heuristica admissivel (Manhattan x c_min).",
    ]

    conteudo = "\n".join(linhas_md) + "\n"
    with open("resultados/RESULTADOS.md", "w", encoding="utf-8") as f:
        f.write(conteudo)
    print("Relatorio salvo em resultados/RESULTADOS.md")


if __name__ == "__main__":
    gerar()
