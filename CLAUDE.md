# Contexto do projeto: TCC de Indústria 5.0 + IA em simulação de célula de solda a ponto

> Este arquivo explica o projeto, o que já foi validado, as armadilhas técnicas conhecidas e o plano de trabalho.
> Leia tudo antes de propor código ou alterações.
> **Mantenha este arquivo atualizado** (ver seção 0).

---

## 0. Manutenção deste arquivo (obrigatório)

- **Sempre que algo for desenvolvido, validado ou decidido no projeto, atualize este CLAUDE.md na mesma tarefa.** Isso vale para scripts novos ou alterados, resultados de testes no Plant, nomes de objetos e atributos confirmados, parâmetros com fonte, problemas resolvidos, itens do plano concluídos e mudanças de próximo passo.
- Corrija o que ficou desatualizado em vez de só acrescentar texto. Marque itens concluídos no plano (seção 6) com ✅ e a data.
- Atualize a seção 9 (próximo passo) ao fim de cada etapa.
- **`todo.txt`** (raiz) é a lista de tarefas, com a meta do projeto no topo. Ao concluir ou criar uma tarefa, marque `[x]` com a data, `[~]` para em andamento, ou acrescente o item novo na mesma tarefa.
- Registre em "Histórico" (seção 10) uma linha por mudança relevante: data, o que mudou e onde.

---

## 1. Como trabalhar

- **Responda sempre em português do Brasil**, num tom direto e informal. Seja honesto: se algo estiver errado, mal fundamentado ou arriscado, diga claramente, mesmo que contrarie o pedido.
- **O assistente não tem acesso ao Plant Simulation.** Quem executa no Plant é o usuário. Ele cola de volta saídas do Console, mensagens de erro e prints. Por isso:
  - entregue código **pronto para colar**, dizendo **onde** colar (PythonModule, qual Method SimTalk, terminal);
  - diga **o que o usuário deve ver** como resultado esperado;
  - quando não tiver certeza de um nome de atributo ou método do Plant, **diga isso** e proponha um teste de diagnóstico (por exemplo, listar com `dir()` no Python ou com Ctrl+Espaço no editor SimTalk). Nunca invente API do Plant.
- **Não invente parâmetros físicos** (potências, velocidades, MTBF/MTTR, tempos de operador). Todo número do modelo precisa de **fonte** (datasheet, artigo, medição). Se não houver fonte, marque como "a definir / hipótese" e avise.
- **Mudanças pequenas e verificáveis.** Um passo de cada vez, com teste. Antes de alterar lógica herdada da IC (Methods `def_*`), peça o código atual.
- **Antes de qualquer alteração no modelo**, lembre o usuário de salvar uma cópia versionada do `.spp` (`celula-solda-vN.spp`).
- **Código do PythonModule:** os arquivos em `scripts/` são a fonte de verdade, mas o Plant guarda uma cópia própria do código colado. Ao alterar um script que roda dentro do Plant, diga ao usuário exatamente o que colar ou substituir no PythonModule.

---

## 2. O projeto em uma frase

TCC de engenharia (UFABC) que parte de um modelo de **célula de solda a ponto automotiva** no **Siemens Tecnomatix Plant Simulation 2404**, herdado de uma Iniciação Científica, para estudar **otimização do consumo energético** usando **IA (aprendizado por reforço)** e os **três pilares da Indústria 5.0**: sustentabilidade, foco no humano e resiliência.

### Origem: a Iniciação Científica (IC)
- Título: *"Análise da Eficiência Energética de um Sistema Flexível de Manufatura (FMS) com uso de Simulação Computacional"*. Aluno: Giovanni Rossi. Orientador: Guilherme Canuto da Silva (UFABC), Edital 01/2024.
- A IC fez uma **revisão sistemática** (metodologia Silva, 2023, em 8 etapas) que chegou a 20 artigos. A **lacuna** identificada: não há trabalhos unindo **simulação de célula de solda automotiva + Tecnomatix Plant Simulation + análise de eficiência energética**.
- A IC construiu o modelo da célula (gêmeo digital) no Plant.

### O TCC (o que estamos fazendo)
- **Pergunta de pesquisa (rascunho):** como otimizar o consumo energético de uma célula de solda a ponto sem degradar a produtividade nem sobrecarregar o operador, mesmo sob falhas?
- **Problema multiobjetivo:** energia × throughput × carga do operador × resiliência.
- **Indústria 5.0** (Comissão Europeia, 2021) é um **complemento** à 4.0, não uma substituição. Cada pilar precisa virar algo **medível no modelo**:
  - **Sustentabilidade:** estados de energia dos robôs (trabalhando, ocioso, standby, desligado), com kWh por carroceria como KPI principal.
  - **Foco no humano:** um operador modelado (Worker), medido por ocupação, deslocamento e pausas. São **proxies** de carga, não ergonomia medida, e isso deve ficar explícito no texto.
  - **Resiliência:** falhas (MTBF/MTTR), variação de mix e de demanda, e a queda e recuperação do throughput.

---

## 3. Ambiente técnico (tudo já validado)

| Item | Situação |
|---|---|
| Plant Simulation | **2404**, Windows |
| Python embutido no Plant | **3.15.1**, instalado em `C:\Python315` |
| Bibliotecas instaladas (no Python que o Plant usa) | numpy 2.5.4, pandas 3.1.0, gymnasium 1.4.0, stable-baselines3 2.9.2, torch 2.15.0+cpu, plotly 7.1.0 e openpyxl 3.1.5 (os dois instalados em 2026-11-09 no site-packages do usuário, `%APPDATA%\Python\Python315`; o plotly não estava instalado antes) |
| Instalar bibliotecas | `C:\Python315\python.exe -m pip install <pacote>`. **Não use `sys.executable`**: dentro do Plant ele aponta para `PlantSimulation2404.exe` |
| Acesso ao computador | Liberado em *File → Model Settings → General → desmarcar "Prohibit access to the computer"* (já feito; fica salvo no `.spp`) |

### 3.1 Integração SimTalk ↔ Python (regras confirmadas na prática)

**Objeto:** `PythonModule` (InformationFlow), chamado `PythonModule` no Frame `.Models.Model`.

**Chamando Python a partir do SimTalk:**
```
var x : integer := PythonModule.call("nome_funcao", arg1, arg2)
```
- **Os argumentos são POSICIONAIS e separados por vírgula.**
  - `PythonModule.call("f", [])` passa uma lista vazia **como 1 argumento** (gera erro em função sem parâmetros).
  - `PythonModule.call("soma", ["a", 2, "b", 3])` passa **uma lista como argumento único** (não vira kwargs).
  - Função sem argumentos: `PythonModule.call("f")`.
  - Útil: passar uma lista como argumento único é a forma de mandar um **vetor de estado** para o agente.
- **Sempre atribua o retorno a uma variável** (`var x := ...`). Chamada solta funciona, mas assim fica explícito.
- **Custo medido:** ~0,6 µs por chamada (o Python roda no mesmo processo). A ponte não é gargalo; o custo real será a inferência da rede neural.
- **Estado persiste entre chamadas e entre execuções de Methods:** variáveis globais do módulo (com `global`) mantêm o valor. O agente pode ficar carregado em memória.
- O `print()` do Python não é garantido no Console do Plant. **Retorne strings e imprima no SimTalk.**

**Acessando o modelo a partir do Python:**
- `current` é o Frame onde está o PythonModule (`.Models.Model`). Caminhos absolutos começam com `basis`, e `root` é o Frame do EventController.
- Acesso por atributo com o **Name exato** (o Python diferencia maiúsculas; o SimTalk não): `current.float_tempoSolda.Value` lê e escreve o valor de uma Variable.
- **Atenção:** o texto exibido no 3D é o **Label**, não o Name. Ex.: o 3D mostra "float tempoSolda", mas o Name é `float_tempoSolda`.
- Tempos podem vir como `datetime.timedelta` → converta com `.total_seconds()`.
- Estatísticas de energia e de estado são lidas diretamente (ver seção 5).

### 3.2 Particularidades do SimTalk (2404) que já causaram erro
- **Editor de Method em aba:** é preciso **Apply Changes (✔ verde / F7)** antes de rodar (F5 ou botão direito → Run). Sem aplicar, roda a versão antiga (ou vazia) e não aparece nada.
- **Methods com nomes especiais** são chamados automaticamente pelo EventController: `Init` (início), `Reset` (reset), `EndSim` (fim da simulação). A aba Controls do EventController **não** tem campo de método.
- **Para listar objetos do Frame use `current.NumNodes` e `current.Node(i)`.** `NumChildren` e `childNo` se referem a classes derivadas por herança e retornam 0.
- **Connectors não têm o atributo `Label`**: acessar `.Label` num Connector dá erro "Unknown identifier".
- Laço: `for var i := 1 to N ... next`. Impressão: `print a, " | ", b`.
- Ao fim de episódios de treino, desmarcar *EventController → Settings → "Show summary report"* para não abrir janela a cada episódio.
- EventController atual: End = 16:00:00 (16 h por episódio).

---

## 4. O modelo herdado da IC (`celula-de-solda-final.spp`, Frame `.Models.Model`)

### 4.1 Inventário (124 nós)
| Grupo | Objetos (Name) | Papel |
|---|---|---|
| Robôs | `ABB_IRB_6700_1` … `_4` (classe **PickAndPlace**) | 4 robôs de solda |
| Fluxo da carroceria | `ENTRADA_BIY` (Source) → `SKID_EFQ_3` (Conveyor) → `SAIDA_BIY` (Drain) | Entra, para na estação, sai |
| Pontos de solda | `R1_P1`…`R1_P10` (e R2, R3, R4), alternando Source/Drain | 10 posições por robô; o PickAndPlace "leva e traz" entre elas para simular o deslocamento |
| Lógica | `def_inPosition`, `def_entranceR1..4`, `def_exitR1..4` (Methods) | Sequenciamento dos pontos (ver 4.5; código em `x_plant-models/infotmation-methods/`) |
| Estado | `int_pontoR1..4`, `float_tempoSolda` (Variables); `str_estadoR1..4` (Displays) | Ponto atual de cada robô e tempo de solda (1,6 s) |
| Dados | `TT_R{1..4}_{HATCH,SEDAN}`, `TC_HATCH`, `TC_SEDAN`, `ListaBIW` (DataTables) | Tempos de trajeto, coordenadas e mix (ver 4.2) |
| Energia/relatório | `EnergyAnalyzer` (monitora 5 objetos), `HtmlReport`, `EventController` | |
| Adicionados por nós | `PythonModule`, `testePython`, `listarObjetos`, `testeCusto`, `rodarEpisodio`, `EndSim` | Testes e infraestrutura |

Dois produtos: **HATCH** e **SEDAN**. **Não há operador humano** no modelo ainda.

### 4.2 Tabelas de trajetória (entendidas por análise)
- **`TC_<modelo>`**: 10 linhas (P1 a P10) × 12 colunas = 4 robôs × (x, y, z), em **metros**. R1 nas colunas 1–3, R2 nas 4–6, R3 nas 7–9, R4 nas 10–12.
- **`TT_R<n>_<modelo>`**: matriz 11×11 de **tempos de deslocamento (s)**, definida em cada robô por `robo.setTimesTable(...)` no `def_inPosition`. No Plant, as colunas aparecem como `time 1`…`time 11` e as linhas como 1…11, **sem nome de objeto**. Pela intenção do autor (usuário, 2026-11-09): índice 1 = home (nó 0), índices 2…11 = P1…P10. Valor 0 significa que não há caminho direto. **Só tem valores entre pontos consecutivos** (a sequência é fixa), simétricos (i→j = j→i). **Ainda não confirmado** como o PickAndPlace associa cada índice a um objeto ou posição.
- Tempos de projeto da SEDAN (planilha do autor), em s, R1 / R2 / R3 / R4: 0→1 = 17,11 / 15,61 / 17,72 / 21,77; 9→10 = 0 / 14,08 / 0 / 0; 10→0 = 14,19 / 15,44 / 9,32 / 12,64; soma do ciclo = 90,60 / 76,23 / 58,51 / 70,20 (+ 9 × 1,6 s de solda → R1 ≈ 105 s, o que bate com os ~106 s observados).
- **Verificado (2026-11-09, as 8 tabelas):** TT = distância euclidiana (da TC) ÷ V nos trechos P1…P9, mas **V difere por produto**:
  - SEDAN: ≈ 12,3 s/m → **V ≈ 0,081 m/s**;
  - HATCH: ≈ 15,8 s/m → **V ≈ 0,063 m/s** (ainda mais lento).
- Soma dos deslocamentos P1→P9 por robô: HATCH 35,3 / 39,7 / 40,4 / 46,0 s; SEDAN 59,3 / 45,2 / 31,5 / 35,8 s (R1…R4). Isso exclui os trechos de home e os 9 × 1,6 s de solda.
- **Armadilha de export:** o Plant usa `.` como separador decimal (correto dentro do modelo). Ao colar ou abrir esses dados no Excel pt-BR, valores como `19.1226` viram o inteiro `191226` (o Excel lê o `.` como separador de milhar). Valores como `0.9651` ou `0.0000` ficam como texto e não são afetados. Ao ler um xlsx assim, divida por 10.000. Prefira exportar como CSV ou texto, ou configurar o Excel com `.` como separador decimal antes de colar.

### 4.3 Problemas conhecidos (a corrigir na Fase 0)
1. **A velocidade foi calibrada pelo takt, não é física** (confirmado pelo relatório da IC, ver 4.6). O ciclo de 132 s menos o transporte do skid e as soldas foi distribuído entre os trajetos, na proporção da distância. Resultado: V ≈ 0,06–0,08 m/s, contra **1,6 m/s de velocidade linear máxima do IRB 6700** (datasheet), ou seja, 20–25× mais lento. Os robôs ficam 52–65% em Working e só 24–37% ociosos. Isso esconde a ociosidade real e, portanto, **o potencial do standby**.
   - Referência: tempo padrão de ~3,3 s por ponto (movimento + solda), com ~1 s de solda (WSC 2024, *cycle time prediction of robot arm welding*). No modelo: solda 1,6 s (razoável) e movimento ~9 s por ponto (cerca de 4× maior).
   - **Correção:** recalcular as TT com V realista (alvo ~2–2,5 s de movimento médio por ponto), manter 1,6 s de solda e **impor o takt (~132 s) na linha** (`ENTRADA_BIY`/`SKID`). Validar que o throughput continua ~436 em 16 h.
2. **O P10 é cópia do P9** na TC em 7 das 8 combinações: só o **R2 SEDAN** difere (e é a única TT com P9↔P10 = 14,08 s). Segundo o relatório da IC, o P10 é um **Drain fictício**: a modelagem com pares Source/Drain exige número par de objetos, e o robô só tem 9 soldas. Por isso ele fica com as coordenadas do P9 "sem impactar o tempo". O comentário "ponto de limpeza" no `def_exitR1` é só um nome. **BUG confirmado (2026-11-09):** no R2 SEDAN o P10 é um ponto de solda real. **O R2 deve soldar 10 vezes no sedan** (confirmado pelo usuário), mas o `def_exitR*` sempre pula a solda no P10, então ele faz só 9 soldas: o tempo total em solda do R2 dá 9,005 soldas por carroceria, igual aos outros robôs. Isso **explica o desvio de 3,4% do R2 na validação da IC**: 158 sedans × 1,6 s × 90 kW = 6,32 kWh, mais ~0,3 kWh de diferença comum a todos os robôs (437 contra 436 carrocerias) = 6,60 kWh, exatamente a diferença entre o esperado (193,15) e o medido (186,55). **O "esperado" da IC estava certo; o modelo estava errado.** **CORRIGIDO na v3 (2026-11-09):** variável `str_modeloAtual := @.name` no `def_inPosition` e, no `else` do `def_exitR2`, `?.startPause(float_tempoSolda)` quando `str_modeloAtual = "BIY_SEDAN"`. Validação (cenário `r2_sedan`): R2 +6,280 kWh (186,55 → 192,83), +251,2 s de solda = 157 soldas extras (uma por sedan), 9,365 soldas/carroceria. R1, R3, R4, skid e throughput **inalterados**, então o skid não é liberado cedo.
3. ~~Erro na volta para o home~~ **Resolvido em 2026-11-09: não é bug.** O P10→home está na linha 11/coluna 2 e não na coluna 1, mas o teste A/B (copiar o valor para a coluna 1 nas 8 TT, cenário `tt_volta`) deu resultado **idêntico** ao original. E o tempo de movimento medido por carroceria bate com o de projeto **incluindo** ida e volta do home (R1 78,04 / R2 85,49 / R3 69,23 / R4 83,06 s medidos contra 77,97 / 85,42 / 69,17 / 83,00 s de projeto, com 279H/157S, diferença < 0,1%). Sem a volta, a diferença seria de 19–42%. Ou seja, o PickAndPlace obtém o tempo de volta de outra célula, provavelmente a simétrica (linha 1, coluna 11). Ainda não se sabe qual é a orientação de/para da tabela no Plant, mas **matrizes simétricas tornam isso irrelevante**: ao gerar as TT completas, mantê-las simétricas.
4. **O modelo é determinístico.** Execuções repetidas dão resultado idêntico. É preciso introduzir variabilidade (tempos com distribuição, mix aleatório, falhas) e rodar replicações.
5. **Potências por estado: fonte encontrada (relatório da IC, Tabelas 9 e 11), mas com dois problemas graves para o TCC.** Pesquisa de 2026-11-09 em `z_references/fontes-parametros.md`: **ocioso com freios liberados = 0,84 kW, freios acionados = 0,17 kW** (ABB 3HAC044265-001 rev. N, IRB 6700-205/2.80, IRC5); **energia por ponto = 5–11 kJ na rede** (Li et al., SMWC 2004), contra 144 kJ no modelo (~13–30× a mais); o tempo de retomada não tem fonte A e vai para a análise de sensibilidade.
   - **a solda está modelada como Standby (90 kW).** Foi escolhido porque o `startPause` coloca o objeto em Standby automaticamente. Isso **colide com a Fase 1**, que precisa do Standby como estado de economia. É preciso remodelar a solda: outro estado, ou energia por ponto contabilizada à parte;
   - **Operational (ocioso) = 0 kW.** Com o robô parado consumindo zero, entrar em standby **não economiza nada** e a premissa de RL/standby desaparece. Um robô real ocioso consome (controlador, servos energizados, freios liberados). É preciso de uma fonte para a potência ociosa e para a de standby/economia do IRC5.
   - **90 kW é a potência nominal da pinça** (GWT C9), aplicada durante 1,6 s inteiros. Isso dá 144 kJ por ponto e **~85% da energia da célula** (157 de 184 kWh por robô). Verificar na literatura a energia real por ponto: potência nominal não é potência média.

### 4.4 Resultados de referência (modelo atual, 16 h)
- 436 carrocerias → ciclo ≈ 132 s.
- Energia: R1 = 183,94, R2 = 186,55, R3 = 180,98, R4 = 185,71, SKID = 7,20; **total = 744,37 kWh** (a unidade foi confirmada no relatório da IC, que dá 744,38). ≈ 1,71 kWh por carroceria.
- Separação por estado (relatório da IC, Tabela 12): cada robô tem ~157 kWh em Standby (= solda), 24–30 kWh em Working (movimento) e 0 em Operational. O skid tem 7,20 kWh em Working.
- Tempo por estado (Tabela 13): robôs com Operational 24–37%, Working 52–65% e Standby 10,91%; skid com Working 20,47% e Standby 79,53%.
- Validação da IC: consumo esperado de 751,85 contra 744,38 medido (aderência de 99,0%). O **R2 desvia 3,4%** (193,15 contra 186,55), sem explicação no relatório. Pode estar ligado às bordas da TT ou ao P10 do R2 SEDAN.
- Pico de potência: 360 kW (4 robôs soldando ao mesmo tempo), que só ocorre na SEDAN. A IC sugeriu reduzir o pico ressincronizando, o que é um gancho para o KPI de pico (item 5 [D]).
- **Baseline corrigida (v3, R2 SEDAN com 10 soldas, 2026-11-09): 750,66 kWh, 1,722 kWh/carroceria, R2 = 192,83 kWh**, demais iguais. É a referência para os próximos cenários. (Com 0,3 kWh da carroceria 437, fica ≈ 751,0, contra 751,85 do "esperado" da IC.)
- O mix simulado em 436 carrocerias é **279 hatch / 157 sedan** (deduzido das 157 soldas extras do R2).
- Reset por código validado: `EventController.reset` + `EventController.start`, com `EndSim` disparando no fim.

### 4.5 Lógica de sequenciamento (analisada em 2026-11-09, só o R1; R2–R4 supostos análogos, a confirmar)
- **`def_inPosition`** (sensor do skid, quando a carroceria chega):
  1. escolhe `TC_HATCH`/`TC_SEDAN` pelo `@.name` (`BIY_HATCH` / `BIY_SEDAN`) e aplica `robo.setTimesTable(TT_R<r>_<modelo>)` nos 4 robôs;
  2. posiciona os 40 pontos `R<r>_P<p>` no 3D com `_3D.Position.X/Y/Z` lidos da TC por `tabela["X_R<r>", "P<p>"]`;
  3. para o skid (`SKID_EFQ_3.startPause`);
  4. cria o MU `UserObjects.SOLDA` nos pontos **ímpares** (P1, P3, …, P9) de cada robô. O PickAndPlace leva cada SOLDA do ímpar para o par seguinte (Drain);
  5. espera o R1 chegar a `int_pontoR1 = 9`, depois voltar a 0, depois todos os 4 robôs ficarem parados com `int_pontoR* = 0`;
  6. libera o skid (`SKID_EFQ_3.pause = false`).
- **`def_entranceR1`:** `int_pontoR1 += 1` e `?.startPause(float_tempoSolda)` (solda na coleta).
- **`def_exitR1`:** se `int_pontoR1 < 9`, faz `+= 1`, pausa 1,6 s (solda na entrega) e `@.move`. Senão (ponto de limpeza), zera o contador e faz `@.move` sem pausa.
- **Consequência:** são **9 soldas por robô por carroceria** (5 coletas + 4 entregas), ou seja, 14,4 s de solda, não 10.
- **O takt JÁ é imposto pelo `ENTRADA_BIY` (print de 2026-11-09):** Source com Blocking, Time of creation = *Interval Adjustable*, **Interval = Const 2:12 (132 s)**, Start 0, Stop 0, Amount −1, MU selection = **Percentage** com a tabela `ListaBIW`, saída Cyclic. **`SKID_EFQ_3`**: Conveyor de **8,05 m a 0,3 m/s → 26,83 s** de transporte, accumulating, sem aceleração (o skid em Working por 27,0 s por carroceria confere). Balanço da IC: 132 s = 26,83 s de skid + ~105 s do robô mais lento (R1 SEDAN), daí a V calibrada. **Consequência para o item 2:** basta trocar as TT por tempos realistas; o intervalo de 132 s mantém o throughput, e a folga aparece como ociosidade dos robôs. Os 0,3 m/s do skid vêm do datasheet Expert-Tünkers EFQ (segundo o usuário, 2026-11-09; conferir a página ao citar).
- **`ListaBIW`:** `.MUs.BIY_HATCH` 0,64 e `.UserObjects.BIY_SEDAN` 0,36 (mix 64/36, da produção real 279/158). O Source usa MU selection = **Percentage**: **o Plant sorteia cada carroceria pela proporção da tabela** (confirmado pelo usuário, 2026-11-12). As réplicas saem idênticas porque a semente aleatória é a mesma a cada rodada. **Semente (2026-11-12, `listar_attrs`):** `EventController.RandomNumbersVariant` (variante global dos números aleatórios), `EventController.IncrementRandomNumbersVariantOnReset` e `ENTRADA_BIY.RandomSeed`. Plano: o `EndSim` faz `EventController.RandomNumbersVariant := int_replica` depois de incrementar a réplica (réplica r ↔ variante r, reprodutível). **Teste de 2026-11-12 (10 réplicas da v6, variantes 1..10 gravadas no JSON): as 10 saíram IDÊNTICAS** (100,532 kWh, 436, mix estimado 278/158, que é o 279/157 real mais a carroceria em processo). Como todos os tempos do modelo são constantes, o único elemento aleatório seria o mix. Então **o mix não depende da variante**. Hipóteses: (a) o modo *Percentage* distribui as carrocerias de forma determinística, mantendo a proporção exata (279 = 0,64 × 436 arredondado, o que reforça); (b) o Source usa a própria `RandomSeed` e ignora a variante. **Resolvido (2026-11-12):** o MU selection oferece Constant, Sequence Cyclical, Sequence, **Random**, Percentage e Order Controlled. Com **Random** (v7), o mix passa a ser sorteado: 10 réplicas (variantes 1–10) com **sedans 144–166 (média 154,9, dp 7,5; binomial esperado 157 ± 10)**, throughput 436 em todas, **energia 100,52 ± 0,02 kWh (IC 95%) = 0,2306 kWh/carroceria**, robôs 77,3% ociosos. **v7 = nova baseline (estocástica).** Achado: com a linha limitada pelo takt, o kWh/carroceria é quase insensível ao mix (dp 0,0001), porque sedan e hatch diferem pouco em energia com os tempos realistas. A variabilidade relevante virá das falhas e dos tempos com distribuição (Fase 1). O JSON agora grava `variante_aleatoria` e `mix` (sedans estimados = (Standby R2 − Standby R1) ÷ 1,6 s, ±1 por causa da carroceria em processo no fim; na v6 dá 157,74 para 157 reais).

### 4.6 Documentação da IC (lida em 2026-11-09)
Arquivos: `z_references/giovanni-rossi_relat-final_assinado.pdf` (relatório final da IC) e `z_references/estado-arte-fms_giovanni-rossi.pdf` (revisão sistemática). Fatos que servem de fonte para o modelo:
- **Caso de referência:** célula de fixação por solda a ponto do conjunto lateral à carroceria, com dados de uma *Filial de Montadora Europeia Instalada no Brasil* (FMEIB, 2025, documentação interna, São Bernardo do Campo). Dois modelos, hatch e sedan. **A célula não existe fisicamente hoje** (usuário, 2026-11-09): componentes e parâmetros sem dado da FMEIB podem ser escolhidos como **hipóteses de projeto justificadas** (ex.: controlador IRC5).
- **Produção real em 16 h:** 437 carrocerias (279 hatch, 158 sedan), ciclo médio de **2:12 min = 132 s** (FMEIB, 2025). O modelo dá 436.
- **Calibração temporal:** ciclo − transporte do skid (velocidade × comprimento) − soldas (1,6 s/ponto) = resto, distribuído entre os trajetos do robô na proporção da distância. As tabelas 2 e 3 do relatório têm os tempos de cada trecho, incluindo **"P10 a P0"**, o que confirma o diagnóstico do item 3 de 4.3.
- **Geometria:** coordenadas em mm de P0 (repouso) e P1–P10 por robô e por modelo (FMEIB), com origem no centro do eixo dianteiro e convenção SAE J670:2008 (eixo X invertido). Carroceria: hatch X 200–2950 mm, sedan 200–3250 mm; Y ±725 mm; Z −25 a 1200 mm. No Plant, a TC está em metros, em coordenadas do mundo.
- **Componentes e datasheets (Tabela 9):**
  - robô ABB IRB 6700-205: alcance 2,80 m, carga 205 kg, **velocidade linear máxima 1,6 m/s, potência nominal 2,85 kW** (ABB, *Product specification IRB 6700*, 3HAC080365-001 rev. K, 2025);
  - pinça ABB GWT C9: massa 65–99 kg, **"consumo nominal 90 kW" segundo a IC. Verificado em 2026-11-09: o datasheet diz "Transformer MFDC 90 kVA (50%)" / "Power (S50) 90 kVA"**, ou seja, potência nominal térmica do transformador a 50% de fator de serviço, não consumo (flyer 9AKK107680A4035 rev. B 2022; apresentação 9AKK108468A1525 rev. A 2023; PDFs em `z_references/`). A IC usou o número certo com a interpretação errada;
  - skid Expert-Tünkers EFQ: velocidade linear máxima 1,6 m/s, **potência nominal 2,2 kW** (Expert-Tünkers, datasheet EFQ 1, 2024).
- **Potências por estado no Plant (Tabela 11):** PickAndPlace Operational (aguardando) = 0, Working (movendo) = 2,85 kW, **Standby (soldando) = 90 kW**. Conveyor Operational (parado) = 0, Working = 2,2 kW.
- **Revisão sistemática:** 20 artigos; a lacuna é a mesma da seção 2. As inconsistências estão na seção 7.

---

## 5. Estrutura do workspace e pipeline de resultados

### 5.1 Estrutura
```
TG/
├── CLAUDE.md                 este arquivo (contexto do projeto)
├── todo.txt                  meta do projeto + lista de tarefas (manter em dia)
├── z_references/             PDFs: tempo-solda.pdf, relatório final da IC, revisão sistemática da IC
├── x_plant-models/
│   ├── celula-de-solda-tg-v1.spp   modelo atual (versionar como -vN)
│   └── infotmation-methods/        código dos Methods (.txt) e tables.xlsx exportados do Plant
└── scripts/
    ├── coleta_plant.py       código do PythonModule (colar no Plant)
    ├── gerar_relatorio.py    relatório HTML (roda fora do Plant)
    ├── diagnostico_plant.py  listar_attrs/ler_attr para descobrir a API do Plant (colar no PythonModule)
    ├── gerar_tt.py           gera as TT pelo modelo cinemático (cenários K1/K2/K3/H) + memória de cálculo
    └── resultados/           JSONs dos episódios + relatorio.html
├── docs/
│   └── opcoes-A-B-C-economia-RL.md   decisão das opções A/B/C (Fase 1 e RL), com referências, implementação e análise
```
O workspace **é um repositório Git** (branch `main`, desde 2026-11-09), com remoto `origin` = **github.com/g06rossi/tg-celula-solda** (privado). O `.gitignore` exclui `*.spp.bak`, `__pycache__` e o `relatorio.html` (regenerável). Os `.spp` (~3,8 MB cada) e os PDFs entram no repositório, que deve ser **privado** (há documentação interna da FMEIB e PDFs de terceiros). **Commitar a cada etapa concluída** (o usuário faz o push).

### 5.2 Scripts
- `scripts/coleta_plant.py`: código para **colar no final do PythonModule**.
  - `amostrar()`: chamado por um Generator a cada 60 s. Guarda a energia acumulada e o tempo acumulado em cada estado de energia de cada recurso.
  - `fechar_episodio(cenario, replica)`: chamado no `EndSim`. Salva `C:\Users\giova\Arquivos\UFABC\TG\scripts\resultados\<cenario>_rNN.json`.
  - `limpar_episodio()`: chamado no Method `Reset`.
  - Configuração no topo: `PASTA_RESULTADOS`, `RECURSOS`, `SAIDA`, `UNIDADE_ENERGIA`, `PARAMETROS` (dicionário com **valor e fonte** de cada parâmetro; atualizar a cada mudança de modelo; desde 2026-11-09 tem as fontes da IC) e `ROTULOS_ESTADO` (o que cada estado de energia do Plant significa neste modelo; hoje Standby = "Soldando". **Atualizar quando a solda sair do Standby**).
- `scripts/gerar_relatorio.py`: roda **fora do Plant** (`C:\Python315\python.exe gerar_relatorio.py`; sem argumento usa `scripts\resultados`) e gera `relatorio.html` (Plotly embutido, arquivo único, offline). Conteúdo:
  - comparação entre cenários (média ± IC 95%, t de Student);
  - cartões de KPI;
  - energia por recurso e estado;
  - % de tempo em cada estado;
  - energia acumulada e potência;
  - linha do tempo do estado predominante;
  - tabela de recursos;
  - tabela de parâmetros com fonte.

**Atributos de estatística disponíveis nos robôs (PickAndPlace)**, confirmados:
`StatEnergy{Working,Operational,Setup,Standby,Off,Fail}{Consumption,ConsumptionPortion,Time}`, `StatEnergyTotalConsumption`, `Stat{Working,Waiting,Blocking,Fail,Pausing,Stopped,Empty,PoweringUpDown,Unplanned}{Count,Delta,Mu,Portion,Time}`, `StatFailCount`, `StatNumIn`, `StatNumOut`, `StatRelativeOccupation`, `StatAverageWorkingTime`, `StatAverageDwellTime`, `StatEntranceBlocked*`, `StatExitBlocked*`, `StatRotation{Empty,Loaded}{Portion,Time}`.
O Frame também expõe `StatEnergy*Consumption` (o total da célula).

**Atributos de energia do PickAndPlace (via `listar_attrs`, 2026-11-09), úteis para a Fase 1 e para a sensibilidade:** `EnergyActive`, `EnergyCurrentState`, **`EnergyTargetState`** (provável comando de troca de estado), **`EnergyPauseStartState` / `EnergyPauseEndState` / `EnergyPausePowerUpEarly`** (qual estado o `startPause` usa), `EnergyUnplanned{Start,End}State`, `EnergyUnplannedPowerUpEarly`, **`PowerInput{Working,Operational,Standby,Off,Failed,SettingUp}`** (potências, provavelmente graváveis por código), **`TransitionTime{Off,Operational,Standby}To{…}`** (6 tempos de transição), `ResCurrentState`, `Pause`, `PauseCtrl`, `startPause`, `startPauseIn`, `endPause`, `endPauseIn`, `erasePauseEvents`, `StatPoweringUpDown{Count,Delta,Mu,Portion,Time}`, `StatEmpty*`. A semântica de `EnergyTargetState` e de `EnergyPause*State` **ainda não foi testada**.

**Formato do JSON:** `cenario`, `replica`, `gerado_em`, `sim_time_s`, `throughput`, `unidade_energia`, `energia_total_frame`, `parametros{nome:{valor,fonte}}`, `rotulos_estado{estado:rótulo}` (opcional; o relatório usa o nome do Plant se faltar), `variante_aleatoria`, `mix{sedan, hatch, metodo}` (desde 2026-11-12), `recursos{nome:{energia{estado}, energia_total, tempo_energia{estado}, porcao_estado{estado}, falhas}}`, `serie{t[], <recurso>{energia_acum[], tempo_estados{estado:[]}}}`.

Durante o **treino** de RL, salvar só o necessário (KPIs). O relatório completo é para rodadas de **avaliação**.

---

## 6. Plano de desenvolvimento

Legenda: **[M] mínimo**, **[D] desejável**, **[B] bônus**. Ordem prática: itens 1–5 → protótipo da integração com RL → 6–8 → 9 e 11 → 12 e 13 → restante.

### Fase 0: sanear o modelo base
1. **[M]** Corrigir a TC e a TT (P10 duplicado, bordas da matriz) e conferir as tabelas HATCH.
2. **[M]** Separar o tempo do robô do takt: V realista, solda de 1,6 s, takt imposto na linha. Validar ~436 carrocerias / 16 h, agora com ociosidade visível.
3. **[M]** Potências por estado (Working, Operational, Standby, Off, Fail) nos 4 ABB e no skid, **com fonte**.
4. **[M]** Variabilidade: distribuições de tempo, mix HATCH/SEDAN aleatório a partir do `ListaBIW`, replicações com IC.
5. **[M]** KPIs: kWh por carroceria (principal), throughput, ociosidade, tempo por estado; [D] pico de potência.

### Fase 1: pilares da Indústria 5.0
6. **[M]** Standby nos robôs **com custo de retomada** (tempo e energia para "acordar"; sem isso a resposta ótima é trivial). Baseline: standby após X segundos ocioso. **Pré-requisitos (4.3, item 5):** tirar a solda do estado Standby e dar ao Operational (ocioso) uma potência > 0 com fonte.
7. **[M]** Falhas (MTBF/MTTR) e variação de mix e demanda; [D] modo degradado (redistribuição de pontos ou desaceleração da linha).
8. **[M]** Operador (Worker, WorkerPool, Broker, FootPath) com:
   - troca e retífica das capas dos eletrodos a cada N soldas;
   - atendimento de falhas (o MTTR passa a depender de o operador estar livre);
   - [D] inspeção por amostragem.

### Fase 2: otimização clássica (baselines)
9. **[M]** Sequência ótima de pontos por robô. Calcular a **matriz completa** a partir da TC; com 10 pontos, **força bruta ou programação dinâmica** dá o ótimo exato (9! = 362.880). Medir o ganho sobre a sequência da IC. **Não use metaheurística aqui**: seria resolver com heurística um problema que tem solução exata.
10. **[D]** Distribuir os 40 pontos entre os 4 robôs com **GA ou NSGA-II** (min. tempo do robô mais lento e energia). Aqui a metaheurística se justifica. Base: survey de Wang et al. (2021), Eq. 4 (equilíbrio entre robôs) e ref. 71 (TSP com tempos ponto a ponto, resolvido por GA).
11. **[M]** Otimizar o timeout de standby (ExperimentManager ou GAWizard). É o "melhor sem IA".

### Fase 3: IA (aprendizado por reforço)
12. **[M]** Agente **PPO (stable-baselines3)** decidindo quando cada robô entra em standby e quando acorda.
    - **Estado:** `int_pontoR*`, tempo até a próxima carroceria, modelo da carroceria, robô em falha, operador ocupado.
    - **Ação:** standby on/off por robô.
    - **Recompensa:** −energia − penalidade por atrasar o takt − penalidade por sobrecarregar o operador.
13. **[M]** Comparar 4 políticas: (a) sem standby, (b) timeout fixo, (c) timeout otimizado, (d) RL. Cenários: normal, com falhas e com mix alto de SEDAN.
14. **[B]** LLM ou Copilot do Plant como interface what-if (trabalho futuro).

### Fase 4: experimentos e texto
15. **[M]** Cenários × políticas × replicações, com IC 95%.
16. **[M]** Análise de sensibilidade de potências e custo de retomada.
17. **[M]** Atualizar a revisão sistemática com Indústria 5.0, RL + simulação de eventos discretos e energia em robôs industriais.

### Riscos
- **A inversão de controle no RL é o maior risco técnico.** O SB3 espera chamar `env.step()`, mas no Plant **é a simulação que chama o Python**. Prototipar cedo uma destas opções:
  - (a) SB3 numa thread com filas dentro do PythonModule;
  - (b) controlar o Plant por fora via COM (pywin32), pausando a cada decisão;
  - (c) laço de treino próprio (por exemplo, Q-learning tabular ou um PPO adaptado ao estilo callback).
  Explique os prós e contras antes de implementar.
- **Fontes dos parâmetros:** manter uma planilha e o dicionário `PARAMETROS` atualizados.
- **Escopo:** se apertar, os itens [D] e [B] caem; o TCC continua completo com os [M].

---

## 7. Achados metodológicos a preservar no texto

- *"Modelos calibrados apenas pelo takt mascaram a ociosidade dos recursos e subestimam o potencial de economia de energia."* É um achado do TCC, não da IC.
- O método TT = distância ÷ V é o mesmo da literatura; o problema é só o valor de V.
- A revisão da IC tem inconsistências a não repetir:
  - o total de 884.507 documentos não fecha com a Tabela 2 (o valor do SpringerLink está 64.595 numa tabela e 64.665 na outra);
  - a expressão (4) também teve 4 documentos selecionados;
  - a numeração das figuras está quebrada;
  - as Redes de Petri aparecem na interpretação sem estar nas buscas;
  - o artigo de 2016 está fora do filtro.

## 8. Referências já usadas
- PI (PROFIBUS & PROFINET International). *Assessing PROFIenergy's potential*, white paper v1.0, nov. 2011. Medições de 7 dias (1 s) em células de carroceria da Daimler (Sindelfingen) e da VW (Hanôver): 47% da energia em períodos ociosos; 64% do tempo ocioso em paradas ≥ 5 min; modos de economia só para paradas ≥ 5 min; robô parado até 300 W. PDF em `z_references/`.
- Frigerio, N.; Matta, A. *Energy-efficient control strategies for machine tools with stochastic arrivals.* IEEE T-ASE 12(1) 50–61, 2015, DOI 10.1109/TASE.2014.2344507 (lido pelo resumo; PDF aberto no repositório Polimi bloqueado ao download automático). Limiares ótimos de desligar/religar com chegadas aleatórias.
- Loffredo, A.; Matta, A. et al. *Reinforcement learning for sustainability enhancement of production lines.* J. Intelligent Manufacturing 35(8), 2024 (lido pelo resumo). RL para controle energético com dados de linha automotiva.
- Alaka, H. T. O. et al. *Developing reliability centered maintenance in automotive robotic welding machines for a tier 1 supplier.* Frontiers in Robotics and AI 12:1620370, 2025, DOI 10.3389/frobt.2025.1620370. Disponibilidade de 70–72%; causas de parada (água, tip dressing, grampos, robô travado). Sem MTBF/MTTR numéricos.
- ABB. *Application manual – PROFIenergy device*, 3HAC050967: **inacessível** (acesso negado também ao usuário, 2026-11-13). Substituído por:
- KUKA Roboter GmbH. *Controller Option KR C4 PROFINET 2.2* (KSS/VSS 8.2), V5, 08/05/2012, seção 5.6.2.3. *Drive bus OFF*: entra 5 s, volta **20 s**; *Hibernate*: entra 50 s, mín. 10 s, volta **50 s**. PDF em `z_references/`. Usado como fonte dos tempos de transição da opção B (outro fabricante, mesmo perfil PROFIenergy).
- Yokogawa/KUKA Systems (notícia técnica, PX8000): robô parado ~700 W → ~200 W após 20 s; hibernação ~18 W (conf. C).
- ABB. *Product specification IRB 6700* (IRC5), 3HAC044265-001, rev. N, 2019, p. 15 (potência ISO cube e com freios acionados/liberados). PDF em `z_references/`.
- Bukata, L.; Šůcha, P.; Hanzálek, Z.; Burget, P. *Energy Optimization of Robotic Cells.* IEEE Trans. Ind. Informatics 13 (2017) 92–102, DOI 10.1109/TII.2016.2626472. Célula Škoda; modos freios e bus power-off; economia de 2,4% a 12% conforme o ciclo. PDF em `z_references/`.
- Li, W.; Feng, E.; Cerjanec, D.; Grzadzinski, G. *Energy consumption in AC and MFDC resistance spot welding.* Sheet Metal Welding Conference XI, 2004. Energia primária de 4,7–7,3 kJ por ponto. PDF em `z_references/`.
- Wang, X. et al. *A survey of welding robot intelligent path optimization.* J. Manuf. Processes 63 (2021) 14–23. (É um survey: revisa PSO, MOPSO, GA, NSGA-II, MOEA/D, ACO e ABC; para solda a ponto, formula o problema como TSP.)
- Cho, S.; Kim, D.; Park, S. *Simulation based cycle time prediction for robot welding.* Winter Simulation Conference 2024, p. 2775–. (3,3 s/ponto é a "standard unit process time" empírica da indústria, com acurácia de 72% no artigo; solda de 1 s/ponto; movimento = trajetória ÷ V configurada no RobotStudio.) PDF: `z_references/tempo-solda.pdf`.
- Banga et al. (2021). *Optimization of the cycle time of robotics resistance spot welding for automotive applications.* J. Adv. Manuf. Processing.
- Comissão Europeia (2021). *Industry 5.0: Towards a sustainable, human-centric and resilient European industry.*
- Siemens: Plant Simulation 2404 (objeto PythonModule); tutorial da Universidade de Twente para o 2404.

## 9. Próximo passo pendente
**RESULTADO DO TESTE DE ECONOMIA (2026-11-12): o mecanismo funciona.** `ABB_IRB_6700_1.EnergyTargetState := "Off"` e `:= "Operational"` no `def_inPosition` são aceitos e mudam o estado de energia.
- `teste_off_t0` (retomada 0 s, variante 1, contra o `v7_r01`): R1 **12,238 h em Off**, Operational 0,16 h; **R1 23,258 → 15,059 kWh (−8,20 kWh, −35% no robô, −8,2% na célula)**; R2–R4, skid e throughput (436) idênticos.
- `teste_off_t2` (Off→Operational = 2 s): PoweringUpDown = 0,2416 h = **435 retomadas × 2 s**; Off −316 s e Operational +316 s em relação ao t0. Inferência: a retomada é cobrada a 0,84 kW (Operational) e o ciclo do R1 atrasa 2 s quando ele é o robô mais lento. **Custo total da retomada: 0,06 kWh (0,7% da economia)**; throughput 436.
- Estimativa com os 4 robôs em economia: ~67,7 kWh (−33%).
- **PROBLEMA DE DESENHO DA PESQUISA (honesto):** com chegadas determinísticas a cada 132 s e ~100 s de folga, a política "dormir sempre que todos voltam ao home e acordar quando a carroceria chega" já é ótima: a retomada custa quase nada e não atrasa a linha. **Nesse cenário o RL não tem o que aprender** (o item 6 já previa: "sem custo de retomada a resposta ótima é trivial"). Para a decisão ter conteúdo, ela precisa de incerteza ou de trade-off. Candidatos: (a) **chegadas incertas** (falhas a montante, variação de demanda, takt variável), em que acordar tarde atrasa a linha e acordar cedo gasta energia; (b) **retomada longa** em modos mais profundos (bus power-off, ~segundos a dezenas de segundos, Bukata 2017) comparável às janelas ociosas; (c) **falhas dos robôs** e o operador (Fase 1, itens 7–8); (d) desgaste dos freios (5 milhões de ciclos, Bukata 2017) como custo por ciclo. **A decidir com o usuário e o orientador antes do RL.** Detalhamento completo em `docs/opcoes-A-B-C-economia-RL.md` (2026-11-13): A sozinha não basta (com retomada rápida, acordar na chegada continua ótimo); B cria o trade-off; **Ordem aprovada pelo usuário (2026-11-13): B → A → C.** Modos da opção B: Standby = freios/acionamentos desligados 0,17 kW (ABB), retomada 0,2–20 s; Off = hibernação ~0,02 kW, entrar 50 s / voltar 50 s (KUKA KR C4). Para B é preciso liberar o Standby: solda passa ao Operational via `EnergyPauseStartState` e a energia do arco é somada no Python (a testar).

**AGORA (2026-11-12): testar o mecanismo de economia (Fase 1, item 6) numa cópia da v7, só no R1.** No `def_inPosition`: depois de `str_modeloAtual := @.name`, `ABB_IRB_6700_1.EnergyTargetState := "Operational"` (acordar); depois do último `waituntil` (todos no home), antes de liberar o skid, `ABB_IRB_6700_1.EnergyTargetState := "Off"` (economia). Cenários `teste_off_t0` (TransitionTimeOffToOperational = 0) e `teste_off_t2` (= 2 s), ambos com variante 1, comparados com o `v7_r01`. Estimativa grosseira para o t0: R1 ~12,2 h em Off e R1 de ~23,3 para ~15 kWh. Validar: throughput 436, outros robôs iguais e se o `EnergyTargetState` aceita escrita.

**Antes (concluído):** **AGORA: item 2 da Fase 0, tempos de movimento realistas, sobre a v4 (baseline validada: 154,717 kWh).** O takt de 132 s já está imposto no `ENTRADA_BIY`, então basta trocar as 8 TT. **O usuário não tem RobotStudio.** Proposta (2026-11-09, `scripts/gerar_tt.py`): modelo cinemático trapezoidal por trecho, `t = d/v + v/a + PSt` (ou `2√(d/a) + PSt` em trechos curtos), com d = reta entre pontos da TC. Os trechos de home usam a distância implícita na TT da IC (tempo ÷ s/m calibrado), porque a TC não tem o P0. Dados ABB rev. N: v = 1,6 m/s (teste ISO 9283), **a = 24 m/s²** (aceleração cartesiana máx. em movimento controlado, 205/2.8, seção 1.5.5) e **PSt = 0,17 s** (pose stabilization time, 205/2.80, seção 1.8.2). Cenários: K1 = limite do fabricante, K2 = v1000 e a/2, K3 = 0,5 m/s e a/4, **H = K2 + 0,73 s por trecho**, calibrado para 3,3 s/ponto no total (Cho et al. 2024), cobrindo aproximação, recuo e reorientação que a reta não captura. Movimento médio por solda: IC 8,55 / K1 0,65 / K2 0,89 / K3 1,51 / **H 1,70** / regra de Cho 2,31 s. Ciclo do robô (movimento + solda): IC 73–105 s, **H 29–33 s**, faixa 20–39 s. **H aprovado como central (2026-11-11); K1 ↔ regra de Cho na sensibilidade.** Tabelas geradas em `x_plant-models/tt_cenario_H/` (8 `.txt` para colar no Plant + `memoria_calculo_H.csv` + `LEIAME.md` com método, fontes e resultado esperado). **c = 0,7287 s.** Previsão da v5 (v4 + TT do H): 436 carrocerias, **100,50 kWh = 0,2305 kWh/carroceria**, robôs 76,5–78,1% ociosos (R1 23,26 / R2 23,67 / R3 23,09 / R4 23,28 / skid 7,20 kWh). **v5 rodada (2026-11-12):** os robôs bateram com a previsão (R1 23,28 / R2 23,69 / R3 23,10 / R4 23,30 kWh; 76,5–78,0% ociosos; 436 carrocerias; colar as TT no Plant funcionou). **Mas o total deu 120,28 kWh:** o `SKID_EFQ_3` passou a andar **vazio** (Working 12,23 h = 76,5%, Empty 56,1%, 26,91 kWh contra 7,15 kWh de transporte real). Na v4 isso não aparecia porque os robôs ocupavam quase todo o takt. É um artefato do modelo: o Conveyor do Plant fica em Working enquanto gira, mesmo sem carga, e um skid real só se move para transportar. **Correção proposta (v6):** marcar *Automatic stop* no `SKID_EFQ_3` (o significado exato ainda não foi confirmado: validar pelo resultado). Esperado: skid ~7,2 kWh, total **~100,5 kWh = 0,2306 kWh/carroceria**, 436 carrocerias.

**v6 VALIDADA (2026-11-12, cenário `v6`) = NOVA BASELINE:** *Automatic stop* no skid → skid **7,16 kWh** (Working 3,255 h = 20,3%; o tempo vazio virou Operational/Waiting), total **100,532 kWh = 0,2306 kWh/carroceria**, 436 carrocerias, robôs idênticos à v5 (R1 23,28 / R2 23,69 / R3 23,10 / R4 23,30). Confirma que *Automatic stop* para o Conveyor quando está vazio. **Itens 1 e 2 da Fase 0 concluídos.** Incidente: a primeira rodada com *Automatic stop* saiu com o cenário `v5` e sobrescreveu o `v5_r01.json` (cópias em `_testes/`: `v5_r01_original_do_commit.json` = 120,28 kWh, o correto; `v5_r01_sobrescrito_com_autostop.json`). O `.spp` da v5 foi salvo às 12:01 e pode ter ficado com *Automatic stop* marcado. **Lição:** trocar o `str_cenario` antes de rodar.

**Histórico do desenho da v4 (concluída):**

Desenho proposto (2026-11-09; depende dos diagnósticos abaixo):
- Robô: Working = 2,6 kW (ISO cube, ABB rev. N; superestima movimento lento, revisar com a V nova), **Operational = 0,84 kW** (freios liberados), **Standby = 0,17 kW** (freios acionados, modo de economia da Fase 1).
- Solda: **manter o `startPause`** (o teste do `wait` mostrou que não há alternativa simples, ver abaixo) e dar ao **Standby = "Soldando" ≈ 4,6 kW** = 0,84 kW (robô parado) + ~3,75 kW (6 kJ ÷ 1,6 s; faixa 3,1–6,9 kW). Assim a energia da solda fica nativa no Plant.
- Modo de economia (freios acionados, 0,17 kW): ir para **outro estado**, provavelmente **Off** com tempo de power up como custo de retomada. Depende do print da aba Energy.
- Pico: 90 kVA como limite superior durante o pulso de corrente (hipótese).

Falta trazer do Plant:
1. ~~Teste "wait"~~ **Feito (cenário `wait_tempoSolda`, 2026-11-09): o `wait` num controle de entrada NÃO segura o robô.** O Plant aceita o `wait`, mas o PickAndPlace segue sem esperar. R1: −3.489,6 s de Standby (= 2.181 soldas × 1,6 s) viraram Waiting/Empty (robô vazio parado no home), Working só +1,6 s. O ciclo do sedan, em que o R1 é o gargalo, encurtou exatamente **8,0 s** (= 5 soldas × 1,6 s; skid +1.256 s / 157 sedans). Conclusão: a solda sumiu do ciclo. Manter o `startPause`. Um `wait` antes do `@.move` num controle de **saída** provavelmente seguraria o robô (o MU só sai no move), mas só cobre 4 das 9 soldas: não vale a pena.
2. ~~Print da aba Energy~~ **Feito (2026-11-09).** PickAndPlace: Power input Working / Setting-up (cinza) / Operational / Failed / Standby / Off, e **6 tempos de transição** (Operational↔Off, Operational↔Standby, Standby↔Off), todos 0, mais o campo "State" e o botão "State Transition". Valores da IC: Working 2,85, Operational 0, Failed 0, Standby 90, Off 0. Conveyor (skid): Working 2,2, Operational 0, **Failed 2,2, Off 2,2** (erro: hoje sem efeito, mas precisa ir a 0 antes da Fase 1), Standby desabilitado, transições Operational↔Off = 0.
   - **Configuração da v4:** robôs Working **2,6**, Operational **0,84**, Standby **4,59** (soldando), Off **0,17** (economia/freios), Failed 0 (a definir na Fase 1), transições 0. Skid: Off e Failed → 0. O **Off→Operational** será o tempo de retomada da Fase 1. Não usar tempo em Operational↔Standby, porque atrasaria cada solda.
   - **Resultado esperado (calculado com os tempos da v3):** total **154,7 kWh = 0,355 kWh/carroceria** (contra 750,66 e 1,722). R1 36,62 / R2 38,47 / R3 34,74 / R4 37,69 / skid 7,20. Com 5 / 11 kJ por ponto: 150,3 / 176,7 kWh. Tempos e throughput idênticos à v3.
   - **Controlador = IRC5 (decisão de 2026-11-09):** a célula não existe fisicamente, então é hipótese de projeto, justificada por ser a versão com spec ABB verificada para as potências parado/freios (3HAC044265-001 rev. N). No texto, citar a rev. N para as potências; a rev. K (2025) citada pela IC provavelmente é a spec OmniCore.
   - **v4 VALIDADA (2026-11-09, cenário `v4`):** tempos por estado **idênticos** à v3 (diferença 0,000 s em todos os recursos), 436 carrocerias, **154,717 kWh = previsão** (0,355 kWh/carroceria). R1 36,62 / R2 38,47 / R3 34,74 / R4 37,69 / skid 7,20. Potências efetivas conferidas (2,6 / 0,84 / 4,59). **A v4 é a nova baseline.**
   - **`ler_attr` (2026-11-09):** `EnergyPauseStartState = 'Standby'`, `EnergyPauseEndState = 'Previous state'`, `EnergyTargetState = 'Operational'`, `EnergyCurrentState = 'Operational'`. Confirma que o `startPause` leva ao Standby por configuração. O `EnergyTargetState` é o candidato a comando de economia na Fase 1 (`:= "Off"` / `"Operational"`), ainda a testar.
3. **Atributos de energia** do robô via `listar_attrs` (`scripts/diagnostico_plant.py`).
4. **Configuração do `ENTRADA_BIY`** (intervalo, seleção do MU, uso do `ListaBIW`) e do **`SKID_EFQ_3`** (comprimento, velocidade, sensor), para o takt.
5. ~~Exportar os Methods~~ feito: `def_inPosition` e `def_exitR2` da v3 e os `def_*R3/R4` estão em `infotmation-methods/`; R3 e R4 são iguais ao R1.

Velocidade realista (item 2): **não há fonte forte para a V**. A regra de 3,3 s/ponto (Cho, Kim e Park, WSC 2024, `z_references/tempo-solda.pdf`) é empírica e o próprio artigo mostra 72% de acurácia. Opções: usar a regra como referência com análise de sensibilidade, ou buscar a V programada típica (por exemplo, v1000 em RobotStudio) com fonte.

## 10. Histórico
- **2026-11-09:** contexto migrado do Claude web para o workspace (`copilot-instructions.md` → `CLAUDE.md`, removido o original). Pasta de resultados mudada de `C:\TCC\resultados` para `scripts\resultados` em `coleta_plant.py` e `gerar_relatorio.py` (agora a pasta padrão quando roda sem argumento).
- **2026-11-09:** analisados `def_inPosition`, `def_entranceR1`, `def_exitR1` e as tabelas (`x_plant-models/infotmation-methods/`). Achados: 9 soldas por robô (P10 = limpeza), V diferente por produto (HATCH 0,063, SEDAN 0,081 m/s), bordas da TT inconsistentes nas 8 tabelas e takt emergente. Instalado `openpyxl` (no site-packages do usuário: `%APPDATA%\Python\Python315`).
- **2026-11-09:** instalado o plotly 7.1.0 (estava faltando). `gerar_relatorio.py` validado com JSONs sintéticos (2 cenários × 2 réplicas): gerou um `relatorio.html` de ~5 MB sem erro. Falta validar com dados reais do Plant.
- **2026-11-09:** o usuário mostrou a TT_R1_SEDAN no Plant e a planilha de tempos de projeto. Diagnóstico: o P10→home foi digitado na coluna de P1 (linha 11, coluna 2 em vez de coluna 1) nas 8 tabelas.
- **2026-11-09:** lidos o relatório final da IC e a revisão sistemática (`z_references/`). Criada a seção 4.6. Unidade kWh, potências e datasheets confirmados. Achados críticos: a solda usa o estado Standby (90 kW) e o ocioso vale 0 kW, o que invalida a alavanca de standby sem remodelagem; a V do modelo é 20–25× menor que a máxima do IRB 6700 (1,6 m/s); o P10 é um Drain fictício (exceção no R2 SEDAN). A pasta `Referências/` foi renomeada para `z_references/`.
- **2026-11-09:** EndSim recriado do zero (o antigo foi apagado); variáveis `str_cenario`/`int_replica` criadas. 1º episódio real de 16 h (roda em menos de 15 s): `base_r01.json` reproduz a IC exatamente (436 carrocerias, 744,37 kWh, R1 183,94, Working 59,07%, Standby 1,744 h = 436 × 9 × 1,6 s). O relatório foi gerado, mas a **série temporal tem 1 ponto só**: falta o Generator chamando `amostrar`. Observação: o skid parado (`startPause` sem tempo) aparece como estado de energia **Operational** (12,7 h), não Standby, e em `porcao_estado` como Pausing (79,5%). A Tabela 13 da IC chama isso de "Standby".
- **2026-11-09:** **pipeline de resultados validado com dados reais.** Generator `amostrar_gen` (60 s) e Method `Reset` criados. `base_r01`/`base_r02` têm 961 pontos e são idênticos (modelo determinístico, IC ± 0). O relatório mostra 1,707 kWh/carroceria, 436 carrocerias, 744,4 kWh, robôs 29,3% ociosos e 59,8% em movimento. Problemas de apresentação pendentes: o Standby aparece como "Standby" mas é a solda; "trabalhando" significa só movimento; o gráfico de potência é a média de 60 s e esconde os picos de 90–360 kW; o `PARAMETROS` está desatualizado.
- **2026-11-09:** relatório ajustado: os rótulos dos estados vêm de `rotulos_estado` (Standby = "Soldando", Working = "Em movimento"), há um KPI novo de % em solda, o gráfico de potência avisa que é a média de 60 s, e os parâmetros aparecem com casas decimais limpas. O `PARAMETROS` foi atualizado com as fontes da IC. **Pendente:** o usuário colar o `coleta_plant.py` novo no PythonModule e rodar de novo.
- **2026-11-09:** relatório final validado com o `coleta_plant.py` novo (rótulos e 13 parâmetros com fonte no JSON). **Pipeline de resultados concluído.** Próximo passo: teste A/B da volta P10→home (usuário) e pesquisa das potências ociosa/standby e da energia por ponto (assistente).
- **2026-11-09:** teste A/B da volta P10→home (v2, cenário `tt_volta`): resultado idêntico à v1. O tempo de movimento medido bate com o de projeto incluindo a volta (< 0,1%). Não há bug; o item 3 de 4.3 foi fechado. O desvio do R2 na IC vem do cálculo do "esperado".
- **2026-11-09:** CORREÇÃO do registro anterior: o desvio do R2 na IC **não** é erro de cálculo. É bug do modelo: o R2 SEDAN deveria soldar 10 vezes e faz 9 (o P10 nunca solda). A conta fecha: 6,32 + 0,3 = 6,60 kWh.
- **2026-11-09:** criada a v3 (`celula-de-solda-tg-v3.spp`) com o R2 SEDAN soldando 10 vezes. Validada pelo cenário `r2_sedan`: +6,28 kWh só no R2, nada mais muda. Nova baseline: 750,66 kWh. Os `def_entranceR2`/`def_exitR2` antigos estão em `infotmation-methods/` (iguais aos do R1 com o índice trocado).
- **2026-11-09:** pesquisa de fontes de energia concluída (`z_references/fontes-parametros.md` + 3 PDFs). Resultado: o ocioso deve ser 0,84 kW (e não 0), o standby com freios 0,17 kW, e a solda 5–11 kJ por ponto (e não 144). Com isso, o total de um robô cairia de ~184 para ~35–38 kWh, e o potencial do standby fica em ~9% por robô na V atual. Ainda falta decidir como remodelar a solda e as potências no Plant.
- **2026-11-09:** validado o datasheet da GWT C9: 90 kVA é a potência S50 (50% de fator de serviço) do transformador MFDC, não o consumo. A IC aplicou 90 kW durante 1,6 s (144 kJ por ponto). Decisão recomendada: usar a **energia por ponto** da literatura (5–11 kJ) e manter os 90 kVA só como **limite superior de pico** durante a corrente. Ver `z_references/fontes-parametros.md` 3.1.
- **2026-11-09:** desenho da v4 proposto (seção 9): Operational 0,84 / Standby 0,17 kW, solda contada por ponto fora do Standby. Criado `scripts/diagnostico_plant.py`. Lido o `tempo-solda.pdf` (Cho et al., WSC 2024): os 3,3 s/ponto são regra empírica com 72% de acurácia.
- **2026-11-09:** teste do `wait` no `def_entranceR1` (cenário `wait_tempoSolda`): o `wait` não segura o PickAndPlace e a solda some do ciclo (ciclo do sedan −8,0 s). Decisão: manter o `startPause` e usar Standby = "Soldando" ≈ 4,6 kW; o modo de economia vai para outro estado (provavelmente Off), a confirmar pela aba Energy. **Indício para o item 2:** com o ciclo mais curto o throughput ficou em 436 e o skid passou a rodar vazio (+1.256 s), ou seja, o intervalo do `ENTRADA_BIY` já limita a linha em ~132 s. No base, o skid fica vazio só 75 s em 16 h (linha balanceada pela calibração da IC).
- **2026-11-09:** recebidos os prints da aba Energy (robô e skid). O Plant tem tempos de transição nativos entre Operational/Standby/Off, e o Off→Operational vira o custo de retomada da Fase 1. Definida a configuração da v4 (Working 2,6 / Operational 0,84 / Standby 4,59 / Off 0,17 kW; skid Off/Failed → 0). `coleta_plant.py` atualizado (PARAMETROS da v4; Off = "Economia - freios acionados"). Previsão: 154,7 kWh (0,355 kWh/carroceria).
- **2026-11-09:** prints do `ENTRADA_BIY` (intervalo constante de 2:12 = takt já imposto, MU selection Percentage) e do skid (8,05 m a 0,3 m/s = 26,83 s). `listar_attrs` revelou `EnergyTargetState`, `EnergyPause*State`, `PowerInput*` e `TransitionTime*`. Resultados reorganizados: `base` → `ic_original`, `r2_sedan` → `v3_r2_10soldas`, e os testes `tt_volta`/`wait_tempoSolda` foram para `scripts/resultados/_testes/`.
- **2026-11-09:** **v4 validada e adotada como baseline** (154,717 kWh, 0,355 kWh/carroceria, tempos idênticos à v3). Controlador IRC5 como hipótese de projeto (a célula não existe fisicamente). Velocidade do skid de 0,3 m/s pelo datasheet EFQ. Methods R3/R4 conferidos. `PARAMETROS` ganhou a velocidade do skid, o takt e o controlador. Próximo passo: item 2 (tempos de movimento realistas).
- **2026-11-09:** sem RobotStudio, criado `scripts/gerar_tt.py` (modelo cinemático com dados da spec ABB: 24 m/s², PSt 0,17 s, 1,6 m/s). Cenários K1/K2/K3/H e regra de Cho. Proposta: H (K2 + 0,73 s/trecho, calibrado em 3,3 s/ponto) como central. Os ciclos dos robôs caem de 73–105 s para 20–39 s em qualquer cenário, contra o takt de 132 s.
- **2026-11-09:** `git init` + commit inicial (modelos v1–v4, scripts, resultados, referências). Falta criar o repositório privado no GitHub e fazer o push.
- **2026-11-09:** primeiro push para github.com/g06rossi/tg-celula-solda (branch `main` rastreando `origin/main`).
- **2026-11-11:** cenário H aprovado. `gerar_tt.py` ganhou a memória de cálculo por trecho. Geradas as 8 TT em `x_plant-models/tt_cenario_H/` com `LEIAME.md` (método, fontes, limitações, resultado esperado). `coleta_plant.py`: as V calibradas da IC foram trocadas pelos parâmetros do modelo de TT. Previsão da v5: 100,50 kWh (0,2305 kWh/carroceria), ~77% de ociosidade.
- **2026-11-12:** v5 (TT do cenário H) rodada: robôs = previsão (~77% ociosos), 436 carrocerias. Achado: o skid anda vazio 56% do tempo (+19,8 kWh, artefato do Conveyor). Proposta: v6 com *Automatic stop* no skid.
- **2026-11-12:** **v6 validada (nova baseline):** *Automatic stop* no skid → 100,532 kWh, 0,2306 kWh/carroceria, robôs ~77% ociosos, 436 carrocerias. Itens 1 e 2 da Fase 0 concluídos. O `v5_r01.json` foi sobrescrito por engano; o original está guardado em `_testes/`.
- **2026-11-12:** restaurados do commit o `v5_r01.json` (120,28 kWh) e o `celula-de-solda-tg-v5.spp` (sem Automatic stop). O usuário confirmou que o mix é sorteado pelo Plant pela proporção da `ListaBIW`. Próximo: item 4 (sementes por réplica).
- **2026-11-12:** `listar_attrs` achou `RandomNumbersVariant` / `IncrementRandomNumbersVariantOnReset` no EventController e `RandomSeed` no `ENTRADA_BIY`. `coleta_plant.py` grava a variante e o mix estimado; o relatório ganhou a coluna Sedans. Próximo: EndSim trocando a variante por réplica e 10 réplicas da v6.
- **2026-11-12:** 10 réplicas da v6 com variantes 1..10: resultados idênticos. O mix (único elemento aleatório) não muda com a variante; suspeita de que o *Percentage* é determinístico. As réplicas entraram como `v6_r01..r10` (o cenário não foi trocado para `v6_rep`; mesma configuração da v6).
- **2026-11-12:** **v7 = v6 + MU selection Random: nova baseline estocástica.** 10 réplicas: sedans 144–166, 436 carrocerias fixas, 100,52 ± 0,02 kWh, 0,2306 kWh/carroceria. O *Percentage* mantinha a proporção fixa. Item 5 (KPIs) concluído; tempos com distribuição adiados para a Fase 1.
- **2026-11-12:** desenhado o teste do mecanismo de economia (EnergyTargetState Off/Operational no R1, via `def_inPosition`), com e sem tempo de retomada.
- **2026-11-12:** mecanismo de economia validado no R1 (`EnergyTargetState` Off/Operational): −8,20 kWh no R1 (−35%), retomada de 2 s custa 0,06 kWh, throughput 436. Alerta: com chegadas determinísticas, "dormir sempre" é ótimo e o RL fica trivial; é preciso definir a fonte de incerteza (chegadas, falhas, modos profundos) antes da Fase 3.
- **2026-11-13:** escrito `docs/opcoes-A-B-C-economia-RL.md` (opções A/B/C com referências, implementação no Plant, Python de otimização e RL, análise estatística). Novas fontes: white paper PROFIenergy (PI 2011, PDF salvo), Frigerio e Matta (2015), Loffredo et al. (2024), Alaka et al. (2025). O manual ABB PROFIenergy (3HAC050967) não pôde ser baixado.
- **2026-11-13:** usuário aprovou a ordem B → A → C e as referências. Manual ABB PROFIenergy inacessível; substituído pelo manual KUKA KR C4 PROFINET 2.2 (2012), com os tempos dos modos *Drive bus OFF* (volta em 20 s) e *Hibernate* (entra 50 s / volta 50 s). Hibernação ~18 W (Yokogawa/KUKA, C).
