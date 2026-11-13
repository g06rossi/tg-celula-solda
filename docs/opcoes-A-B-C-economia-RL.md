# Opções A, B e C: o que dá conteúdo à decisão de economia de energia (e ao RL)

Documento de decisão, 2026-11-13. Base: v7 (mix sorteado, 100,52 kWh, 0,2306 kWh/carroceria, robôs ~77% parados) e o teste do mecanismo de economia no R1 (`EnergyTargetState` Off/Operational funciona; −8,2 kWh no R1).

Confiabilidade das fontes: **A** = documento lido por nós; **B** = lido só pelo resumo ou por citação; **C** = indicativo (comercial ou trecho de busca).

---

## 0. Por que precisamos de A, B ou C

Hoje as carrocerias chegam a cada 132 s exatos e cada robô fica ~100 s parado entre elas. A regra "dormir quando todos voltam ao home e acordar quando a carroceria chega" já é ótima, porque:
1. o próximo evento é perfeitamente previsível;
2. acordar (freios) custa ~0,06 kWh por turno e atrasa o robô 2 s, que cabem nos ~100 s de folga.

Um problema de decisão só existe quando a política simples erra em alguma situação. Isso exige **incerteza** (não se sabe quanto tempo o robô vai ficar parado) **e** um **custo de errar** (acordar tarde atrasa a linha, acordar cedo gasta energia, e o modo mais econômico demora mais para voltar). A literatura de controle energético de máquinas trata exatamente disso (Frigerio e Matta, 2015; Loffredo et al., 2023–2024; Bukata et al., 2017).

**Importante:** A sozinha **não basta**. Mesmo com chegadas aleatórias, se o único modo de economia for o de freios (retomada de 2 s), acordar ao chegar a carroceria continua quase sem custo, e a regra simples continua ótima. O conflito de verdade aparece quando a incerteza (A, C) encontra um modo que demora para voltar (B).

---

## Opção A: chegadas incertas (paradas antes da célula)

### O que é
Hoje o `ENTRADA_BIY` entrega uma carroceria a cada 132 s. Numa linha real, a estação anterior para por falta de material, falhas ou ajustes, e a carroceria seguinte atrasa. Durante essas paradas, a nossa célula fica ociosa por um tempo **desconhecido** no momento em que ela começa.

### Referências
| Fonte | O que dá | Conf. |
|---|---|---|
| PI (PROFIBUS & PROFINET International). *Assessing PROFIenergy's potential*, white paper v1.0, nov. 2011. PDF em `z_references/` | Medições de 7 dias, a cada 1 s, em células de carroceria da **Daimler (Sindelfingen)** e da **VW Veículos Comerciais (Hanôver)**: numa fábrica de carrocerias com 2 turnos, **47% da energia é consumida em períodos ociosos**; as paradas são planejadas, não planejadas (falta de material, quebras) ou dependentes do produto (ex.: o robô espera um hatch passar até chegar um sedan); **64% do tempo ocioso está em paradas de 5 min ou mais**; "é consenso" que só paradas ≥ 5 min valem a pena para modos de economia; robôs parados consomem até 300 W não produtivos | A |
| Frigerio, N.; Matta, A. *Energy-efficient control strategies for machine tools with stochastic arrivals.* IEEE Trans. Automation Science and Engineering 12(1), 50–61, 2015. DOI 10.1109/TASE.2014.2344507 | Arcabouço de políticas para **desligar a máquina quando a produção não é crítica e religar quando o fluxo de peças volta**, com chegadas aleatórias; dá **analiticamente** os parâmetros ótimos (limiares de tempo) para distribuições gerais | B |
| Alaka, H. T. O. et al. *Developing reliability centered maintenance in automotive robotic welding machines for a tier 1 supplier.* Frontiers in Robotics and AI 12:1620370, 2025. DOI 10.3389/frobt.2025.1620370 | Célula robótica de solda automotiva real com **disponibilidade de 70–72%** (alvo de 97%), 2 turnos de 12 h. Mostra que paradas são frequentes em células reais | A (parcial: lido o texto, sem tabelas numéricas de MTBF/MTTR) |

### Como implementar no Plant
- **Paradas a montante** no `ENTRADA_BIY`, pela aba **Failures** (existe no Source, conforme o print). Uma falha do Source interrompe a criação de carrocerias durante o reparo, que é exatamente uma parada da estação anterior. Parâmetros: disponibilidade e MTTR, com distribuições (ex.: exponencial para o tempo entre paradas). **A semântica exata da aba Failures no Source ainda não foi testada** e deve ser confirmada no Plant.
- Alternativa mais simples: deixar o **Interval** com uma distribuição em vez de "Const 2:12" (o campo tem dropdown de distribuições). Isso dá variação de takt, mas não as paradas longas que o white paper descreve. Por isso a aba Failures é a melhor representação.
- O `def_inPosition` já reage à chegada (acorda o robô). Nada muda na lógica de solda.
- A variante aleatória (`RandomNumbersVariant`) já é trocada por réplica no `EndSim`, então as paradas passam a ser diferentes em cada réplica.

### Parâmetros que faltam
Disponibilidade e MTTR da estação anterior. **Não há fonte específica para esta célula.** Proposta: (i) calibrar a distribuição de paradas para reproduzir o perfil do white paper (47% de energia ociosa, 64% do tempo ocioso em paradas ≥ 5 min); (ii) usar a disponibilidade de Alaka et al. (70–72%) como cenário "pessimista"; (iii) análise de sensibilidade.

---

## Opção B: modo de economia profundo, com retomada lenta

### O que é
Além dos **freios acionados** (0,17 kW, retomada rápida), os controladores industriais têm modos mais profundos: **motores/servos desligados** e **barramento ou I/O desligados**. Esses modos economizam mais, mas demoram mais para voltar a operar. A decisão passa a ser: **se a parada for longa, vale o modo profundo; se a carroceria chegar antes do previsto, a retomada lenta atrasa a linha.**

### Referências
| Fonte | O que dá | Conf. |
|---|---|---|
| Bukata, L.; Šůcha, P.; Hanzálek, Z.; Burget, P. *Energy Optimization of Robotic Cells.* IEEE Trans. Industrial Informatics 13 (2017) 92–102. PDF em `z_references/` | Célula real da **Škoda** (solda/colagem, 6 robôs): só **freios** e **bus power-off** são aplicáveis entre ciclos, porque modos mais profundos têm transição longa demais; o bus power-off exige interação com o controlador superior; os modos de economia rendem **2,4% com ciclo de 56 s, 6,8% com 70 s e 12% com 80 s** (quanto mais folga, mais ganho) | A |
| PI (2011), white paper PROFIenergy (acima) | Comandos padronizados `Start_Pause`/`End_Pause`/`Query_Modes`; o dispositivo informa os modos suportados e seus tempos; a transição para economia é apropriada para paradas ≥ 5 min; um transportador pode precisar de 30 s de desaceleração antes de o robô dormir | A |
| **KUKA Roboter GmbH. *Controller Option KR C4 PROFINET 2.2* (KUKA System Software 8.2 / VW System Software 8.2), versão V5, 08/05/2012, seção 5.6.2.3, p. 24–25. PDF em `z_references/`** | **Substitui o manual ABB (inacessível).** Estados PROFIenergy do controlador: *Ready_To_Operate*; ***Drive bus OFF*** (acionamentos desligados): entrar = **5 s**, permanência mínima = 0 s, **voltar a operar = 20 s**; ***Hibernate*** (controlador em repouso, só responde ao Wake-on-LAN): entrar = **50 s**, permanência mínima = **10 s**, **voltar a operar = 50 s** (valores padrão, configuráveis) | A |
| ABB. *Application manual – PROFIenergy device* (RobotWare 6), 3HAC050967 | Segundo um trecho de busca: freios ≥ 20 s, motores desligados ≥ 2 min, I/O desligado ≥ 10 min. **Acesso negado também ao usuário (2026-11-13): não usar como fonte.** Citar no máximo como "o ABB IRC5 também implementa PROFIenergy" | C |
| Yokogawa / KUKA Systems (notícia técnica: *Yokogawa's precision power scope helps KUKA Systems minimise the energy consumption of industrial robots*) | Medição com o analisador PX8000: robô parado ~700 W, cai para ~200 W após 20 s parado; em hibernação, ~18 W para controle, inversor e robô | C |
| ABB. *Product specification IRB 6700*, 3HAC044265-001 rev. N (2019) | Freios acionados = 0,17 kW; freios liberados = 0,84 kW (já em uso) | A |

### Como implementar no Plant
O Plant tem só 5 estados de energia (Working, Operational, Standby, Off, Failed), e hoje o **Standby está ocupado pela solda**. Para ter dois modos de economia, é preciso liberar o Standby:
1. **Solda passa a usar o Operational:** mudar `EnergyPauseStartState` de "Standby" para "Operational" (o atributo existe, conforme o `listar_attrs`). Assim o `startPause` continua segurando o robô 1,6 s, mas a 0,84 kW. A energia do arco (~3,75 kW × 1,6 s = 6 kJ por ponto) passa a ser **somada no Python** pela contagem de soldas, que já sabemos medir (tempo em pausa ÷ 1,6 s). **Precisa de teste:** confirmar que o atributo aceita escrita e que o tempo de pausa continua mensurável.
2. **Standby = freios acionados** (0,17 kW; Standby→Operational = tempo curto, ex.: 0,2–2 s).
3. **Off = hibernação** (controlador em repouso): **Off→Operational = 50 s**, Operational→Off = 50 s e permanência mínima de 10 s (KUKA KR C4, valores padrão); potência **~0,02 kW** (Yokogawa/KUKA, conf. C → análise de sensibilidade).
   - Interpretação dos modos para o IRB 6700: o "freios acionados" da spec ABB (0,17 kW) corresponde a robô parado com os servos desligados, ou seja, ao *Drive bus OFF* do KUKA. Então **Standby = freios/acionamentos desligados, 0,17 kW (ABB, A), retomada de 0,2–20 s** (20 s = padrão do *Drive bus OFF* KUKA, o pior caso; o limite inferior é o tempo de soltura dos freios). **O tempo real de retomada do IRC5 não tem fonte A**: usar 20 s como cenário conservador e 2 s como otimista, com sensibilidade.
   - Isso dá um trade-off real: o Standby economiza 0,67 kW e volta em segundos; a hibernação economiza ~0,82 kW, mas exige ~100 s entre entrar e sair (50 + 50), que é quase toda a janela ociosa normal (~100 s). Ou seja, só compensa em paradas longas, e errar custa até 50 s de atraso na linha.
4. Comando: `EnergyTargetState := "Standby"` / `"Off"` / `"Operational"`, já validado para o Off.

### Parâmetros que faltam
- **Tempos de transição:** cobertos pelo manual KUKA KR C4 (fonte A, mas de outro fabricante; justificar no texto como "valores padrão de um controlador automotivo que implementa o mesmo perfil PROFIenergy"; o IRC5 da ABB também implementa PROFIenergy).
- **Potência na hibernação:** só fonte C (~18 W) → sensibilidade (ex.: 0,02–0,10 kW).
- **Tempo de retomada do Standby no IRC5:** sem fonte A → sensibilidade de 0,2 a 20 s.

---

## Opção C: falhas nos robôs e operador

### O que é
Quando um robô falha, a carroceria fica parada na célula até o reparo, e os outros 3 robôs ficam ociosos por um tempo incerto (o MTTR). Se o reparo depende de um **operador** que também faz a troca das capas dos eletrodos, o tempo de parada depende de onde ele está. Isso cria janelas ociosas longas e imprevisíveis **dentro** da célula, e liga os pilares de **resiliência** (queda e recuperação do throughput) e **foco no humano** (ocupação do operador).

### Referências
| Fonte | O que dá | Conf. |
|---|---|---|
| Alaka et al. (2025), acima | Célula robótica de solda automotiva: disponibilidade 70–72%; principais causas de parada: falha de água, **troca/retífica de capas (tip dressing)**, falha de grampo, cortina de luz, **robô travado**, sensor de peça, solda fraca. Manutenção = 79% do tempo parado | A (parcial) / B (contagens de falhas lidas só pelo resumo) |
| Comissão Europeia (2021). *Industry 5.0: Towards a sustainable, human-centric and resilient European industry* | Enquadramento dos pilares de resiliência e foco no humano | (já no plano) |
| Loffredo, A.; Matta, A. et al. *Reinforcement learning for sustainability enhancement of production lines.* Journal of Intelligent Manufacturing 35(8), 2024 | RL para controle energético de linhas, **sem conhecer toda a dinâmica do sistema**, testado com dados de uma **linha automotiva real**; os estados das máquinas incluem standby, partida, trabalhando e **falha** | B |
| MTBF "médio" de robô industrial ≈ 40.000 h (artigo de oficina de solda, derivado de especificação de fabricante) | Ordem de grandeza só do **braço**; com isso quase não haveria falha em 16 h. As paradas reais vêm da célula (água, grampos, capas, sensores), não do braço | C |

### Como implementar no Plant
- **Falhas dos robôs:** aba **Failures** de cada `ABB_IRB_6700_*` (disponibilidade, MTTR, distribuições). O estado de energia vira **Failed** (potência a definir; robô parado com controlador ligado ≈ freios acionados ou liberados).
- **Operador:** objetos **Worker**, **WorkerPool**, **Broker** e **FootPath** (já previstos no plano, item 8). O reparo passa a exigir o operador (o MTTR depende de ele estar livre), e a cada N soldas o robô para para trocar ou retificar as capas, também com o operador.
- **Resiliência:** medir a queda e a recuperação do throughput depois de cada falha (o `coleta_plant.py` já amostra a cada 60 s).

### Parâmetros que faltam
Taxas de falha e MTTR da célula, tempo e intervalo de troca das capas, tempos do operador. **Sem fonte numérica ainda.** Alaka et al. dão a disponibilidade e as causas, não os tempos. Proposta: calibrar para a disponibilidade de 70–72% e fazer análise de sensibilidade; procurar dados de troca de capas (nº de soldas entre dressings) em literatura de solda a ponto.

---

## Parte Python: otimização e aprendizado

### Políticas a comparar (item 13 do plano)
| Política | Como decide | Implementação |
|---|---|---|
| (a) Sem economia | Nunca dorme | v7 atual |
| (b) Regra fixa | Dorme sempre que todos voltam ao home (freios); acorda na chegada | já validada no R1 |
| (c) Timeout ótimo | Dorme após τ s parado; com B, escolhe o modo pelo tempo parado (τ₁ freios, τ₂ profundo) | τ otimizado por busca em grade sobre réplicas (Python fora do Plant, ou ExperimentManager). Referência teórica: Frigerio e Matta (2015) dão os limiares ótimos para chegadas aleatórias, então dá para comparar o τ simulado com o analítico |
| (d) RL (PPO) | Decide a cada momento de decisão (fim do ciclo, ou a cada X s parado): {ficar ligado, freios, profundo, acordar} | stable-baselines3 |

### RL: formulação
- **Momento de decisão:** quando um robô termina o ciclo e volta ao home, e periodicamente enquanto ele estiver parado (ex.: a cada 10 s), para permitir "esperar e decidir depois".
- **Estado (observação):** tempo desde a última chegada; estado da estação anterior (parada/rodando, se o modelo expuser, o que é realista no PROFIenergy, em que o controlador superior conhece o estado da linha); há quanto tempo ela está parada; modelo da próxima carroceria; estado de energia atual de cada robô; robô em falha (C); operador ocupado (C).
- **Ação:** por robô, {Operational, Standby (freios), Off (profundo)}.
- **Recompensa:** −(energia no intervalo) − λ × (atraso causado à linha), em que o atraso é o tempo em que a carroceria esperou um robô acordar. λ define o trade-off energia × produtividade; varrer λ dá a **fronteira de Pareto**.
- **Integração com o Plant (o risco técnico):** o Plant chama o Python a cada decisão (`PythonModule.call("decidir", [estado])`), mas o SB3 espera chamar `env.step()`. Plano em duas etapas:
  1. **Protótipo com política aleatória:** só a chamada `decidir` → ação → `EnergyTargetState`, gravando (estado, ação, recompensa) em memória. Valida o laço sem aprendizado.
  2. **Aprendizado:** o SB3 roda numa thread do próprio PythonModule e conversa com a simulação por filas (o `decidir` põe a observação numa fila e espera a ação na outra). Se o Plant não tolerar threads, a alternativa é um laço próprio: coleta-se o episódio inteiro com a política atual e atualiza-se a rede no `EndSim` (PPO por episódio), usando torch diretamente. A terceira opção (controlar o Plant por COM, de fora) fica como reserva.
- **Treino e teste:** treinar com variantes aleatórias 1…N e **testar em variantes nunca vistas** (o que mede generalização). Cada episódio de 16 h roda em menos de 15 s, então ~1.000 episódios levam ~4 h.

---

## Análise e comparação dos dados

Tudo sai do pipeline atual (`coleta_plant.py` → JSON → `gerar_relatorio.py`), com algumas extensões.

1. **Desenho experimental:** cenários (normal; com paradas a montante; com falhas e operador; mix alto de sedan) × políticas (a, b, c, d) × **10–30 réplicas**. Para a **mesma réplica**, usar a **mesma variante aleatória** em todas as políticas (números aleatórios comuns): as políticas enfrentam exatamente as mesmas paradas, e a diferença entre elas fica muito mais precisa.
2. **KPIs** (já no relatório, mais os novos):
   - sustentabilidade: **kWh/carroceria** (principal), kWh por estado, nº de retomadas;
   - produtividade: throughput e **atraso causado à linha** (novo);
   - resiliência (C): queda e tempo de recuperação do throughput depois de cada falha (novo, pela série de 60 s);
   - foco no humano (C): ocupação e deslocamento do operador (novo).
3. **Estatística:**
   - média ± IC 95% (t de Student), já no relatório;
   - **diferença pareada** entre políticas na mesma variante, com IC 95% (novo);
   - **fronteira de Pareto** energia × atraso, varrendo λ do RL e τ do timeout (novo);
   - **análise de sensibilidade** dos parâmetros sem fonte A: energia por ponto (5–11 kJ), tempo e potência do modo profundo, parâmetros das paradas e das falhas, tempos de movimento (K1 ↔ regra de Cho).
4. **RL:** curva de aprendizado (recompensa por episódio), desempenho em variantes de teste contra o timeout ótimo e a regra fixa. **Se o RL empatar com o timeout ótimo, isso também é um resultado válido**: mostra que a política clássica já é suficiente naquele cenário, como Loffredo et al. comparam o RL com a solução ótima do MDP.

---

## Resumo para decidir a ordem
| | Cria incerteza? | Cria custo de errar? | Fontes | Esforço no Plant |
|---|---|---|---|---|
| **A** | sim (paradas a montante) | só com B | boas para o perfil (PI 2011), fracas para os números da célula | baixo (aba Failures do Source) |
| **B** | não sozinha | sim (retomada lenta) | boas: Bukata 2017, PI 2011 e **tempos do KUKA KR C4 (A)**; potência da hibernação só C | médio (liberar o Standby: solda no Operational + energia no Python) |
| **C** | sim (falhas, operador) | sim, com B | fracas para os números | alto (Failures + Worker/Broker/FootPath) |

**Sugestão:** B → A → C. B é a peça que cria o trade-off e não depende de dados de falha; A aproveita o mesmo mecanismo e tem a melhor fonte de contexto (medições reais da Daimler e da VW); C fecha os pilares de resiliência e foco no humano e é a mais trabalhosa.
