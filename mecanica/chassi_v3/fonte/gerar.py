"""Gera tudo do chassi v3 a partir do modelo e roda as verificacoes. Sai com erro (codigo 1) se alguma falhar.

  python3 gerar.py                 # verificacoes + STEP + DXF + PDF 1:1 + imagens + resumo  (em ../)
  python3 gerar.py --so-verificar  # so as verificacoes
  python3 gerar.py --para-cortar   # medidas estimadas que mudam o corte viram ERRO (use antes de ir ao laser)
  T=2.85 FOLGA=-0.1 python3 gerar.py   # espessura medida e folga escolhida no pente de teste
"""
import os, sys, json, math, argparse, time
import numpy as np
import shapely.geometry as sg
import cadquery as cq
import ezdxf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Circle as MCirc
import modelo, verificacoes as V, render, analise
import geometria as geo
from geometria import Chapa, ret, ret_c, circ, oblongo, rasgo, Furo
from pecas import v, MASSAS, M as MEDIDAS

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, '..'))

# ------------------------------------------------------------------------------------------- pente de teste
def pecas_teste(m):
    T, S = m.T, m.S
    out = []
    # pente: rasgos de T-0,3 a T+0,1 (de 0,05 em 0,05)
    larg = [round(T - 0.3 + 0.05 * k, 2) for k in range(9)]
    base = ret(0, 0, 10 * len(larg) + 6, 20)
    ent = [ret(6 + 10 * k + 2, 12, 6 + 10 * k + 2 + w, 20.01) for k, w in enumerate(larg)]
    txt = [(f'{w:.2f}', 6 + 10 * k + 2 + w / 2, 6, 2.0) for k, w in enumerate(larg)] + [(f'T={T:.2f}', 3.5, 15, 1.6)]
    out.append(Chapa('pente_rasgos', base, [], [], ent, txt, qtd=1, descricao='escolher a folga do rasgo'))
    # furos: M2 (camera), M2.5 (Jetson, esfera), pino 3,3, M3 (passante)
    fs = [circ(6, 7, 2.2, 'M2'), circ(14, 7, 2.9, 'M2.5'), circ(22, 7, 3.3, 'pino 3 mm'), circ(30, 7, 3.4, 'M3'),
          circ(39, 7, 7.0, 'chave de fenda'), circ(50, 7, 8.0, 'passa-fio')]
    out.append(Chapa('teste_furos', ret(0, 0, 57, 16), fs, textos=[('M2 M2.5 P3 M3 7 8', 28, 13, 1.6)], qtd=1))
    # porca presa (a mesma da parede): peca com o bolso da porca + aba; tampinha com o rasgo da aba e o furo do parafuso
    zd, xp, xa = 20.0, 8.0, 22.0
    ent_p = [sg.Polygon([(xp - 1.6, zd + 0.01), (xp - 1.6, zd - 4.5), (xp - 2.9, zd - 4.5), (xp - 2.9, zd - 7.1), (xp - 1.6, zd - 7.1),
                         (xp - 1.6, zd - 11), (xp + 1.6, zd - 11), (xp + 1.6, zd - 7.1), (xp + 2.9, zd - 7.1), (xp + 2.9, zd - 4.5),
                         (xp + 1.6, zd - 4.5), (xp + 1.6, zd + 0.01)])]
    out.append(Chapa('teste_porca', ret(0, 0, 30, zd), [], [ret_c(xa, zd + T / 2, 10, T)], ent_p,
                     [('PORCA M3', 15, 3, 1.6)], qtd=1, descricao='encaixe da porca presa do tampo'))
    out.append(Chapa('teste_porca_tampa', ret(0, 0, 30, 14), [circ(xp, 7, 3.4, 'M3'), rasgo(xa, 7, 10, S, 'aba')],
                     textos=[('TAMPO', 15, 12, 1.4)], qtd=1, descricao='aba no rasgo, parafuso M3 por cima na porca presa'))
    # gabaritos de furacao das pecas compradas (molduras finas: por a peca em cima e conferir)
    J_W, J_D, _ = v('jet_placa')
    jf = [(J_W - (x - m.P['J0']) , 40 - y) for (x, y) in m.jet_furos]      # de volta para (u, v)
    jet = Chapa('gabarito_jetson', ret(0, 0, J_W, J_D), [circ(u, vv, 2.9, 'jetson') for u, vv in jf] +
                [Furo(ret(16, 6, J_W - 16, J_D - 6), 'miolo', funcao='vazado')],
                textos=[('JETSON  portas v', 50, 3, 2.0), ('P4', 8, 3, 1.6)], qtd=1, descricao='furos da Jetson (u, v)')
    out.append(jet)
    XL_L, XL_W = v('xl')
    out.append(Chapa('gabarito_xl4016', ret(0, 0, XL_L, XL_W), [circ(l, w, 3.4, 'xl') for l, w in v('xl_furos')] +
                     [Furo(ret(9, 9, XL_L - 9, XL_W - 9), 'miolo', funcao='vazado')] +
                     [circ(l, w, 7.0, 'trimpot') for l, w in v('xl_trimpots')],
                     textos=[('BORNES', 4.5, 24, 1.6), ('XL4016', 32, 4.5, 1.8)], qtd=1))
    EW, EL, _ = v('esp_placa')
    out.append(Chapa('gabarito_esp32', ret(0, 0, EW, EL), [circ(u, vv, 3.4, 'esp32') for u, vv in v('esp_furos')] +
                     [Furo(ret(8, 8, EW - 8, EL - 8), 'miolo', funcao='vazado')], textos=[('ESP32 frente ^', 40, EL - 4, 1.8)], qtd=1))
    cr = v('chave_recorte')
    out.append(Chapa('teste_chave', ret(0, 0, cr[0] + 8, cr[1] + 9), [Furo(ret_c((cr[0] + 8) / 2, (cr[1] + 9) / 2 + 1, *cr), 'chave')],
                     textos=[('CHAVE', (cr[0] + 8) / 2, 2.2, 1.5)], qtd=1))
    eh = v('esfera_furos') / 2
    out.append(Chapa('teste_esfera_motor', ret(0, 0, 50, 16),
                     [circ(10 - eh + 2, 8, 2.8, 'esfera'), circ(10 + eh + 2, 8, 2.8, 'esfera'),
                      oblongo((30, 8), (32.3, 8), 2.3, 'suporte'), oblongo((47.3 - 2.3, 8), (47.3, 8), 2.3, 'suporte')],
                     textos=[('ESFERA', 12, 13.5, 1.5), ('SUPORTE N20', 38, 13.5, 1.5)], qtd=1))
    return out

# ------------------------------------------------------------------------------------------- arranjo nas chapas
def expandir(chapas):
    itens = []
    for c in chapas:
        for k in range(c.qtd):
            itens.append(c)
    return itens

def arranjar(itens, mesa, sep=3.0):
    """Prateleiras: maior primeiro; gira 90 graus se ajudar. Devolve lista de folhas, cada uma [(chapa, dx, dy, girar)]."""
    W, H = mesa
    def dims(c, g):
        x0, y0, x1, y1 = c.contorno.bounds
        return ((y1 - y0, x1 - x0) if g else (x1 - x0, y1 - y0))
    itens = sorted(itens, key=lambda c: -max(dims(c, False)) * min(dims(c, False)))
    folhas = []
    for c in itens:
        colocado = False
        for f in folhas:
            for g in (False, True):
                w, h = dims(c, g)
                for prat in f['prat']:
                    if prat['x'] + w <= W and h <= prat['h']:
                        f['itens'].append((c, prat['x'], prat['y'], g)); prat['x'] += w + sep; colocado = True; break
                if colocado:
                    break
                if f['y'] + h <= H and w <= W:
                    f['prat'].append(dict(x=w + sep, y=f['y'], h=h)); f['itens'].append((c, 0.0, f['y'], g))
                    f['y'] += h + sep; colocado = True; break
            if colocado:
                break
        if not colocado:
            w, h = dims(c, False)
            g = False
            if w > W or h > H:
                g = True; w, h = dims(c, True)
            if w > W or h > H:
                raise ValueError(f'{c.nome} nao cabe na mesa {W} x {H}')
            folhas.append(dict(prat=[dict(x=w + sep, y=0.0, h=h)], y=h + sep, itens=[(c, 0.0, 0.0, g)]))
    return [f['itens'] for f in folhas]

def transformar(c, dx, dy, girar):
    x0, y0, x1, y1 = c.contorno.bounds
    def tr(p):
        x, y = p
        if girar:
            x, y = -(y - y0), x - x0
            return (x + (y1 - y0) + dx, y + dy)
        return (x - x0 + dx, y - y0 + dy)
    return tr

def escrever_dxf(folha, arq):
    doc = ezdxf.new('R2010', setup=True); doc.units = ezdxf.units.MM
    doc.layers.add('CORTE', color=1); doc.layers.add('GRAVAR', color=5)
    msp = doc.modelspace()
    for c, dx, dy, g in folha:
        tr = transformar(c, dx, dy, g)
        msp.add_lwpolyline([tr(p) for p in list(c.contorno.exterior.coords)[:-1]], close=True, dxfattribs={'layer': 'CORTE'})
        for f in c.furos:
            if f.tipo == 'circ':
                msp.add_circle(tr(f.centro), f.d / 2, dxfattribs={'layer': 'CORTE'})
            else:
                msp.add_lwpolyline([tr(p) for p in list(f.geom.exterior.coords)[:-1]], close=True, dxfattribs={'layer': 'CORTE'})
        for (txt, x, y, h) in c.textos:
            t = msp.add_text(txt, dxfattribs={'layer': 'GRAVAR', 'height': h, 'rotation': 90 if g else 0})
            t.set_placement(tr((x, y)), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(arq)

def desenhar_folha(folha, ax, mesa):
    for c, dx, dy, g in folha:
        tr = transformar(c, dx, dy, g)
        ax.add_patch(MPoly([tr(p) for p in c.contorno.exterior.coords], closed=True, fill=True, fc=(0.97, 0.93, 0.86),
                           ec='red', lw=0.35))
        for f in c.furos:
            if f.tipo == 'circ':
                ax.add_patch(MCirc(tr(f.centro), f.d / 2, fill=True, fc='white', ec='red', lw=0.35))
            else:
                ax.add_patch(MPoly([tr(p) for p in f.geom.exterior.coords], closed=True, fc='white', ec='red', lw=0.35))
        for (txt, x, y, h) in c.textos:
            ax.text(*tr((x, y)), txt, fontsize=h * 2.2, color='blue', ha='center', va='center', rotation=90 if g else 0)

def pdf_1x1(folhas, arq_pdf, titulos, mesa, nota):
    from matplotlib.backends.backend_pdf import PdfPages
    PW, PH = 420.0, 297.0      # A3 deitado
    with PdfPages(arq_pdf) as pdf:
        for folha, tit in zip(folhas, titulos):
            fig = plt.figure(figsize=(PW / 25.4, PH / 25.4))
            ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, PW); ax.set_ylim(0, PH); ax.set_aspect('equal'); ax.axis('off')
            ox, oy = 15.0, 22.0
            sub = []
            for c, dx, dy, g in folha:
                sub.append((c, dx + ox, dy + oy, g))
            desenhar_folha(sub, ax, mesa)
            ax.add_patch(MPoly([(ox, oy), (ox + mesa[0], oy), (ox + mesa[0], oy + mesa[1]), (ox, oy + mesa[1])], closed=True,
                               fill=False, ec=(0.6, 0.6, 0.6), lw=0.3, ls='--'))
            # regua de conferencia: 100 mm com marcas de 10 mm e um quadrado de 50 mm
            rx, ry = 15.0, 8.0
            ax.plot([rx, rx + 100], [ry, ry], 'k-', lw=0.6)
            for k in range(11):
                ax.plot([rx + 10 * k, rx + 10 * k], [ry, ry + (3 if k % 5 == 0 else 1.8)], 'k-', lw=0.5)
            ax.text(rx + 50, ry - 4, 'REGUA: esta linha tem 100,0 mm. Imprima em 100 % (sem "ajustar a pagina") e confira.',
                    fontsize=6.5, ha='center')
            ax.add_patch(MPoly([(130, 4), (180, 4), (180, 54 - 40), (130, 54 - 40)], closed=True, fill=False, ec='k', lw=0.5))
            ax.text(155, 9, '50 x 10 mm', fontsize=6, ha='center')
            ax.text(200, 12, tit, fontsize=9, ha='left', weight='bold')
            ax.text(200, 6, nota, fontsize=6.5, ha='left')
            pdf.savefig(fig); plt.close(fig)

def png_folha(folha, arq, mesa, titulo):
    fig = plt.figure(figsize=(mesa[0] / 40, mesa[1] / 40 + 0.4), dpi=110)
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.92]); ax.set_xlim(-2, mesa[0] + 2); ax.set_ylim(-2, mesa[1] + 2)
    ax.set_aspect('equal'); ax.axis('off')
    desenhar_folha(folha, ax, mesa)
    ax.add_patch(MPoly([(0, 0), (mesa[0], 0), mesa, (0, mesa[1])], closed=True, fill=False, ec='gray', ls='--', lw=0.6))
    ax.set_title(titulo, fontsize=9)
    fig.savefig(arq, facecolor='white'); plt.close(fig)

# ------------------------------------------------------------------------------------------- STEP e imagens
def montagem(m, ang=None, cabos=True):
    asm = cq.Assembly(name='robocar_blitz_v3')
    itens = []
    for nome, sol, ch in modelo.chapas_3d(m, ang):
        asm.add(cq.Workplane().add(sol), name=nome, color=cq.Color(*render.COR_MDF[:3]))
        itens.append((sol, render.COR_MDF))
    for p in m.compradas + modelo.camera_compradas(m, m.P['CAM_ANG_NOMINAL'] if ang is None else ang):
        asm.add(cq.Workplane().add(p['solido']), name=p['nome'], color=cq.Color(*p['cor']))
        itens.append((p['solido'], tuple(p['cor']) + (1.0,)))
    if cabos:
        cores = {'0,75 mm2 vermelho + preto': (0.8, 0.1, 0.1), '0,75 mm2 vermelho': (0.85, 0.1, 0.1),
                 'cabo de 6 vias do motor': (0.95, 0.95, 0.95), '0,2 mm2 (fio fino)': (0.9, 0.5, 0.1)}
        for cb in m.cabos:
            cor = cores.get(cb['bitola'], (0.15, 0.15, 0.15))
            segs = [geo.cilindro(p, q, cb['d']) for p, q in zip(cb['pontos'][:-1], cb['pontos'][1:])
                    if np.linalg.norm(np.array(q) - np.array(p)) > 0.01]
            sol = cq.Compound.makeCompound(segs)
            asm.add(cq.Workplane().add(sol), name='cabo_' + cb['nome'], color=cq.Color(*cor))
            itens.append((sol, cor + (1.0,)))
    return asm, itens

def imagens(m, pasta):
    os.makedirs(pasta, exist_ok=True)
    _, itens = montagem(m)
    tri = render.triangulos(itens)
    lim = ((-105, -82, 0), (145, 82, 158))
    render.vista3d(tri, os.path.join(pasta, 'vista_3d.png'), 24, -52, 'Robocar Blitz v3 - frente e lado DIREITO (chave, fusivel, XT60)', lim)
    render.vista3d(tri, os.path.join(pasta, 'vista_3d_tras_esquerda.png'), 28, 128, 'Tras e lado ESQUERDO (portas da Jetson: P4 e USB)', lim)
    render.vista3d(tri, os.path.join(pasta, 'vista_lado_direito.png'), 0, -90, 'Lado direito (frente para a direita)', lim, tamanho=(11, 6.5))
    render.vista3d(tri, os.path.join(pasta, 'vista_lado_esquerdo.png'), 0, 90, 'Lado esquerdo (frente para a esquerda)', lim, tamanho=(11, 6.5))
    render.vista3d(tri, os.path.join(pasta, 'vista_cima.png'), 90, -90, 'Vista de cima (frente para a direita)', lim, tamanho=(11, 7))
    render.vista3d(tri, os.path.join(pasta, 'vista_frente.png'), 0, 0, 'Vista de frente', lim, tamanho=(8, 7))
    render.vista3d(tri, os.path.join(pasta, 'vista_tras.png'), 0, 180, 'Vista de tras (janelas de ar dos XL4016)', lim, tamanho=(8, 7))
    # sem tampo e sem placa da ESP32: o que fica embaixo
    sem = [(s, c) for (s, c), (nome) in zip(itens, [n for n, _, _ in modelo.chapas_3d(m)] + [p['nome'] for p in m.compradas] +
                                             [p['nome'] for p in modelo.camera_compradas(m, m.P['CAM_ANG_NOMINAL'])] +
                                             ['cabo_' + cb['nome'] for cb in m.cabos])
           if not (nome == 'tampo' or nome.startswith(('placa_esp32', 'esp32', 'barras', 'drv8833', 'c470', 'plugue_usb_esp32',
                                                        'placa_desligar', 'botao_desligar', 'led_pode', 'jetson', 'plugue_p4',
                                                        'plugue_usb_a', 'espacador_jetson')))]
    render.vista3d(render.triangulos(sem), os.path.join(pasta, 'vista_sem_tampo_e_jetson.png'), 40, -60,
                   'Sem o tampo e sem a Jetson: XL4016, quilha, bateria, fusivel, chave', lim)
    figura_camera(m, os.path.join(pasta, 'camera_faixa_angulo.png'))

def figura_camera(m, arq):
    """Lado (x para a direita): mastro, Jetson, piso e, para 3 angulos, camera, eixo otico e campo de visao vertical."""
    vf = v('cam_vfov')
    fig, ax = plt.subplots(figsize=(10, 6.2), dpi=130)
    postes = next(c for c in m.chapas if c.nome == 'poste_mastro')
    ax.add_patch(MPoly(list(postes.contorno.exterior.coords), closed=True, fc=(0.85, 0.72, 0.5), ec='k', lw=0.6))
    ax.add_patch(MPoly([(13, m.Z1), (141, m.Z1), (141, m.Z2), (13, m.Z2)], closed=True, fc=(0.85, 0.72, 0.5), ec='k', lw=0.5))
    ax.add_patch(MPoly([(m.P['J0'], m.ZJ), (m.P['J0'] + 100, m.ZJ), (m.P['J0'] + 100, m.ZJ + v('jet_altura')),
                        (m.P['J0'], m.ZJ + v('jet_altura'))], closed=True, fc=(0.4, 0.45, 0.5), ec='k', lw=0.5))
    ax.text(m.P['J0'] + 50, m.ZJ + 12, 'Jetson', ha='center', color='white', fontsize=8)
    ax.add_patch(MPoly([(m.P['XT60_X'] - 7.75, m.Z2), (m.P['XT60_X'] + 7.75, m.Z2), (m.P['XT60_X'] + 7.75, m.Z2 + 8),
                        (m.P['XT60_X'] - 7.75, m.Z2 + 8)], closed=True, fc=(0.95, 0.8, 0.1), ec='k', lw=0.5))
    ax.add_patch(MCirc((0, 21), 21, fc=(0.15, 0.15, 0.15)))
    ax.plot([-30, 330], [0, 0], 'k-', lw=1)
    for ang, cor in ((m.P['CAM_ANG'][0], 'tab:blue'), (m.P['CAM_ANG_NOMINAL'], 'k'), (m.P['CAM_ANG'][1], 'tab:red')):
        m.partes_camera(ang)
        p = np.array(m.cam_centro)[[0, 2]]
        for d_ang, ls, lw in ((0, '-', 1.2), (-vf / 2, ':', 0.9), (vf / 2, ':', 0.9)):
            a_ = math.radians(ang + d_ang)
            d = np.array([math.cos(a_), -math.sin(a_)])
            t = p[1] / -d[1] if d[1] < 0 else 300
            q = p + d * min(t, 330)
            ax.plot([p[0], q[0]], [p[1], q[1]], ls=ls, color=cor, lw=lw)
        ax.plot(*p, 'o', color=cor, ms=4)
        x_perto = p[0] + p[1] / math.tan(math.radians(ang + vf / 2)) if ang + vf / 2 < 90 else None
        x_eixo = p[0] + p[1] / math.tan(math.radians(ang))
        txt = f'{ang:.0f} graus: eixo no chao a {x_eixo - p[0]:.0f} mm a frente da camera'
        txt += f'; ve o chao a partir de {x_perto - p[0]:.0f} mm' if x_perto else '; a borda de baixo da imagem ja pega o carro'
        ax.text(150, 150 - 10 * [m.P['CAM_ANG'][0], m.P['CAM_ANG_NOMINAL'], m.P['CAM_ANG'][1]].index(ang), txt, color=cor, fontsize=7.5)
    ax.set_aspect('equal'); ax.set_xlim(-30, 330); ax.set_ylim(-5, 165)
    ax.set_xlabel('x (mm, 0 = eixo das rodas)'); ax.set_ylabel('z (mm)')
    ax.set_title(f'Camera: centro da lente, eixo otico (cheio) e campo vertical estimado de {vf:.0f} graus (pontilhado)', fontsize=9)
    ax.grid(alpha=0.2)
    fig.tight_layout(); fig.savefig(arq, facecolor='white'); plt.close(fig)

# ------------------------------------------------------------------------------------------- fixadores (de cada furo)
FIXADORES = {
    'parafuso M2 do suporte': ('Parafuso M2 x 16 + porca (vem com o suporte do N20)', 1),
    'parafuso M3 do XL4016': ('Parafuso M3 x 12 + porca + espacador nylon M3 x 4 mm (ou 2 porcas)', 1),
    'parafuso M3 que une os pisos': ('Parafuso M3 x 10 + porca', 1),
    'parafuso M2.5 do espacador da Jetson': ('Espacador M2.5 x 20 mm (femea-femea) + parafuso M2.5 x 6 embaixo e em cima', 0.5),
    'parafuso M2.5 da esfera': ('Parafuso M2.5 x 8 CABECA CHATA (escareado) por cima + porca embaixo; escarear o furo a mao', 1),
    'parafuso M3 da placa da ESP32': ('Parafuso M3 x 10 + espacador nylon M3 x 5 mm + porca', 1),
    'parafuso M3 da placa de desligar': ('Parafuso M3 x 10 + espacador M3 x 3 mm + porca', 1),
    'parafuso M3 do tampo (porca presa na parede)': ('Parafuso M3 x 12 + porca M3 presa no bolso da parede', 1),
    'pivo da camera (M3)': ('Parafuso M3 x 10 + porca (pivo da camera, um de cada lado)', 1),
    'trava do angulo (M3)': ('Parafuso M3 x 10 + porca borboleta (trava do angulo, um de cada lado)', 1),
    'parafuso M2 da camera': ('Parafuso M2 x 8 + porca + arruela fina (camera)', 1),
    'pino que trava a bateria (tirar com a mao)': ('Pino de trava: arame/prego de 3 mm x 50 mm dobrado em L', 0.5),
}

def lista_fixadores(m):
    cont = {}
    for c in m.chapas:
        for f in c.furos:
            if f.funcao in FIXADORES:
                item, k = FIXADORES[f.funcao]
                cont[item] = cont.get(item, 0) + k * c.qtd
    return sorted(((k, int(math.ceil(q))) for k, q in cont.items()), key=lambda x: x[0])

# ------------------------------------------------------------------------------------------- principal
def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument('--so-verificar', action='store_true')
    ap.add_argument('--para-cortar', action='store_true')
    ap.add_argument('--sem-imagens', action='store_true')
    ap.add_argument('--saida', default=RAIZ)
    a = ap.parse_args()
    P = {}
    for k in ('T', 'FOLGA'):
        if os.environ.get(k):
            P[k] = float(os.environ[k])
    t0 = time.time()
    m = modelo.construir(P)
    print(f'chassi v3: T = {m.T} mm, rasgo = {m.S:.2f} mm ({len(m.chapas)} tipos de peca)')
    R, tab_cabos = V.tudo(m, a.para_cortar)
    falhas = [r for r in R if not r.ok]
    out = a.saida
    linhas = ['# Verificacao automatica do chassi v3 (gerada por `fonte/gerar.py`)', '',
              f'Espessura T = {m.T} mm, rasgo = {m.S:.2f} mm. Resultado: **{"FALHOU" if falhas else "tudo ok"}** '
              f'({len(R) - len(falhas)} ok, {len(falhas)} falhas).', '', '| | grupo | verificacao | detalhe |', '|---|---|---|---|']
    for r in R:
        linhas.append(f"| {'ok' if r.ok else '**FALHOU**'} | {r.grupo} | {r.nome} | {r.detalhe} |")
    linhas += ['', '## Cabos: rota e comprimento de corte', '',
               'Corte = rota x 1,10 + 20 mm (descascar, terminal, termorretratil). Cabos prontos (motor, USB, flat, Dupont) so sao conferidos.', '',
               '| cabo | bitola | de | para | rota (mm) | corte (mm) | disponivel | maior trecho solto (mm) | obs |', '|---|---|---|---|---|---|---|---|---|']
    for t in tab_cabos:
        corte = '—' if t['disponivel'] else f"{t['corte']:.0f}"
        disp = f"{t['disponivel']:.0f}" if t['disponivel'] else '—'
        linhas.append(f"| {t['nome']} | {t['bitola']} | {t['de']} | {t['para']} | {t['rota']:.0f} | {corte} | {disp} | "
                      f"{t['vao']:.0f} | {t['obs']} |")
    M_, c = modelo.cg(modelo.massas(m))
    est = analise.estabilidade(c, m.P['ESFERA_X'], m.P['BITOLA'], m.P['MU'])
    dim = V.dimensoes(m)
    linhas += ['', '## Massas (para refazer o CG depois de pesar)', '', '| item | g | x | y | z | origem |', '|---|---|---|---|---|---|']
    for nome, g, (x, y, z) in sorted(modelo.massas(m), key=lambda q: -q[1]):
        if g >= 0.5:
            base = nome.split('_')[0]
            orig = next((f"{MASSAS[k][1]}{' (PESAR)' if MASSAS[k][2] else ''}" for k in MASSAS if nome.startswith(k)), 'calculada')
            linhas.append(f'| {nome} | {g:.1f} | {x:.0f} | {y:.0f} | {z:.0f} | {orig} |')
    linhas += [f'| **total** | **{M_:.0f}** | **{c[0]:.1f}** | **{c[1]:.1f}** | **{c[2]:.1f}** | |']
    linhas += ['', '## Fixadores (contados pelos furos)', '', '| item | qtd |', '|---|---|']
    for item, q in lista_fixadores(m):
        linhas.append(f'| {item} | {q} |')
    open(os.path.join(out, 'verificacao.md'), 'w').write('\n'.join(linhas) + '\n')
    for r in R:
        if not r.ok:
            print('  FALHOU', r)
    resumo = dict(T=m.T, rasgo=round(m.S, 3), comprimento_mm=round(dim['comprimento'], 1), largura_mm=round(dim['largura'], 1),
                  altura_mm=round(dim['altura'], 1), x_min_max=[round(dim['lo'][0], 1), round(dim['hi'][0], 1)],
                  y_min_max=[round(dim['lo'][1], 1), round(dim['hi'][1], 1)], massa_g=round(M_), cg_mm=[round(q, 1) for q in c],
                  peso_nas_rodas=round(est['carga_rodas'], 3), tomba_g=round(est['a_tomb'], 2), empina_g=round(est['a_empina'], 2),
                  z=dict(piso_traseiro=[m.Z0, m.Z1], piso_dianteiro=[m.Z1, m.Z2], tampo=[m.ZD, m.ZD + m.T], jetson_placa=m.ZJ,
                         esp32_placa=m.Z_ESP),
                  verificacoes=dict(total=len(R), falhas=len(falhas)),
                  pecas=[dict(nome=ch.nome, qtd=ch.qtd, area_mm2=round(ch.area()), massa_g=round(ch.area() * m.T * v('massa_mdf_dens') / 1000, 1),
                              descricao=ch.descricao) for ch in m.chapas])
    json.dump(resumo, open(os.path.join(out, 'resumo.json'), 'w'), indent=1, ensure_ascii=False)
    print(f"  {dim['comprimento']:.1f} x {dim['largura']:.1f} x {dim['altura']:.1f} mm, {M_:.0f} g, CG {c.round(1)}, "
          f"tomba {est['a_tomb']:.2f} g, empina {est['a_empina']:.2f} g")
    if a.so_verificar:
        print('falhas:', len(falhas)); return 1 if falhas else 0
    # ---- corte
    pasta_c = os.path.join(out, 'corte'); os.makedirs(pasta_c, exist_ok=True)
    mesa = m.P['MESA']
    folhas = arranjar(expandir(m.chapas), mesa)
    nota = f'MDF T = {m.T} mm, rasgo {m.S:.2f} mm. Vermelho = cortar; azul = gravar (opcional).'
    tit = []
    for k, f in enumerate(folhas):
        escrever_dxf(f, os.path.join(pasta_c, f'chapa_{k + 1}.dxf'))
        tit.append(f'Robocar Blitz v3 - chapa {k + 1} de {len(folhas)} ({mesa[0]:.0f} x {mesa[1]:.0f} mm)')
    pdf_1x1(folhas, os.path.join(pasta_c, 'chapas_1x1_A3.pdf'), tit, mesa, nota)
    teste = arranjar(expandir(pecas_teste(m)), (270.0, 180.0))
    escrever_dxf(teste[0], os.path.join(pasta_c, 'TESTE_cortar_primeiro.dxf'))
    pdf_1x1(teste, os.path.join(pasta_c, 'TESTE_cortar_primeiro_1x1_A3.pdf'), ['Robocar Blitz v3 - CORTAR PRIMEIRO: pente, furos e gabaritos'],
            (270.0, 180.0), nota)
    # ---- STEP e imagens
    asm, _ = montagem(m)
    asm.save(os.path.join(out, 'chassi_montado.step'))
    if not a.sem_imagens:
        os.makedirs(os.path.join(out, 'imagens'), exist_ok=True)
        for k, f in enumerate(folhas):
            png_folha(f, os.path.join(out, 'imagens', f'corte_chapa_{k + 1}.png'), mesa, tit[k])
        png_folha(teste[0], os.path.join(out, 'imagens', 'corte_TESTE.png'), (270.0, 180.0), 'Cortar primeiro: pente, furos e gabaritos')
        imagens(m, os.path.join(out, 'imagens'))
    analise.relatorio(m, os.path.join(out, 'analise.md'))
    print(f'pronto em {time.time() - t0:.0f} s: {len(folhas)} chapa(s) {mesa[0]:.0f} x {mesa[1]:.0f}, falhas: {len(falhas)}')
    return 1 if falhas else 0

if __name__ == '__main__':
    sys.exit(principal())
