# Revisão do relatório preliminar (`v_relatorios/preliminar_tg2.pdf`)

2026-11-25. Objetivo: verificar se o texto está correto até onde foi escrito e listar o que falta para apresentar ao orientador um **ponto de estabilidade do projeto até a otimização do pico de solda (caminho 2)**.

Legenda: ✅ correto · ⚠️ ajustar · ❌ incorreto ou desatualizado · ➕ falta.

---

## 1. Visão geral

O texto está bem escrito e a parte de **revisão do modelo herdado** (seções 2.2 e 2.3) está quase toda correta. Os problemas são de três tipos:

1. **O texto está desatualizado em relação às decisões do projeto.** Ele ainda trata a sequência ótima de pontos (cortada em 25/11) como objetivo e hipótese (H4) e põe o RL na decisão dos modos de economia, que os resultados mostraram ter margem de ~1%. E **não menciona o caminho 2** (pico de solda) como objetivo, embora ele já esteja concluído.
2. **Falta o capítulo de resultados.** Tudo o que foi medido (v1 a v16) ainda não está no texto.
3. **Partes de modelo descritas como feitas ainda não existem** (falhas dos robôs, operador, tempos com distribuição).

Há também erros pontuais de fato, numeração e referências.

---

## 2. Erros de fato (corrigir)

| Seção | Texto atual | Correção |
|---|---|---|
| 1.1 | "célula robótica existente da Skoda Auto, onde contava com **12 robôs**" | ❌ A célula da Škoda tinha **6 robôs** (o "12" é o tamanho máximo das instâncias de teste da heurística). Bukata et al. (2017), seção VI: "welded, glued, and assembled by 6 industrial robots with a robot cycle time of 56 seconds". |
| 2.5.1 | "O mesmo estudo **mediu**, em uma célula real, [...] 6,8% em um ciclo de 70 s e 12% com 80 s" | ⚠️ Foi **estimado** por otimização, não medido ("it was estimated..."; "would improve the consumption by about 6.8 % and 12 %"). |
| 2.2.4, Tabela 2 | "ABB GWT C9 — Consumo Nominal 90 kW" | ⚠️ O datasheet diz **90 kVA (S50)**, potência do transformador a 50% de fator de serviço, não consumo. Como a tabela reproduz a IC, marcar: "90 kVA (S50), lido como consumo na IC; ver 2.3.2". |
| 2.2.4 | "o comando **StarPulse**, do SimTalk" | ❌ É **`startPause`**. |
| 2.3.2 | "PROFlenergy" | ❌ **PROFIenergy**. |
| 2.3.2 | "0,15 s, o qual é o **tempo máximo** de liberação dos freios do IRC5" | ⚠️ É o **valor padrão** do parâmetro *Max Brake Release Time* (faixa de 0 a 2 s) (ABB, 3HAC050948-001 rev. AD, seção 6.7.11). |
| 2.3.2 | "A potência em hibernação é cerca de 0,02 kW." | ⚠️ Falta a fonte, que é fraca (notícia técnica Yokogawa/KUKA Systems, ~18 W). Declarar como hipótese com sensibilidade (0,02–0,10 kW). |
| 2.3.2 | "mesmo quatro pinças soldando juntas elevariam essa média em menos de 1 kW" | ⚠️ Raciocínio confuso: **soldar junto ou separado não altera a média de 15 min** (a energia é a mesma). Reescrever: "a simultaneidade não altera a demanda faturada; o pico que importa é o instantâneo, para dimensionar a alimentação". |
| 2.3.4 | "Alaska et al. (2025)" | ❌ **Alaka** et al. (2025). |
| 2.3.4 | Disponibilidade de 85% "baseada em" Alaka (70–72%) | ⚠️ Deixar claro: 85% é o cenário **central** (hipótese); 72% (Alaka) entra como pior caso na sensibilidade. |
| 2.2.1 | "A célula não existe fisicamente, de modo que **os parâmetros** são hipóteses de projeto." | ⚠️ Generaliza demais: produção, mix, geometria e tempo de solda vêm da FMEIB. Só os **componentes e parâmetros sem dado da FMEIB** (controlador, potências por estado, modos de economia, paradas) são hipóteses de projeto. |
| 1.1 | "Em 2025, o consumo final de energia elétrica no país foi de 667,8 TWh" (EPE, 2025) | ⚠️ Conferir o ano de referência: publicações da EPE de 2025 trazem em geral dados de **2024**. "Cenário Energia (2026)" é fonte jornalística; preferir a ANEEL. |
| 1.2 | "O Plant Simulation é **comumente** utilizado como ferramenta de RL, conectado a Python por COM (Müller, 2025)" | ⚠️ Um único trabalho não sustenta o "comumente". E este projeto usa o **PythonModule**, não o COM; explicar a diferença. |
| 2.4.1 | Bangsow (**2016**) | ⚠️ A IC cita a 2ª edição, de **2020** (Springer Nature). Unificar. |
| 2.3.3 | "considerá-se" | ❌ "considera-se". |
| 2.5.3 | "as decisões ocorrem as decisões seguem" | ❌ Frase duplicada. |

**Numeração:** há duas "Tabela 2" (2.2.4 e 2.7), e em 2.3.2 o texto diz "A Tabela 1 compara..." quando a tabela é a **5**. As equações (1) e (2) saíram ilegíveis no PDF (verificar a renderização). A Tabela 4 deveria mostrar também os **50 s de entrada** da hibernação, não só a retomada.

---

## 3. Desatualizado em relação às decisões do projeto

| Onde | Problema | O que fazer |
|---|---|---|
| 1.3 (Problemática), 1.4, 1.5, 2.1, **2.3.5**, 2.6, H4 | A **sequência ótima de pontos** aparece como objetivo, hipótese (H4) e seção de método. | ❌ **Cortada em 25/11:** a sequência e a distribuição dos pontos seguem o **padrão de processo da célula da FMEIB**. Remover H4, o objetivo específico, a seção 2.3.5 e o "DEFINIR" da 2.6 (fica: sequência original). Uma frase de escopo basta. |
| 1.3, H1, 2.5.3 | O RL decide os **modos de economia**, e a tese é que o timeout "deixa de ser viável" com incerteza. | ❌ Os resultados (v11) mostram que a regra fixa de freios já captura quase tudo: `timeout` = `freios`, e o **oráculo** da hibernação ganha só **1,04% ± 0,25%**. O RL foi **redirecionado para a manutenção oportunista** (caminho 1). Reescrever H1 e a 2.5.3 nesse sentido. Este achado é um resultado do TCC, não um problema. |
| Objetivos, hipóteses, 2.3.2, 2.7 | O **caminho 2** (pico de solda) só aparece como discussão na 2.3.2. | ➕ Incluir como objetivo específico e hipótese (ex.: "limitar as soldas simultâneas reduz o pico de dimensionamento sem perda de produção, e o escalonamento otimizado reduz o custo de energia do intertravamento") e criar a seção de método (substitui a 2.3.5). |
| 2.7, Tabela "2" | Pico de potência = "maior potência média em uma janela de integração declarada". | ❌ O indicador usado é o **pico instantâneo de solda**: K soldas simultâneas × 90 kVA (dimensionamento, Farrow 2004). A média de 15 min (ANEEL) é outro indicador e não muda. |
| 2.3.4 | Tempos com distribuição, falhas dos robôs (MTBF/MTTR) e operador descritos como parte do modelo. | ⚠️ **Não implementados ainda.** Implementados: mix sorteado (v7) e paradas da estação anterior (v10). Escrever como "a implementar" (operador e falhas = caminho 1). |
| 2.5.2 | Timeout ótimo por busca em grade, com τ₁ (freios) e τ₂ (hibernação). | ⚠️ Feito só o τ = 300 s para hibernação (= `freios`). A busca em grade continua a fazer, mas o resultado já esperado é "regra fixa ≈ ótimo" (oráculo de 1%). |
| 2.4.1 | Ferramentas | ➕ Acrescentar o **OR-Tools (CP-SAT)**, rodando em Python 3.13 fora do Plant, usado no caminho 2; e a arquitetura que já funciona (o Plant chama o Python nos eventos e o Python comanda os robôs). |
| 2.1 | "Segundo, o modelo é estendido com tempos variáveis, sorteio do mix, falhas e um operador" | ⚠️ Atualizar para o que foi feito e o que falta. |

---

## 4. O que está correto (manter)

- Contexto do IRB 6700 com 2,6 / 0,84 / 0,17 kW (ABB, 2019) e a razão de ~1/3 (0,84 ÷ 2,6 = 32%).
- Produção 437 (279 + 158), takt 57.600 ÷ 437 ≈ 132 s; 9 soldas por robô e 10 no R2 sedan (2.2.1).
- As quatro limitações do modelo herdado: velocidades de 0,06–0,08 m/s contra 1,6 m/s (20–25×); 52–65% em Working; solda pela potência nominal e ocioso nulo; R2 sedan; modelo determinístico.
- Geometria, convenção SAE J670 com o X invertido, P0 a 2.000 mm, distância em reta como limite inferior.
- Estrutura do modelo no Plant (Source/Drain como pontos de solda, P10 duplicado, as três rotinas SimTalk).
- Resultados da IC: 744,38 kWh, 52–65% / 24–37% / 10,91%, aderência de 99,006%.
- Energia por ponto (Li et al., 2004: 4,7–7,3 kJ; adotado 6 kJ → 3,75 kW; 4,59 kW total), 144 kJ ≈ 20–30× a faixa medida.
- Hibernação: 67 kJ a mais por transição, equilíbrio em ~450 s de Off, ou seja, pausas de ~9 min.
- Modelo cinemático (1), v = 1,0 m/s, a = 12 m/s², PSt = 0,17 s, c = 0,7287 s, calibração em 3,3 s/ponto (Cho et al., 2024, acurácia de 72%).
- Por que a falha não vai no Source (rajadas a cada ~9 s).
- Números aleatórios comuns (Law, 2015) na comparação de políticas.
- Indicadores de foco no humano como *proxies* (ocupação, deslocamento, pausas), sem medir esforço físico.

**Sugestão para 2.2.5:** acrescentar que o desvio de 3,4% do R2 na validação da IC é explicado pelo erro de lógica (158 sedans × 1,6 s × 90 kW = 6,32 kWh + ~0,3 kWh da carroceria 437 = 6,60 kWh, exatamente a diferença), ou seja, o "esperado" da IC estava certo e o modelo estava errado. É um bom argumento de rigor.

---

## 5. O que falta para o ponto de estabilidade (até o caminho 2)

### 5.1 Capítulo de resultados (o principal)
Todos os números estão em `CLAUDE.md` (seção 4.4 e histórico), `docs/caminho2-pico-resultados.md` e `scripts/resultados/`.

1. **Saneamento do modelo, versão a versão** (tabela única): v1 (IC, 744,4 kWh) → v3 (R2 sedan com 10 soldas: 750,7 kWh, bate com o "esperado" da IC) → v4 (potências com fonte: 154,7 kWh = previsão) → v5 (tempos do cenário H: robôs ~77% parados, mesma produção) → v6 (parada automática do skid: 100,5 kWh = 0,2306 kWh/carroceria) → v7 (mix sorteado: 100,52 ± 0,02 kWh). Para cada versão, o critério de validação (o que não podia mudar e não mudou).
2. **Primeiro resultado:** com tempos de movimento realistas, a ociosidade dos robôs passa de 24–37% para ~77% **sem mudar a produção** (o modelo calibrado pelo takt escondia a ociosidade).
3. **Cenário com paradas (v10):** 85,7% de disponibilidade efetiva, 0,2515 kWh/carroceria (+9% sobre a v7), 16,9% do tempo parado em pausas ≥ 9 min.
4. **Políticas de economia (v11, opção B):** `freios` −36,5% (0,1598 kWh/carroceria) sem perda de produção; `timeout` = `freios`; oráculo da hibernação +1,04% ± 0,25%. Conclusão: a regra simples basta; o RL não tem margem nessa decisão.
5. **Pico de solda (caminho 2):** linha de base (K_max = 4 sempre, 20,5% do tempo de solda com os 4 juntos); otimização CP-SAT (fronteira K × fim do ciclo × espera); validação v13 (reativo: +0,39% / +1,45% / +14,62%) e v16 (planejado K = 1: **+0,74%**, −12,1% contra o reativo, pico −75%).
6. **Validações de método:** modelo da linha do tempo fora do Plant com erro < 1%; comparações pareadas com IC 95%.

### 5.2 Ajustes de texto
- Reescrever problemática, hipóteses e objetivos: remover H4; H1 → RL na manutenção oportunista; acrescentar a hipótese do pico; manter H3 (já sustentada: a ociosidade passou de ~30% para ~77% e a economia acompanhou).
- Substituir a 2.3.5 (sequência) por **"Otimização do pico de solda"**: o problema (Farrow 2004; ANEEL), a formulação CP-SAT, o intertravamento reativo e o escalonamento planejado (política `plano`).
- Seção curta de **lições de implementação**: os `waituntil` do R1, o `wait` que não segura o PickAndPlace, a ordem da variante aleatória, a rajada do Source. Mostram o rigor da validação.
- **Próximos passos:** caminho 1 (operador, troca das capas, falhas) + RL; integração de treino; sensibilidade; revisão da literatura.

### 5.3 Referências
A lista atual está **incompleta** e tem entradas **não citadas**.
- **Citadas e ausentes da lista:** EPE (2025), Cenário Energia (2026), Donders et al. (2005), ABB (2019, 2023, 2026), Bukata et al. (2017), Xu et al. (2021), Mouzon, Yildirim e Twomey (2007), Loffredo et al. (2023, 2024), Loffredo, May e Matta (2023), Schmidl et al. (2020), Henderson et al. (2018), Paryanto et al. (2015), Li et al. (2004), Müller (2025), Rossi (2025), FMEIB (2025), SAE (2008), Cho, Kim e Park (2024), KUKA (2012), ANEEL (2021), Farrow (2004), Alaka et al. (2025), Bangsow, Law (2015), Sutton e Barto (2018), Schulman et al. (2017), Raffin et al. (2021).
- **Na lista e não citadas:** Florescu e Barabas (2020), Barak et al. (2021), Nahavandi (2019), Homayouni e Fontes (2025), Leng et al. (2026), ISO/TS 15066, Kritzinger et al. (2018). Citar ou remover.
- Os PDFs e dados de quase todas estão em `z_references/` e `CLAUDE.md` (seção 8).

### 5.4 Elementos ainda de modelo (template)
Resumo, abstract, palavras-chave, listas de figuras e tabelas, sumário (incompleto), considerações finais e apêndice A (tabelas da IC, citadas como "A.X") ainda são o texto do modelo da UFABC. **Figuras:** não há nenhuma real. Sugestões: leiaute da célula, linha do tempo das soldas com K = 4 contra K = 1, energia por estado em cada versão e a fronteira K × energia.

---

## 6. Prioridade sugerida para a reunião com o orientador
1. Capítulo de resultados (5.1), que é o que mostra a estabilidade.
2. Problemática, hipóteses e objetivos atualizados (sequência cortada, RL redirecionado, pico incluído).
3. Correções de fato (seção 2 deste documento).
4. Referências completas.
5. Resumo e figuras.
