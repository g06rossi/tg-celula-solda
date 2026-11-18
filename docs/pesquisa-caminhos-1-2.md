# Pesquisa para os caminhos 1 (manutenção oportunista com operador) e 2 (pico de potência)

2026-11-18. Contexto: na v11, a política `freios` reduziu 36,5% da energia e o oráculo da hibernação ganharia só ~1% a mais. O RL precisa de outra decisão difícil. O usuário escolheu implementar o caminho 2 e pesquisar o 1 para decidir.

Confiabilidade: **A** = documento lido por nós; **B** = lido só pelo resumo ou por citação; **C** = comercial ou indicativo.

---

## Caminho 2: pico de potência das soldas

### Qual pico importa
| Fonte | O que diz | Conf. |
|---|---|---|
| ANEEL, REN 1000/2021, definição de *demanda medida*: "maior demanda de potência ativa [...] verificada por medição e **integralizada em intervalos de 15 minutos** durante o período de faturamento, em kW" | A demanda faturada é uma média de 15 min. Pulsos de solda de ~80 ms não a alteram de forma relevante; a célula inteira consome ~4–6 kW em média | B (texto citado na busca; conferir o texto consolidado) |
| Farrow, J. *Sizing the primary power system for resistance welders.* Welding Technology Corp., Sheet Metal Welding Conference, 2004. PDF em `z_references/` | "Com 4 soldadoras ou menos, há probabilidade muito alta de todas soldarem **ao mesmo tempo** várias vezes por dia; o sistema deve ser dimensionado para que a tensão não caia mais de **10%** com todas soldando juntas." "Se não for possível, um **intertravamento** (*interlock*) garante que só uma solde por vez; o sistema passa a ser dimensionado para **uma** soldadora, e com fator de serviço ≤ 5% o intertravamento reduz a produção em **muito menos de 1%**" | A |
| Welding Technology Corp. *Sizing circuit breaker* (nota técnica). PDF em `z_references/` | Transformadores disparados juntos: kVA efetivo = **soma**; em **cascata** (um por vez): kVA efetivo = o do **maior** transformador | A |
| ABB GWT C9 (já em uso) | 90 kVA (S50) por pinça | A |

**Objetivo do caminho 2 (definido pelas fontes):** não é a conta de demanda, é o **pico instantâneo para dimensionar a alimentação** (transformador, barramento, queda de tensão). Com 4 pinças de 90 kVA soldando juntas, o sistema precisa de 360 kVA (o pico de 360 kW da IC); com intertravamento de 1 por vez, 90 kVA. A pergunta passa a ser: **quantas soldas simultâneas (K) permitir, e quanto isso custa em tempo de ciclo, produção e energia?** Com ~80% de tempo livre por ciclo, a hipótese é que K = 1 cabe na folga sem perder produção, mas isso precisa ser medido.

### Formulação matemática (Fase 2, otimização clássica)
- Para cada modelo de carroceria, cada robô r tem uma sequência fixa de trajetos (tempos da TT do cenário H) e soldas de 1,6 s.
- Variáveis: o atraso antes de cada solda.
- Restrição: em qualquer instante, no máximo K robôs soldando (restrição cumulativa / disjuntiva).
- Objetivo: minimizar o tempo do robô mais lento (*makespan*) para cada K. Com 4 robôs e ~37 soldas por carroceria, cabe numa programação inteira mista (MILP) ou em programação por restrições, resolvida de forma **exata**.
- Resultado esperado: a curva **K × makespan × kVA efetivo** (K = 4: 360 kVA; K = 1: 90 kVA).

### Implementação no Plant
1. **Medir a linha de base:** registrar cada início de solda (chamada ao Python nos 8 `def_entranceR*` / `def_exitR*`) e reconstruir quantos robôs soldam ao mesmo tempo, a cada instante.
2. **Intertravamento com K soldas simultâneas:** antes de soldar, o robô pede uma vaga ao Python (`reservar_solda`), que devolve o atraso d até haver vaga; no SimTalk, `?.startPause(d + float_tempoSolda)`. Como a pausa inteira fica no Standby (4,59 kW), o Python corrige a energia da espera (d × (4,59 − 0,84) kW, porque o robô está parado com freios liberados). Cenários K = 4 (sem intertravamento), 3, 2, 1.
3. **Exige alterar os `def_*` da IC** (8 Methods); o código atual já está em `infotmation-methods/`.

---

## Caminho 1: manutenção oportunista (capas dos eletrodos) com operador

### O que as fontes dizem
| Item | Valor | Fonte | Conf. |
|---|---|---|---|
| Vida da capa em aço galvanizado | **300–500 soldas sem retífica**; até **~2.500 soldas com retífica** | Franczak, K. et al. *Investigation of electrode cap life made of new Cu–Cr–Zr copper alloys with scandium addition...* Materials 18(21):4950, 2025, DOI 10.3390/ma18214950 (citando a literatura, refs. 11–16) | A (o texto) / B (a origem dos números) |
| Intervalo entre retíficas | **20–300 soldas**, conforme o caso | CORDIS, projeto *ADAPT – Adaptive tip dress control for automated resistance spot welding* (UE, 286598), relatório | B |
| | ~25 soldas em chapa galvanizada | Robzoft (página de produto) | C |
| Tempo de uma retífica | **1,5–2,5 s por porta-fresa** (força 1,0 kN) | ABB, *Electrode tip dresser* datasheet, 9AKK107045A3883 (10/2018). PDF em `z_references/` | **A (ABB, continuidade)** |
| Troca de capa automática | 15–30 s | AMDP (catálogo); G.E. Schmidt / Kyokutoh (20–30 s) | C |
| Troca de capa **manual** | **5–10 min** | G.E. Schmidt (página de produto) | C |
| Peso nas paradas reais | A retífica (*tip dressing*) é a 2ª maior causa de parada (80 ocorrências em 3 anos) numa célula robótica de solda automotiva | Alaka et al. (2025) | B |

### Ordem de grandeza na nossa célula
- Cada robô faz ~3.900 soldas por turno de 16 h (436 × 9) na v7, ~3.350 na v10.
- **Retífica automática** (sem operador): a cada ~25–300 soldas → 13 a 150 retíficas por robô por turno, de ~2 s cada → **30 s a 5 min por robô por turno**. É pequeno e não envolve o operador.
- **Troca de capa** (fim de vida, ~2.500 soldas com retífica): **~1,3–1,6 troca por robô por turno, ~5–6 por turno na célula**. Se for manual (5–10 min, conf. C): **25–60 min de parada por turno**, a menos que seja feita durante as paradas da estação anterior. **Aí está a decisão difícil:** trocar antes do fim da vida, aproveitando uma parada (desperdiça vida útil da capa), ou esperar o fim da vida (para a célula e depende de o operador estar livre).

### Viabilidade
- **Viável**, e a decisão tem impacto grande: dezenas de minutos de produção por turno contra ~1% do caminho B.
- Fontes: a física da capa (vida, retífica) tem fonte A/B; **o tempo de troca manual e o deslocamento do operador só têm fonte C** → hipótese explícita com análise de sensibilidade (ex.: 3, 5 e 10 min).
- Literatura para enquadrar a decisão: **manutenção oportunista** em linhas de produção (aproveitar paradas para fazer manutenção preventiva) é um tema estabelecido. **A pesquisar** antes de implementar, para citar o estado da arte e uma política clássica de comparação (por exemplo, limiar de vida + janela de oportunidade).
- Encaixe nos pilares: **foco no humano** (ocupação e deslocamento do operador), **resiliência** (produção perdida por troca e falhas) e **sustentabilidade** (energia e consumo de capas).

**Recomendação:** implementar o caminho 2 agora (fontes A, matemático, ligado à IC) e, em paralelo, pesquisar a literatura de manutenção oportunista para fechar o desenho do caminho 1 antes de decidir.
