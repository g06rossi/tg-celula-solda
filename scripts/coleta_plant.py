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
    global _serie
    _serie = {"t": []}
    return "ok"


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
        "recursos": {n: _resumo_recurso(getattr(current, n)) for n in RECURSOS},
        "serie": _serie,
    }
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)
    arq = os.path.join(PASTA_RESULTADOS, "%s_r%02d.json" % (cenario, int(replica)))
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)
    limpar_episodio()
    return arq
