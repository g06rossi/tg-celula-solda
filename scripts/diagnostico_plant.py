# =====================================================================
# DIAGNÓSTICO - colar no PythonModule (abaixo do bloco de coleta)
# Serve para descobrir atributos e métodos de objetos do Plant sem
# adivinhar API. Chamar a partir de um Method SimTalk e imprimir o retorno.
#
#   var s : string := PythonModule.call("listar_attrs", "ABB_IRB_6700_1", "energ,standby,power,pause,off,state")
#   print s
# =====================================================================


def listar_attrs(nome_objeto, filtros=""):
    """Lista os nomes de atributos/métodos do objeto que contêm algum dos filtros
    (separados por vírgula, sem diferenciar maiúsculas). Sem filtro, lista tudo."""
    try:
        o = getattr(current, nome_objeto)
    except Exception as e:
        return "ERRO ao acessar %s: %s" % (nome_objeto, e)
    try:
        nomes = dir(o)
    except Exception as e:
        return "ERRO no dir(%s): %s" % (nome_objeto, e)
    fs = [f.strip().lower() for f in str(filtros).split(",") if f.strip()]
    if fs:
        nomes = [n for n in nomes if any(f in n.lower() for f in fs)]
    return "%s (%d): %s" % (nome_objeto, len(nomes), " | ".join(nomes))


def ler_attr(nome_objeto, atributo):
    """Lê um atributo e devolve o valor como texto (para conferir valores configurados)."""
    try:
        v = getattr(getattr(current, nome_objeto), atributo)
        if hasattr(v, "total_seconds"):
            return "%s.%s = %s s" % (nome_objeto, atributo, v.total_seconds())
        return "%s.%s = %r" % (nome_objeto, atributo, v)
    except Exception as e:
        return "ERRO lendo %s.%s: %s" % (nome_objeto, atributo, e)
