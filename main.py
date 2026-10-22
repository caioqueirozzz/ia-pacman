"""CLI principal do projeto Pac-Man.

Uso:
    python main.py --mapa mapas/atalho_perigoso.txt --algoritmos bfs,ucs,astar --lambda 5 --raio 4
    python main.py --mapa mapas/arcade.txt --gui
    python main.py --aleatorio 41 --seed 7 --algoritmos ucs,astar
"""
import argparse
import math
import sys


def _tabela(resultados, lab):
    """Imprime tabela comparativa dos resultados."""
    cabecalho = (
        f"{'Algoritmo':<18} {'Enc':>3} {'Passos':>7} {'Custo':>10} "
        f"{'Exp':>6} {'Gerads':>7} {'Frontmax':>9} {'ms':>7}"
    )
    print(cabecalho)
    print("-" * len(cabecalho))
    for r in resultados:
        enc = "sim" if r.encontrado else "nao"
        custo = f"{r.custo_total:.2f}" if r.encontrado else "---"
        exp = f"{r.exposicao_risco:.1f}" if r.encontrado else "---"
        print(
            f"{r.algoritmo:<18} {enc:>3} {r.passos:>7} {custo:>10} "
            f"{exp:>6} {r.nos_gerados:>7} {r.fronteira_maxima:>9} {r.tempo_ms:>7.2f}"
        )


def _algoritmos_da_string(s: str, lab, heuristicas_disponiveis: dict):
    from src.busca import bfs, busca_custo_uniforme, a_estrela, busca_gulosa
    from src.heuristicas import manhattan

    mapa_nomes = {
        "bfs": lambda: bfs(lab, registrar_ordem=False),
        "ucs": lambda: busca_custo_uniforme(lab, registrar_ordem=False),
        "astar": lambda: a_estrela(lab, registrar_ordem=False),
        "gulosa": lambda: busca_gulosa(lab, registrar_ordem=False),
    }
    nomes = [n.strip().lower() for n in s.split(",")]
    resultado = []
    for nome in nomes:
        if nome not in mapa_nomes:
            print(f"Algoritmo desconhecido: {nome}. Opcoes: {list(mapa_nomes)}")
            sys.exit(1)
        resultado.append(mapa_nomes[nome]())
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Pac-Man: comparacao de algoritmos de busca")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--mapa", help="Arquivo .txt do labirinto")
    grupo.add_argument("--aleatorio", type=int, metavar="TAMANHO",
                       help="Tamanho do labirinto aleatorio (ex: 41)")

    parser.add_argument("--seed", type=int, default=42, help="Seed do gerador aleatorio")
    parser.add_argument("--algoritmos", default="bfs,ucs,astar",
                        help="Lista separada por virgula (bfs,ucs,astar,gulosa)")
    parser.add_argument("--lambda", dest="lambda_risco", type=float, default=5.0,
                        help="Peso do risco (padrao: 5.0)")
    parser.add_argument("--raio", type=int, default=4,
                        help="Raio do campo de risco dos fantasmas (padrao: 4)")
    parser.add_argument("--gui", action="store_true", help="Abre a interface grafica (pygame)")
    parser.add_argument("--sem-gui", action="store_true",
                        help="Apenas gera imagens estaticas (matplotlib)")
    parser.add_argument("--fantasmas", type=int, default=2,
                        help="Numero de fantasmas no labirinto aleatorio")

    args = parser.parse_args()

    # Carrega ou gera o labirinto
    if args.mapa:
        from src.labirinto import carregar_labirinto
        print(f"Carregando: {args.mapa} (lambda={args.lambda_risco}, raio={args.raio})")
        lab = carregar_labirinto(args.mapa, lambda_risco=args.lambda_risco)
    else:
        from src.gerador import gerar_labirinto
        print(
            f"Gerando labirinto {args.aleatorio}x{args.aleatorio} "
            f"seed={args.seed} lambda={args.lambda_risco}"
        )
        lab = gerar_labirinto(
            linhas=args.aleatorio,
            colunas=args.aleatorio,
            seed=args.seed,
            num_fantasmas=args.fantasmas,
            lambda_risco=args.lambda_risco,
            raio=args.raio,
        )

    if args.gui:
        try:
            from src.visualizacao import iniciar_gui
            iniciar_gui(lab)
        except ImportError as e:
            print(f"pygame nao disponivel: {e}")
            print("Instale com: pip install pygame")
        return

    # Modo terminal
    resultados = _algoritmos_da_string(args.algoritmos, lab, {})
    print(f"\nMapa: {args.mapa or f'aleatorio {args.aleatorio}x{args.aleatorio} seed={args.seed}'}")
    print(f"Dimensao: {lab.linhas}x{lab.colunas}  "
          f"Fantasmas: {len(lab.posicoes_fantasmas())}  "
          f"lambda={args.lambda_risco}  raio={args.raio}\n")

    _tabela(resultados, lab)

    # Verificacao de otimalidade
    custos = [r.custo_total for r in resultados if r.algoritmo != "BFS" and r.encontrado]
    if len(custos) >= 2 and not all(math.isclose(custos[0], c, rel_tol=1e-9) for c in custos):
        print("\nAVISO: custo dos algoritmos otimos diverge! Verifique a implementacao.")

    # Imprime mapa ASCII com o primeiro caminho encontrado
    from src.labirinto import labirinto_para_str
    melhor = next((r for r in resultados if r.encontrado), None)
    if melhor:
        print(f"\nMapa com caminho ({melhor.algoritmo}):")
        print(labirinto_para_str(lab, melhor.caminho))


if __name__ == "__main__":
    main()
