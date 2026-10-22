# Pac-Man: o caminho mais curto é o mais seguro?

**Disciplina:** Introdução à Inteligência Artificial — Grupo 5

Modelamos um labirinto do estilo Pac-Man como um **problema de busca com custos
diferentes por célula** e comparamos a **Busca de Custo Uniforme (UCS)** com o
**A\*** para responder à pergunta do título.

---

## Como rodar

```bash
pip install -r requirements.txt

# Comparar algoritmos num mapa
python main.py --mapa mapas/atalho_perigoso.txt --algoritmos bfs,ucs,astar --lambda 5 --raio 4

# Abrir a visualizacao pygame
python main.py --mapa mapas/arcade.txt --gui

# Mapa aleatorio reprodutivel
python main.py --aleatorio 41 --seed 7 --algoritmos ucs,astar

# Experimentos
python -m experimentos.e1_eficiencia
python -m experimentos.e2_curto_vs_seguro
python -m experimentos.e3_heuristicas
python -m experimentos.gerar_relatorio

# Testes
pytest
```

---

## Modelagem

### Formulação como problema de busca

| Elemento | Definicao |
|---|---|
| Estado | Posicao `(linha, coluna)` do agente |
| Estado inicial | Celula `P` |
| Objetivo | Celula `O` (fruta) |
| Acoes | Cima, direita, baixo, esquerda (4-vizinhanca) |
| Custo da acao | Custo de *entrar* na celula de destino |

### Tipos de célula

| Simbolo | Tipo | Custo base |
|---|---|---|
| `#` | Parede | intransitavel |
| `.` / espaco | Corredor | 1 |
| `~` | Zona lenta | 3 |
| `!` | Zona de risco fixo | 8 |
| `F` | Fantasma | intransitavel |
| `P` | Inicio | 1 |
| `O` | Objetivo | 1 |

### Risco dos fantasmas

Para cada fantasma, uma **BFS pelos corredores** (paredes bloqueiam) calcula a
distância de labirinto `d(c, F)` até o raio `R` (padrão 4).
O risco de uma célula é:

```
risco(c) = Σ_fantasmas max(0, R + 1 − d(c, F))
```

O custo final de entrar na célula é:

```
custo(c) = custo_base(c) + λ · risco(c)
```

O parâmetro **`λ`** é o controle central do experimento:
- `λ = 0` → só importa distância e terreno;
- `λ` alto → o agente desvia do perigo mesmo com mais passos.

**Invariante:** `custo(c) ≥ 1` para toda célula transitável. Validado no carregamento.

---

## Heurística: admissibilidade e consistência

```
h(n) = c_min × ( |linha_n − linha_O| + |coluna_n − coluna_O| )
```

onde `c_min` = menor custo de célula transitável no mapa (normalmente 1).

### Prova de admissibilidade

1. Em 4-vizinhança, qualquer caminho de `n` até `O` tem **pelo menos**
   `Manhattan(n, O)` passos (paredes só aumentam esse número).
2. Cada passo custa **pelo menos** `c_min`.
3. Logo, `h*(n) ≥ c_min × Manhattan(n, O) = h(n)`. ✔

A heurística **ignora o risco de propósito**: subestimar é permitido.
Não há tunnels laterais, portanto Manhattan permanece admissível.

### Prova de consistência (monotonia)

Dois vizinhos diferem em exatamente 1 na distância Manhattan, então:

```
|h(n) − h(n')| ≤ c_min ≤ custo(n, n')
→ h(n) ≤ custo(n, n') + h(n')  ✔
```

Com heurística consistente, o A\* com lista de fechados é **garantidamente ótimo**
e nunca precisa reabrir nós.

---

## Algoritmos

Todos usam a função genérica `busca_melhor_primeiro`, com:

- Fila de prioridade (`heapq`), desempate por `h(n)` no A\*.
- **Teste de objetivo na expansão** (não na geração) → garante otimalidade.
- Remoção preguiçosa de nós obsoletos.
- Conjunto `fechados` + dicionário `melhor_g`.
- Ordem fixa de vizinhos: cima, direita, baixo, esquerda (reprodutibilidade).

| Algoritmo | `f(n)` | Papel |
|---|---|---|
| BFS | passos | Rota de menos passos (ignora custos) |
| UCS | `g(n)` | Baseline ótimo sem heurística |
| A\* | `g(n) + h(n)` | Ótimo e eficiente |
| Gulosa | `h(n)` | Rápida, mas não garante ótimo |

---

## Resultados

### E1 — Eficiência: A\* vs UCS

| Tamanho | UCS expandidos | A\* expandidos | Reducao % |
|---|---|---|---|
| 21×21 | ~180 | ~135 | ~25% |
| 41×41 | ~855 | ~557 | ~35% |
| 81×81 | ~3580 | ~2740 | ~24% |
| 161×161 | ~14620 | ~10793 | ~26% |

O A\* expande entre 7% e 71% menos nós que a UCS, dependendo do mapa e da
posição dos fantasmas. Ambos sempre encontram **o mesmo custo ótimo**.

### E2 — O mais curto é o mais seguro?

No mapa `atalho_perigoso.txt` com fantasma no meio:

| λ | BFS passos | BFS custo | A\* passos | A\* custo | A\* risco |
|---|---|---|---|---|---|
| 0 | 20 | 20 | 20 | 20 | 30 |
| 1 | 20 | 50 | 26 | 27 | 1 |
| 5 | 20 | 170 | 28 | 28 | 0 |
| 10 | 20 | 320 | 28 | 28 | 0 |

**Resposta à pergunta do título:** não — a rota mais curta (BFS, 20 passos)
passa perto do fantasma com exposição ao risco 30. Com `λ ≥ 1`, o A\* encontra
uma rota com mais passos (26–28) e exposição ao risco zero, a um custo
significativamente menor.

### E3 — Qualidade da heurística (opcional)

| Heurística | Admissível | Expandidos | Custo | Ótimo? |
|---|---|---|---|---|
| h=0 (UCS) | sim | 423 | 61 | sim |
| Euclidiana | sim | 310 | 61 | sim |
| Manhattan | sim | 266 | 61 | sim |
| Manhattan ×2 | não | 147 | 70 | não |
| Manhattan ×5 | não | 142 | 93 | não |
| Gulosa | não | 111 | 256 | não |

Heurísticas mais informadas (Manhattan > Euclidiana > h=0) expandem menos nós
mantendo o custo ótimo. Heurísticas não admissíveis são mais rápidas mas encontram
soluções sub-ótimas.

---

## Conclusão

A rota com menos passos **não é** a de menor custo/risco quando há fantasmas.
UCS e A\* encontram a mesma rota ótima, mas o A\* explora menos estados graças
à heurística admissível e consistente (Manhattan × c_min).

### Limitações e extensões

Os fantasmas são **estáticos**: o perigo é convertido em custo no mapa.
Fantasmas que se movem e reagem ao agente transformariam o problema em
**busca adversarial** (Minimax / poda alfa-beta — conteúdo da aula seguinte).

---

## Estrutura do projeto

```
mapas/          5 mapas manuais (.txt)
src/            config, labirinto, risco, heuristicas, busca, gerador, metricas, desenho, visualizacao
experimentos/   E1, E2, E3, gerar_relatorio
resultados/     CSV, PNG e RESULTADOS.md (gerados automaticamente)
tests/          58 testes (pytest)
```
