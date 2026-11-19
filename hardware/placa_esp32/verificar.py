"""Robocar Blitz - verificacoes da placa da ESP32 (rodar com o Python do KiCad, que tem o modulo pcbnew).

    python3 hardware/placa_esp32/verificar.py          (Linux: o python3 do sistema ja enxerga o pcbnew)
    "C:\\Program Files\\KiCad\\<versao>\\bin\\python.exe" hardware\\placa_esp32\\verificar.py   (Windows)

Grava em verificacao/:
  drc.rpt                     DRC completo (inclui as regras de face simples do placa_esp32.kicad_dru)
  paridade_esquema_placa.txt  mesmas pecas, pegadas e redes no esquematico e na placa
  face_simples.txt            nenhuma trilha/via/zona fora de B.Cu
Sai com codigo 1 se algo falhar.
"""
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import pcbnew

AQUI = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(AQUI, "placa_esp32.kicad_pcb")
SCH = os.path.join(AQUI, "placa_esp32.kicad_sch")
OUT = os.path.join(AQUI, "verificacao")
os.makedirs(OUT, exist_ok=True)
falhas = []

placa = pcbnew.LoadBoard(PCB)

# 0) a zona salva no arquivo tem de estar preenchida com a placa atual (os PDFs/Gerber usam o preenchimento salvo)
def area_zonas(b):
    return sum(z.GetFilledPolysList(pcbnew.B_Cu).Area() for z in b.Zones())
salva = area_zonas(placa)
pcbnew.ZONE_FILLER(placa).Fill(placa.Zones())
nova = area_zonas(placa)
if abs(nova - salva) > 0.001 * max(nova, 1):
    falhas.append("zona de GND desatualizada no arquivo: no KiCad, Inspecionar > Preencher todas as zonas (B) e salvar")

# 1) DRC
rpt = os.path.join(OUT, "drc.rpt")
pcbnew.WriteDRCReport(placa, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
texto = open(rpt, encoding="utf-8").read()
for linha in texto.splitlines():
    if linha.startswith("** Found") and not linha.startswith("** Found 0 "):
        falhas.append("DRC: " + linha.strip("* "))

# 2) face simples: so B.Cu
fora = [t for t in placa.GetTracks() if t.GetClass() == "PCB_VIA" or t.GetLayer() != pcbnew.B_Cu]
zonas = [z for z in placa.Zones() if z.GetLayerSet().Contains(pcbnew.F_Cu)]
n_trilhas = sum(1 for t in placa.GetTracks() if t.GetClass() == "PCB_TRACK")
with open(os.path.join(OUT, "face_simples.txt"), "w", encoding="utf-8") as f:
    f.write("trilhas: %d (todas em B.Cu: %s); vias: %d; trilhas/zonas em F.Cu: %d\n"
            % (n_trilhas, "sim" if not fora else "NAO",
               sum(1 for t in placa.GetTracks() if t.GetClass() == "PCB_VIA"), len(fora) + len(zonas)))
    f.write("jumpers de fio (lado dos componentes): %s\n"
            % ", ".join(sorted(fp.GetReference() for fp in placa.GetFootprints() if fp.GetReference().startswith("JP"))))
if fora or zonas:
    falhas.append("face simples: %d itens fora de B.Cu" % (len(fora) + len(zonas)))

# 2b) angulos (so 0/45/90), largura minima de 1,0 mm e cobre que nao e GND longe dos furos de fixacao
#     (o espacador M3 encosta no cobre por baixo: raio ~3,2 mm; exigimos 3,6 mm ate a borda da trilha/ilha)
import math
mm = pcbnew.ToMM
tortos, finas = [], []
for t in placa.GetTracks():
    if t.GetClass() != "PCB_TRACK":
        continue
    dx, dy = mm(t.GetEnd().x - t.GetStart().x), mm(t.GetEnd().y - t.GetStart().y)
    ang = math.degrees(math.atan2(dy, dx)) % 45
    if min(ang, 45 - ang) > 0.5:
        tortos.append(t)
    if mm(t.GetWidth()) < 0.999:
        finas.append(t)
furos = [fp for fp in placa.GetFootprints() if fp.GetReference().startswith("H")]
def dist_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L = vx * vx + vy * vy
    k = 0 if L == 0 else max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / L))
    return math.hypot(px - ax - k * vx, py - ay - k * vy)
perto = []
for h in furos:
    hx, hy = mm(h.GetPosition().x), mm(h.GetPosition().y)
    for t in placa.GetTracks():
        if t.GetNetname() != "GND":
            d = dist_seg(hx, hy, mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y)) - mm(t.GetWidth()) / 2
            if d < 3.6:
                perto.append((h.GetReference(), t.GetNetname(), round(d, 2)))
    for fp in placa.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != "GND" and fp.GetReference() != h.GetReference():
                bb = pad.GetBoundingBox()
                ddx = max(mm(bb.GetX()) - hx, 0, hx - mm(bb.GetRight()))
                ddy = max(mm(bb.GetY()) - hy, 0, hy - mm(bb.GetBottom()))
                d = math.hypot(ddx, ddy)
                if d < 3.6:
                    perto.append((h.GetReference(), "%s.%s" % (fp.GetReference(), pad.GetNumber()), round(d, 2)))
larg = sorted({round(mm(t.GetWidth()), 2) for t in placa.GetTracks() if t.GetClass() == "PCB_TRACK"})
with open(os.path.join(OUT, "angulos_e_larguras.txt"), "w", encoding="utf-8") as f:
    f.write("trechos de trilha: %d; fora de 0/45/90 graus: %d; larguras usadas: %s mm; mais finas que 1,0 mm: %d\n"
            % (n_trilhas, len(tortos), ", ".join("%.2f" % w for w in larg), len(finas)))
    f.write("cobre (nao GND) a menos de 3,6 mm do centro de um furo de fixacao: %s\n" % (perto or "nenhum"))
if tortos or finas or perto:
    falhas.append("angulos/larguras/furos: %d tortos, %d finas, %d perto dos furos" % (len(tortos), len(finas), len(perto)))

# 3) paridade esquematico x placa (netlist exportada pelo kicad-cli)
with tempfile.TemporaryDirectory() as tmp:
    xml = os.path.join(tmp, "net.xml")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", xml, SCH],
                   check=True, stdout=subprocess.DEVNULL)
    raiz = ET.parse(xml).getroot()
esq_fp = {c.get("ref"): c.findtext("footprint") for c in raiz.iter("comp")}
esq = {}
for net in raiz.iter("net"):
    for no in net.iter("node"):
        esq[(no.get("ref"), no.get("pin"))] = net.get("name")
pcb_fp, pcb = {}, {}
for fp in placa.GetFootprints():
    if fp.IsBoardOnly():
        continue
    pcb_fp[fp.GetReference()] = fp.GetFPIDAsString()
    for pad in fp.Pads():
        if pad.GetNetname():
            pcb[(fp.GetReference(), pad.GetNumber())] = pad.GetNetname()
dif = []
if esq_fp != pcb_fp:
    dif.append("pegadas: %s" % sorted(set(esq_fp.items()) ^ set(pcb_fp.items())))
for k in sorted(set(esq) | set(pcb)):
    # pinos sem ligacao tambem contam: o KiCad 10 avisa (net_conflict) se a ilha ficar sem a rede unconnected-(...)
    if esq.get(k) != pcb.get(k):
        dif.append("%s pino %s: esquema=%s placa=%s" % (k[0], k[1], esq.get(k), pcb.get(k)))
fora_bom_pcb = {fp.GetReference() for fp in placa.GetFootprints()
                if not fp.IsBoardOnly() and fp.IsExcludedFromBOM()}
if fora_bom_pcb:
    dif.append("pegadas marcadas 'fora da lista de materiais' (o simbolo esta na lista): %s" % sorted(fora_bom_pcb))
redes = {v for v in esq.values() if not v.startswith("unconnected")}
with open(os.path.join(OUT, "paridade_esquema_placa.txt"), "w", encoding="utf-8") as f:
    f.write("PARIDADE OK: mesmas pecas, mesmas pegadas e mesmas ligacoes em todos os pinos\n" if not dif
            else "DIFERENCAS:\n" + "\n".join(dif) + "\n")
    f.write("%d componentes; %d redes\n" % (len(esq_fp), len(redes)))
if dif:
    falhas.append("paridade: %d diferencas" % len(dif))

print("\n".join(falhas) if falhas else "OK: DRC limpo, so B.Cu, esquema = placa")
sys.exit(1 if falhas else 0)
