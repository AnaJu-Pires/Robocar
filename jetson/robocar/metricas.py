"""Metricas de uma corrida a partir do log CSV (registro.LogCSV): os numeros de cada rodada de ajuste.

Sem E/S nesta parte (recebe as linhas ja lidas): testavel no PC. O programa e jetson/metricas_log.py.
Python 3.6, sem numpy obrigatorio.
"""


def _num(txt):
    if txt is None or txt == "":
        return None
    try:
        return float(txt)
    except ValueError:
        return None


def _pct(lista, p):
    """Percentil p (0-100) por interpolacao linear; None se vazio."""
    if not lista:
        return None
    s = sorted(lista)
    k = (len(s) - 1) * p / 100.0
    i = int(k)
    j = min(i + 1, len(s) - 1)
    return s[i] + (s[j] - s[i]) * (k - i)


def calcular(linhas, pulsos_por_volta=None, diametro_roda_m=0.042):
    """linhas: lista de dicts (cabecalho do CSV). Devolve dict com as metricas da corrida.

    So conta o trecho em que o controle estava andando (SEGUINDO ou BUSCANDO).
    """
    andando = [r for r in linhas if r.get("estado") in ("SEGUINDO", "BUSCANDO")]
    m = {"quadros_total": len(linhas), "quadros_andando": len(andando)}
    if not andando:
        m["aviso"] = "o robo nao andou neste log (nenhum quadro em SEGUINDO/BUSCANDO)"
        return m
    t = [_num(r.get("t")) for r in andando]
    t = [x for x in t if x is not None]
    m["duracao_s"] = (t[-1] - t[0]) if len(t) > 1 else 0.0
    dts = [b - a for a, b in zip(t[:-1], t[1:]) if b > a]
    m["fps_real"] = (len(dts) / sum(dts)) if dts else None
    m["dt_max_ms"] = (max(dts) * 1000.0) if dts else None           # travadas (quadro atrasado)

    com_linha = [r for r in andando if _num(r.get("erro")) is not None]
    m["linha_vista_pct"] = 100.0 * len(com_linha) / len(andando)
    erros = [abs(_num(r["erro"])) for r in com_linha]
    m["erro_abs_p50"] = _pct(erros, 50)
    m["erro_abs_p95"] = _pct(erros, 95)

    # eventos: entrou em BUSCANDO (linha perdida) e cruzamentos detectados (bordas de subida)
    buscas, cruz = 0, 0
    ant_estado, ant_cruz = None, "0"
    for r in andando:
        if r.get("estado") == "BUSCANDO" and ant_estado != "BUSCANDO":
            buscas += 1
        if r.get("cruzamento") == "1" and ant_cruz != "1":
            cruz += 1
        ant_estado, ant_cruz = r.get("estado"), r.get("cruzamento")
    m["perdeu_linha_vezes"] = buscas
    m["cruzamentos_detectados"] = cruz

    proc = [_num(r.get("proc_ms")) for r in andando]
    proc = [x for x in proc if x is not None]
    m["proc_ms_p50"] = _pct(proc, 50)
    m["proc_ms_p99"] = _pct(proc, 99)

    vs = [_num(r.get("v")) for r in andando if r.get("estado") == "SEGUINDO"]
    vs = [x for x in vs if x is not None]
    m["v_cmd_media"] = (sum(vs) / len(vs)) if vs else None

    vb = [_num(r.get("vbat")) for r in linhas]
    vb = [x for x in vb if x is not None and x > 1.0]
    if vb:
        m["vbat_max"] = max(vb)
        m["vbat_min"] = min(vb)
        m["vbat_queda"] = max(vb) - min(vb)                         # queda sob carga (bateria + fios)

    ee = [_num(r.get("enc_e")) for r in andando]
    ed = [_num(r.get("enc_d")) for r in andando]
    ee = [x for x in ee if x is not None]
    ed = [x for x in ed if x is not None]
    if ee and ed:
        pe, pd = abs(ee[-1] - ee[0]), abs(ed[-1] - ed[0])
        m["pulsos_esq"], m["pulsos_dir"] = pe, pd
        if pulsos_por_volta:
            volta_m = 3.141592653589793 * diametro_roda_m
            dist = (pe + pd) / 2.0 / pulsos_por_volta * volta_m
            m["distancia_m"] = dist
            if m["duracao_s"] > 0:
                m["velocidade_media_m_s"] = dist / m["duracao_s"]

    fim = linhas[-1].get("estado")
    m["estado_final"] = fim
    return m


def texto(m):
    """Resumo legivel (uma linha por metrica, na ordem que importa para a pontuacao)."""
    ordem = [("aviso", "AVISO", "%s"), ("duracao_s", "tempo andando (s)", "%.2f"),
             ("distancia_m", "distancia pelos encoders (m)", "%.2f"),
             ("velocidade_media_m_s", "velocidade media (m/s)", "%.2f"),
             ("perdeu_linha_vezes", "vezes que perdeu a linha", "%d"),
             ("linha_vista_pct", "quadros com a linha (%)", "%.1f"),
             ("erro_abs_p50", "|erro| mediano", "%.3f"), ("erro_abs_p95", "|erro| p95", "%.3f"),
             ("cruzamentos_detectados", "cruzamentos detectados", "%d"),
             ("v_cmd_media", "v comandado medio (0-1)", "%.2f"),
             ("fps_real", "fps real", "%.1f"), ("dt_max_ms", "maior intervalo entre quadros (ms)", "%.0f"),
             ("proc_ms_p50", "processamento mediano (ms)", "%.1f"), ("proc_ms_p99", "processamento p99 (ms)", "%.1f"),
             ("vbat_max", "bateria max (V)", "%.2f"), ("vbat_min", "bateria min (V)", "%.2f"),
             ("vbat_queda", "queda da bateria (V)", "%.2f"),
             ("pulsos_esq", "pulsos encoder esq", "%d"), ("pulsos_dir", "pulsos encoder dir", "%d"),
             ("estado_final", "estado final", "%s")]
    out = []
    for chave, rotulo, f in ordem:
        if m.get(chave) is not None:
            out.append(("%-36s " + f) % (rotulo, m[chave]))
    return "\n".join(out)
