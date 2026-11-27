"""Robocar Blitz - placa de distribuicao de energia (fusivel + chave + saidas), face simples para corrosao manual.

  python3 placa.py              # gera placa_distribuicao.kicad_pcb, verifica e grava as saidas (PDF 1:1, imagens)
  python3 placa.py --negativos  # prova que cada verificacao pega um defeito plantado

Precisa do Python do KiCad (modulo pcbnew; KiCad 7 ou mais novo) e, para as saidas, kicad-cli, pdftoppm e convert.

Circuito (D-036):
  BAT+ --[F1 7 A]-- FUS+ --fio--> chave KCD1 (terminal 1)   chave (terminal 2) --fio--> SW+
  SW+  --> XL4016 #1 (Jetson), XL4016 #2 (motores), VBAT (ESP32 J1), LED verde "chave ligada" (R1 4k7)
  GND  --> BAT-, XL4016 #1 -, XL4016 #2 -
  D1 1N5408 de SW+ (catodo) para GND (anodo): bateria invertida -> D1 conduz e queima o fusivel (sem perda no uso normal)

Cobre: 4 ilhas grandes (BAT+, FUS+, SW+, GND), como a placa improvisada de cobre dividido, mas na ordem certa.
Coordenadas: x = 0 (borda de TRAS) .. 30 (FRENTE); y = 0 (lado ESQUERDO do carro) .. 40 (lado DIREITO).
No carro (chassi v4, andar 2, atras da Jetson): X = -52 + x, Y = 31 - y.
"""
import math
import os
import re
import subprocess
import sys
import tempfile

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ferramentas'))
import kicad_sch  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(AQUI, 'placa_distribuicao.kicad_pcb')
SCH = os.path.join(AQUI, 'placa_distribuicao.kicad_sch')
FP = '/usr/share/kicad/footprints'
for cand in (os.environ.get('KICAD_FOOTPRINT_DIR', ''), '/usr/share/kicad/footprints',
             'C:/Program Files/KiCad/10.0/share/kicad/footprints'):
    if cand and os.path.isdir(os.path.join(cand, 'Fuse.pretty')):
        FP = cand
        break

W, H = 32.0, 44.0
OX, OY = 100.0, 100.0
FM, mm = pcbnew.FromMM, pcbnew.ToMM
def P(x, y): return pcbnew.VECTOR2I(FM(OX + x), FM(OY + y))

FOLGA = 0.6          # cobre a cobre (como o plano de GND da v0.8)
DIVISAO = 1.2        # vao entre as ilhas (facil de corroer e de conferir com a lupa)
X_DIV, Y_DIV = 13.5, 22.0

# ilhas: rede -> retangulo (x0, y0, x1, y1) antes de descontar o vao
ILHAS = {
    'FUS+': (0.0, 0.0, X_DIV, Y_DIV),          # tras, esquerda (lado da chave)
    'SW+': (X_DIV, 0.0, W, Y_DIV),             # frente, esquerda
    'BAT+': (0.0, Y_DIV, X_DIV, H),            # tras, direita (lado do XT60)
    'GND': (X_DIV, Y_DIV, W, H),               # frente, direita
}

# pecas: ref -> (biblioteca, pegada, x, y, angulo, {pino: rede}, rotulo de cobre ou None)
FIO = ('Connector_Wire', 'SolderWire-0.75sqmm_1x01_D1.25mm_OD2.3mm')
FIO_FINO = ('Connector_Wire', 'SolderWire-0.127sqmm_1x01_D0.48mm_OD1mm')
PECAS = {
    'F1': ('Fuse', 'Fuseholder_Clip-5x20mm_Littelfuse_111_Inline_P20.00x5.00mm_D1.05mm_Horizontal', 0, 0, 0,
           {'1': 'FUS+', '2': 'BAT+'}, None),
    'J_BATP': FIO + (6.5, 40.0, 0, {'1': 'BAT+'}, 'BAT+'),
    'J_BATN': FIO + (21.5, 40.0, 0, {'1': 'GND'}, 'BAT-'),
    'J_CH1': FIO + (6.5, 4.0, 0, {'1': 'FUS+'}, 'CHAVE 1'),
    'J_CH2': FIO + (21.0, 4.0, 0, {'1': 'SW+'}, 'CHAVE 2'),
    'J_XL1P': FIO + (28.5, 4.0, 0, {'1': 'SW+'}, 'XL1 +'),
    'J_XL2P': FIO + (28.5, 13.0, 0, {'1': 'SW+'}, 'XL2 +'),
    'J_XL1N': FIO + (29.0, 34.0, 0, {'1': 'GND'}, 'XL1 -'),
    'J_XL2N': FIO + (28.5, 40.0, 0, {'1': 'GND'}, 'XL2 -'),
    'J_VBAT': FIO_FINO + (25.0, 8.5, 0, {'1': 'SW+'}, 'VBAT'),
    'D1': ('Diode_THT', 'D_DO-201AD_P15.24mm_Horizontal', 0, 0, 0, {'1': 'SW+', '2': 'GND'}, None),
    'R1': ('Resistor_THT', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal', 0, 0, 0, {'1': 'SW+', '2': 'LED'}, None),
    'D2': ('LED_THT', 'LED_D3.0mm', 0, 0, 0, {'1': 'GND', '2': 'LED'}, None),
}
# pecas de 2 pinos: posicao de cada pino (o script acha a rotacao e a posicao da pegada)
PINOS = {
    'F1': ((6.5, 12.0), (6.5, 32.0)),          # clipe do lado FUS+ (pino 1) e do lado BAT+ (pino 2); fusivel ao longo de y
    'D1': ((18.5, 9.5), (18.5, 24.74)),        # catodo (faixa) no SW+, anodo no GND
    'R1': ((24.5, 16.5), (24.5, 26.66)),       # 4k7: SW+ -> anodo do LED
    'D2': ((24.5, 31.74), (24.5, 29.2)),       # LED verde: catodo (1) no GND, anodo (2, perna longa) pelo R1
}
# LED_D3.0mm: pino 1 = catodo (K), 2 = anodo (A).
FIX = {'H1': (14.5, 4.0), 'H2': (15.0, 39.5)}          # M3 em cima do vao entre tras e frente, longe das pecas
TRILHAS = [('LED', 1.0, [(24.5, 26.66), (24.5, 29.2)])]   # R1 -> anodo do LED

REDES = {   # o que o circuito pede: rede -> pinos (ref, pino)
    'BAT+': {('F1', '2'), ('J_BATP', '1')},
    'FUS+': {('F1', '1'), ('J_CH1', '1')},
    'SW+': {('J_CH2', '1'), ('J_XL1P', '1'), ('J_XL2P', '1'), ('J_VBAT', '1'), ('D1', '1'), ('R1', '1')},
    'GND': {('J_BATN', '1'), ('J_XL1N', '1'), ('J_XL2N', '1'), ('D1', '2'), ('D2', '1')},
    'LED': {('D2', '2'), ('R1', '2')},
}
CORRENTE = {'BAT+': 7.0, 'FUS+': 7.0, 'SW+': 7.0, 'GND': 7.0}   # A (fusivel); largura minima de cobre exigida abaixo
LARG_MIN_MM = 3.0     # IPC-2221, cobre de 35 um por fora, ~7 A com 20 C de aquecimento: ~2,5 mm; folga para corrosao


def _por_pinos(fp, a, c):
    """Gira e move a pegada para o pino 1 ficar em a e o pino 2 em c (pecas de 2 pinos e o clipe do fusivel)."""
    def pino(n):
        ps = [p for p in fp.Pads() if p.GetNumber() == n]
        return (sum(mm(p.GetPosition().x) for p in ps) / len(ps) - OX, sum(mm(p.GetPosition().y) for p in ps) / len(ps) - OY)
    p1, p2 = pino('1'), pino('2')
    alvo = math.degrees(math.atan2(-(c[1] - a[1]), c[0] - a[0]))
    agora = math.degrees(math.atan2(-(p2[1] - p1[1]), p2[0] - p1[0]))
    fp.SetOrientationDegrees(fp.GetOrientationDegrees() + alvo - agora)
    p1 = pino('1')
    pos = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(pos.x + FM(a[0] - p1[0]), pos.y + FM(a[1] - p1[1])))


def montar(pecas=PECAS, ilhas=ILHAS, fix=FIX, trilhas=TRILHAS, sem_cobre=()):
    b = pcbnew.NewBoard(PCB) if hasattr(pcbnew, 'NewBoard') else pcbnew.CreateEmptyBoard()
    ds = b.GetDesignSettings()
    ds.m_MinClearance = FM(0.5)
    ds.m_HoleClearance = FM(0.5)
    ds.m_CopperEdgeClearance = FM(0.6)
    ds.m_TrackMinWidth = FM(1.0)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(FM(FOLGA)); nc.SetTrackWidth(FM(1.0))
    nets = {}
    def rede(n):
        if n not in nets:
            nets[n] = pcbnew.NETINFO_ITEM(b, n); b.Add(nets[n])
        return nets[n]
    for ref, (lib, nome, x, y, ang, pinos, rot) in pecas.items():
        fp = pcbnew.FootprintLoad(os.path.join(FP, lib + '.pretty'), nome)
        fp.SetFPID(pcbnew.LIB_ID(lib, nome)); fp.SetReference(ref)
        b.Add(fp)
        fp.SetOrientationDegrees(ang); fp.SetPosition(P(x, y))
        if ref in PINOS:
            _por_pinos(fp, *PINOS[ref])
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            n = pinos.get(pad.GetNumber())
            if n:
                pad.SetNet(rede(n))
            # ilhas maiores para corrosao manual e solda de fio grosso
            if lib == 'Connector_Wire' and pad.GetDrillSize().x > 0:
                d = mm(pad.GetDrillSize().x)
                tam = 4.0 if d > 1.0 else 2.4
                pad.SetSize(pcbnew.VECTOR2I(FM(tam), FM(tam))); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            elif lib in ('Fuse', 'Diode_THT'):
                pad.SetSize(pcbnew.VECTOR2I(FM(3.0), FM(3.0))); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            elif lib in ('Resistor_THT', 'LED_THT'):
                pad.SetSize(pcbnew.VECTOR2I(FM(1.9), FM(1.9)))
            pad.SetLayerSet(pad.GetLayerSet().RemoveLayer(pcbnew.F_Cu) if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else pad.GetLayerSet())
        fp.Value().SetVisible(False)
        if lib == 'Connector_Wire':                       # o nome grande (BAT+, CHAVE 1...) ja esta na folha de montagem
            fp.Reference().SetVisible(False)
            for g in fp.GraphicalItems():
                if isinstance(g, pcbnew.PCB_TEXT) or g.GetClass() in ('PCB_TEXT', 'FP_TEXT'):
                    g.SetVisible(False)
    for ref, (x, y) in fix.items():
        fp = pcbnew.FootprintLoad(os.path.join(FP, 'MountingHole.pretty'), 'MountingHole_3.2mm_M3')
        fp.SetFPID(pcbnew.LIB_ID('MountingHole', 'MountingHole_3.2mm_M3')); fp.SetReference(ref)
        fp.SetBoardOnly(True); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        b.Add(fp); fp.SetPosition(P(x, y))
    cant = [(0, 0), (W, 0), (W, H), (0, H)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FM(0.1))
        s.SetStart(P(*cant[i])); s.SetEnd(P(*cant[(i + 1) % 4])); b.Add(s)
    for net, w, pts in trilhas:
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(FM(w))
            t.SetLayer(pcbnew.B_Cu); t.SetNet(rede(net)); b.Add(t)
    m = DIVISAO / 2
    for net, (x0, y0, x1, y1) in ilhas.items():
        z = pcbnew.ZONE(b); z.SetLayer(pcbnew.B_Cu)
        ol = z.Outline(); ol.NewOutline()
        xa = x0 + (m if x0 > 0 else 0.4); xb = x1 - (m if x1 < W else 0.4)
        ya = y0 + (m if y0 > 0 else 0.4); yb = y1 - (m if y1 < H else 0.4)
        for (u, v) in ((xa, ya), (xb, ya), (xb, yb), (xa, yb)):
            ol.Append(FM(OX + u), FM(OY + v))
        z.SetNet(rede(net)); z.SetZoneName(net)
        z.SetLocalClearance(FM(FOLGA)); z.SetMinThickness(FM(1.0))
        z.SetThermalReliefGap(FM(0.6)); z.SetThermalReliefSpokeWidth(FM(1.6))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)      # solido: corrente maxima (como a placa improvisada)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        b.Add(z)
    # nomes na folha de montagem (a placa corroida nao tem serigrafia; cobre com letras partia as ilhas)
    for ref, (lib, nome, x, y, ang, pinos, rot) in pecas.items():
        if rot:
            t = pcbnew.PCB_TEXT(b); t.SetText(rot); t.SetLayer(pcbnew.F_Fab)
            t.SetPosition(P(x, y + (3.2 if y < H / 2 else -3.2))); t.SetTextSize(pcbnew.VECTOR2I(FM(1.2), FM(1.2)))
            t.SetTextThickness(FM(0.2)); b.Add(t)
    for net, (x0, y0, x1, y1) in ilhas.items():
        t = pcbnew.PCB_TEXT(b); t.SetText(net); t.SetLayer(pcbnew.F_Fab)
        t.SetPosition(P((x0 + x1) / 2 - 2.5, (y0 + y1) / 2)); t.SetTextSize(pcbnew.VECTOR2I(FM(1.6), FM(1.6)))
        t.SetTextThickness(FM(0.3)); b.Add(t)
    for txt, x, y in (('D1: 1N5408 ou VAZIO', 9.5, 44.8), ('NUNCA 1N4728 (zener)', 9.5, 46.4)):
        t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetLayer(pcbnew.F_Fab); t.SetPosition(P(x, y))
        t.SetTextSize(pcbnew.VECTOR2I(FM(1.0), FM(1.0))); t.SetTextThickness(FM(0.18)); b.Add(t)
    # sem cobre a menos de 3,6 mm do centro dos furos de fixacao (o parafuso nao encosta em nenhuma ilha)
    for ref, (x, y) in fix.items():
        z = pcbnew.ZONE(b); z.SetLayer(pcbnew.B_Cu); z.SetIsRuleArea(True)
        z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        ol = z.Outline(); ol.NewOutline()
        for k in range(24):
            a = 2 * math.pi * k / 24
            ol.Append(FM(OX + x + 3.6 * math.cos(a)), FM(OY + y + 3.6 * math.sin(a)))
        z.SetZoneName('furo_' + ref); b.Add(z)
    for (x0, y0, x1, y1) in sem_cobre:                       # so para os testes negativos
        z = pcbnew.ZONE(b); z.SetLayer(pcbnew.B_Cu); z.SetIsRuleArea(True); z.SetDoNotAllowCopperPour(True)
        ol = z.Outline(); ol.NewOutline()
        for (u, v) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(FM(OX + u), FM(OY + v))
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    return b


# ------------------------------------------------------------------------------------------- verificacoes
def verificar(b, pecas=PECAS, redes=REDES):
    erros = []
    with tempfile.TemporaryDirectory() as d:
        rpt = os.path.join(d, 'drc.rpt')
        pcbnew.WriteDRCReport(b, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
        txt = open(rpt).read()
    # sem serigrafia nem mascara na placa corroida: so contam cobre, furos, bordas, corpos e ligacoes
    ignorar = ('silk_', 'solder_mask_bridge', 'lib_footprint')
    blocos = re.split(r'\n(?=\[)', txt)
    ruins = [bl.strip().splitlines() for bl in blocos if bl.startswith('[') and not bl.startswith(tuple('[' + i for i in ignorar))]
    for bl in ruins:
        erros.append('DRC: ' + ' | '.join(l.strip() for l in bl[:4]))
    # pino a pino contra o circuito
    tem = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname():
                tem.setdefault(p.GetNetname(), set()).add((f.GetReference(), p.GetNumber()))
    for rede, pinos in redes.items():
        if tem.get(rede, set()) != pinos:
            falta = sorted(pinos - tem.get(rede, set())); sobra = sorted(tem.get(rede, set()) - pinos)
            erros.append(f'rede {rede}: falta {falta} / sobra {sobra}')
    for rede in tem:
        if rede not in redes:
            erros.append(f'rede {rede} nao existe no circuito: {sorted(tem[rede])}')
    # so B.Cu
    for t in b.GetTracks():
        if t.GetLayer() != pcbnew.B_Cu:
            erros.append('trilha fora do B.Cu (a placa e de face simples)')
    for z in b.Zones():
        if z.GetLayer() != pcbnew.B_Cu:
            erros.append('zona fora do B.Cu')
    # largura de cobre no caminho da corrente: cada ilha de potencia, medida por "erosao" (o cobre que sobra depois de
    # encolher LARG_MIN/2 tem de continuar inteiro e tocando todas as ilhas dos pinos da rede)
    import shapely.geometry as sg
    import shapely.ops as so
    for z in b.Zones():
        rede = z.GetNetname()
        if rede not in CORRENTE:
            continue
        pol = z.GetFilledPolysList(pcbnew.B_Cu)
        partes = []
        for i in range(pol.OutlineCount()):
            o = pol.Outline(i)
            ext = [(mm(o.CPoint(k).x) - OX, mm(o.CPoint(k).y) - OY) for k in range(o.PointCount())]
            furos = []
            for h in range(pol.HoleCount(i)):
                hh = pol.Hole(i, h)
                furos.append([(mm(hh.CPoint(k).x) - OX, mm(hh.CPoint(k).y) - OY) for k in range(hh.PointCount())])
            partes.append(sg.Polygon(ext, furos))
        cobre = so.unary_union(partes).buffer(0.02).buffer(-0.02)   # fecha a "costura" de largura zero do KiCad
        if cobre.geom_type != 'Polygon':
            erros.append(f'ilha {rede} partida em {len(cobre.geoms)} pedacos')
            continue
        miolo = cobre.buffer(-LARG_MIN_MM / 2)
        pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == rede
                and (f.GetReference() in ('F1', 'D1') or (f.GetReference().startswith('J_') and f.GetReference() != 'J_VBAT'))]
        # grafo: pedacos do miolo (cobre com >= LARG_MIN de largura) + pinos; pino liga nos pedacos que encostam no anel
        # de cobre em volta dele. Todos os pinos de potencia tem de cair no mesmo componente.
        pedacos = list(miolo.geoms) if miolo.geom_type == 'MultiPolygon' else ([] if miolo.is_empty else [miolo])
        pai = list(range(len(pedacos) + len(pads)))
        def raiz(i):
            while pai[i] != i:
                i = pai[i]
            return i
        for j, p in enumerate(pads):
            r = max(mm(p.GetSize().x), mm(p.GetSize().y)) / 2
            anel = sg.Point(mm(p.GetPosition().x) - OX, mm(p.GetPosition().y) - OY).buffer(r + LARG_MIN_MM / 2 + 0.2)
            for i, pc in enumerate(pedacos):
                if pc.intersects(anel):
                    pai[raiz(len(pedacos) + j)] = raiz(i)
        comps = {raiz(len(pedacos) + j) for j in range(len(pads))}
        if len(comps) > 1 or not pedacos:
            erros.append(f'ilha {rede}: passagem mais estreita que {LARG_MIN_MM} mm entre os pinos ({len(comps)} trechos)')
    # cada peca de potencia dentro da propria ilha
    for ref, (lib, nome, x, y, ang, pinos, rot) in pecas.items():
        for f in b.GetFootprints():
            if f.GetReference() != ref:
                continue
            for p in f.Pads():
                n = p.GetNetname()
                if n in ILHAS:
                    x0, y0, x1, y1 = ILHAS[n]
                    px, py = mm(p.GetPosition().x) - OX, mm(p.GetPosition().y) - OY
                    if not (x0 <= px <= x1 and y0 <= py <= y1):
                        erros.append(f'{ref} pino {p.GetNumber()} ({n}) fora da ilha {n}')
    return erros


def negativos():
    import copy
    casos = []
    def caso(nome, contendo, pecas=None, redes=None, ilhas=None, fix=None, trilhas=None, sem_cobre=()):
        b = montar(pecas or PECAS, ilhas or ILHAS, fix or FIX, trilhas if trilhas is not None else TRILHAS, sem_cobre)
        err = verificar(b, pecas or PECAS, redes or REDES)
        casos.append((nome, any(contendo in e for e in err), err[:1]))
    p = copy.deepcopy(PECAS); p['F1'] = p['F1'][:5] + ({'1': 'BAT+', '2': 'FUS+'},) + p['F1'][6:]
    caso('fusivel ligado ao contrario das ilhas (curto BAT+ com FUS+)', 'DRC', pecas=p)
    p = copy.deepcopy(PECAS); p['D1'] = p['D1'][:5] + ({'1': 'GND', '2': 'SW+'},) + p['D1'][6:]
    caso('diodo de protecao invertido (curto na bateria)', 'rede', pecas=p)
    p = copy.deepcopy(PECAS); p['J_XL2N'] = p['J_XL2N'][:5] + ({'1': 'SW+'},) + p['J_XL2N'][6:]
    caso('XL2- soldado na ilha do SW+', 'rede', pecas=p)
    caso('LED sem a trilha ate o R1', 'DRC', trilhas=[])
    il = dict(ILHAS); il['SW+'] = (X_DIV, 0.0, W, 6.0)
    caso('ilha do SW+ estreita (gargalo para 7 A)', 'SW+', ilhas=il)
    caso('ilha do SW+ ligada so por um gargalo de 2,6 mm (corrente de 7 A)', 'passagem mais estreita',
         sem_cobre=[(13.0, 10.6, 29.0, 11.4)])
    f = dict(FIX); f['H2'] = (28.5, 7.5)
    caso('parafuso em cima do fio do XL1+', 'DRC', fix=f)
    # esquematico: o KiCad le um esquematico com o diodo invertido e a conferencia tem de acusar
    with tempfile.TemporaryDirectory() as d:
        p2 = copy.deepcopy(PECAS); p2['D1'] = p2['D1'][:5] + ({'1': 'GND', '2': 'SW+'},) + p2['D1'][6:]
        arq = os.path.join(d, 'x.kicad_sch')
        esquematico(arq, p2)
        err = kicad_sch.conferir(arq, REDES)
        casos.append(('esquematico com o diodo de protecao invertido', any('rede' in e for e in err), err[:1]))
    return casos


SIMBOLO = {'F1': ('Device:Fuse', '7A 5x20'), 'D1': ('Device:D', '1N5408'),
           'R1': ('Device:R', '4k7'), 'D2': ('Device:LED', 'verde 3 mm')}
ROTULO_FIO = {'J_BATP': 'BAT+ (XT60)', 'J_BATN': 'BAT- (XT60)', 'J_CH1': 'CHAVE 1', 'J_CH2': 'CHAVE 2', 'J_XL1P': 'XL4016 #1 IN+',
              'J_XL2P': 'XL4016 #2 IN+', 'J_XL1N': 'XL4016 #1 IN-', 'J_XL2N': 'XL4016 #2 IN-', 'J_VBAT': 'VBAT (ESP32 J1)'}


def esquematico(arq=SCH, pecas=PECAS):
    """Esquematico do KiCad com as mesmas pecas e redes da placa (conferido pelo kicad-cli contra REDES)."""
    e = kicad_sch.Esquema('placa_distribuicao', 'Robocar Blitz - placa de distribuicao de energia', '2026-11-27')
    lugar = {'J_BATP': (38.1, 50.8), 'F1': (76.2, 50.8), 'J_CH1': (114.3, 50.8), 'J_CH2': (152.4, 50.8),
             'J_XL1P': (215.9, 50.8), 'J_XL2P': (215.9, 66.04), 'J_VBAT': (215.9, 81.28), 'D1': (177.8, 101.6),
             'R1': (139.7, 96.52), 'D2': (139.7, 124.46), 'J_BATN': (38.1, 139.7), 'J_XL1N': (215.9, 124.46),
             'J_XL2N': (215.9, 139.7)}
    rot = {'F1': 90, 'D1': 90, 'D2': 270}
    for ref, (lib, nome, x, y, ang, pinos, rotulo) in pecas.items():
        if ref.startswith('J_'):
            sim, val = 'Connector_Generic:Conn_01x01', ROTULO_FIO[ref]
        else:
            sim, val = SIMBOLO[ref]
        e.peca(ref, sim, val, f'{lib}:{nome}', *lugar[ref], rot.get(ref, 0), pinos)
    e.texto('Bateria -> fusivel -> chave -> SW+ em estrela para os 2 XL4016 (D-036). D1 em paralelo: bateria invertida '
            'queima o fusivel. LED verde = chave ligada.', 25.4, 25.4, 1.27)
    e.texto('D1: 1N5408 (ou 1N4007). Sem eles, deixe VAZIO. NUNCA 1N4728: e zener de 3,3 V e vira curto na bateria.',
            25.4, 30.48, 1.27)
    e.gravar(arq)


def saidas():
    F = os.path.join(AQUI, 'fabricacao'); os.makedirs(F, exist_ok=True); os.makedirs(os.path.join(AQUI, 'imagens'), exist_ok=True)
    cli = lambda *a: subprocess.run(['kicad-cli', 'pcb', 'export'] + list(a) + [PCB], check=True, stdout=subprocess.DEVNULL)
    cli('pdf', '--layers', 'B.Cu,Edge.Cuts', '--black-and-white', '--drill-shape-opt', '1', '-o',
        os.path.join(F, '1_cobre_transferencia_1x1.pdf'))
    cli('pdf', '--layers', 'F.SilkS,F.Fab,Edge.Cuts', '-o', os.path.join(F, '2_montagem.pdf'))
    cli('drill', '--format', 'excellon', '--drill-origin', 'plot', '--excellon-separate-th', '-o', F + '/')
    env = dict(os.environ)
    for var in ('KICAD6_3DMODEL_DIR', 'KICAD7_3DMODEL_DIR', 'KICAD10_3DMODEL_DIR'):
        env.setdefault(var, '/usr/share/kicad/3dmodels')
    subprocess.run(['kicad-cli', 'pcb', 'export', 'step', '--subst-models', '--force', '-o',
                    os.path.join(AQUI, 'placa_distribuicao.step'), PCB], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, env=env)
    subprocess.run(['kicad-cli', 'sch', 'export', 'pdf', '-o', os.path.join(AQUI, 'placa_distribuicao_esquematico.pdf'), SCH],
                   check=True, stdout=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory() as d:
        pdf = os.path.join(d, 'e.pdf')
        subprocess.run(['kicad-cli', 'sch', 'export', 'pdf', '-o', pdf, SCH], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['pdftoppm', '-r', '150', '-png', '-singlefile', pdf, os.path.join(d, 'e')], check=True)
        subprocess.run(['convert', os.path.join(d, 'e.png'), '-trim', '+repage', '-bordercolor', 'white', '-border', '20',
                        os.path.join(AQUI, 'imagens', 'esquematico.png')], check=True)
    with tempfile.TemporaryDirectory() as d:
        for nomeimg, camadas, extra in (('cobre_vista_de_cima.png', 'B.Cu,F.SilkS,Edge.Cuts', []),
                                        ('lado_do_cobre.png', 'B.Cu,Edge.Cuts', ['--mirror'])):
            pdf = os.path.join(d, 'x.pdf')
            subprocess.run(['kicad-cli', 'pcb', 'export', 'pdf', '--layers', camadas] + extra + ['-o', pdf, PCB], check=True,
                           stdout=subprocess.DEVNULL)
            subprocess.run(['pdftoppm', '-r', '600', '-png', '-singlefile', pdf, os.path.join(d, 'x')], check=True)
            subprocess.run(['convert', os.path.join(d, 'x.png'), '-trim', '+repage', '-bordercolor', 'white', '-border', '30',
                            os.path.join(AQUI, 'imagens', nomeimg)], check=True)


def principal():
    if '--negativos' in sys.argv:
        casos = negativos()
        for nome, pegou, err in casos:
            print('PEGOU    ' if pegou else 'NAO PEGOU', nome, '->', err[0] if err else '(nenhum erro)')
        base = verificar(montar())
        ok = all(p for _, p, _ in casos) and not base
        if base:
            print('o projeto sem defeito NAO passa:', base)
        print('TODOS OS DEFEITOS FORAM PEGOS' if ok else 'FALHOU')
        return 0 if ok else 1
    esquematico()
    b = montar()
    erros = verificar(b)
    # paridade: o que o KiCad le do esquematico = o circuito = as ilhas e pinos da placa
    erros += kicad_sch.conferir(SCH, REDES)
    for e in erros:
        print('ERRO:', e)
    if erros:
        return 1
    b.Save(PCB)
    saidas()
    print(f'placa de distribuicao {W:.0f} x {H:.0f} mm: {len(PECAS)} pecas, {len(REDES)} redes, DRC limpo, so B.Cu, '
          f'cobre >= {LARG_MIN_MM} mm nos caminhos de 7 A: OK')
    return 0


if __name__ == '__main__':
    sys.exit(principal())
