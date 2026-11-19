"""Leitura de arquivos KiCad como texto (sem o KiCad): s-expressions e netlist de um esquematico de uma folha.

Usado quando o kicad-cli instalado e mais velho que o arquivo (ex.: kicad-cli 7 e esquematico salvo no KiCad 10).
Conferido contra a netlist do kicad-cli 7 no esquematico da v0.8: mesmas redes em todos os pinos.
"""
import math
import re

TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')
def parse(text):
    stack = [[]]
    for m in TOK.finditer(text):
        t = m.group(0)
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop(); stack[-1].append(x)
        elif t[0] == '"':
            stack[-1].append(Str(bytes(t[1:-1], 'utf-8').decode('unicode_escape') if '\\' in t else t[1:-1]))
        else:
            stack[-1].append(t)
    return stack[0][0]
class Str(str): pass
def head(n): return n[0] if isinstance(n, list) and n else None
def kids(n, name): return [c for c in n[1:] if isinstance(c, list) and c and c[0] == name]
def kid(n, name):
    k = kids(n, name); return k[0] if k else None
def val(n, name, i=1, d=None):
    k = kid(n, name); return k[i] if k and len(k) > i else d
def lib_pins(libsym):
    pins = []
    for sub in kids(libsym, 'symbol'):
        nm = sub[1]; unit = int(nm.rsplit('_', 2)[-2])
        for p in kids(sub, 'pin'):
            at = kid(p, 'at')
            pins.append(dict(unit=unit, num=val(p, 'number'), name=val(p, 'name'), x=float(at[1]), y=float(at[2]),
                             etype=p[1], hidden=('hide' in [x for x in p if isinstance(x, str)]) or (kid(p, 'hide') is not None and val(p, 'hide') == 'yes')))
    for p in kids(libsym, 'pin'):
        at = kid(p, 'at'); pins.append(dict(unit=0, num=val(p, 'number'), name=val(p, 'name'), x=float(at[1]), y=float(at[2]), etype=p[1], hidden=False))
    return pins

def xform(px, py, X, Y, rot, mirror):
    # coordenadas da biblioteca: y para cima
    x, y = px, py
    r = math.radians(rot)
    x, y = x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)
    if mirror == 'x': y = -y
    if mirror == 'y': x = -x
    return round(X + x, 3), round(Y - y, 3)

def netlist(path):
    s = parse(open(path, encoding='utf-8').read())
    libs = {ls[1]: ls for ls in kids(kid(s, 'lib_symbols'), 'symbol')}
    pts = {}   # ponto -> lista de (ref, pin)
    syms = []
    for sym in kids(s, 'symbol'):
        lib_id = val(sym, 'lib_id'); at = kid(sym, 'at'); X, Y = float(at[1]), float(at[2]); rot = float(at[3]) if len(at) > 3 else 0
        mir = val(sym, 'mirror'); unit = int(val(sym, 'unit', 1, 1))
        pr = {q[1]: q[2] for q in kids(sym, 'property')}
        libname = val(sym, 'lib_name') or lib_id
        ls = libs[libname]
        is_power = kid(ls, 'power') is not None
        pins = [p for p in lib_pins(ls) if p['unit'] in (0, unit)]
        syms.append(dict(ref=pr['Reference'], value=pr.get('Value'), lib=lib_id, power=is_power, X=X, Y=Y, rot=rot, mir=mir,
                         pins=[(p, xform(p['x'], p['y'], X, Y, rot, mir)) for p in pins], fp=pr.get('Footprint', ''), uuid=val(sym, 'uuid')))
    wires = []
    for w in kids(s, 'wire'):
        P = [(round(float(p[1]), 3), round(float(p[2]), 3)) for p in kid(w, 'pts')[1:]]
        wires.append(P)
    labels = [(l[1], (round(float(kid(l, 'at')[1]), 3), round(float(kid(l, 'at')[2]), 3))) for l in kids(s, 'label') + kids(s, 'global_label')]
    ncs = [(round(float(kid(j, 'at')[1]), 3), round(float(kid(j, 'at')[2]), 3)) for j in kids(s, 'no_connect')]
    # union-find
    par = {}
    def f(a):
        par.setdefault(a, a)
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    def u(a, b): par[f(a)] = f(b)
    def on_seg(p, a, b):
        if abs((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) > 1e-3: return False
        return min(a[0], b[0]) - 1e-3 <= p[0] <= max(a[0], b[0]) + 1e-3 and min(a[1], b[1]) - 1e-3 <= p[1] <= max(a[1], b[1]) + 1e-3
    allpts = set()
    for w in wires:
        u(('p', w[0]), ('p', w[-1])); allpts |= {w[0], w[-1]}
    for sy in syms:
        for p, xy in sy['pins']: allpts.add(xy)
    for n, xy in labels: allpts.add(xy)
    for p in allpts:
        for w in wires:
            if on_seg(p, w[0], w[-1]): u(('p', p), ('p', w[0]))
    for n, xy in labels: u(('p', xy), ('lab', n))
    for sy in syms:
        if sy['power']:
            for p, xy in sy['pins']:
                if p['etype'] == 'power_in': u(('p', xy), ('lab', '#PWR:' + sy['value']))
    nets = {}
    for sy in syms:
        if sy['power']: continue
        for p, xy in sy['pins']:
            nets[(sy['ref'], p['num'])] = f(('p', xy))
    # nome da rede
    names = {}
    for key in list(par):
        if key[0] == 'lab':
            r = f(key); nm = key[1][5:] if key[1].startswith('#PWR:') else '/' + key[1]
            if r not in names or key[1].startswith('#PWR:'): names[r] = nm
    out = {}
    for k, r in nets.items():
        out[k] = names.get(r)
    return out, syms, wires, labels, ncs, s


def netlist_esquematico(sch):
    """Devolve (componentes, pinos): componentes[ref] = {valor, pegada, tstamp}; pinos[(ref, pino)] = rede.
    Tenta o kicad-cli; se ele nao ler o arquivo (versao mais nova), usa a leitura em texto."""
    import os, subprocess, tempfile
    import xml.etree.ElementTree as ET
    try:
        with tempfile.TemporaryDirectory() as tmp:
            xml = os.path.join(tmp, "net.xml")
            subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", xml, sch],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            raiz = ET.parse(xml).getroot()
        comp = {c.get("ref"): dict(valor=c.findtext("value"), pegada=c.findtext("footprint"),
                                   tstamp=(c.findtext("tstamps") or "").split()[0] if c.findtext("tstamps") else None)
                for c in raiz.iter("comp")}
        pinos = {(no.get("ref"), no.get("pin")): n.get("name") for n in raiz.iter("net") for no in n.iter("node")}
        return comp, pinos
    except (subprocess.CalledProcessError, FileNotFoundError, ET.ParseError):
        out, syms, *_ = netlist(sch)
        comp = {s["ref"]: dict(valor=s["value"], pegada=s["fp"], tstamp=s["uuid"]) for s in syms if not s["power"]}
        pinos = {}
        for s in syms:
            if s["power"]:
                continue
            for p, xy in s["pins"]:
                pinos[(s["ref"], p["num"])] = out.get((s["ref"], p["num"])) or "unconnected-(%s-%s-Pad%s)" % (s["ref"], p["name"].replace("/", "{slash}"), p["num"])
        return comp, pinos
