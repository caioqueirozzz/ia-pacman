# Pac-Man: o caminho mais curto é o mais seguro?

Trabalho da disciplina **Introdução à Inteligência Artificial** — Grupo 5.

Modelamos um labirinto do estilo Pac-Man como um problema de busca com **custos
diferentes por célula** (corredor, terreno difícil, zona de risco e risco gerado
por fantasmas) e comparamos a **Busca de Custo Uniforme (UCS)** com o **A\***,
usando uma heurística admissível, para responder à pergunta do título.

> **Status:** em construção (implementação por fases — ver `enunciado`/plano).

## Pergunta central

A rota com **menos passos** (BFS) é a mesma de **menor custo/risco** (UCS / A\*)?
O parâmetro `λ` (peso do risco) controla o quanto o agente foge do perigo.

## Como rodar

```bash
pip install -r requirements.txt

# Comparar algoritmos num mapa
python main.py --mapa mapas/atalho_perigoso.txt --algoritmos bfs,ucs,astar --lambda 5 --raio 4

# Abrir a visualização (pygame)
python main.py --mapa mapas/arcade.txt --gui

# Mapa aleatório reprodutível
python main.py --aleatorio 41 --seed 7 --algoritmos ucs,astar

# Experimentos
python -m experimentos.e1_eficiencia
python -m experimentos.e2_curto_vs_seguro
python -m experimentos.gerar_relatorio

# Testes
pytest
```

## Estrutura

```
mapas/          mapas .txt
src/            config, labirinto, risco, heuristicas, busca, gerador, metricas, desenho, visualizacao
experimentos/   E1, E2, E3 e gerador de relatorio
resultados/     CSV, PNG e RESULTADOS.md (gerados)
tests/          testes (pytest)
```

## Modelagem

<!-- TODO (Fase 6): grid, tipos de célula, risco dos fantasmas e papel de λ -->

## Heurística: admissibilidade e consistência

<!-- TODO (Fase 6): prova de h = c_min × Manhattan admissível e consistente -->

## Resultados

<!-- TODO (Fase 6): resumo de E1 e E2 com links para gráficos -->

## Conclusão

<!-- TODO (Fase 6): resposta à pergunta, com dados -->

## Limitações e extensões

Os fantasmas são **estáticos**: o perigo deles é convertido em custo no mapa.
Fantasmas que se movem e reagem ao agente transformariam o problema em **busca
adversarial** (Minimax / poda alfa-beta) — citado como extensão futura.
