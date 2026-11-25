# Caminho 2: pico de potência das soldas — resultados da otimização (fora do Plant)

2026-11-18. Scripts: `scripts/otimiza_pico.py` (CP-SAT/OR-Tools, Python 3.13). Saídas em `scripts/resultados/otimiza_pico_*.json`.

## Base
- Objetivo (Farrow 2004; WTC): pico instantâneo para **dimensionar a alimentação**. Sem intertravamento, com 4 pinças GWT C9 (90 kVA cada), 360 kVA; limitando a K soldas simultâneas, K × 90 kVA. A demanda faturada (ANEEL, média de 15 min) não muda.
- Linha de base medida no Plant (v12_K4): **K_max = 4 em todas as réplicas**; 20,5% do tempo com solda tem os 4 robôs soldando juntos (~5 s por carroceria).
- Modelo da linha do tempo em Python (trajetos do cenário H + soldas de 1,6 s) **reproduz a v12 com erro < 1%** → otimização fora do Plant, validação no Plant.
- Janela por carroceria: 132 s − 26,83 s (skid) = **105,2 s**.
- Custo de energia de uma espera com o robô acordado: (0,84 − 0,17) kW = 0,67 kW (robô parado com freios liberados em vez de acionados).

## 1. Menor fim de ciclo para cada K (com esperas entre soldas permitidas)
| K | kVA | Hatch | Sedan |
|---|---|---|---|
| 4 | 360 | 29,94 s | 32,98 s |
| 3 | 270 | 30,34 s | 32,98 s |
| 2 | 180 | 33,00 s | 35,13 s |
| **1** | **90** | **61,54 s** | **63,19 s** |

Todos cabem na janela de 105,2 s. **Até K = 1 é viável com ~40 s de folga.** (Só com defasagem do início de cada robô, sem esperas no meio, o sedan não passava de K = 2.)

## 2. Fronteira fim do ciclo × espera com o robô acordado (s por carroceria)
| | fim ≤ mín. | ≤ 50 s | ≤ 60 s | ≤ 70 s | ≤ 80 s | ≤ 90 s | ≤ 100 s | ≤ 105,2 s |
|---|---|---|---|---|---|---|---|---|
| Hatch K=3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Hatch K=2 | 9,6 | 2,0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Hatch K=1 | 28,8 | — | — | 7,2 | 5,0 | 2,5 | 1,0 | 0 |
| Sedan K=3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Sedan K=2 | 8,9 | 1,2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Sedan K=1 | 48,1 | — | — | 9,6 | 6,2 | 3,3 | 1,4 | 0,4 |

(Valores com limite de 20 s por resolução; os marcados como FEASIBLE no JSON são boas soluções, não necessariamente ótimas.)

**Leitura:** K = 3 é de graça; K = 2 é de graça com fim ≤ 60 s; **K = 1 com fim ≤ 70 s (35 s de folga) custa ~7–10 s de espera por carroceria ≈ 0,5 kWh por turno (~1% da energia da política `freios`).**

## 3. Intertravamento reativo (prática industrial, Farrow) × escalonamento planejado
Reativo: todos os robôs começam na chegada; cada robô, ao pedir para soldar, entra na fila e recebe a primeira vaga com menos de K soldando (`reservar_solda` do `coleta_plant.py`, simulado fora do Plant por eventos). **Corrigido em 2026-11-18:** uma primeira estimativa, feita com um cálculo simplificado à parte, dava para K = 1 fim de 64,6/68,7 s e espera de 72/80 s; a simulação com o código que o Plant vai executar dá os valores abaixo.

| | Reativo: fim / espera acordado | Ótimo (menor fim) |
|---|---|---|
| Hatch K=3 | 30,94 s / 1,5 s | 30,34 s |
| Hatch K=2 | 33,00 s / 12,5 s | 33,00 s |
| **Hatch K=1** | **61,80 s / 120,8 s** | 61,54 s |
| Sedan K=3 | 33,54 s / 1,8 s | 32,98 s |
| Sedan K=2 | 36,23 s / 13,4 s | 35,13 s |
| **Sedan K=1** | **63,68 s / 120,9 s** | 63,19 s |

**Achado:** com K = 1, o intertravamento reativo termina quase tão cedo quanto o ótimo, mas deixa os robôs **~121 s por carroceria acordados esperando a vez** (0,67 kW × 121 s ≈ 81 kJ por carroceria ≈ **8,4 kWh por turno, ~14%** da energia da política `freios`). O escalonamento **planejado** (fim ≤ 70 s, cada robô acordando na sua hora) faz o mesmo pico com ~0,5 kWh (~1%): **~94% a menos de custo de energia**. Com K = 2 ou 3, o reativo já fica perto do ótimo (custo ~1,5% e ~0,2%).

## Validação no Plant — etapa 1, intertravamento reativo (v13, 2026-11-18)
Política `freios`, 10 réplicas por K; comparação pareada com a `v12_K4` nas variantes 2–10 (K = 3, 2, 1 rodaram com as variantes 2–11).

| K | Pico medido | Espera acordado (s/carroceria) | Energia vs. sem intertravamento | Throughput |
|---|---|---|---|---|
| 4 | 360 kVA | 0 | 0 (idêntico à v12) | igual |
| 3 | **270 kVA** | 1,6 | **+0,39% ± 0,00%** | −0,1 carroceria/turno |
| 2 | **180 kVA** | 12,8 | **+1,45% ± 0,01%** | −0,1 |
| 1 | **90 kVA** | 121,0 | **+14,62% ± 0,07%** (+8,75 kWh) | −0,3 |

O pico medido nunca passou de K e os números batem com a previsão fora do Plant (espera de 121 s com K = 1, custo de ~14%). A perda de produção é desprezível (a carroceria que ficava pronta no último minuto do turno).

## Validação no Plant — etapa 2, escalonamento planejado (v16, 2026-11-25)
Política `plano` (`politicas.py` + `plano_K1_fim70.json`), K = 1, 10 réplicas. Comparação pareada nas variantes 2–10 (a réplica 1 usou outra sequência aleatória: variante ajustada depois do Reset).

| Política (pico) | kWh/carroceria | Espera acordado (s/carroceria) | Throughput | Energia vs `freios` |
|---|---|---|---|---|
| `freios`, sem intertravamento (360 kVA) | 0,1596 | 0 | 375,0 | — |
| Reativo K = 1 (90 kVA) | 0,1832 | 121,0 | 374,6 | **+14,62% ± 0,07%** |
| **Planejado K = 1 (90 kVA)** | **0,1612** | **9,8** | 372,3* | **+0,74% ± 0,03%** |

\* média das 10 réplicas, incluindo a réplica 1 (351); nos 9 pares válidos a diferença de throughput contra `freios` é −0,33 ± 0,38 carroceria/turno, igual à do reativo.

**Planejado − reativo (mesmo pico de 90 kVA, mesmo throughput):** −8,31 ± 0,23 kWh por turno (**−12,11% ± 0,06%**). O planejamento elimina **~95% do custo de energia** do intertravamento convencional (+0,74% contra +14,62%).

**Conclusão do caminho 2:** limitar as soldas simultâneas a 1 reduz o pico de dimensionamento da alimentação em **75% (360 → 90 kVA)** sem perder produção; com o escalonamento otimizado (CP-SAT) e os robôs acordando e freando cada um na sua hora, o custo é de **+0,74% de energia**, contra +14,6% do intertravamento reativo (Farrow, 2004).

Lições de implementação: (1) os `waituntil` originais do `def_inPosition` seguiam o R1 e travavam quando o R1 terminava antes da criação dos MUs dos outros robôs; substituídos por um contador de robôs concluídos (`int_concluidos`); (2) ajustar a variante aleatória **antes** do Reset.

## Implementação no Plant (histórico do planejamento)
1. **Etapa 1, intertravamento reativo K** (`reservar_solda` no Python devolve o atraso d; `?.startPause(d + float_tempoSolda)` nos 8 `def_*`; o Python corrige a energia da espera, que o Plant cobra a 4,59 kW no Standby, para 0,84 kW). Cenários K = 3, 2, 1. Validação: K_max medido ≤ K, fim e esperas iguais à tabela 3.
2. **Etapa 2, escalonamento planejado:** acordar cada robô na sua hora e acionar os freios de cada robô quando ele volta ao home (o `tick` passa a 1 s), com o intertravamento garantindo K.
3. **Margem para a retífica** (~2 s por robô a cada N soldas, ABB): a escolher (ex.: fim ≤ 70 s deixa 35 s).
