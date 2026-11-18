# =====================================================================
# POLÍTICAS DE ECONOMIA - colar no PythonModule, ABAIXO do bloco de coleta
#
# O Plant só avisa eventos; o Python decide e comanda os 4 robôs:
#   evento("chegada")     -> def_inPosition, quando a carroceria chega (acorda os robôs)
#   evento("todos_home")  -> def_inPosition, quando os 4 robôs voltam ao home
#   tick()                -> Method chamado por um Generator a cada 1 s (decisões ao longo da pausa)
# A política é lida das Variables do Frame `str_politica` e `float_tau` (se existirem);
# senão valem as constantes abaixo.
#
# Políticas (item 13 do plano):
#   "nenhuma" : nunca economiza (referência; deve reproduzir a v10)
#   "freios"  : freios acionados sempre que todos voltam ao home; acorda na chegada
#   "timeout" : freios no home; se a pausa passar de TAU s, passa para hibernação
#   "plano"   : caminho 2, escalonamento planejado das soldas (PLANO_ARQ, gerado por otimiza_pico.py):
#               cada robô começa e solda no instante planejado, acorda só na sua hora e aciona os
#               freios quando ele próprio volta ao home (tick a cada 1 s). O limite K continua garantido
#               pelo reservar_solda (coleta_plant.py).
# Modos (ver docs/opcoes-A-B-C-economia-RL.md e z_references/fontes-parametros.md):
#   freios     : Off a 0,17 kW, entrada 0 s, retomada 0,15 s (ABB)
#   hibernacao : Off a 0,02 kW, entrada 50 s, retomada 50 s (KUKA KR C4; potência conf. C)
# =====================================================================
import json

POLITICA_PADRAO = "nenhuma"
TAU_PADRAO = 300.0             # s desde "todos_home" para passar a hibernação (política timeout)
ROBOS = ["ABB_IRB_6700_1", "ABB_IRB_6700_2", "ABB_IRB_6700_3", "ABB_IRB_6700_4"]
MODOS = {
    "freios": {"p": 0.17, "t_in": 0.0, "t_out": 0.15},
    "hibernacao": {"p": 0.02, "t_in": 50.0, "t_out": 50.0},
}

PLANO_ARQ = r"C:\Users\giova\Arquivos\UFABC\TG\scripts\resultados\otimizacao\plano_K1_fim70.json"
ANTECEDENCIA = 0.2            # s: acorda o robô antes de criar os MUs dele (retomada dos freios = 0,15 s)

_pol = {}
_plano_cache = {}


def _politica_reset():
    global _pol
    _pol = {"modo": "ligado", "desde": None, "n_freios": 0, "n_hib": 0, "n_acordar": 0,
            "pendente": None, "erros": [],
            "chegada_t": None, "produto": None, "contagem": {}, "freado": set(), "n_freio_robo": 0, "ult_fim": {}}


_politica_reset()


def _config():
    nome, tau = POLITICA_PADRAO, TAU_PADRAO
    try:
        nome = str(current.str_politica.Value)
    except Exception:
        pass
    try:
        tau = float(_num(current.float_tau.Value))
    except Exception:
        pass
    return nome, tau


def _comandar(alvo, modo=None, robos=None):
    """alvo: 'Operational' ou 'Off'. Para 'Off', ajusta antes potência e tempos do modo."""
    for n in (robos or ROBOS):
        try:
            o = getattr(current, n)
            if alvo == "Off":
                m = MODOS[modo]
                o.PowerInputOff = m["p"]
                o.TransitionTimeOperationalToOff = m["t_in"]
                o.TransitionTimeOffToOperational = m["t_out"]
            o.EnergyTargetState = alvo
        except Exception as e:
            if len(_pol["erros"]) < 5:
                _pol["erros"].append("%s %s: %s" % (n, alvo, e))


def _politica_evento(nome):
    politica, tau = _config()
    if politica == "nenhuma":
        return
    if nome == "chegada":
        _pol["pendente"] = None
        _pol["chegada_t"], _pol["produto"] = _sim_time(), _produto()
        _pol["contagem"], _pol["freado"], _pol["ult_fim"] = {}, set(), {}
        if politica == "plano":          # cada robô é acordado na sua hora por inicio_robo
            _pol["modo"], _pol["desde"] = "ligado", None
            return
        if _pol["modo"] != "ligado":
            _comandar("Operational")
            _pol["n_acordar"] += 1
        _pol["modo"], _pol["desde"] = "ligado", None
    elif nome == "todos_home":
        _comandar("Off", "freios")
        _pol["n_freios"] += 1
        _pol["modo"], _pol["desde"] = "freios", _sim_time()


def _produto():
    try:
        return "Sedan" if "SEDAN" in str(current.str_modeloAtual.Value).upper() else "Hatch"
    except Exception:
        return "Hatch"


def _plano_robo(r):
    """Dados do plano para o robô r no produto da carroceria atual (ou None fora da política plano)."""
    if _config()[0] != "plano":
        return None
    if PLANO_ARQ not in _plano_cache:
        with open(PLANO_ARQ, encoding="utf-8") as f:
            _plano_cache[PLANO_ARQ] = json.load(f)
    return _plano_cache[PLANO_ARQ]["produtos"][_pol["produto"] or _produto()]["robos"][str(int(r))]


def robo_na_ordem(k):
    """k-ésimo robô a começar (1..4). Na política plano, por ordem de início; senão, k."""
    if _plano_robo(1) is None:
        return int(k)
    ordem = sorted(range(1, 5), key=lambda r: _plano_robo(r)["inicio_s"])
    return ordem[int(k) - 1]


def espera_ate_robo(k):
    """Quanto o def_inPosition deve esperar (s) antes de acordar o k-ésimo robô (0 fora do plano)."""
    pr = _plano_robo(robo_na_ordem(k))
    if pr is None or _pol["chegada_t"] is None:
        return 0.0
    return round(max(0.0, _pol["chegada_t"] + pr["inicio_s"] - ANTECEDENCIA - _sim_time()), 4)


def inicio_robo(r):
    """Acorda o robô r (só na política plano; nas outras ele já foi acordado na chegada)."""
    if _plano_robo(r) is not None:
        _comandar("Operational", robos=["ABB_IRB_6700_%d" % int(r)])
        _pol["n_acordar"] += 1
    return 1


def _politica_planejado(r):
    """Instante planejado (absoluto) da próxima solda do robô r; conta as soldas do robô na carroceria."""
    r = int(r)
    i = _pol["contagem"].get(r, 0)
    _pol["contagem"][r] = i + 1
    pr = _plano_robo(r)
    if pr is None or _pol["chegada_t"] is None or i >= len(pr["soldas_s"]):
        return None
    return _pol["chegada_t"] + pr["soldas_s"][i]


def _freios_por_robo():
    """Política plano: aciona os freios de cada robô quando ele terminou as soldas e voltou ao home."""
    agora, n = _sim_time(), 0
    for r in range(1, 5):
        if r in _pol["freado"]:
            continue
        pr = _plano_robo(r)
        if pr is None or _pol["contagem"].get(r, 0) < len(pr["soldas_s"]):
            continue
        if agora >= _pol["ult_fim"].get(r, 0) + pr["cauda_s"]:
            _comandar("Off", "freios", robos=["ABB_IRB_6700_%d" % r])
            _pol["freado"].add(r)
            _pol["n_freio_robo"] += 1
            n += 1
    return n


def tick():
    """Chamado a cada 1 s (Generator). Na política timeout, passa de freios a hibernação após TAU s.
    A troca é feita em dois ticks (acordar 0,15 s, depois Off com os parâmetros da hibernação),
    porque o robô já está no Off; custo: até 10 s a 0,84 kW por hibernação."""
    politica, tau = _config()
    if politica == "plano":
        return _freios_por_robo()
    if politica != "timeout":
        return 0
    if _pol["pendente"] == "hibernar":
        _comandar("Off", "hibernacao")
        _pol["n_hib"] += 1
        _pol["modo"], _pol["pendente"] = "hibernacao", None
        return 2
    if _pol["modo"] == "freios" and _pol["desde"] is not None and _sim_time() - _pol["desde"] >= tau:
        _comandar("Operational")
        _pol["pendente"] = "hibernar"
        return 1
    return 0


def _politica_info():
    politica, tau = _config()
    return {"politica": politica, "tau_s": tau if politica == "timeout" else None,
            "n_freios": _pol["n_freios"], "n_hibernacoes": _pol["n_hib"],
            "n_acordar": _pol["n_acordar"], "n_freio_por_robo": _pol["n_freio_robo"],
            "plano": PLANO_ARQ if politica == "plano" else None, "erros": _pol["erros"], "modos": MODOS}
