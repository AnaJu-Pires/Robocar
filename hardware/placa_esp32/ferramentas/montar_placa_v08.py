"""Robocar Blitz - monta a placa da ESP32 v0.8 (espelhada) a partir do esquematico.

Rodar com o Python do KiCad (modulo pcbnew), na raiz do repositorio:
    python3 hardware/placa_esp32/ferramentas/montar_placa_v08.py

O que faz (tudo em B.Cu, face simples):
  * apaga pecas, trilhas, zonas e desenhos da placa e recoloca tudo a partir da netlist do esquematico
    (pegadas da biblioteca do projeto, ja com as ilhas retangulares arredondadas);
  * posiciona as pecas (tabela POS) e roteia as trilhas (tabela ROTAS: so 0/45/90 graus, sem curva de 90;
    toda trilha sai reta da ilha, no sentido do lado comprido dela);
  * cria o plano de GND, a area livre embaixo da antena da ESP32 e as gotas (teardrops) nas ilhas;
  * escreve a serigrafia.
Depois de rodar: make drc (verificacoes) e make placa (saidas).

Coordenadas em mm a partir do canto de cima a esquerda da placa (vista de cima; cima = frente do carro).
"""
import math
import os
import re
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET

import pcbnew

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)
PCB = os.path.join(BASE, "placa_esp32.kicad_pcb")
SCH = os.path.join(BASE, "placa_esp32.kicad_sch")
LIB = os.path.join(BASE, "lib", "robocar_sm.pretty")
LIB_FURO = "/usr/share/kicad/footprints/MountingHole.pretty"
for cand in (os.environ.get("KICAD_FOOTPRINT_DIR", ""), "/usr/share/kicad/footprints",
             "C:/Program Files/KiCad/10.0/share/kicad/footprints"):
    if cand and os.path.isdir(os.path.join(cand, "MountingHole.pretty")):
        LIB_FURO = os.path.join(cand, "MountingHole.pretty")
        break

W, H = 80.0, 73.0                 # placa (80 x 73: 3 mm a mais na frente, ajuste da equipe em 19/11)
OX, OY = 108.5, 71.5              # origem das coordenadas (mantida das versoes anteriores)
TOPO = -3.0                       # borda da frente da placa (v = -3); a borda de tras fica em v = 70
FM, mm = pcbnew.FromMM, pcbnew.ToMM
def P(u, v): return pcbnew.VECTOR2I(FM(OX + u), FM(OY + v))

S, PW = 1.0, 1.5                  # largura: sinal 1,0 mm; potencia (VM, GND dos drivers, motores) 1,5 mm

# ---------------------------------------------------------------------------------------------- netlist
# kicad-cli quando ele le o esquematico; senao (esquematico salvo num KiCad mais novo), leitura em texto
import sys
sys.path.insert(0, AQUI)
from netlist_texto import netlist_esquematico
COMP, PINO = netlist_esquematico(SCH)

# ---------------------------------------------------------------------------------------------- posicoes
# (u, v, orientacao em graus KiCad). Posicao = pino 1.
Y0 = 18.3                                    # fileira de cima da ESP32 (pino 1)
def row(r): return Y0 + 2.54 * (r - 1)       # linha r (1..15) das fileiras da ESP32
POS = {
    "U1": (27.3, Y0, 0),                     # ESP32: USB para tras (borda de baixo), antena para a frente
    "U2": (19.0, 9.06, -90), "U3": (70.5, 9.06, -90),          # DRV8833: entradas embaixo, saidas em cima
    "JP1": (6.3, 20.7, 0), "JP2": (57.8, 20.7, 0), "JP3": (73.4, 23.3, 90),
    "R1": (34.1, 5.5, 180), "R2": (35.0, row(2), 0), "R3": (35.0, row(6), 0), "R4": (42.62, 40.44, 180),
    "C1": (7.9, 53.3, 180), "C2": (76.8, 53.3, 180),
    "J2": (7.9, 60.5, 180), "J3": (76.8, 60.5, 180),       # + do VM reto do capacitor ate o fio
    "J10": (9.12, 2.75, 0), "J11": (60.62, 2.75, 0),
    "J12": (11.0, row(9), 0), "J13": (72.0, row(9), 0), "J14": (60.0, row(11), 0),
    "J1": (39.5, 5.5, 0),
}
FUROS = {"H1": (3.5, TOPO + 3.5), "H2": (W - 3.5, TOPO + 3.5), "H3": (3.5, TOPO + H - 3.5), "H4": (W - 3.5, TOPO + H - 3.5)}

# ---------------------------------------------------------------------------------------------- trilhas
r = row
ROTAS = [
    # ----- lado ESQUERDO (motor esquerdo)
    ("/VBAT_ADC", S, [(27.3, r(2)), (24.37, r(2)), (23.46, r(2) - 0.91), (23.46, 7.54), (25.5, 5.5), (26.5, 5.5)]),
    ("/VBAT_ADC", S, [(27.3, r(2)), (35.0, r(2))]),
    ("/VBAT", S, [(34.1, 5.5), (39.5, 5.5)]),
    ("/SLEEP_E", S, [(27.3, r(6)), (24.01, r(6)), (22.91, r(6) - 1.1), (22.91, 22.89), (19.0, 18.98), (19.0, 9.06)]),
    ("/SLEEP_E", S, [(27.3, r(6)), (35.0, r(6))]),
    ("/ME_IN1", S, [(27.3, r(7)), (20.0, r(7)), (19.0, r(7) - 1), (19.0, 24.3)]),
    ("/ME_IN1", S, [(8.84, 24.3), (8.84, 26.5), (9.84, 27.5), (18.0, 27.5), (19.0, 26.5)]),
    ("/ME_IN2", S, [(27.3, r(8)), (7.3, r(8)), (6.3, r(8) - 1), (6.3, 24.3), (6.3, 20.7)]),
    ("/ME_IN2_JP", S, [(16.46, 24.3), (16.46, 20.7)]),
    ("/ENC_E_A", S, [(27.3, r(9)), (11.0, r(9))]),
    ("/ENC_E_B", S, [(27.3, r(10)), (11.0, r(10))]),
    ("/VM_E", PW, [(11.38, 24.3), (11.38, 19.1), (10.38, 18.1), (4.6, 18.1), (3.6, 19.1), (3.6, 46.6), (7.9, 50.9), (7.9, 53.3)]),
    ("GND", PW, [(13.92, 24.3), (13.92, 16.6), (12.92, 15.6), (2.4, 15.6), (1.4, 16.6), (1.4, 47.8), (4.4, 50.8), (4.4, 53.3)]),
    ("/VM_E", PW, [(7.9, 53.3), (7.9, 60.5)]),
    ("GND", PW, [(4.4, 53.3), (4.4, 55.3), (3.1, 56.6), (3.1, 60.5)]),
    ("/ME_M1", PW, [(13.92, 9.06), (13.92, 12.32), (12.97, 13.27), (9.79, 13.27), (8.84, 12.32), (8.84, 9.06)]),
    ("/ME_M1", PW, [(8.84, 9.06), (8.84, 6.6), (9.12, 6.32), (9.12, 2.75)]),
    ("/ME_M2", PW, [(11.38, 9.06), (11.38, 6.8), (13.92, 4.26), (16.46, 6.8), (16.46, 9.06)]),     # Y saindo do centro do M-
    ("/ME_M2", PW, [(13.92, 4.26), (13.92, 2.75)]),
    # ----- lado DIREITO (motor direito)
    ("/MD_IN2", S, [(52.7, r(5)), (56.8, r(5)), (57.8, r(5) - 1), (57.8, 24.3), (57.8, 20.7)]),
    ("/MD_IN2_JP", S, [(67.96, 24.3), (67.96, 20.7)]),
    ("/MD_IN1", S, [(52.7, r(6)), (59.34, r(6)), (60.34, r(6) - 1), (60.34, 24.3)]),
    ("/MD_IN1", S, [(70.5, 24.3), (70.5, 26.5), (69.5, 27.5), (61.34, 27.5), (60.34, 26.5)]),
    ("/SLEEP_D", S, [(52.7, r(7)), (72.4, r(7)), (73.4, r(7) - 1), (73.4, 23.3)]),
    ("/SLEEP_D", S, [(52.7, r(7)), (49.0, r(7)), (46.0, r(7) + 3), (46.0, 39.44), (45.0, 40.44), (42.62, 40.44)]),
    ("/SLEEP_D_JP", S, [(73.4, 13.14), (73.4, 7.4), (72.9, 6.9), (71.0, 6.9), (70.5, 7.4), (70.5, 9.06)]),
    ("/ENC_D_A", S, [(52.7, r(9)), (72.0, r(9))]),
    ("/ENC_D_B", S, [(52.7, r(10)), (72.0, r(10))]),
    ("/BOTAO", S, [(52.7, r(11)), (60.0, r(11))]),
    ("/VM_D", PW, [(62.88, 24.3), (62.88, 16.6), (63.88, 15.6), (76.9, 15.6), (77.9, 16.6), (77.9, 48.3), (76.8, 49.4), (76.8, 53.3)]),
    ("GND", PW, [(65.42, 24.3), (65.42, 19.1), (66.42, 18.1), (74.9, 18.1), (75.9, 19.1), (75.9, 47.0), (73.3, 49.6), (73.3, 53.3)]),
    ("/VM_D", PW, [(76.8, 53.3), (76.8, 60.5)]),
    ("GND", PW, [(73.3, 53.3), (73.3, 55.3), (72.0, 56.6), (72.0, 60.5)]),
    ("/MD_M1", PW, [(65.42, 9.06), (65.42, 12.32), (64.47, 13.27), (61.29, 13.27), (60.34, 12.32), (60.34, 9.06)]),
    ("/MD_M1", PW, [(60.34, 9.06), (60.34, 6.6), (60.62, 6.32), (60.62, 2.75)]),
    ("/MD_M2", PW, [(62.88, 9.06), (62.88, 6.8), (65.42, 4.26), (67.96, 6.8), (67.96, 9.06)]),
    ("/MD_M2", PW, [(65.42, 4.26), (65.42, 2.75)]),
    # ----- 3V3 dos encoders: sai do pino 3V3 (embaixo a direita) pelos dois lados da ilha
    ("+3V3", S, [(52.7, r(15)), (50.0, r(15)), (49.0, r(15) + 1), (49.0, r(15) + 3), (48.0, r(15) + 4),
                 (15.0, r(15) + 4), (14.0, r(15) + 3), (14.0, r(12) + 1), (13.0, r(12)), (11.0, r(12))]),
    ("+3V3", S, [(52.7, r(15)), (68.0, r(15)), (69.0, r(15) - 1), (69.0, r(12) + 1), (70.0, r(12)), (72.0, r(12))]),
]

# ---------------------------------------------------------------------------------------------- monta
b = pcbnew.LoadBoard(PCB)
for it in list(b.GetFootprints()) + list(b.GetTracks()) + list(b.Zones()) + list(b.GetDrawings()):
    b.Delete(it)

def rede(nome):
    n = b.FindNet(nome)
    if n is None:
        n = pcbnew.NETINFO_ITEM(b, nome)
        b.Add(n)
    return n

for ref, (u, v, ang) in POS.items():
    c = COMP[ref]
    lib, nome = c["pegada"].split(":")
    fp = pcbnew.FootprintLoad(LIB, nome)
    fp.SetFPID(pcbnew.LIB_ID(lib, nome))
    fp.SetReference(ref)
    fp.SetValue(c["valor"])
    if c["tstamp"]:
        fp.SetPath(pcbnew.KIID_PATH("/" + c["tstamp"]))
    b.Add(fp)
    fp.SetOrientationDegrees(ang)
    fp.SetPosition(P(u, v))
    for pad in fp.Pads():
        nm = PINO.get((ref, pad.GetNumber()))
        if nm:
            pad.SetNet(rede(nm))
    if ref == "U1":   # GND da ESP32: alivio termico com raios retos (esquerda/direita resolvem)
        for pad in fp.Pads():
            if pad.GetNumber() in ("14", "29"):
                pad.SetThermalSpokeAngleDegrees(90)
REF_ESCONDE = ("J1", "J2", "J3", "J10", "J11", "J12", "J13", "J14", "C1", "C2", "R1", "R2")
REF_POS = {"C1": (6.15, 58.3), "C2": (75.05, 58.3), "U2": (12.65, 16.5), "U3": (64.15, 16.5)}
for f in b.GetFootprints():
    f.Value().SetVisible(False)          # o valor fica na lista de pecas; a folha de montagem mostra so a referencia
    if f.GetReference() in REF_ESCONDE:
        f.Reference().SetVisible(False)
    if f.GetReference() in REF_POS:
        f.Reference().SetPosition(P(*REF_POS[f.GetReference()])); f.Reference().SetTextAngleDegrees(0)
for ref, (u, v) in FUROS.items():
    fp = pcbnew.FootprintLoad(LIB_FURO, "MountingHole_3.2mm_M3")
    fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
    fp.SetReference(ref)
    fp.SetBoardOnly(True)
    fp.Reference().SetVisible(False)
    b.Add(fp)
    fp.SetPosition(P(u, v))

# contorno
cant = [(0, TOPO), (W, TOPO), (W, TOPO + H), (0, TOPO + H)]
for i in range(4):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FM(0.1))
    s.SetStart(P(*cant[i])); s.SetEnd(P(*cant[(i + 1) % 4]))
    b.Add(s)

# trilhas
for net, w, pts in ROTAS:
    n = b.FindNet(net)
    assert n is not None, net
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(FM(w)); t.SetLayer(pcbnew.B_Cu); t.SetNet(n)
        b.Add(t)

def zona(pts, net=None, prioridade=0, regra=False, nome=""):
    z = pcbnew.ZONE(b)
    z.SetLayer(pcbnew.B_Cu)
    ol = z.Outline(); ol.NewOutline()
    for (u, v) in pts:
        ol.Append(FM(OX + u), FM(OY + v))
    if regra:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    else:
        z.SetNet(net)
        z.SetAssignedPriority(prioridade)
    if nome:
        z.SetZoneName(nome)
    b.Add(z)
    return z

# plano de GND
g = zona([(0.5, TOPO + 0.5), (W - 0.5, TOPO + 0.5), (W - 0.5, TOPO + H - 0.5), (0.5, TOPO + H - 0.5)], rede("GND"), 0, nome="GND")
g.SetLocalClearance(FM(0.6)); g.SetMinThickness(FM(1.0))
g.SetThermalReliefGap(FM(0.6)); g.SetThermalReliefSpokeWidth(FM(1.0))
g.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
g.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
# area sem cobre embaixo da antena da ESP32 (entre as fileiras, da ponta da antena ate a fileira de cima)
zona([(30.5, Y0 - 6.5), (49.5, Y0 - 6.5), (49.5, Y0 + 1.0), (30.5, Y0 + 1.0)], regra=True, nome="antena_ESP32")

# ---------------------------------------------------------------------------------------------- gotas
# Para cada trecho que sai de uma ilha: trapezio do centro da ilha (90 % da largura da ilha) ate 1,5 mm
# depois da borda (largura da trilha). Fica numa zona da mesma rede, de prioridade maior que o GND.
gotas = []
FP = {f.GetReference(): f for f in b.GetFootprints()}
pads = [(f.GetReference(), p) for f in b.GetFootprints() for p in f.Pads() if p.GetNetname()]
for t in b.GetTracks():
    for (A, B) in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
        for ref, p in pads:
            if p.GetNetname() != t.GetNetname() or not p.HitTest(A):
                continue
            ax, ay, bx, by = mm(A.x), mm(A.y), mm(B.x), mm(B.y)
            L = math.hypot(bx - ax, by - ay)
            if L < 1e-6:
                continue
            dx, dy = (bx - ax) / L, (by - ay) / L
            if abs(dx) > 1e-6 and abs(dy) > 1e-6:
                continue                      # so trechos retos (saida reta da ilha)
            sx, sy = mm(p.GetBoundingBox().GetWidth()), mm(p.GetBoundingBox().GetHeight())
            cx, cy = mm(p.GetPosition().x), mm(p.GetPosition().y)
            meia_ao_longo = (sx if abs(dx) > 0.5 else sy) / 2
            larg_pad = (sy if abs(dx) > 0.5 else sx)
            # distancia do centro da ilha ate a borda, ao longo do trecho
            proj = (cx - ax) * dx + (cy - ay) * dy          # posicao do centro da ilha no eixo do trecho
            fim_pad = proj + meia_ao_longo                  # borda da ilha medida a partir de A
            comp = min(1.5, L - fim_pad)
            if comp < 0.6:
                continue
            w = mm(t.GetWidth())
            meia_pad = min(0.45 * larg_pad, 1.6)
            if meia_pad <= w / 2 + 0.05:
                continue
            nx, ny = -dy, dx
            ox_, oy_ = ax + dx * proj, ay + dy * proj       # centro da ilha projetado no eixo do trecho
            px, py = ax + dx * (fim_pad + comp), ay + dy * (fim_pad + comp)
            poly = [(ox_ + nx * meia_pad, oy_ + ny * meia_pad), (ax + dx * fim_pad + nx * meia_pad, ay + dy * fim_pad + ny * meia_pad),
                    (px + nx * w / 2, py + ny * w / 2), (px - nx * w / 2, py - ny * w / 2),
                    (ax + dx * fim_pad - nx * meia_pad, ay + dy * fim_pad - ny * meia_pad), (ox_ - nx * meia_pad, oy_ - ny * meia_pad)]
            z = zona([(u - OX, v - OY) for (u, v) in poly], t.GetNet(), 30000, nome="$teardrop_padvia$")
            z.SetLocalClearance(FM(0.5)); z.SetMinThickness(FM(0.2))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
            gotas.append(z)

# ---------------------------------------------------------------------------------------------- serigrafia
def texto(s, u, v, tam=1.0, ang=0, camada=pcbnew.F_SilkS, espelho=False):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s); t.SetLayer(camada); t.SetPosition(P(u, v))
    t.SetTextSize(pcbnew.VECTOR2I(FM(tam), FM(tam))); t.SetTextThickness(FM(0.15 if tam <= 1.0 else 0.2))
    t.SetTextAngleDegrees(ang); t.SetMirrored(espelho)
    b.Add(t)
TXT = [
    ("MOTOR E", 19.1, 2.75), ("M+", 9.12, 5.75, 0.8), ("M-", 13.92, 5.75, 0.8),
    ("MOTOR D", 55.4, 2.75), ("M+", 60.62, 5.75, 0.8), ("M-", 65.42, 5.75, 0.8),
    ("VBAT", 39.5, 9.3), ("ENC E", 11.0, 36.4, 0.9), ("ENC D", 72.0, 36.4, 0.9),
    ("A", 7.4, r(9), 0.8), ("B", 7.4, r(10), 0.8), ("-", 7.4, r(11), 0.8), ("+", 7.4, r(12), 0.8),
    ("A", 75.0, r(9), 0.8), ("B", 75.0, r(10), 0.8), ("-", 75.0, r(11), 0.8), ("+", 75.0, r(12), 0.8),
    ("LARGADA", 60.0, 49.0, 0.9), ("VM E", 6.4, 65.2, 0.9), ("+", 10.6, 60.5, 1.0),
    ("VM D", 72.4, 65.2, 0.9), ("+", 79.3, 61.8, 1.0),
    ("USB", 40.0, 66.0), ("ROBOCAR BLITZ v0.8", 40.0, 61.0),
]
for item in TXT:
    s, u, v = item[:3]
    texto(s, u, v, item[3] if len(item) > 3 else 1.0)
texto("BLITZ", 40.0, 45.0, 1.5, 0, pcbnew.B_Cu, True)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(PCB)

# marca as zonas de gota como teardrop (formato do KiCad 7; o KiCad 10 converte ao abrir)
txt = open(PCB, encoding="utf-8").read()
txt = re.sub(r'(\(name "\$teardrop_padvia\$"\)[^\n]*\n(\s*)\(hatch[^\n]*\n)',
             lambda m: m.group(1) + m.group(2) + "(attr (teardrop (type padvia)))\n", txt)
open(PCB, "w", encoding="utf-8").write(txt)
b = pcbnew.LoadBoard(PCB)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(PCB)
print("ok: %d pecas, %d trechos, %d gotas" % (len(POS) + len(FUROS), sum(len(p) - 1 for _, _, p in ROTAS), len(gotas)))
