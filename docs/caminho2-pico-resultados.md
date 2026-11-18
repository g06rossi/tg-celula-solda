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
Reativo: todos os robôs começam na chegada; cada solda começa no primeiro instante com menos de K soldando.

| | Reativo: fim / espera acordado | Ótimo (menor fim) |
|---|---|---|
| Hatch K=3 | 30,94 s / 1,5 s | 30,34 s |
| Hatch K=2 | 33,32 s / 12,6 s | 33,00 s |
| **Hatch K=1** | **64,61 s / 72,4 s** | 61,54 s |
| Sedan K=3 | 33,54 s / 1,8 s | 32,98 s |
| Sedan K=2 | 36,27 s / 13,9 s | 35,13 s |
| **Sedan K=1** | **68,72 s / 79,8 s** | 63,19 s |

**Achado:** com K = 1, o intertravamento reativo deixa os robôs ~76 s por carroceria acordados esperando a vez (≈ 5,3 kWh por turno, ~9%). O escalonamento **planejado**, com cada robô acordando na sua hora, faz o mesmo pico com ~0,5 kWh (~1%): **~90% a menos de custo de energia**. Com K = 2 ou 3, o reativo já fica perto do ótimo.

## Implementação no Plant (próximo passo)
1. **Etapa 1, intertravamento reativo K** (`reservar_solda` no Python devolve o atraso d; `?.startPause(d + float_tempoSolda)` nos 8 `def_*`; o Python corrige a energia da espera, que o Plant cobra a 4,59 kW no Standby, para 0,84 kW). Cenários K = 3, 2, 1. Validação: K_max medido ≤ K, fim e esperas iguais à tabela 3.
2. **Etapa 2, escalonamento planejado:** acordar cada robô na sua hora e acionar os freios de cada robô quando ele volta ao home (o `tick` passa a 1 s), com o intertravamento garantindo K.
3. **Margem para a retífica** (~2 s por robô a cada N soldas, ABB): a escolher (ex.: fim ≤ 70 s deixa 35 s).
