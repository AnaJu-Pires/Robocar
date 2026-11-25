"""Verificacoes automaticas do chassi v3. Cada funcao devolve uma lista de Resultado(ok, nome, detalhe).

  regulamento   - 250 x 150 / 50 x 60, pneu, tensao e rotacao do motor, rodas e esfera no chao
  interferencia - chapas x compradas x conectores x plugues x volumes de acesso (dedo, chave, bateria)
  camera        - a mesma interferencia em toda a faixa de angulo da camera + o que a camera ve do proprio carro
  material      - material minimo entre furos e entre furo e borda; corte que vira entalhe; peca que se solta
  cg            - centro de massa, tombamento na curva, empinar, peso nas rodas
  cabos         - comprimento (com sobra), distancia da roda e do redutor, nao atravessar chapa, abracadeiras
Rodar tudo: python3 gerar.py --so-verificar
"""
import math
import numpy as np
import cadquery as cq
import shapely.geometry as sg
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
import modelo
import geometria as geo
from pecas import v, pendencias

class Resultado:
    def __init__(s, ok, grupo, nome, detalhe=''):
        s.ok, s.grupo, s.nome, s.detalhe = ok, grupo, nome, detalhe
    def __repr__(s):
        return f"[{'ok' if s.ok else 'FALHOU'}] {s.grupo}: {s.nome} {s.detalhe}"

def volume_comum(a, b):
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    op.Build()
    if not op.IsDone():
        return 0.0
    pr = GProp_GProps()
    BRepGProp.VolumeProperties_s(op.Shape(), pr)
    return abs(pr.Mass())

def bbox(s):
    b = s.BoundingBox()
    return np.array([b.xmin, b.ymin, b.zmin]), np.array([b.xmax, b.ymax, b.zmax])

def bbox_toca(a, b, folga=0.0):
    return np.all(a[0] <= b[1] + folga) and np.all(b[0] <= a[1] + folga)

# ------------------------------------------------------------------------------------------- montagem para checar
def solidos(m, ang=None, com_cabos=False):
    """Lista de dicts (nome, solido, tipo, grupo, ignora) de tudo que ocupa espaco."""
    out = []
    for nome, sol, ch in modelo.chapas_3d(m, ang):
        out.append(dict(nome=nome, solido=sol, tipo='chapa', grupo=nome, ignora=set()))
    for p in m.compradas + modelo.camera_compradas(m, m.P['CAM_ANG_NOMINAL'] if ang is None else ang):
        out.append(dict(nome=p['nome'], solido=p['solido'], tipo=p['cat'], grupo=p['grupo'], ignora=set()))
    for a in m.acessos:
        out.append(dict(nome=a['nome'], solido=a['solido'], tipo='acesso', grupo=a['nome'], ignora=set(a['ignora'])))
    for s in out:
        s['bb'] = bbox(s['solido'])
    return out

def _pode_tocar(a, b):
    if a['grupo'] == b['grupo']:
        return True
    if a['nome'] in b['ignora'] or b['nome'] in a['ignora'] or a['grupo'] in b['ignora'] or b['grupo'] in a['ignora']:
        return True
    if a['tipo'] == 'acesso' and b['tipo'] == 'acesso':
        return True
    return False

def interferencias(lista_a, lista_b=None, tol=0.5):
    """Pares que se sobrepoem com volume > tol mm3 (lista_b None = todos contra todos)."""
    achados = []
    pares = []
    if lista_b is None:
        for i in range(len(lista_a)):
            for j in range(i + 1, len(lista_a)):
                pares.append((lista_a[i], lista_a[j]))
    else:
        pares = [(a, b) for a in lista_a for b in lista_b]
    for a, b in pares:
        if _pode_tocar(a, b) or not bbox_toca(a['bb'], b['bb']):
            continue
        vol = volume_comum(a['solido'], b['solido'])
        if vol > tol:
            achados.append((a['nome'], b['nome'], vol))
    return achados

# ------------------------------------------------------------------------------------------- dimensoes
def dimensoes(m):
    lo = np.array([1e9] * 3); hi = -lo
    angs = np.arange(m.P['CAM_ANG'][0], m.P['CAM_ANG'][1] + 0.1, 5.0)
    itens = [s for _, s, _ in modelo.chapas_3d(m)] + [p['solido'] for p in m.compradas]
    for a in angs:
        itens += [s for _, s, _ in m.partes_camera(a)]
    for s in itens:
        a, b = bbox(s); lo = np.minimum(lo, a); hi = np.maximum(hi, b)
    for cb in m.cabos:
        P_ = np.array(cb['pontos']); r = cb['d'] / 2
        lo = np.minimum(lo, P_.min(axis=0) - r); hi = np.maximum(hi, P_.max(axis=0) + r)
    chapas_lo = np.array([1e9] * 3); chapas_hi = -chapas_lo
    for _, s, _ in modelo.chapas_3d(m):
        a, b = bbox(s); chapas_lo = np.minimum(chapas_lo, a); chapas_hi = np.maximum(chapas_hi, b)
    return dict(lo=lo, hi=hi, comprimento=hi[0] - lo[0], largura=hi[1] - lo[1], altura=hi[2] - lo[2],
                chassi=(chapas_hi - chapas_lo)[:2])

# ------------------------------------------------------------------------------------------- 1. regulamento
def regulamento(m):
    R = []
    d = dimensoes(m)
    R.append(Resultado(d['comprimento'] <= 250.0, 'regulamento', 'comprimento <= 250 mm',
                       f"{d['comprimento']:.1f} mm (de x = {d['lo'][0]:.1f} a {d['hi'][0]:.1f}, com plugues, cabos e camera em toda a faixa)"))
    R.append(Resultado(d['largura'] <= 150.0, 'regulamento', 'largura <= 150 mm',
                       f"{d['largura']:.1f} mm (de y = {d['lo'][1]:.1f} a {d['hi'][1]:.1f})"))
    R.append(Resultado(d['chassi'][0] >= 60.0 and d['chassi'][1] >= 50.0, 'regulamento', 'chassi >= 50 x 60 mm',
                       f"{d['chassi'][0]:.0f} x {d['chassi'][1]:.0f} mm"))
    D, L = v('roda')
    R.append(Resultado(20.0 <= D <= 113.0, 'regulamento', 'diametro do pneu 20-113 mm', f'{D:.0f} mm'))
    R.append(Resultado(11.0 <= L <= 45.0, 'regulamento', 'largura do pneu 11-45 mm', f'{L:.0f} mm'))
    volts = 7.2
    rpm = v('motor_rpm_6v') * volts / 6
    R.append(Resultado(3.0 <= volts <= 12.0, 'regulamento', 'tensao do motor 3-12 V', f'{volts} V (XL4016 #2, D-019)'))
    R.append(Resultado(500 <= v('motor_rpm_6v') and rpm <= 7000, 'regulamento', 'rotacao 500-7000 rpm',
                       f"{v('motor_rpm_6v'):.0f} rpm nominal (6 V), ~{rpm:.0f} rpm em vazio a 7,2 V"))
    rodas = [p for p in m.compradas if p['cat'] == 'roda']
    toca = [bbox(p['solido'])[0][2] for p in rodas]
    R.append(Resultado(len(rodas) == 2 and all(abs(z) < 0.3 for z in toca), 'regulamento', '2 rodas tracionadas tocam o chao',
                       f'z minimo das rodas: {", ".join(f"{z:.2f}" for z in toca)} mm'))
    R.append(Resultado(abs(m.esfera_z_chao) < 0.5, 'regulamento', 'esfera no chao (carro nivelado)',
                       f'fundo da esfera a {m.esfera_z_chao:+.2f} mm do chao (piso dianteiro a {m.Z1:.1f} mm, esfera de {v("esfera_altura"):.0f} mm)'))
    vao = min(bbox(s)[0][2] for _, s, _ in modelo.chapas_3d(m))
    R.append(Resultado(vao >= 8.0, 'regulamento', 'vao livre >= 8 mm (emendas do tapete)', f'{vao:.1f} mm'))
    return R

# ------------------------------------------------------------------------------------------- 2. interferencia
def interferencia(m):
    mv = modelo.construir(m.P, verif=True)
    lista = solidos(mv)
    ach = interferencias(lista)
    R = [Resultado(False, 'interferencia', f'{a} x {b}', f'{vol:.1f} mm3') for a, b, vol in ach]
    if not ach:
        R.append(Resultado(True, 'interferencia', 'nenhuma sobreposicao',
                           f'{len(lista)} solidos ({sum(1 for s in lista if s["tipo"] == "acesso")} volumes de acesso)'))
    return R

def camera(m):
    mv = modelo.construir(m.P, verif=True)
    base = [s for s in solidos(mv) if s['grupo'] != 'camera' and 'camera' not in s['nome']]
    R = []
    angs = list(np.arange(m.P['CAM_ANG'][0], m.P['CAM_ANG'][1] + 0.1, 5.0))
    for ang in angs:
        cam = []
        for nome, sol, tipo in mv.partes_camera(ang):
            cam.append(dict(nome=nome, solido=sol, tipo='camera', grupo='camera', ignora=set(), bb=bbox(sol)))
        ach = interferencias(cam, base)
        for a, b, vol in ach:
            R.append(Resultado(False, 'camera', f'{ang:.0f} graus: {a} x {b}', f'{vol:.1f} mm3'))
    if not any(not r.ok for r in R):
        R.append(Resultado(True, 'camera', 'camera livre em toda a faixa',
                           f'{m.P["CAM_ANG"][0]:.0f} a {m.P["CAM_ANG"][1]:.0f} graus, de 5 em 5'))
    # o que a camera ve do proprio carro (borda de baixo do campo de visao, no plano de simetria e a +-20 graus)
    vf = v('cam_vfov')
    livre = []
    for ang in angs:
        mv.partes_camera(ang)
        p0 = np.array(mv.cam_centro)
        bate = False
        for lat in (-20.0, 0.0, 20.0):
            a_ = math.radians(ang + vf / 2)
            d = np.array([math.cos(a_) * math.cos(math.radians(lat)), math.sin(math.radians(lat)), -math.sin(a_)])
            t = (p0[2] - 0.5) / -d[2] if d[2] < 0 else 400
            p1 = p0 + d * t
            raio = geo.cilindro(tuple(p0 + d * 3), tuple(p1), 1.0)
            for s in base:
                if s['tipo'] == 'acesso':
                    continue
                if bbox_toca(bbox(raio), s['bb']) and volume_comum(raio, s['solido']) > 0.01:
                    bate = True
                    break
            if bate:
                break
        livre.append((ang, not bate))
    nom = m.P['CAM_ANG_NOMINAL']
    ok_nom = dict(livre).get(nom, True)
    angs_livres = [a for a, ok in livre if ok]
    R.append(Resultado(ok_nom, 'camera', 'a camera nao ve o proprio carro no angulo nominal',
                       f'{nom:.0f} graus; livre ate {max(angs_livres) if angs_livres else 0:.0f} graus (campo vertical estimado {vf:.0f} graus)'))
    return R

# ------------------------------------------------------------------------------------------- 3. material
def material(m):
    R = []
    teia = m.P['MIN_TEIA']
    for c in m.chapas:
        cont = c.contorno
        prob = []
        if not cont.is_valid:
            prob.append('contorno invalido (se cruza)')
        borda = cont.exterior
        for i, f in enumerate(c.furos):
            if not cont.contains(f.geom):
                prob.append(f'ENTALHE: furo "{f.nome or f.funcao}" encosta ou passa da borda (vira entalhe sem querer)')
                continue
            d = f.geom.exterior.distance(borda)
            if d < teia - 1e-6:
                prob.append(f'furo "{f.nome or f.funcao}" a {d:.2f} mm da borda (min {teia})')
            for g in c.furos[i + 1:]:
                dd = f.geom.distance(g.geom)
                if dd < teia - 1e-6:
                    tipo = 'FUROS SE JUNTAM' if dd <= 1e-6 else 'pouco material entre furos'
                    prob.append(f'{tipo}: "{f.nome or f.funcao}" x "{g.nome or g.funcao}" ({dd:.2f} mm, min {teia})')
        p2 = c.peca2d()
        if p2.geom_type != 'Polygon':
            prob.append(f'a chapa se divide em {len(p2.geoms)} pedacos (peca que se solta)')
        elif len(p2.interiors) != len(c.furos):
            prob.append(f'{len(c.furos)} furos viraram {len(p2.interiors)} buracos (furos sobrepostos ou na borda)')
        # parte fina do proprio contorno (abas ou pontas estreitas)
        # parte fina: o que some numa "abertura" de raio teia/2. Canto vivo perde um triangulo pequeno (normal);
        # uma aba ou ponta estreita perde uma regiao comprida (problema).
        aberto = cont.buffer(-teia / 2 + 1e-3, join_style=1).buffer(teia / 2 - 1e-3, join_style=1)
        dif = cont.difference(aberto)
        partes = list(dif.geoms) if hasattr(dif, 'geoms') else [dif]
        for q in partes:
            if q.is_empty:
                continue
            x0, y0, x1, y1 = q.bounds
            if max(x1 - x0, y1 - y0) > 1.5 * teia:
                prob.append(f'parte do contorno mais fina que {teia} mm perto de ({(x0 + x1) / 2:.1f}, {(y0 + y1) / 2:.1f})')
        for (txt, x, y, h) in c.textos:      # gravacao em cima de furo ou fora da peca (o laser grava no vazio)
            cx = geo.ret_c(x, y, len(txt) * h * 0.62, h)
            if not cont.contains(cx) or any(f.geom.intersects(cx) for f in c.furos):
                prob.append(f'gravacao "{txt}" cai em furo ou fora da peca')
        R.append(Resultado(not prob, 'material', c.nome, '; '.join(prob) if prob else
                           f'{len(c.furos)} furos, teia >= {teia} mm, 1 peca'))
    return R

# ------------------------------------------------------------------------------------------- 4. CG
def cg(m, limites=None):
    from analise import estabilidade
    L = dict(z_max=40.0, y_max=3.0, rodas=(0.75, 0.92), tomb_fator=1.15, empina_min=0.40)
    L.update(limites or {})
    M_, c = modelo.cg(modelo.massas(m))
    e = estabilidade(c, m.P['ESFERA_X'], m.P['BITOLA'], m.P['MU'])
    mu = m.P['MU']
    R = [Resultado(True, 'cg', 'massa total estimada', f'{M_:.0f} g; CG x {c[0]:.1f} / y {c[1]:.1f} / z {c[2]:.1f} mm'),
         Resultado(c[2] <= L['z_max'], 'cg', f'altura do CG <= {L["z_max"]:.0f} mm', f'{c[2]:.1f} mm'),
         Resultado(abs(c[1]) <= L['y_max'], 'cg', f'CG centrado (|y| <= {L["y_max"]:.0f} mm)', f'{c[1]:+.1f} mm'),
         Resultado(L['rodas'][0] <= e['carga_rodas'] <= L['rodas'][1], 'cg',
                   f'peso nas rodas entre {L["rodas"][0] * 100:.0f} e {L["rodas"][1] * 100:.0f} %', f'{e["carga_rodas"] * 100:.0f} %'),
         Resultado(e['a_tomb'] >= L['tomb_fator'] * mu, 'cg', f'tomba so acima de {L["tomb_fator"]:.2f} x mu (escorrega antes)',
                   f'tomba com {e["a_tomb"]:.2f} g; escorrega com {mu:.2f} g'),
         Resultado(e['a_empina'] >= L['empina_min'], 'cg', f'empina so acima de {L["empina_min"]:.2f} g',
                   f'{e["a_empina"]:.2f} g -> rampa do firmware deve limitar a aceleracao abaixo disso')]
    return R

# ------------------------------------------------------------------------------------------- 5. cabos
def _cabo_ffc(m, ang):
    m.partes_camera(ang)
    csi = np.array(m.cabos_ffc)
    pts = [tuple(csi), (csi[0] + 6, csi[1] + 10, csi[2] + 8), (m.P['PIVO'][0] - 6, -3.0, 100.0), tuple(m.cam_ffc_baixo),
           tuple(m.cam_ffc_pt)]
    return pts

def cabos(m, folga_roda=3.0):
    R = []
    mv = modelo.construir(m.P, verif=True)
    chapas = [dict(nome=n, solido=s, bb=bbox(s)) for n, s, _ in modelo.chapas_3d(mv)]
    girando = [dict(nome=p['nome'], solido=p['solido'], bb=bbox(p['solido'])) for p in mv.compradas
               if p['cat'] in ('roda', 'redutor')]
    lista = [dict(c) for c in mv.cabos]
    pior = max(np.arange(m.P['CAM_ANG'][0], m.P['CAM_ANG'][1] + 0.1, 5.0), key=lambda a: geo.comprimento(_cabo_ffc(mv, a)))
    lista.append(dict(nome='ffc_camera', pontos=_cabo_ffc(mv, pior), d=1.0, bitola='flat 15 vias', de='CSI da Jetson',
                      para='camera', apoios=[], disponivel=v('ffc_compr'), extra=0.0, obs=f'pior angulo: {pior:.0f} graus'))
    tabela = []
    for cb in lista:
        pts = cb['pontos']; Lr = geo.comprimento(pts)
        prob = []
        corte = Lr * (1 + m.P['CABO_FOLGA']) + cb['extra']
        if cb['disponivel'] is not None and corte > cb['disponivel']:
            prob.append(f'precisa de {corte:.0f} mm e tem {cb["disponivel"]:.0f} mm')
        # roda e redutor: tubo com o raio do cabo + folga
        tubo_folga = geo.tubo(pts, cb['d'] + 2 * folga_roda)
        bb_t = bbox(tubo_folga)
        for g in girando:
            if bbox_toca(bb_t, g['bb']) and volume_comum(tubo_folga, g['solido']) > 0.05:
                prob.append(f'a menos de {folga_roda:.0f} mm de {g["nome"]}')
        # nao atravessar chapa: o eixo do cabo (tubo fino) nao pode entrar no MDF
        tubo_eixo = geo.tubo(pts, max(0.6, cb['d'] * 0.4))
        bb_e = bbox(tubo_eixo)
        for c in chapas:
            if bbox_toca(bb_e, c['bb']) and volume_comum(tubo_eixo, c['solido']) > 0.05:
                prob.append(f'atravessa a chapa {c["nome"]}')
        # abracadeiras: cada apoio tem de estar no caminho e o trecho solto <= 110 mm
        sup = [0.0, Lr]
        for a in cb['apoios']:
            if a not in mv.apoios:
                prob.append(f'apoio "{a}" nao existe nas chapas')
                continue
            p = np.array(mv.apoios[a]); best = (1e9, 0.0); acum = 0.0
            for p0, p1 in zip(pts[:-1], pts[1:]):
                p0, p1 = np.array(p0), np.array(p1); seg = p1 - p0; ls = np.linalg.norm(seg)
                t = 0.0 if ls < 1e-9 else np.clip(np.dot(p - p0, seg) / ls ** 2, 0, 1)
                dist = np.linalg.norm(p0 + t * seg - p)
                if dist < best[0]:
                    best = (dist, acum + t * ls)
                acum += ls
            if best[0] > 12.0:
                prob.append(f'apoio "{a}" a {best[0]:.0f} mm do cabo')
            sup.append(best[1])
        sup = sorted(sup)
        vao = max(b - a for a, b in zip(sup[:-1], sup[1:]))
        if cb['disponivel'] is None and vao > 110.0:
            prob.append(f'trecho solto de {vao:.0f} mm (max 110: falta abracadeira)')
        tabela.append(dict(nome=cb['nome'], bitola=cb['bitola'], de=cb['de'], para=cb['para'], rota=Lr, corte=corte,
                           disponivel=cb['disponivel'], obs=cb.get('obs', ''), vao=vao))
        R.append(Resultado(not prob, 'cabos', cb['nome'], '; '.join(prob) if prob else
                           f'rota {Lr:.0f} mm, corte {corte:.0f} mm' + (f' (tem {cb["disponivel"]:.0f})' if cb['disponivel'] else '')))
    return R, tabela

# ------------------------------------------------------------------------------------------- pendencias
def medidas(para_cortar=False):
    pend = pendencias()
    return [Resultado(not para_cortar, 'medidas', f'conferir antes de cortar: {k}', nota) for k, nota in pend]

def tudo(m, para_cortar=False):
    R = []
    R += regulamento(m)
    R += interferencia(m)
    R += camera(m)
    R += material(m)
    R += cg(m)
    rc, tab = cabos(m)
    R += rc
    R += medidas(para_cortar)
    return R, tab
