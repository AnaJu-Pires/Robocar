"""Chassi do Robocar Blitz em chapas cortadas a laser (MDF 3 mm; o andar 2 pode ser acrilico 3 mm).
Uma fonte so para: arquivos de corte (DXF), PDF 1:1 para conferir no papel, modelo 3D (STEP) e imagens.
Eixos: x para a frente (0 = eixo das rodas), y para a esquerda, z para cima (0 = chao). Medidas em mm.
Uso: python3 chassi.py <pasta_saida>   (ajuste T e FOLGA depois do pente de teste)"""
import sys, os, math, json
import cadquery as cq
import ezdxf, ezdxf.bbox
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else 'saida'
os.makedirs(OUT, exist_ok=True)
T = float(os.environ.get('T', 3.0))        # espessura medida da chapa
FOLGA = float(os.environ.get('FOLGA', -0.1))  # largura do rasgo = T + FOLGA (MDF: aperto; acrilico: use +0.1)
S = T + FOLGA
c45 = math.sqrt(0.5)

# ---------------------------------------------------------------- formas 2D
def rect(x0, y0, x1, y1): return ('poly', [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
def circ(x, y, d): return ('circ', (x, y), d / 2)
def slot(p1, p2, w): return ('slot', p1, p2, w / 2)
def poly_of(sh, n=24):
    if sh[0] == 'poly': return sh[1]
    if sh[0] == 'circ':
        (x, y), r = sh[1], sh[2]
        return [(x + r * math.cos(2 * math.pi * k / n), y + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    (x1, y1), (x2, y2), r = sh[1], sh[2], sh[3]
    a = math.atan2(y2 - y1, x2 - x1); pts = []
    for k in range(n // 2 + 1):
        t = a - math.pi / 2 + math.pi * k / (n // 2); pts.append((x2 + r * math.cos(t), y2 + r * math.sin(t)))
    for k in range(n // 2 + 1):
        t = a + math.pi / 2 + math.pi * k / (n // 2); pts.append((x1 + r * math.cos(t), y1 + r * math.sin(t)))
    return pts

class Peca:
    def __init__(s, nome, qtd, material, contorno, furos, frames, textos=()):
        s.nome, s.qtd, s.material, s.contorno, s.furos, s.frames, s.textos = nome, qtd, material, contorno, furos, frames, list(textos)
    def area(s):
        def A(p): return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2
        return A(s.contorno) - sum(A(poly_of(f)) for f in s.furos)
    def solido(s):
        w = cq.Workplane('XY').polyline(s.contorno).close().extrude(T)
        for f in s.furos:
            w = w.cut(cq.Workplane('XY').polyline(poly_of(f, 32)).close().extrude(T))
        return w.val()

from OCP.gp import gp_Trsf
def M(ex, ey, ez, o):  # colunas: eixo a, eixo b, eixo w (espessura), origem
    t = gp_Trsf()
    t.SetValues(ex[0], ey[0], ez[0], o[0], ex[1], ey[1], ez[1], o[1], ex[2], ey[2], ez[2], o[2])
    return cq.Location(t)

# ---------------------------------------------------------------- medidas das pecas compradas
RODA_D, RODA_L, BITOLA = 42.0, 19.0, 104.0
EIXO_Z = RODA_D / 2                 # 21
EIXO_NO_SUPORTE = 6.0               # altura do eixo do motor acima da chapa, no suporte branco 25x12x12 (estimado)
Z1 = EIXO_Z - EIXO_NO_SUPORTE       # topo do andar 1 = 15
H_PAREDE = 35.0                     # vao entre andares
Z2 = Z1 + H_PAREDE                  # fundo do andar 2 = 50
Y_SUP = BITOLA / 2 - RODA_L / 2 - 1.5 - 6.0   # centro do suporte do motor (y) = 35
ESP_X1 = 118.0                      # borda da frente da placa da ESP32
PL_W, PL_H = 72.5, 63.0             # placa da ESP32 v0.6 (hardware/placa_esp32): largura (x_b) e altura (y_b)
PL_FUROS = [(3.5, 3.5), (PL_W - 3.5, 3.5), (PL_W - 3.5, PL_H - 3.5), (3.5, PL_H - 3.5)]  # M3 nos 4 cantos
def furo_esp(xb, yb): return (ESP_X1 - yb, PL_W / 2 - xb)   # placa: x_b para a direita (= -y), y_b para tras
def caixa_placa(u0, u1, v0, v1): return (ESP_X1 - v1, ESP_X1 - v0, PL_W / 2 - u1, PL_W / 2 - u0)  # (x0, x1, y0, y1)
JET_X0 = 14.0                       # Jetson Nano 100 x 80; furos 86 x 58 (conferir)
JET_FUROS = [(JET_X0 + 7, s * 29) for s in (1, -1)] + [(JET_X0 + 93, s * 29) for s in (1, -1)]
BAT = (14.0, 49.0, 37.5)            # bateria deitada: x0, x1, meia largura (75 x 35 x ~25)
XL = (-89.5, -24.5)                 # XL4016 (65 x 46) lado a lado atras do eixo
Q = (138.0, 130.0)                  # centro (costas) da placa da camera; inclinacao 45 graus
ESFERA_X = 137.0
PAREDE_X = (52.0, 120.0); PAREDE_Y = 44.0
POSTE_Y = 15.0; POSTE_X = (116.0, 126.5); TRAVESSA_X = 121.25

# ---------------------------------------------------------------- andar 1 (MDF)
a1 = [(-95, -52), (-24, -52), (-24, -41), (24, -41), (24, -49), (121, -49), (147, -16), (147, 16), (121, 49), (24, 49), (24, 41), (-24, 41), (-24, 52), (-95, 52)]
f1 = []
for sy in (1, -1):
    for sx in (1, -1):
        f1.append(slot((sx * 8.5, sy * Y_SUP), (sx * 10.8, sy * Y_SUP), 2.3))       # suporte do motor (M2), oblongo p/ ajustar
for (xb, yb) in PL_FUROS:
    f1.append(circ(*furo_esp(xb, yb), 3.4))                                        # placa da ESP32 (M3)
f1 += [circ(ESFERA_X, 8, 2.8), circ(ESFERA_X, -8, 2.8)]                             # esfera (M2.5, furos a 16 mm)
for sy in (1, -1):
    f1.append(rect(21.5, sy * 39.0 - 1.5, 41.5, sy * 39.0 + 1.5) if sy > 0 else rect(21.5, -40.5, 41.5, -37.5))  # cinta da bateria
f1 = f1[:-2] + [rect(21.5, 39.0, 41.5, 42.0), rect(21.5, -42.0, 41.5, -39.0)]
for xc in (58, 86, 114):                                                            # abas de baixo das paredes
    for sy in (1, -1): f1.append(rect(xc - 5, sy * PAREDE_Y - S / 2, xc + 5, sy * PAREDE_Y + S / 2))
for sy in (1, -1): f1.append(rect(-93.5 + (3 - S) / 2, sy * 12 - 5, -90.5 - (3 - S) / 2, sy * 12 + 5))  # painel traseiro
for xc in (-79.5, -34.5):                                                           # abracadeiras dos XL4016
    for sy in (1, -1): f1.append(rect(xc - 2.25, sy * 48 - 1.25, xc + 2.25, sy * 48 + 1.25))
for sy in (1, -1): f1.append(rect(-72, sy * 6 if sy > 0 else -40, -42, 40 if sy > 0 else -6))  # alivio embaixo dos XL4016
f1.append(rect(62, -25, 108, 25))                                                   # alivio embaixo da placa da ESP32
andar1 = Peca('andar1', 1, 'MDF', a1, f1, [M((1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, Z1 - T))],
              [('ANDAR 1 - FRENTE >', 95, -44, 4), ('BLITZ', -60, 0, 6)])

# ---------------------------------------------------------------- andar 2 (MDF ou acrilico)
a2 = [(10, -49), (124, -49), (124, -22), (130, -22), (130, 22), (124, 22), (124, 49), (10, 49)]
f2 = [circ(x, y, 2.9) for (x, y) in JET_FUROS]                                      # Jetson (M2.5)
for xc in (70, 102):
    for sy in (1, -1): f2.append(rect(xc - 5, sy * PAREDE_Y - S / 2, xc + 5, sy * PAREDE_Y + S / 2))
for xc in (60, 86, 112):
    for sy in (1, -1): f2.append(circ(xc, sy * PAREDE_Y, 3.4))                       # parafusos M3 das porcas presas
for sy in (1, -1): f2.append(rect(117, sy * POSTE_Y - S / 2, 125, sy * POSTE_Y + S / 2))  # postes da camera
f2.append(rect(30, -22, 98, 22))                                                    # alivio + passagem do USB da ESP32
andar2 = Peca('andar2', 1, 'MDF ou acrilico', a2, f2, [M((1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, Z2))],
              [('ANDAR 2 - FRENTE >', 60, -40, 4)])

# ---------------------------------------------------------------- paredes laterais (2x, MDF)
L_P = PAREDE_X[1] - PAREDE_X[0]
pw = [(0, 0)]
for uc in (6, 34, 62):  # abas de baixo
    pw += [(uc - 5, 0), (uc - 5, -T), (uc + 5, -T), (uc + 5, 0)]
pw += [(L_P, 0), (L_P, H_PAREDE)]
for uc in (50, 18):     # abas de cima (sentido inverso)
    pw += [(uc + 5, H_PAREDE), (uc + 5, H_PAREDE + T), (uc - 5, H_PAREDE + T), (uc - 5, H_PAREDE)]
pw += [(0, H_PAREDE)]
fw = []
for uc in (8, 34, 60):  # porca presa (T-nut): rasgo do parafuso + bolso da porca M3
    fw.append(('poly', [(uc - 1.6, H_PAREDE + 0.01), (uc - 1.6, H_PAREDE - 5.0), (uc - 2.9, H_PAREDE - 5.0), (uc - 2.9, H_PAREDE - 7.6),
                        (uc - 1.6, H_PAREDE - 7.6), (uc - 1.6, H_PAREDE - 12), (uc + 1.6, H_PAREDE - 12), (uc + 1.6, H_PAREDE - 7.6),
                        (uc + 2.9, H_PAREDE - 7.6), (uc + 2.9, H_PAREDE - 5.0), (uc + 1.6, H_PAREDE - 5.0), (uc + 1.6, H_PAREDE + 0.01)]))
fw += [rect(12, 5, 29, 19), rect(39, 5, 55, 29)]  # janela de alivio + janela do USB da ESP32
# o rasgo da porca encosta na borda: une ao contorno (corta como entalhe)
import shapely.geometry as sg
def sub(contorno, furos_borda):
    p = sg.Polygon(contorno)
    for f in furos_borda: p = p.difference(sg.Polygon(f[1]))
    return [tuple(map(float, q)) for q in list(p.exterior.coords)[:-1]]
pw = sub(pw, [f for f in fw if len(f[1]) == 12]); fw = [f for f in fw if len(f[1]) != 12]
paredes = Peca('parede', 2, 'MDF', pw, fw,
               [M((1, 0, 0), (0, 0, 1), (0, -1, 0), (PAREDE_X[0], s * PAREDE_Y + T / 2, Z1)) for s in (1, -1)],
               [('PAREDE', 20, 12, 3)])

# ---------------------------------------------------------------- postes da camera (2x, MDF), travessas (2x) e placa da camera
ux, uz = c45, c45; nx, nz = c45, -c45
A_ = (Q[0] - 16 * ux, Q[1] - 16 * uz); B_ = (Q[0] + 16 * ux, Q[1] + 16 * uz)
zf = Q[1] + (POSTE_X[1] - Q[0])            # linha de 45 graus em x = frente do poste
B2 = (B_[0] - 6 * c45, B_[1] + 6 * c45)
tab = [(Q[0] - 5 * ux, Q[1] - 5 * uz), (Q[0] - 5 * ux + T * nx, Q[1] - 5 * uz + T * nz), (Q[0] + 5 * ux + T * nx, Q[1] + 5 * uz + T * nz), (Q[0] + 5 * ux, Q[1] + 5 * uz)]
zb = Z2 + T
pp = [(POSTE_X[0], zb), (117, zb), (117, zb - T), (125, zb - T), (125, zb), (POSTE_X[1], zb), (POSTE_X[1], zf)] + tab + [B_, B2, (POSTE_X[0], B2[1])]
fp = [rect(TRAVESSA_X - S / 2, 68, TRAVESSA_X + S / 2, 76), rect(TRAVESSA_X - S / 2, 100, TRAVESSA_X + S / 2, 108)]
postes = Peca('poste_camera', 2, 'MDF', pp, fp, [M((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, s * POSTE_Y + T / 2, 0)) for s in (1, -1)],
              [('POSTE', 121, 85, 3)])
rw = [(-13.5 - (3 - S) / 2 + 0, 66), (-13.5, 66)]
rw = [(-13.5, 66), (13.5, 66), (13.5, 68), (16.5, 68), (16.5, 76), (13.5, 76), (13.5, 78), (-13.5, 78), (-13.5, 76), (-16.5, 76), (-16.5, 68), (-13.5, 68)]
travessa1 = Peca('travessa', 2, 'MDF', rw, [], [M((0, 1, 0), (0, 0, 1), (1, 0, 0), (TRAVESSA_X - T / 2, 0, dz)) for dz in (0, 32)])
cw = rect(-19, -16, 19, 16)[1]
fc = [rect(s * POSTE_Y - S / 2, -5, s * POSTE_Y + S / 2, 5) for s in (1, -1)]
fc += [circ(sx * 10.5, sy * 6.25, 2.2) for sx in (1, -1) for sy in (1, -1)]       # camera IMX219: furos 21 x 12,5 (M2)
camera = Peca('placa_camera', 1, 'MDF', cw, fc, [M((0, 1, 0), (ux, 0, uz), (nx, 0, nz), (Q[0], 0, Q[1]))],
              [('CIMA ^', 0, 11, 2.5)])

# ---------------------------------------------------------------- painel traseiro (chave geral)
pr = [(-20, 0), (-17, 0), (-17, -T), (-7, -T), (-7, 0), (7, 0), (7, -T), (17, -T), (17, 0), (20, 0), (20, 30), (-20, 30)]
painel = Peca('painel_chave', 1, 'MDF', pr, [rect(-9.5, 10.5, 9.5, 23.5), circ(-15, 25, 3.2), circ(15, 25, 3.2)],
              [M((0, 1, 0), (0, 0, 1), (1, 0, 0), (-93.5, 0, Z1))])
PECAS = [andar1, andar2, paredes, postes, travessa1, camera, painel]

# ---------------------------------------------------------------- modelo 3D (chapas + pecas compradas simplificadas)
asm = cq.Assembly(name='robocar_blitz_chassi')
cores = {'MDF': cq.Color(0.80, 0.66, 0.45), 'MDF ou acrilico': cq.Color(0.70, 0.85, 0.95, 0.6)}
for p in PECAS:
    sol = p.solido()
    for k, m in enumerate(p.frames):
        asm.add(cq.Workplane().add(sol.moved(m)), name=f'{p.nome}_{k + 1}', color=cores[p.material])
def caixa(nome, x0, x1, y0, y1, z0, z1, cor):
    asm.add(cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0)), name=nome, color=cq.Color(*cor))
for s, lado in ((1, 'esq'), (-1, 'dir')):
    asm.add(cq.Workplane('XZ').circle(RODA_D / 2).extrude(RODA_L / 2, both=True).translate((0, s * BITOLA / 2, EIXO_Z)), name=f'roda_{lado}', color=cq.Color(0.15, 0.15, 0.15))
    y_cx = s * (BITOLA / 2 - RODA_L / 2 - 1.5)
    asm.add(cq.Workplane('XZ').rect(12, 10).extrude(-s * 9).translate((0, y_cx, EIXO_Z)), name=f'redutor_{lado}', color=cq.Color(0.8, 0.65, 0.2))
    asm.add(cq.Workplane('XZ').circle(6).extrude(-s * 22).translate((0, y_cx - s * 9, EIXO_Z)), name=f'motor_{lado}', color=cq.Color(0.6, 0.6, 0.62))
    caixa(f'suporte_{lado}', -12.5, 12.5, s * Y_SUP - 6, s * Y_SUP + 6, Z1, Z1 + 12, (0.95, 0.95, 0.95))
    caixa(f'xl4016_{lado}', XL[0], XL[1], 0.5 if s > 0 else -46.5, 46.5 if s > 0 else -0.5, Z1, Z1 + 24, (0.25, 0.5, 0.35))
caixa('bateria', BAT[0], BAT[1], -BAT[2], BAT[2], Z1, Z1 + 25, (0.9, 0.7, 0.2))
caixa('placa_esp32', *caixa_placa(0, PL_W, 0, PL_H), Z1 + 10, Z1 + 11.6, (0.2, 0.45, 0.25))
caixa('esp32_devkit', *caixa_placa(0.47, 51.43, 2.22, 30.78), Z1 + 22.6, Z1 + 24.2, (0.1, 0.1, 0.12))   # sobre barras femea de 8,5 mm
caixa('drv8833_esq', *caixa_placa(10.68, 27.98, 35.07, 54.57), Z1 + 21.6, Z1 + 23, (0.6, 0.1, 0.1))
caixa('drv8833_dir', *caixa_placa(41.7, 59.0, 35.07, 54.57), Z1 + 21.6, Z1 + 23, (0.6, 0.1, 0.1))
caixa('jetson', JET_X0, JET_X0 + 100, -40, 40, Z2 + T + 12, Z2 + T + 12 + 30, (0.35, 0.45, 0.55))
asm.add(cq.Workplane('XY').sphere(9.525 / 2).translate((ESFERA_X, 0, Z1 - T - 15 + 9.525 / 2)), name='esfera', color=cq.Color(0.7, 0.7, 0.7))
cam = cq.Workplane('XY').box(24, 25, 4).translate((0, 0, 2)).val()
asm.add(cq.Workplane().add(cam.moved(M((ux, 0, uz), (0, 1, 0), (nx, 0, nz), (Q[0] + (T + 2) * nx, 0, Q[1] + (T + 2) * nz)))), name='camera', color=cq.Color(0.1, 0.1, 0.1))
asm.save(os.path.join(OUT, 'chassi_montado.step'))

# ---------------------------------------------------------------- arquivos de corte (DXF, 1:1, mm)
def dxf_peca(msp, p, dx, dy, girar=False):
    def tr(q):
        x, y = q
        if girar: x, y = -y, x
        return (x + dx, y + dy)
    msp.add_lwpolyline([tr(q) for q in p.contorno], close=True, dxfattribs={'layer': 'CORTE', 'color': 1})
    for f in p.furos:
        if f[0] == 'circ':
            msp.add_circle(tr(f[1]), f[2], dxfattribs={'layer': 'CORTE', 'color': 1})
        else:
            msp.add_lwpolyline([tr(q) for q in poly_of(f, 40)], close=True, dxfattribs={'layer': 'CORTE', 'color': 1})
    for (txt, x, y, h) in p.textos:
        t = msp.add_text(txt, dxfattribs={'layer': 'GRAVAR', 'color': 5, 'height': h})
        t.set_placement(tr((x, y)), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
def bbox(p, girar=False):
    xs = [q[0] for q in p.contorno]; ys = [q[1] for q in p.contorno]
    if girar: xs, ys = [-y for y in ys], xs
    return min(xs), min(ys), max(xs), max(ys)
# pente de teste: rasgos de T-0,3 a T+0,1
pente_c = [(0, 0), (92, 0), (92, 20)]
pente_f = []
larg = [round(T - 0.3 + 0.05 * k, 2) for k in range(9)]
xk = 88
for w in larg:
    pente_c += [(xk, 20), (xk, 12), (xk - w, 12), (xk - w, 20)]; xk -= 10
pente_c += [(0, 20)]
pente = Peca('pente_teste', 1, 'teste', pente_c[:], [], [], [(f'{w:.2f}', 84.5 - 10 * k, 6, 2.2) for k, w in enumerate(larg)])
pente.textos.append(('T=' + f'{T:.1f}', 4, 15, 2.2))
chave = Peca('chave_teste', 1, 'teste', [(0, 0), (30, 0), (30, 12), (0, 12)], [circ(6, 6, 3.4), circ(14, 6, 2.9), circ(22, 6, 2.2)], [], [('M3 M2.5 M2', 15, 2.5, 1.6)])

def layout(nome, itens, larg_mesa=380):
    doc = ezdxf.new('R2010', setup=True); doc.units = ezdxf.units.MM
    doc.layers.add('CORTE', color=1); doc.layers.add('GRAVAR', color=5)
    msp = doc.modelspace(); x = y = 0; linha_h = 0; pos = []
    for p, girar in itens:
        x0, y0, x1, y1 = bbox(p, girar)
        w, h = x1 - x0, y1 - y0
        if x + w > larg_mesa: x = 0; y += linha_h + 4; linha_h = 0
        dxf_peca(msp, p, x - x0, y - y0, girar); pos.append((p.nome, x, y, w, h))
        x += w + 4; linha_h = max(linha_h, h)
    doc.saveas(os.path.join(OUT, nome))
    return pos
lay_mdf = layout('corte_MDF.dxf', [(andar1, False), (paredes, False), (paredes, False), (postes, True), (postes, True),
                                    (travessa1, False), (travessa1, False), (camera, False), (painel, False), (pente, False), (chave, False)])
lay_a2 = layout('corte_andar2.dxf', [(andar2, False)])
lay_teste = layout('corte_TESTE_primeiro.dxf', [(pente, False), (chave, False)])

# ---------------------------------------------------------------- resumo
dens = {'MDF': 0.75e-3, 'MDF ou acrilico': 0.75e-3}
massa = sum(p.area() * T * 0.75e-3 * p.qtd for p in PECAS)
info = {'T': T, 'folga_rasgo': FOLGA, 'massa_MDF_g': round(massa, 1),
        'massa_andar2_acrilico_g': round(andar2.area() * T * 1.19e-3, 1), 'massa_andar2_MDF_g': round(andar2.area() * T * 0.75e-3, 1),
        'comprimento_mm': [-95, round(B_[0] + 3 * c45, 1)], 'largura_chapa_mm': 104, 'largura_com_rodas_mm': BITOLA + RODA_L,
        'altura_camera_mm': Q[1], 'z_andar1_topo': Z1, 'z_andar2_fundo': Z2,
        'pecas': [(p.nome, p.qtd, p.material) for p in PECAS]}
json.dump(info, open(os.path.join(OUT, 'resumo.json'), 'w'), indent=1, ensure_ascii=False)
print(json.dumps(info, indent=1, ensure_ascii=False))

# ---------------------------------------------------------------- imagens (3D) e PDF 1:1 dos cortes
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
tri = []
for nome, obj in asm.traverse():
    if obj.obj is None: continue
    shp = obj.obj.val() if hasattr(obj.obj, 'val') else obj.obj
    shp = shp.moved(obj.loc)
    vs, fs = shp.tessellate(0.3, 0.3)
    v = np.array([(p.x, p.y, p.z) for p in vs]) if False else [(p.x, p.y, p.z) for p in vs]
    col = obj.color.toTuple() if obj.color else (0.7, 0.7, 0.7, 1)
    for f in fs: tri.append(([v[i] for i in f], col))
def vista(arq, elev, azim, titulo):
    fig = plt.figure(figsize=(10, 7), dpi=130); ax = fig.add_subplot(111, projection='3d')
    luz = (0.4, -0.3, 0.86)
    polys, cs = [], []
    for t, c in tri:
        a, b, d = [__import__('numpy').array(q) for q in t]
        n = __import__('numpy').cross(b - a, d - a); nn = __import__('numpy').linalg.norm(n)
        k = 0.55 + 0.45 * abs(__import__('numpy').dot(n / nn, luz)) if nn > 0 else 0.8
        polys.append(t); cs.append((c[0] * k, c[1] * k, c[2] * k, c[3]))
    ax.add_collection3d(Poly3DCollection(polys, facecolors=cs, edgecolors='none'))
    ax.set_xlim(-100, 155); ax.set_ylim(-127, 127); ax.set_zlim(-5, 150)
    ax.set_box_aspect((255, 254, 155)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    ax.set_title(titulo, fontsize=11); fig.tight_layout(); fig.savefig(os.path.join(OUT, arq)); plt.close(fig)
vista('vista_3d.png', 22, -60, 'Robocar Blitz - chassi em chapas (frente para a direita)')
vista('vista_lado.png', 0, -90, 'Vista de lado (frente para a direita)')
vista('vista_cima.png', 89, -90, 'Vista de cima (frente para a direita)')
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
for arq in ('corte_MDF.dxf', 'corte_andar2.dxf', 'corte_TESTE_primeiro.dxf'):
    doc = ezdxf.readfile(os.path.join(OUT, arq)); msp = doc.modelspace()
    ext = ezdxf.bbox.extents(msp); w = ext.size.x + 20; h = ext.size.y + 20
    fig = plt.figure(figsize=(w / 25.4, h / 25.4)); ax = fig.add_axes([0, 0, 1, 1])
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(msp)
    fig.set_size_inches(w / 25.4, h / 25.4); ax.set_position([0, 0, 1, 1]); ax.set_aspect('auto'); ax.set_axis_off()
    ax.set_xlim(ext.extmin.x - 10, ext.extmax.x + 10); ax.set_ylim(ext.extmin.y - 10, ext.extmax.y + 10)
    ax.plot([ext.extmin.x - 5, ext.extmin.x + 95], [ext.extmin.y - 6] * 2, 'k-', lw=0.8)
    ax.text(ext.extmin.x + 45, ext.extmin.y - 5, 'conferir com regua: esta linha tem 100 mm', fontsize=6, ha='center', va='bottom')
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    fig.savefig(os.path.join(OUT, arq.replace('.dxf', '_1x1.pdf')))
    fig.savefig(os.path.join(OUT, arq.replace('.dxf', '.png')), dpi=60); plt.close(fig)
print('imagens ok')
