# =====================================================================
# POLÍTICAS DE ECONOMIA - colar no PythonModule, ABAIXO do bloco de coleta
#
# O Plant só avisa eventos; o Python decide e comanda os 4 robôs:
#   evento("chegada")     -> def_inPosition, quando a carroceria chega (acorda os robôs)
#   evento("todos_home")  -> def_inPosition, quando os 4 robôs voltam ao home
#   tick()                -> Method chamado por um Generator a cada 10 s (decisões ao longo da pausa)
# A política é lida das Variables do Frame `str_politica` e `float_tau` (se existirem);
# senão valem as constantes abaixo.
#
# Políticas (item 13 do plano):
#   "nenhuma" : nunca economiza (referência; deve reproduzir a v10)
#   "freios"  : freios acionados sempre que todos voltam ao home; acorda na chegada
#   "timeout" : freios no home; se a pausa passar de TAU s, passa para hibernação
# Modos (ver docs/opcoes-A-B-C-economia-RL.md e z_references/fontes-parametros.md):
#   freios     : Off a 0,17 kW, entrada 0 s, retomada 0,15 s (ABB)
#   hibernacao : Off a 0,02 kW, entrada 50 s, retomada 50 s (KUKA KR C4; potência conf. C)
# =====================================================================

POLITICA_PADRAO = "nenhuma"
TAU_PADRAO = 300.0             # s desde "todos_home" para passar a hibernação (política timeout)
ROBOS = ["ABB_IRB_6700_1", "ABB_IRB_6700_2", "ABB_IRB_6700_3", "ABB_IRB_6700_4"]
MODOS = {
    "freios": {"p": 0.17, "t_in": 0.0, "t_out": 0.15},
    "hibernacao": {"p": 0.02, "t_in": 50.0, "t_out": 50.0},
}

_pol = {}


def _politica_reset():
    global _pol
    _pol = {"modo": "ligado", "desde": None, "n_freios": 0, "n_hib": 0, "n_acordar": 0,
            "pendente": None, "erros": []}


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


def _comandar(alvo, modo=None):
    """alvo: 'Operational' ou 'Off'. Para 'Off', ajusta antes potência e tempos do modo."""
    for n in ROBOS:
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
        if _pol["modo"] != "ligado":
            _comandar("Operational")
            _pol["n_acordar"] += 1
        _pol["modo"], _pol["desde"] = "ligado", None
    elif nome == "todos_home":
        _comandar("Off", "freios")
        _pol["n_freios"] += 1
        _pol["modo"], _pol["desde"] = "freios", _sim_time()


def tick():
    """Chamado a cada 10 s. Na política timeout, passa de freios a hibernação após TAU s.
    A troca é feita em dois ticks (acordar 0,15 s, depois Off com os parâmetros da hibernação),
    porque o robô já está no Off; custo: até 10 s a 0,84 kW por hibernação."""
    politica, tau = _config()
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
            "n_acordar": _pol["n_acordar"], "erros": _pol["erros"], "modos": MODOS}
