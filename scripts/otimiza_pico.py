"""
Caminho 2: escalonamento ótimo das soldas para limitar o pico de potência (K soldas simultâneas).

Roda FORA do Plant, com o Python 3.13 (OR-Tools não tem versão para o 3.15 do Plant):
    C:\\Users\\giova\\AppData\\Local\\Programs\\Python\\Python313\\python.exe scripts\\otimiza_pico.py

Modelo (programação por restrições, CP-SAT, resolvido de forma exata), por modelo de carroceria:
- cada robô r tem uma sequência fixa de soldas de 1,6 s; entre elas, os trajetos do cenário H (gerar_tt.py);
- variáveis: instante de início de cada solda (inteiro, em centésimos de segundo);
- precedência: solda_i >= fim da solda anterior + trajeto (esperas permitidas = intertravamento);
- a primeira solda começa depois do trajeto home -> P1 a partir de um início livre s_r >= 0
  (o robô fica em economia até s_r; ver politicas.py);
- fim do robô = fim da última solda + trajetos até o home;
- AddCumulative: no máximo K soldas ao mesmo tempo (K = 1..4);
- (a) minimizar o fim do ciclo (makespan);
- (b) com o fim do ciclo <= janela - margem, minimizar a soma das esperas DEPOIS do início de cada robô
  (robô acordado e parado = 0,84 kW em vez de 0,17 kW com freios).
Janela por carroceria: 132 s de takt - 8,05 m / 0,3 m/s de skid = 105,2 s.
Validação do modelo da linha do tempo: reproduz a v12 com erro < 1% (CLAUDE.md).
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_tt as g
from ortools.sat.python import cp_model

ESC = 100                      # centésimos de segundo
SOLDA = 1.6
JANELA = 132 - 8.05 / 0.3      # 105,2 s
P_ACORDADO, P_FREIOS = 0.84, 0.17
KVA = 90.0
TEMPO_LIMITE = 30.0            # s por resolução


def sequencias(mod):
    """Por robô: d0 (home->P1), lista de trajetos entre soldas consecutivas, cauda (última solda -> home)."""
    tc, tt = g.carregar()
    c = g.calibrar_c(tc, tt)
    v, a, pst, _ = g.CENARIOS["K2"]
    seqs = {}
    for r in range(1, 5):
        M, _ = g.matriz(tc, tt, r, mod, v, a, pst, c)
        pontos = [p for p in range(1, 11) if p <= 9 or (r == 2 and mod == "Sedan")]
        d0 = M[0][1]
        entre = [sum(M[q][q + 1] for q in range(p, pontos[i + 1])) for i, p in enumerate(pontos[:-1])]
        ult = pontos[-1]
        cauda = sum(M[q][q + 1] for q in range(ult, 10)) + M[10][0]
        seqs[r] = {"d0": d0, "entre": entre, "cauda": cauda, "n": len(pontos)}
    return seqs


def resolver(mod, K, limite_fim=None):
    seqs = sequencias(mod)
    H = int(3 * JANELA * ESC)
    m = cp_model.CpModel()
    w = int(round(SOLDA * ESC))
    ini, intervalos, fins, esperas = {}, [], [], []
    for r, s in seqs.items():
        st = m.NewIntVar(0, H, "s_%d" % r)
        xs = [m.NewIntVar(0, H, "x_%d_%d" % (r, i)) for i in range(s["n"])]
        m.Add(xs[0] >= st + int(round(s["d0"] * ESC)))
        esperas.append(xs[0] - st - int(round(s["d0"] * ESC)))
        for i in range(1, s["n"]):
            mv = int(round(s["entre"][i - 1] * ESC))
            m.Add(xs[i] >= xs[i - 1] + w + mv)
            esperas.append(xs[i] - xs[i - 1] - w - mv)
        for i, x in enumerate(xs):
            intervalos.append(m.NewFixedSizeIntervalVar(x, w, "I_%d_%d" % (r, i)))
        fim = m.NewIntVar(0, H, "f_%d" % r)
        m.Add(fim == xs[-1] + w + int(round(s["cauda"] * ESC)))
        fins.append(fim)
        ini[r] = (st, xs)
    m.AddCumulative(intervalos, [1] * len(intervalos), K)
    mk = m.NewIntVar(0, H, "mk")
    m.AddMaxEquality(mk, fins)
    espera_total = sum(esperas)
    if limite_fim is None:
        m.Minimize(mk)
    else:
        m.Add(mk <= int(limite_fim * ESC))
        m.Minimize(espera_total * 1000 + mk)     # espera primeiro; desempate pelo fim
    sol = cp_model.CpSolver()
    sol.parameters.max_time_in_seconds = TEMPO_LIMITE
    sol.parameters.num_workers = 8
    st = sol.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": sol.StatusName(st)}
    res = {"status": sol.StatusName(st), "fim_s": sol.Value(mk) / ESC, "espera_s": sol.Value(espera_total) / ESC,
           "inicio_robos_s": {r: sol.Value(v[0]) / ESC for r, v in ini.items()},
           "soldas_s": {r: [sol.Value(x) / ESC for x in v[1]] for r, v in ini.items()}}
    res["energia_extra_kJ"] = round((P_ACORDADO - P_FREIOS) * res["espera_s"], 2)
    return res


def principal(margem=0.0):
    saida = {}
    print("Janela por carroceria: %.1f s | margem reservada: %.1f s" % (JANELA, margem))
    for mod in ("Hatch", "Sedan"):
        print("\n== %s" % mod)
        for K in (4, 3, 2, 1):
            a = resolver(mod, K)
            if "fim_s" not in a:
                print("  K=%d: %s" % (K, a["status"])); continue
            lim = JANELA - margem
            b = resolver(mod, K, limite_fim=lim) if a["fim_s"] <= lim else {"status": "INVIAVEL na janela"}
            linha = "  K=%d (%3.0f kVA): menor fim %.2f s [%s]" % (K, K * KVA, a["fim_s"], a["status"])
            if "fim_s" in b:
                linha += " | com fim <= %.1f s: espera acordado %.2f s (+%.2f kJ/carroceria), fim %.2f s, início dos robôs %s [%s]" % (
                    lim, b["espera_s"], b["energia_extra_kJ"], b["fim_s"], b["inicio_robos_s"], b["status"])
            else:
                linha += " | %s" % b["status"]
            print(linha)
            saida["%s_K%d" % (mod, K)] = {"menor_fim": a, "na_janela": b}
    return saida


if __name__ == "__main__":
    margem = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    res = principal(margem)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados", "otimizacao", "otimiza_pico_margem%.0f.json" % margem)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("\nsalvo:", out)
