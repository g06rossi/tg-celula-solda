# =====================================================================
# COLETA DE RESULTADOS - colar dentro do PythonModule do Plant Simulation
# (pode ficar junto das funções de teste que já existem lá)
#
# Chamadas a partir do SimTalk:
#   amostrar                -> Method chamado por um Generator (ex.: a cada 60 s)
#   fechar_episodio(c, r)   -> chamado no EndSim; salva resultados/<c>_r<r>.json
#   limpar_episodio()       -> opcional, chamado num Method "Reset"
# =====================================================================
import os
import json
import datetime

# ---------- CONFIGURAÇÃO (ajuste aqui) ----------
PASTA_RESULTADOS = r"C:\Users\giova\Arquivos\UFABC\TG\scripts\resultados"

RECURSOS = ["ABB_IRB_6700_1", "ABB_IRB_6700_2", "ABB_IRB_6700_3",
            "ABB_IRB_6700_4", "SKID_EFQ_3"]
SAIDA = "SAIDA_BIY"            # Drain que conta as carrocerias prontas
UNIDADE_ENERGIA = "kWh"        # confira na aba de energia dos robôs

# Energia do arco de solda somada FORA do Plant (opção B): quando a pausa da solda vai para o
# estado Operational (EnergyPauseStartState = "Operational"), o Plant só cobra 0,84 kW do robô
# parado; a energia do arco (6 kJ por ponto) é somada aqui. Soldas = tempo em Pausing / tempo de solda.
SOLDA_NO_PYTHON = False         # False: EnergyPauseStartState não aceita "Operational" (2026-11-17); solda segue no Standby
E_ARCO_KJ = 6.0                 # Li et al. (SMWC 2004), faixa 5-11 kJ

# Parâmetros documentados no relatório (rastreabilidade para a banca).
# Atualize a cada mudança de modelo e cite a fonte.
# "IC" = Rossi & Silva, relatório final de Iniciação Científica (UFABC, 2025).
PARAMETROS = {
    "Produção real em 16 h (carrocerias)": {"valor": 437, "fonte": "FMEIB (2025), doc. interna; IC, Tab. 1"},
    "Mix hatch / sedan": {"valor": "279 / 158 (64% / 36%)", "fonte": "FMEIB (2025); IC, Tab. 1; ListaBIW"},
    "Tempo de ciclo médio real (s)": {"valor": 132, "fonte": "FMEIB (2025): 2:12 min; IC, Tab. 1"},
    "Soldas por robô por carroceria": {"valor": 9, "fonte": "IC, seção 4.3; def_exitR* (P10 é Drain fictício)"},
    "Modelo das TT (tempos de deslocamento)": {"valor": "cenário H", "fonte": "scripts/gerar_tt.py: trapézio v/a + PSt + c por trecho; ver x_plant-models/tt_cenario_H/LEIAME.md"},
    "Velocidade programada (m/s)": {"valor": 1.0, "fonte": "Hipótese: speeddata v1000 do RAPID (ABB)"},
    "Aceleração cartesiana (m/s²)": {"valor": 12.0, "fonte": "Metade da máx. 24 m/s² (controlled motion, 205/2.8): ABB 3HAC044265-001 rev. N, seção 1.5.5"},
    "Tempo de estabilização PSt (s)": {"valor": 0.17, "fonte": "ABB 3HAC044265-001 rev. N, seção 1.8.2 (ISO 9283, 205/2.80)"},
    "Sobrecusto por trecho c (s)": {"valor": 0.7287, "fonte": "Calibrado para 3,3 s/ponto (movimento + solda): Cho, Kim e Park, WSC 2024"},
    "Velocidade linear máxima IRB 6700 (m/s)": {"valor": 1.6, "fonte": "ABB, Product spec. IRB 6700, 3HAC080365-001 rev. K (2025)"},
    "Potência robô em movimento - Working (kW)": {"valor": 2.6, "fonte": "ABB 3HAC044265-001 rev. N (2019) p.15: ISO cube, vel. e carga máx., IRB 6700-205/2.80 (IRC5); superestima movimento lento"},
    "Potência robô parado, freios liberados - Operational (kW)": {"valor": 0.84, "fonte": "ABB 3HAC044265-001 rev. N (2019) p.15: brakes disengaged, 205/2.80"},
    "Energia por ponto de solda (kJ)": {"valor": 6.0, "fonte": "Li, Feng, Cerjanec, Grzadzinski, SMWC 2004: 4,7-7,3 kJ primária (MFDC/AC); sensibilidade 5-11 kJ"},
    "Potência soldando - Standby (kW)": {"valor": 4.59, "fonte": "0,84 (robô parado) + 6 kJ / 1,6 s (ciclo da pinça); GWT C9 = 90 kVA S50 é só limite de pico"},
    "Modo freios (Off): potência / retomada": {"valor": "0,17 kW / 0,15 s", "fonte": "ABB 3HAC044265-001 rev. N p.15 (brakes engaged); ABB 3HAC050948-001 rev. AD, Max Brake Release Time (6.7.11)"},
    "Modo hibernação (Off): potência / entrada / retomada": {"valor": "0,02 kW / 50 s / 50 s", "fonte": "Yokogawa/KUKA (~18 W, conf. C); KUKA KR C4 PROFINET 2.2 (2012), Hibernate (5.6.2.3)"},
    "Potência skid em movimento - Working (kW)": {"valor": 2.2, "fonte": "Expert-Tünkers, datasheet EFQ 1 (2024); IC, Tab. 11"},
    "Potência skid parado - Operational (kW)": {"valor": 0.0, "fonte": "IC, Tab. 11 - hipótese, a revisar"},
    "Velocidade do skid (m/s)": {"valor": 0.3, "fonte": "Expert-Tünkers, datasheet EFQ (2024), segundo o autor; SKID_EFQ_3: 8,05 m -> 26,83 s"},
    "Intervalo entre carrocerias - takt (s)": {"valor": 132, "fonte": "ENTRADA_BIY Interval Const 2:12 = ciclo médio real FMEIB (2025)"},
    "Paradas a montante (ENTRADA_BIY): disponibilidade / MTTR": {"valor": "ver nome do cenário", "fonte": "Hipótese com sensibilidade (A 95/85/72%, MTTR 5/10/15 min); 72% = Alaka et al. (2025); pausas >= 5 min: white paper PI (2011)"},
    "Controlador do robô": {"valor": "IRC5", "fonte": "Hipótese de projeto (a célula de referência não existe fisicamente); escolhido por ter a spec ABB com potências parado/freios (3HAC044265-001 rev. N)"},
}

# Como cada estado de energia do Plant é usado NESTE modelo (vai para o JSON e o relatório).
# A solda (startPause) fica no Standby: EnergyPauseStartState não aceita "Operational" (2026-11-17).
# Os dois modos de economia (freios e hibernação) usam o Off; o código troca PowerInputOff e os
# TransitionTime* antes de cada EnergyTargetState := "Off" (opção B, a validar).
ROTULOS_ESTADO = {
    "Working": "Em movimento (Working)",
    "Operational": "Ocioso/parado (Operational)",
    "Setup": "Setup",
    "Standby": "Soldando (Standby)",
    "Off": "Economia: freios ou hibernação (Off)",
    "Fail": "Falha (Fail)",
}

ESTADOS_ENERGIA = ["Working", "Operational", "Setup", "Standby", "Off", "Fail"]
ESTADOS_TEMPO = ["Working", "Waiting", "Blocking", "Fail", "Pausing", "Stopped",
                 "Empty", "PoweringUpDown", "Unplanned"]

_serie = {"t": []}
_eventos = []   # (tempo_s, nome): "chegada" e "todos_home" vindos do def_inPosition
_soldas = []    # (tempo_s, robo): início de cada solda, vindo dos def_entranceR*/def_exitR* (caminho 2)
KVA_PINCA = 90.0   # ABB GWT C9, transformador MFDC 90 kVA (S50)
_reservas = []    # (inicio, fim) das soldas reservadas (intertravamento de K soldas simultâneas)
_esperas = {}     # robo -> soma das esperas do intertravamento (s)


def _num(v):
    """Converte valores do Plant (timedelta, número, string) para float."""
    if v is None:
        return None
    if hasattr(v, "total_seconds"):
        return v.total_seconds()
    try:
        return float(v)
    except Exception:
        return None


def _attr(obj, nome):
    try:
        return _num(getattr(obj, nome))
    except Exception:
        return None


def _sim_time():
    return _attr(current.EventController, "SimTime") or 0.0


def limpar_episodio():
    global _serie, _eventos, _soldas, _reservas, _esperas
    _serie = {"t": []}
    _eventos = []
    _soldas = []
    _reservas = []
    _esperas = {}
    h = globals().get("_politica_reset")   # politicas.py, se colado
    if h:
        h()
    return "ok"


def evento(nome):
    """Registra um evento do ciclo (chamado no def_inPosition). Retorna o nº de eventos."""
    _eventos.append((_sim_time(), str(nome)))
    h = globals().get("_politica_evento")   # politicas.py, se colado
    if h:
        h(str(nome))
    return len(_eventos)


def solda(robo):
    """Registra o início de uma solda do robô (1..4). Chamado antes do startPause nos def_*."""
    _soldas.append((_sim_time(), int(robo)))
    return len(_soldas)


def _k_limite():
    """K = nº máximo de soldas simultâneas (Variable int_K do Frame; 4 = sem intertravamento)."""
    try:
        return max(1, int(_num(current.int_K.Value)))
    except Exception:
        return 4


def reservar_solda(robo):
    """Intertravamento reativo (Farrow 2004): devolve a espera d (s) até haver vaga para soldar
    com no máximo K soldas simultâneas. No SimTalk: ?.startPause(d + float_tempoSolda).
    Registra o início REAL da solda (agora + d) e a espera do robô."""
    global _reservas
    agora = _sim_time()
    w = _attr(current.float_tempoSolda, "Value") or 1.6
    K = _k_limite()
    _reservas = [(s, e) for s, e in _reservas if e > agora + 1e-9]
    h = globals().get("_politica_planejado")      # politicas.py: instante planejado (política plano)
    tp = h(robo) if h else None
    t0 = max(agora, tp) if tp is not None else agora
    t = t0
    for cand in [t0] + sorted(e for s, e in _reservas):
        if cand < t0:
            continue
        n = sum(1 for s, e in _reservas if s < cand + w - 1e-9 and e > cand + 1e-9)
        if n < K:
            t = cand
            break
    _reservas.append((t, t + w))
    if "_pol" in globals():
        globals()["_pol"].setdefault("ult_fim", {})[int(robo)] = t + w
    _soldas.append((t, int(robo)))
    _esperas[int(robo)] = _esperas.get(int(robo), 0.0) + (t - agora)
    return round(t - agora, 4)


def _ajuste_energia():
    """A espera do intertravamento fica dentro do startPause (Standby = potência de solda); o certo é o robô
    parado com freios liberados (Operational). Devolve o ajuste (kWh, negativo) a somar à energia do Plant."""
    tot = 0.0
    for r, d in _esperas.items():
        o = getattr(current, "ABB_IRB_6700_%d" % r)
        ps = _attr(o, "PowerInputStandby") or 4.59
        po = _attr(o, "PowerInputOperational") or 0.84
        tot -= d * (ps - po) / 3600.0
    return tot


def _simultaneidade():
    """Quantos robôs soldam ao mesmo tempo (cada solda dura float_tempoSolda): tempo em cada nível K."""
    if not _soldas:
        return None
    dur = _attr(current.float_tempoSolda, "Value") or 1.6
    ev = sorted([(t, 1) for t, _ in _soldas] + [(t + dur, -1) for t, _ in _soldas], key=lambda x: (x[0], x[1]))
    tempo, k, ult, kmax = {}, 0, None, 0
    for t, d in ev:
        if ult is not None and t > ult:
            tempo[k] = tempo.get(k, 0.0) + (t - ult)
        k += d; ult = t
    kmax = max([kk for kk, v in tempo.items() if v > 1e-6] or [0])   # ignora níveis de duração ~0 (arredondamento)
    return {"n_soldas": len(_soldas), "k_max": kmax, "kva_pico": kmax * KVA_PINCA,
            "tempo_por_k_s": {str(kk): round(v, 2) for kk, v in sorted(tempo.items())},
            "por_robo": {str(r): sum(1 for _, x in _soldas if x == r) for r in range(1, 5)},
            # dados brutos para análise fora do Plant (scripts/analise_soldas.py)
            "inicios_s": {str(r): [round(t, 3) for t, x in _soldas if x == r] for r in range(1, 5)},
            "chegadas_s": [round(t, 3) for t, n in _eventos if n == "chegada"]}


def _pausas():
    """Janelas ociosas da célula: de 'todos_home' até a 'chegada' seguinte (s)."""
    p, ini = [], None
    for t, n in _eventos:
        if n == "todos_home":
            ini = t
        elif n == "chegada" and ini is not None:
            p.append(round(t - ini, 2)); ini = None
    return p


def amostrar():
    """Grava energia acumulada e tempo acumulado por estado de energia de cada recurso."""
    t = _sim_time()
    if _serie["t"] and t < _serie["t"][-1]:   # simulação foi resetada sem limpar
        limpar_episodio()
    _serie["t"].append(t)
    for n in RECURSOS:
        o = getattr(current, n)
        r = _serie.setdefault(n, {"energia_acum": [], "tempo_estados": {e: [] for e in ESTADOS_ENERGIA}})
        r["energia_acum"].append(_attr(o, "StatEnergyTotalConsumption"))
        for e in ESTADOS_ENERGIA:
            r["tempo_estados"][e].append(_attr(o, "StatEnergy" + e + "Time"))
    return len(_serie["t"])


def _resumo_recurso(o):
    r = {
        "energia": {e: _attr(o, "StatEnergy" + e + "Consumption") for e in ESTADOS_ENERGIA},
        "energia_total": _attr(o, "StatEnergyTotalConsumption"),
        "tempo_energia": {e: _attr(o, "StatEnergy" + e + "Time") for e in ESTADOS_ENERGIA},
        "porcao_estado": {e: _attr(o, "Stat" + e + "Portion") for e in ESTADOS_TEMPO},
        "falhas": _attr(o, "StatFailCount"),
    }
    if o.Name.startswith("ABB"):
        ts = _attr(current.float_tempoSolda, "Value") or 1.6
        pausa = (_attr(o, "StatPausingPortion") or 0.0) * _sim_time()
        r["soldas"] = pausa / ts
        r["energia_arco"] = r["soldas"] * E_ARCO_KJ / 3600.0 if SOLDA_NO_PYTHON else 0.0
    return r


def _mix_estimado():
    """Sedans = soldas extras do R2 (10ª solda só no sedan). Usa a contagem de soldas registradas, se houver
    (robusta ao intertravamento); senão (Standby R2 - Standby R1) / tempo de solda."""
    try:
        if _soldas:
            n = _attr(getattr(current, SAIDA), "StatNumIn") or 0.0
            ns = sum(1 for _, r in _soldas if r == 2) - sum(1 for _, r in _soldas if r == 1)
            return {"sedan": ns, "hatch": int(n) - ns, "metodo": "nº de soldas do R2 - nº de soldas do R1"}
        ts = _attr(current.float_tempoSolda, "Value") or 1.6
        st1 = _attr(current.ABB_IRB_6700_1, "StatEnergyStandbyTime") or 0.0
        st2 = _attr(current.ABB_IRB_6700_2, "StatEnergyStandbyTime") or 0.0
        n = _attr(getattr(current, SAIDA), "StatNumIn") or 0.0
        ns = int(round((st2 - st1) / ts))
        return {"sedan": ns, "hatch": int(n) - ns, "metodo": "(Standby R2 - Standby R1) / tempo de solda"}
    except Exception as e:
        return {"erro": str(e)}


def fechar_episodio(cenario="base", replica=1):
    amostrar()  # garante o último ponto da série
    params = {k: dict(v) for k, v in PARAMETROS.items()}
    params["Tempo de solda por ponto (s)"] = {"valor": _attr(current.float_tempoSolda, "Value"),
                                              "fonte": "float_tempoSolda (modelo); FMEIB (2025), IC seção 3"}
    dados = {
        "cenario": str(cenario),
        "replica": int(replica),
        "gerado_em": datetime.datetime.now().isoformat(timespec="seconds"),
        "sim_time_s": _sim_time(),
        "throughput": _attr(getattr(current, SAIDA), "StatNumIn"),
        "unidade_energia": UNIDADE_ENERGIA,
        "energia_total_frame": _attr(current, "StatEnergyTotalConsumption"),
        "solda_no_python": SOLDA_NO_PYTHON,
        "parametros": params,
        "rotulos_estado": ROTULOS_ESTADO,
        "variante_aleatoria": _attr(current.EventController, "RandomNumbersVariant"),
        "mix": _mix_estimado(),
        "pausas_s": _pausas(),
        "soldas_simultaneas": _simultaneidade(),
        "intertravamento": {"K": _k_limite(), "espera_s": {str(r): round(d, 2) for r, d in _esperas.items()}},
        "ajuste_energia_kWh": _ajuste_energia(),
        "politica": globals()["_politica_info"]() if "_politica_info" in globals() else None,
        "recursos": {n: _resumo_recurso(getattr(current, n)) for n in RECURSOS},
        "serie": _serie,
    }
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)
    arq = os.path.join(PASTA_RESULTADOS, "%s_r%02d.json" % (cenario, int(replica)))
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)
    limpar_episodio()
    return arq
