# Tabelas de tempos de deslocamento: cenário H (v5)

Gerado por `scripts/gerar_tt.py` em 2026-11-11 com o comando:
`C:\Python315\python.exe scripts\gerar_tt.py H x_plant-models\tt_cenario_H`

## Arquivos
| Arquivo | Conteúdo |
|---|---|
| `TT_R<n>_<MODELO>_H.txt` | matriz 11×11 (s), separada por tab, ponto decimal, pronta para colar na `TT_R<n>_<MODELO>` do Plant |
| `memoria_calculo_H.csv` | cada trecho usado na sequência (P0→P1→…→P10→P0): distância, origem da distância, regime, parcelas do tempo, tempo final e tempo da IC. Abre no Excel pt-BR (`;` e vírgula decimal) |

Índices da matriz (convenção da IC): linha/coluna 1 = home (P0); 2…11 = P1…P10. A matriz é **simétrica** (i→j = j→i), o que torna irrelevante a orientação de/para que o PickAndPlace usa (ver CLAUDE.md 4.3, item 3).

## Como cada valor foi calculado
Para cada par de pontos (i, j):

1. **Distância d (m)**
   - Entre P1…P10: reta (distância euclidiana) entre as coordenadas da `TC_<MODELO>` (metros, mesmas que o `def_inPosition` usa para posicionar os pontos).
   - Entre o home (P0) e P1/P10: a TC do Plant não tem o P0. A distância foi recuperada da própria IC: d = t_IC ÷ k, em que k (s/m) é a mediana de t/d nos trechos P1…P9 daquele robô e produto. Isso vale porque a IC calculou todos os tempos como distância × k (relatório da IC, seção 3; conferido em 2026-11-09: k ≈ 12,3 s/m no sedan e ≈ 15,8 s/m no hatch).
   - Home ↔ pontos intermediários: sem dado e não usados na sequência, então ficam em 0.
   - d = 0 (P10 duplicado do P9, exceto no R2 SEDAN): tempo 0, como na IC.

2. **Tempo cinemático (perfil trapezoidal de velocidade)**, com v = velocidade programada e a = aceleração:
   - se d ≥ v²/a: `t_kin = d/v + v/a` (acelera, anda em cruzeiro, desacelera);
   - se d < v²/a: `t_kin = 2·√(d/a)` (não chega a v).
   - Cenário H usa os parâmetros de K2: **v = 1,0 m/s** e **a = 12 m/s²**, então v²/a = 0,083 m e todos os trechos reais caem no regime trapezoidal.

3. **Tempo de estabilização: PSt = 0,17 s** por trecho com movimento (o robô assenta no ponto antes da solda).

4. **Sobrecusto c = 0,7287 s** por trecho com movimento. Representa a aproximação, o recuo e a reorientação da pinça, que a reta entre pontos não captura. Foi **calibrado** para que, na média dos 4 robôs × 2 produtos, o tempo total por ponto de solda (movimento + 1,6 s de solda) seja **3,3 s**.

5. **Tempo final:** `t = t_kin + PSt + c` (ou 0 se d = 0).

Exemplo (R1 SEDAN, P2→P3): d = 0,1315 m → 0,1315/1,0 + 1,0/12 + 0,17 + 0,7287 = **1,1136 s** (IC: 1,6066 s). Na sequência completa, o R1 SEDAN passa de 90,6 s de movimento (IC) para 17,2 s.

## Referências e de onde vem cada parâmetro
| Parâmetro | Valor | Fonte | Observação |
|---|---|---|---|
| Aceleração cartesiana máxima (movimento controlado), IRB 6700-205/2.8 | 24 m/s² | ABB, *Product specification IRB 6700*, 3HAC044265-001 rev. N (2019), seção 1.5.5 | H usa **metade** (12 m/s²): hipótese de programação típica, abaixo do limite |
| Velocidade do teste ISO 9283 | 1,6 m/s | idem, seção 1.8.2 (e brochura IRB 6700) | limite usado no cenário K1 |
| Velocidade programada | 1,0 m/s | `v1000` = speeddata predefinido do RAPID (1000 mm/s) | **hipótese** de programação típica; não é medição |
| Tempo de estabilização (PSt, até 0,4 mm) | 0,17 s | idem, seção 1.8.2, tabela ISO 9283, coluna 205/2.80 | |
| Tempo padrão por ponto de solda | 3,3 s (movimento + solda) | Cho, Kim e Park, *Simulation based cycle time prediction for robot welding*, Winter Simulation Conference 2024 (`z_references/tempo-solda.pdf`) | regra empírica da indústria; o próprio artigo mostra 72% de acurácia. Usada **só para calibrar c** |
| Tempo de solda por ponto | 1,6 s | FMEIB (2025) via relatório da IC; `float_tempoSolda` | inalterado |
| Coordenadas P1…P10 | TC_HATCH / TC_SEDAN | FMEIB (2025) via relatório da IC, Tab. 5–8 | inalteradas |
| Distâncias de/para o home | implícitas na TT da IC | relatório da IC, Tab. 2–3 + método da seção 3 | limitação: dependem da calibração da IC |

## Limitações (dizer no texto)
- A reta entre pontos é um **limite inferior** do caminho real. O sobrecusto c compensa isso **em média**, ancorado numa regra empírica, e não trecho a trecho.
- v = 1,0 m/s e a = 12 m/s² são hipóteses de programação; o limite do fabricante (K1) e a regra de Cho pura entram na **análise de sensibilidade**.
- Em qualquer cenário da faixa (K1 até a regra de Cho), o robô fica parado ~72–84% do tempo, contra 20–45% no modelo da IC. **A conclusão principal não depende da escolha do cenário.**

## Resultado esperado no Plant (v5 = v4 + estas tabelas)
Calculado com 279 hatch + 157 sedan e as potências da v4 (Working 2,6 / Operational 0,84 / Standby 4,59 kW):

| Robô | Movimento (h) | Solda (h) | Ocioso (h) | Ocioso | kWh |
|---|---|---|---|---|---|
| R1 | 1,860 | 1,744 | 12,395 | 77,5% | 23,26 |
| R2 | 1,946 | 1,815 | 12,240 | 76,5% | 23,67 |
| R3 | 1,762 | 1,745 | 12,493 | 78,1% | 23,09 |
| R4 | 1,874 | 1,745 | 12,381 | 77,4% | 23,28 |
| Skid | — | — | — | — | 7,20 |
| **Total** | | | | | **100,50 kWh = 0,2305 kWh/carroceria** (v4: 154,72) |

Throughput esperado: **436** (o takt de 132 s do `ENTRADA_BIY` não muda).
