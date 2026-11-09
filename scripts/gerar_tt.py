"""
Gera as tabelas de tempos de deslocamento (TT_R<n>_<MODELO>) a partir das coordenadas (TC_<MODELO>)
com um modelo cinemático de perfil trapezoidal de velocidade + tempo de estabilização.

Roda FORA do Plant:
    C:\\Python315\\python.exe gerar_tt.py                 -> compara os cenários (não grava nada)
    C:\\Python315\\python.exe gerar_tt.py K2 <pasta_saida> -> grava as 8 TT do cenário K2 em .txt para colar no Plant

Modelo por trecho de distância d (linha reta entre pontos, em m):
    d = 0                 -> t = 0 (P10 duplicado do P9)
    d >= v^2/a            -> t = d/v + v/a + PSt         (trapézio: acelera, cruzeiro, desacelera)
    d <  v^2/a            -> t = 2*sqrt(d/a) + PSt       (triângulo: não atinge v)
Fontes:
    v_max = 1,6 m/s (velocidade do teste ISO 9283), a_max = 24 m/s² (aceleração cartesiana máxima em
    movimento controlado, 205/2.80) e PSt = 0,17 s (pose stabilization time, 205/2.80):
    ABB 3HAC044265-001 rev. N (2019), seções 1.5.5 e 1.8.2.
    v1000 = 1000 mm/s é o speeddata predefinido do RAPID (hipótese de velocidade programada típica).
Limitações (deixar explícitas no texto):
    - a distância é a reta entre os pontos (limite inferior do caminho real: aproximação, recuo e
      reorientação da pinça não entram);
    - os trechos de/para o home (P0) usam a distância implícita na TT da IC (tempo ÷ s/m calibrado),
      porque a TC do Plant não tem o P0.
"""
import sys
import os
import math
import statistics

import openpyxl

XLSX = r"C:\Users\giova\Arquivos\UFABC\TG\x_plant-models\infotmation-methods\tables.xlsx"
SOLDA_S = 1.6

CENARIOS = {
    # nome: (v [m/s], a [m/s²], PSt [s], descrição)
    "K1": (1.6, 24.0, 0.17, "limite do fabricante: 1,6 m/s, 24 m/s², PSt 0,17 s"),
    "K2": (1.0, 12.0, 0.17, "programação típica: v1000, metade da aceleração máx."),
    "K3": (0.5, 6.0, 0.17, "conservador: 0,5 m/s, 1/4 da aceleração máx."),
}
REGRA_CHO = 3.3 - 1.0   # s de movimento por ponto (Cho, Kim e Park, WSC 2024: 3,3 s/ponto com ~1 s de solda)
# Cenário híbrido "H": K2 + sobrecusto constante c por trecho com deslocamento (aproximação, recuo e
# reorientação da pinça, que a reta entre pontos não captura). c é calibrado para que o ciclo total
# médio por ponto (movimento + solda de 1,6 s) seja 3,3 s, a regra empírica da indústria (Cho et al. 2024).
ALVO_POR_PONTO = 3.3


def _num(v):
    if v is None:
        return 0.0
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        # o Excel pt-BR leu "19.1226" como 191226 (ponto = milhar)
        return v / 10000.0 if float(v) >= 100 and float(v).is_integer() else float(v)
    return float(str(v).replace(",", "."))


def carregar():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    tc, tt = {}, {}
    for mod in ("Hatch", "Sedan"):
        ws = wb["TC_" + mod]
        linhas = list(ws.iter_rows(values_only=True))[1:]
        for r in range(1, 5):
            tc[(r, mod)] = {int(str(l[0])[1:]): tuple(_num(x) for x in l[1 + 3 * (r - 1): 4 + 3 * (r - 1)])
                            for l in linhas if l[0]}
            ws2 = wb["TT_R%d_%s" % (r, mod)]
            tt[(r, mod)] = [[_num(x) for x in l] for l in ws2.iter_rows(values_only=True)]
    return tc, tt


def s_por_m(tc, tt, r, mod):
    """s/m da IC (mediana de t/d nos trechos P1..P9)."""
    P, T = tc[(r, mod)], tt[(r, mod)]
    k = [T[i][i + 1] / math.dist(P[i], P[i + 1]) for i in range(1, 9) if math.dist(P[i], P[i + 1]) > 0]
    return statistics.median(k)


def t_mov(d, v, a, pst):
    if d <= 1e-9:
        return 0.0
    return (d / v + v / a if d >= v * v / a else 2 * math.sqrt(d / a)) + pst


def matriz(tc, tt, r, mod, v, a, pst, c=0.0):
    """Matriz 11x11 simétrica (índice 0 = home, 1..10 = P1..P10)."""
    P = tc[(r, mod)]
    k = s_por_m(tc, tt, r, mod)
    d_home = {1: tt[(r, mod)][0][1] / k, 10: tt[(r, mod)][0][10] / k}  # distância implícita na IC
    M = [[0.0] * 11 for _ in range(11)]
    for i in range(11):
        for j in range(i + 1, 11):
            if i == 0:
                d = d_home.get(j)
                if d is None:  # home <-> pontos intermediários: sem dado; não usados na sequência
                    continue
            else:
                d = math.dist(P[i], P[j])
            t = t_mov(d, v, a, pst)
            M[i][j] = M[j][i] = round(t + c if t > 0 else 0.0, 4)
    return M, d_home


def ciclo(M, n_trechos=10):
    """Tempo de movimento da sequência home -> P1 -> ... -> P10 -> home."""
    return M[0][1] + sum(M[i][i + 1] for i in range(1, n_trechos)) + M[10][0]


def soldas(r, mod):
    return 10 if (r, mod) == (2, "Sedan") else 9


def n_trechos_com_movimento(M):
    return sum(1 for t in [M[0][1]] + [M[i][i + 1] for i in range(1, 10)] + [M[10][0]] if t > 0)


def calibrar_c(tc, tt):
    """c [s] tal que a média (sobre robôs e produtos) de (movimento + soldas)/soldas = ALVO_POR_PONTO."""
    v, a, pst, _ = CENARIOS["K2"]
    mov, trechos, nsold = 0.0, 0, 0
    for mod in ("Hatch", "Sedan"):
        for r in range(1, 5):
            M, _ = matriz(tc, tt, r, mod, v, a, pst)
            mov += ciclo(M); trechos += n_trechos_com_movimento(M); nsold += soldas(r, mod)
    return ((ALVO_POR_PONTO - SOLDA_S) * nsold - mov) / trechos


def comparar():
    tc, tt = carregar()
    print("Tempo de MOVIMENTO por ciclo (s) | entre parênteses: ciclo total com soldas de %.1f s" % SOLDA_S)
    c = calibrar_c(tc, tt)
    print("%-10s %-14s %-14s %-14s %-14s %-14s %-14s" % ("robô", "IC", "K1", "K2", "K3", "H", "regra 3,3 s"))
    tot = {k: [] for k in ("IC", "K1", "K2", "K3", "H", "CHO")}
    for mod in ("Hatch", "Sedan"):
        for r in range(1, 5):
            T = tt[(r, mod)]
            ic = T[0][1] + sum(T[i][i + 1] for i in range(1, 10)) + T[0][10]
            ns = soldas(r, mod)
            linha = ["%6.1f (%5.1f)" % (ic, ic + ns * SOLDA_S)]
            tot["IC"].append(ic)
            for nome_c, (v, a, pst, _) in CENARIOS.items():
                M, _ = matriz(tc, tt, r, mod, v, a, pst)
                m = ciclo(M)
                tot[nome_c].append(m)
                linha.append("%6.1f (%5.1f)" % (m, m + ns * SOLDA_S))
            v, a, pst, _ = CENARIOS["K2"]
            M, _ = matriz(tc, tt, r, mod, v, a, pst, c)
            tot["H"].append(ciclo(M)); linha.append("%6.1f (%5.1f)" % (ciclo(M), ciclo(M) + ns * SOLDA_S))
            cho = REGRA_CHO * ns
            tot["CHO"].append(cho)
            linha.append("%6.1f (%5.1f)" % (cho, cho + ns * SOLDA_S))
            print("%-10s " % ("R%d %s" % (r, mod)) + " ".join("%-14s" % x for x in linha))
    print("\nMovimento médio por solda (s): " + " | ".join(
        "%s %.2f" % (k, statistics.mean(v) / 9.1) for k, v in tot.items()))
    print("Cenários:"); [print("  %s: %s" % (k, x[3])) for k, x in CENARIOS.items()]
    print("  H: K2 + %.2f s por trecho (calibrado para %.1f s/ponto no total, Cho et al. 2024)" % (c, ALVO_POR_PONTO))


def gravar(cen, pasta):
    tc, tt = carregar()
    c = 0.0
    if cen == "H":
        v, a, pst, _ = CENARIOS["K2"]; c = calibrar_c(tc, tt)
    else:
        v, a, pst, _ = CENARIOS[cen]
    os.makedirs(pasta, exist_ok=True)
    for mod in ("Hatch", "Sedan"):
        for r in range(1, 5):
            M, _ = matriz(tc, tt, r, mod, v, a, pst, c)
            arq = os.path.join(pasta, "TT_R%d_%s_%s.txt" % (r, mod.upper(), cen))
            with open(arq, "w", encoding="utf-8", newline="\r\n") as f:
                for lin in M:
                    f.write("\t".join("%.4f" % x for x in lin) + "\n")
            print("gravado:", arq)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        gravar(sys.argv[1], sys.argv[2])
    else:
        comparar()
