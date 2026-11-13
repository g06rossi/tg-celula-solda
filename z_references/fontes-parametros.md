# Fontes dos parâmetros de energia (pesquisa de 2026-11-09)

Objetivo: dar fonte às potências que a Fase 0 (item 3) e a Fase 1 (standby) precisam: robô ocioso, robô em standby, custo de retomada e energia real por ponto de solda.

Confiabilidade: **A** = documento do fabricante ou artigo revisado com o texto lido; **B** = artigo revisado, mas lido só por resumo ou citação; **C** = fonte comercial ou de fórum (só indicativo).

## 1. Robô ABB IRB 6700-205/2.80 com controlador IRC5

| Parâmetro | Valor | Fonte | Conf. |
|---|---|---|---|
| Potência em movimento, ISO Cube, velocidade máx., carga máx. | **2,6 kW** | ABB, *Product specification IRB 6700*, 3HAC044265-001, rev. N (2019), p. 15, tabela "Power consumption at max load" | A |
| Robô parado, **freios liberados** (servo ligado, segurando a pose), na posição de calibração | **0,84 kW** | idem | A |
| Robô parado, **freios acionados** | **0,17 kW** | idem | A |
| Potência "nominal" usada na IC (Working) | 2,85 kW | ABB, brochura IRB 6700 (2014): "2.85 kW, ISO cube"; a rev. N dá 2,6 kW para a 205/2.80 | A (divergência entre documentos) |

Arquivo: `abb_irb6700_product-spec_3HAC044265-001_revN_2019.pdf` (cópia de terceiro; conferir a revisão mais recente na biblioteca ABB). A rev. H acrescentou os valores com freios acionados e liberados.

**Leitura para o modelo:**
- *Operational* (ocioso, pronto para mover) = **0,84 kW**, não 0 kW como na IC.
- Um estado de economia (freios acionados) = **0,17 kW** é suportado pelo fabricante. A economia é de **0,67 kW por robô parado**.
- A potência em movimento a 2,6–2,85 kW vale para velocidade máxima e carga máxima. Com a V do modelo (0,06–0,08 m/s), ela está superestimada. Revisar junto com o item 2 da Fase 0.

## 2. Modos de economia e custo de retomada

| Item | Valor | Fonte | Conf. |
|---|---|---|---|
| Modos aplicáveis entre ciclos | Só **freios** e **bus power-off**. Hibernação e similares têm transição longa demais | Bukata, Šůcha, Hanzálek, Burget. *Energy Optimization of Robotic Cells*. IEEE Trans. Ind. Informatics 13 (2017) 92–102, DOI 10.1109/TII.2016.2626472 (arXiv 1802.05925) | A |
| Economia dos modos numa célula real de solda (Škoda, 6 robôs, ciclo de 56 s) | **2,4%**; com ciclo de 70 s, **6,8%**; com 80 s, **12%** | idem, seção VI | A |
| Faixa de potência de um robô de 6 eixos com 200 kg | 0,5 a 20 kW | Meike & Ribickis (2011), *Energy efficient use of robotics in the automobile industry*, ICAR, citado em Bukata (2017) | B |
| Vida útil dos freios | 5 milhões de ciclos (limita o uso frequente) | Bukata (2017), Introdução | A |
| Economia na célula com gestão de freios (4 robôs de 210 kg, solda a ponto) | 7,3% na célula, 12,1% num robô | Meike, Pellicciari, Berselli et al. (2012), citado em Bukata (2017) | B |
| Tempo de soltura do freio | ~50–200 ms | base de conhecimento comercial (Industrial Monitor Direct) | C |
| Parada automática por inatividade | Fanuc: 30 s (padrão); ABB "Brake on time": 120 s (sugerido) | fóruns e bases comerciais | C |
| KUKA: 700 W parado → 200 W após 20 s | — | artigo comercial (ien.eu) | C |

**Atualização (2026-11-13), modos profundos:** KUKA Roboter, *Controller Option KR C4 PROFINET 2.2* (VW System Software 8.2), 2012, seção 5.6.2.3 (PDF `kuka_krc4_profinet-2.2_2012_profienergy.pdf`, conf. A): *Drive bus OFF* entra em 5 s e volta em **20 s**; *Hibernate* entra em 50 s, fica no mínimo 10 s e volta em **50 s** (padrões configuráveis). Potência em hibernação ~18 W (Yokogawa/KUKA Systems, conf. C). O manual ABB 3HAC050967 ficou inacessível (acesso negado também ao usuário).

**Lacuna:** não há fonte A para o **tempo e a energia de retomada** de um IRC5. Proposta: tratar como parâmetro de **análise de sensibilidade** (Fase 4, item 16), por exemplo de 0,2 a 2 s, com energia de transição desprezível ou igual à potência ociosa vezes o tempo, deixando isso explícito no texto como hipótese.

## 3. Energia por ponto de solda a resistência

### 3.1 O que o datasheet da GWT C9 diz de fato (verificado em 2026-11-09)

| Documento | Texto | Arquivo |
|---|---|---|
| ABB, *GWT C9 Electrically Driven Servo Weld Gun*, flyer 9AKK107680A4035 rev. B (out/2022) | "Transformer MFDC 90 kVA"; "Welding transformer MFDC … Frequency 1,000–1,200 Hz; **Power (S50) 90 kVA**" | `abb_gwt-c9_flyer_9AKK107680A4035_revB_2022.pdf` |
| ABB, *GWT X9 & C9 – Next generation electrically driven servo weld guns*, apresentação 9AKK108468A1525 rev. A (jun/2023), slide 18 (o nome do arquivo na biblioteca ABB contém 9AKK108468A2518, o ID citado pela IC) | "Transformer MFDC **90 kVA (50%)**"; "Power (S50) 90 kVA" | `abb_gwt-x9-c9_presentation_9AKK108468A1525_revA_2023.pdf` |

Leitura:
- **90 kVA é a potência nominal (térmica) do transformador de solda a 50% de fator de serviço (S50)**, não o consumo da pinça. É potência **aparente** (kVA), não ativa (kW).
- S50 = o transformador aguenta fornecer 90 kVA durante 50% de um período de referência sem superaquecer. É um limite de projeto e dimensionamento, não o que ele puxa a cada ponto.
- A IC leu "90 kVA" como "consumo nominal 90 kW" e aplicou o valor durante os 1,6 s inteiros. **O número está certo; a interpretação e o uso, não.**
- O flyer troca primário e secundário ("Primary voltage 11.1 V / Secondary voltage 600 V"). Pela física e pela apresentação de 2023, o certo é **primário 600 V, secundário 11,1 V** (em vazio).
- O datasheet **não dá energia por ponto**: ela depende de chapa, corrente e tempo de solda, que são parâmetros do processo e não da pinça.

### 3.2 Energia por ponto (literatura)

| Item | Valor | Fonte | Conf. |
|---|---|---|---|
| Energia **primária** (da rede) por ponto, aço galvanizado de 1,2 mm, 9,5–11,5 kA | **AC: 4,7–7,3 kJ; MFDC: 4,7–6,4 kJ** | Li, Feng, Cerjanec, Grzadzinski. *Energy consumption in AC and MFDC resistance spot welding*. Sheet Metal Welding Conference XI, 2004 (Univ. of Washington, WTC, DaimlerChrysler), Tab. 1 | A |
| Energia secundária (que vai para a peça) | 1,0–2,3 kJ | idem | A |
| ~2 Wh (7,2 kJ) por ponto no melhor ajuste, "33% abaixo da média estimada do setor automotivo" (≈ 3 Wh ≈ 10,8 kJ) | — | *A new approach to reduce the carbon footprint in RSW by energy efficiency evaluation*, Int. J. Adv. Manuf. Technol. (2022), DOI 10.1007/s00170-021-08472-7 (lido só pelo resumo) | B |
| Potência de pico de uma soldadora a ponto durante a solda | 100–200 kW | Weldtech, *Sizing the primary power system for resistance welders*, SMWC 2004 | B |
| Duração da corrente de solda | ~10–100 ms (curto em relação ao ciclo da pinça) | Wikipedia "Spot welding" | C |

**Leitura para o modelo:** a IC usa 90 kW durante os 1,6 s inteiros, ou seja, **144 kJ por ponto**. A literatura dá **5–11 kJ por ponto** na rede. **O modelo superestima a solda em ~13–30×.** Os 1,6 s são o ciclo da pinça (fechar, soldar, manter, abrir), e a corrente circula só numa fração dele. Os 90 kW são potência de pico ou nominal, não média.

## 4. Impacto estimado na baseline (v3, R1, 16 h)

| Parcela | Hoje (IC) | Com as fontes acima |
|---|---|---|
| Solda (3.924 pontos) | 157,0 kWh (90 kW × 1,6 s) | ~6,5 kWh (6 kJ/ponto; faixa 5,1–11,8) |
| Ocioso (4,80 h) | 0 kWh | 4,0 kWh (0,84 kW) |
| Movimento (9,45 h) | 26,9 kWh | 24,6–26,9 kWh (a revisar com a V realista) |
| **Total do robô** | **183,9 kWh** | **~35–38 kWh** |
| Potencial do standby com freios (0,67 kW × 4,80 h) | 0 | **~3,2 kWh/robô (~9%)** |

Conclusão: com as fontes, a solda deixa de dominar (85% → ~18%) e o robô parado passa a pesar. Com a V realista do item 2 (mais tempo ocioso), o potencial do standby cresce ainda mais. O resultado é coerente com Bukata (2017): o ganho dos modos de economia aumenta quando sobra tempo no ciclo.
