"""
Gera um relatório HTML (arquivo único, funciona offline) a partir dos JSONs
salvos pelo PythonModule do Plant Simulation.

Uso:
    C:\\Python315\\python.exe gerar_relatorio.py C:\\Users\\giova\\Arquivos\\UFABC\\TG\\scripts\\resultados
    (sem argumento, usa essa mesma pasta por padrão)
Saída:
    C:\\Users\\giova\\Arquivos\\UFABC\\TG\\scripts\\resultados\\relatorio.html
"""
import sys
import os
import glob
import json
import html
import math
import statistics
import datetime

import plotly.graph_objects as go
import plotly.io as pio

CORES_ESTADO = {
    "Working": "#E8A33D", "Operational": "#5B8DEF", "Setup": "#9B6BD6",
    "Standby": "#3DB98A", "Off": "#9AA0A6", "Fail": "#E05252",
}
# Rótulos padrão; o JSON pode sobrescrever com "rotulos_estado" (ver ROTULOS_ESTADO no coleta_plant.py),
# porque o significado de cada estado depende do modelo (na IC, Standby = solda).
NOMES_ESTADO = {
    "Working": "Working", "Operational": "Operational", "Setup": "Setup",
    "Standby": "Standby", "Off": "Off", "Fail": "Fail",
}


def nome(ep, estado):
    return (ep.get("rotulos_estado") or {}).get(estado, NOMES_ESTADO[estado])


def passo_amostragem(ep):
    t = ep["serie"].get("t", [])
    dts = sorted(b - a for a, b in zip(t, t[1:]) if b > a)
    return dts[len(dts) // 2] if dts else None
LAYOUT = dict(template="plotly_white", font=dict(family="Segoe UI, Arial", size=13),
              margin=dict(l=60, r=20, t=50, b=50), legend=dict(orientation="h", y=-0.2, x=0))

# valores críticos da t de Student (bicaudal, 95%) para gl = 1..30
T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
       2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
       2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]


def media_ic(valores):
    v = [x for x in valores if x is not None]
    if not v:
        return None, None
    m = statistics.mean(v)
    if len(v) < 2:
        return m, 0.0
    t = T95[len(v) - 2] if len(v) - 1 <= 30 else 1.96
    return m, t * statistics.stdev(v) / math.sqrt(len(v))


def fmt(x, casas=2):
    if x is None:
        return "–"
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_param(x):
    """Inteiros sem casas; demais com até 3 casas, sem zeros à direita."""
    if isinstance(x, int) or float(x).is_integer():
        return fmt(x, 0)
    s = fmt(x, 3)
    return s.rstrip("0").rstrip(",") if "," in s else s


def carregar(pasta):
    eps = []
    for arq in sorted(glob.glob(os.path.join(pasta, "*.json"))):
        with open(arq, encoding="utf-8") as f:
            d = json.load(f)
        d["_arquivo"] = os.path.basename(arq)
        eps.append(d)
    return eps


def kpis(ep):
    rec = ep["recursos"]
    robos = [n for n in rec if n.startswith("ABB")]
    sim = ep["sim_time_s"] or 1
    total = ep.get("energia_total_frame") or sum((r["energia_total"] or 0) for r in rec.values())
    thr = ep["throughput"] or 0
    ocioso = [((rec[r]["tempo_energia"].get("Operational") or 0) / sim) for r in robos]
    trabalhando = [((rec[r]["tempo_energia"].get("Working") or 0) / sim) for r in robos]
    standby = [((rec[r]["tempo_energia"].get("Standby") or 0) / sim) for r in robos]
    return {
        "energia_total": total,
        "throughput": thr,
        "energia_por_carroceria": total / thr if thr else None,
        "ociosidade_media": statistics.mean(ocioso) if ocioso else None,
        "trabalho_medio": statistics.mean(trabalhando) if trabalhando else None,
        "standby_medio": statistics.mean(standby) if standby else None,
        "horas": sim / 3600,
    }


# ------------------------------------------------------------------ gráficos
def fig_energia_estado(ep):
    rec, u = ep["recursos"], ep["unidade_energia"]
    nomes = list(rec)
    fig = go.Figure()
    for e, cor in CORES_ESTADO.items():
        vals = [rec[n]["energia"].get(e) or 0 for n in nomes]
        if any(vals):
            fig.add_bar(name=nome(ep, e), x=nomes, y=vals, marker_color=cor,
                        hovertemplate="%{x}<br>" + nome(ep, e) + ": %{y:.1f} " + u + "<extra></extra>")
    fig.update_layout(barmode="stack", title="Energia por recurso e por estado", yaxis_title=u, **LAYOUT)
    return fig


def fig_tempo_estado(ep):
    rec = ep["recursos"]
    sim = ep["sim_time_s"] or 1
    nomes = list(rec)
    fig = go.Figure()
    for e, cor in CORES_ESTADO.items():
        vals = [100 * (rec[n]["tempo_energia"].get(e) or 0) / sim for n in nomes]
        if any(vals):
            fig.add_bar(name=nome(ep, e), y=nomes, x=vals, orientation="h", marker_color=cor,
                        hovertemplate="%{y}<br>" + nome(ep, e) + ": %{x:.1f}%<extra></extra>")
    fig.update_layout(barmode="stack", title="Tempo em cada estado (% do turno)",
                      xaxis_title="% do tempo simulado", xaxis_range=[0, 100], **LAYOUT)
    return fig


def fig_energia_tempo(ep):
    s, u = ep["serie"], ep["unidade_energia"]
    t = s.get("t", [])
    if len(t) < 2:
        return None
    horas = [x / 3600 for x in t]
    nomes = [n for n in s if n != "t"]
    total = [sum((s[n]["energia_acum"][i] or 0) for n in nomes) for i in range(len(t))]
    pot = [None] + [
        (total[i] - total[i - 1]) / ((t[i] - t[i - 1]) / 3600) if t[i] > t[i - 1] else None
        for i in range(1, len(t))
    ]
    fig = go.Figure()
    fig.add_scatter(x=horas, y=total, name=f"Energia acumulada ({u})", line=dict(color="#E8A33D", width=3))
    dt = passo_amostragem(ep)
    fig.add_scatter(x=horas, y=pot, name=f"Potência média em janelas de {dt:.0f} s (kW)", yaxis="y2",
                    line=dict(color="#5B8DEF", width=1.5))
    fig.update_layout(title="Energia acumulada e potência da célula ao longo do turno",
                      xaxis_title="Tempo simulado (h)", yaxis_title=u,
                      yaxis2=dict(title="kW", overlaying="y", side="right", showgrid=False), **LAYOUT)
    return fig


def fig_linha_tempo(ep):
    """Estado predominante de cada recurso em cada intervalo de amostragem."""
    s = ep["serie"]
    t = s.get("t", [])
    if len(t) < 2:
        return None
    estados = list(CORES_ESTADO)
    nomes = [n for n in s if n != "t"]
    z, txt = [], []
    for n in nomes:
        linha, ltxt = [], []
        te = s[n]["tempo_estados"]
        for i in range(1, len(t)):
            deltas = [(te[e][i] or 0) - (te[e][i - 1] or 0) for e in estados]
            k = max(range(len(estados)), key=lambda j: deltas[j])
            linha.append(k if max(deltas) > 0 else None)
            ltxt.append(nome(ep, estados[k]) if max(deltas) > 0 else "")
        z.append(linha)
        txt.append(ltxt)
    horas = [x / 3600 for x in t[1:]]
    n_e = len(estados)
    escala = []
    for j, e in enumerate(estados):
        escala += [[j / n_e, CORES_ESTADO[e]], [(j + 1) / n_e, CORES_ESTADO[e]]]
    fig = go.Figure(go.Heatmap(z=z, x=horas, y=nomes, text=txt, zmin=-0.5, zmax=n_e - 0.5,
                               colorscale=escala, showscale=False,
                               hovertemplate="%{y}<br>%{x:.2f} h<br>%{text}<extra></extra>"))
    for e in estados:  # legenda manual
        fig.add_scatter(x=[None], y=[None], mode="markers", name=nome(ep, e),
                        marker=dict(size=12, color=CORES_ESTADO[e], symbol="square"))
    fig.update_layout(title="Linha do tempo: estado predominante por intervalo",
                      xaxis_title="Tempo simulado (h)", **LAYOUT)
    return fig


def fig_comparacao(grupos):
    nomes = list(grupos)
    medias, ics = [], []
    for c in nomes:
        m, ic = media_ic([kpis(e)["energia_por_carroceria"] for e in grupos[c]])
        medias.append(m)
        ics.append(ic)
    fig = go.Figure(go.Bar(x=nomes, y=medias, marker_color="#E8A33D",
                           error_y=dict(type="data", array=ics, visible=True),
                           hovertemplate="%{x}<br>%{y:.3f} ± %{error_y.array:.3f}<extra></extra>"))
    fig.update_layout(title="Energia por carroceria por cenário (média ± IC 95%)",
                      yaxis_title="energia / carroceria", **LAYOUT)
    return fig


# ------------------------------------------------------------------ HTML
def tabela(cabecalho, linhas):
    th = "".join(f"<th>{html.escape(str(c))}</th>" for c in cabecalho)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in linhas)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


def cartao(rotulo, valor, sub=""):
    return (f'<div class="card"><div class="lbl">{rotulo}</div>'
            f'<div class="val">{valor}</div><div class="sub">{sub}</div></div>')


def gerar(pasta):
    eps = carregar(pasta)
    if not eps:
        sys.exit(f"Nenhum JSON encontrado em {pasta}")
    grupos = {}
    for e in eps:
        grupos.setdefault(e["cenario"], []).append(e)

    figs_js = [False]

    def emb(fig):
        if fig is None:
            return "<p class='nota'>Série temporal indisponível (Generator de amostragem não configurado).</p>"
        inc = not figs_js[0]
        figs_js[0] = True
        fig.update_layout(height=440)
        return pio.to_html(fig, include_plotlyjs=inc, full_html=False,
                           default_width="100%", default_height="440px",
                           config={"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2}})

    partes = []
    # comparação entre cenários
    linhas = []
    for c, lst in grupos.items():
        ks = [kpis(e) for e in lst]
        def mi(chave, casas=2, pct=False):
            m, ic = media_ic([k[chave] for k in ks])
            if m is None:
                return "–"
            f = 100 if pct else 1
            return f"{fmt(m * f, casas)} ± {fmt(ic * f, casas)}" + ("%" if pct else "")
        linhas.append([html.escape(c), len(lst), mi("energia_por_carroceria", 3), mi("throughput", 1),
                       mi("energia_total", 1), mi("ociosidade_media", 1, True), mi("trabalho_medio", 1, True),
                       mi("standby_medio", 1, True)])
    partes.append("<h2>Comparação entre cenários</h2>")
    ep0 = eps[0]
    partes.append(tabela(["Cenário", "Replicações", "Energia / carroceria", "Carrocerias", "Energia total",
                          "Robôs: " + nome(ep0, "Operational"), "Robôs: " + nome(ep0, "Working"),
                          "Robôs: " + nome(ep0, "Standby")], linhas))
    if len(grupos) > 1:
        partes.append(emb(fig_comparacao(grupos)))

    # detalhe de cada cenário (primeira replicação)
    for c, lst in grupos.items():
        ep = sorted(lst, key=lambda e: e["replica"])[0]
        k, u = kpis(ep), ep["unidade_energia"]
        partes.append(f"<h2>Cenário: {html.escape(c)} <span class='tag'>replicação {ep['replica']}</span></h2>")
        partes.append('<div class="cards">' +
                      cartao("Energia por carroceria", fmt(k["energia_por_carroceria"], 3), u) +
                      cartao("Carrocerias produzidas", fmt(k["throughput"], 0), f"em {fmt(k['horas'], 1)} h simuladas") +
                      cartao("Energia total", fmt(k["energia_total"], 1), u) +
                      cartao("Robôs: " + nome(ep, "Operational"), fmt(100 * (k["ociosidade_media"] or 0), 1) + "%", "média dos 4 robôs") +
                      "</div>")
        partes.append('<div class="grid">' + emb(fig_energia_estado(ep)) + emb(fig_tempo_estado(ep)) + "</div>")
        partes.append(emb(fig_energia_tempo(ep)))
        if passo_amostragem(ep):
            partes.append(f"<p class='nota'>A potência é a média em cada janela de amostragem "
                          f"({passo_amostragem(ep):.0f} s). Picos instantâneos (vários robôs soldando ao mesmo tempo) "
                          f"não aparecem aqui; para o pico de potência use o EnergyAnalyzer do modelo ou uma amostragem por evento.</p>")
        partes.append(emb(fig_linha_tempo(ep)))
        lin = []
        for n, r in ep["recursos"].items():
            lin.append([n, fmt(r["energia_total"], 1)] +
                       [fmt(100 * (r["tempo_energia"].get(e) or 0) / (ep["sim_time_s"] or 1), 1) + "%"
                        for e in ["Working", "Operational", "Standby", "Fail"]] +
                       [fmt(r.get("falhas"), 0)])
        partes.append(tabela(["Recurso", f"Energia ({u})"] + [nome(ep, e) for e in ["Working", "Operational", "Standby", "Fail"]]
                             + ["Nº falhas"], lin))
        partes.append("<h3>Parâmetros do modelo</h3>")
        partes.append(tabela(["Parâmetro", "Valor", "Fonte"],
                             [[html.escape(p), fmt_param(v.get("valor")) if isinstance(v.get("valor"), (int, float)) else html.escape(str(v.get("valor"))),
                               html.escape(str(v.get("fonte", "")))] for p, v in ep["parametros"].items()]))

    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    doc = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Relatório da célula de solda</title>
<style>
body{{font-family:"Segoe UI",Arial,sans-serif;margin:0;background:#f6f7f9;color:#1f2328}}
header{{background:#1f3a5f;color:#fff;padding:24px 40px}}
header h1{{margin:0;font-size:24px}} header p{{margin:6px 0 0;opacity:.8}}
main{{max-width:1300px;margin:0 auto;padding:10px 40px 60px}}
h2{{margin-top:40px;border-bottom:2px solid #E8A33D;padding-bottom:6px}}
.tag{{font-size:13px;background:#e9edf3;color:#445;padding:3px 8px;border-radius:10px;vertical-align:middle}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:16px 0}}
.card{{background:#fff;border-radius:12px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.lbl{{font-size:13px;color:#667}} .val{{font-size:28px;font-weight:600;margin-top:4px}} .sub{{font-size:12px;color:#889}}
.grid{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}}
.grid>div,main>div:not(.cards):not(.grid){{background:#fff;border-radius:12px;margin:16px 0;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
table{{border-collapse:collapse;width:100%;background:#fff;border-radius:12px;overflow:hidden;margin:12px 0;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
th,td{{padding:9px 12px;text-align:left;font-size:14px;border-bottom:1px solid #eef0f3}}
th{{background:#e9edf3}} .nota{{color:#889;font-style:italic}}
</style></head><body>
<header><h1>Relatório da célula de solda a ponto</h1>
<p>{len(eps)} execução(ões) · {len(grupos)} cenário(s) · gerado em {agora}</p></header>
<main>{''.join(partes)}</main></body></html>"""
    saida = os.path.join(pasta, "relatorio.html")
    with open(saida, "w", encoding="utf-8") as f:
        f.write(doc)
    return saida


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\giova\Arquivos\UFABC\TG\scripts\resultados"
    print("Relatório salvo em:", gerar(pasta))
