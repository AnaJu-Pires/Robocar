"""Modelos 3D de verdade no STEP montado (so para ver; as verificacoes usam as caixas de modelo.py, que sao o envelope).

  placa da ESP32 v0.8     hardware/placa_esp32/placa_esp32.step (exportado do KiCad da placa de voces)
  placa de distribuicao   hardware/placa_distribuicao/placa_distribuicao.step (idem)
  motores N20             modelos_3d/n20_motor_wcrl.step (wcrl/Build-the-Bot, licenca MIT) + o encoder do modelo
  rodas 42 x 19           pneu + aro + cubo com furo em D, desenhados aqui com as medidas da roda
A Jetson, a bateria, os XL4016 e a camera continuam como em modelo.py (medidas conferidas; nao ha modelo com licenca
livre que possa entrar no repositorio).
"""
import os
import cadquery as cq
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, '..', '..', '..'))
STEP_ESP = os.path.join(RAIZ, 'hardware', 'placa_esp32', 'placa_esp32.step')
STEP_DIST = os.path.join(RAIZ, 'hardware', 'placa_distribuicao', 'placa_distribuicao.step')
STEP_N20 = os.path.join(AQUI, '..', 'modelos_3d', 'n20_motor_wcrl.step')
# centro da placa no KiCad (mm), lido do .kicad_pcb (o STEP do KiCad usa X = x, Y = -y)
CENTRO_ESP_KICAD = (148.5, 105.0)
CENTRO_DIST_KICAD = (116.0, 122.0)

# pecas de modelo.py que o modelo de verdade substitui no STEP
SUBSTITUI = {
    'placa_esp32': ('placa_esp32', 'esp32_devkit', 'barras_esp32', 'c470_esq', 'c470_dir'),
    'placa_distribuicao': ('placa_fusivel', 'diodo_protecao'),
    'motor_esq': ('motor_esq', 'redutor_esq', 'eixo_esq'),
    'motor_dir': ('motor_dir', 'redutor_dir', 'eixo_dir'),
    'roda_esq': ('roda_esq',),
    'roda_dir': ('roda_dir',),
}

def _bbox(m, nome):
    p = next(p for p in m.compradas if p['nome'] == nome)
    b = p['solido'].BoundingBox()
    return b

def _ler(arq):
    return cq.importers.importStep(arq).val()

def placa_esp32(m):
    """KiCad (X, Y=-y) -> carro: borda de cima da placa (y KiCad pequeno) = frente; esquerda da placa = esquerda do carro."""
    b = _bbox(m, 'placa_esp32')
    cx, cy = CENTRO_ESP_KICAD
    s = _ler(STEP_ESP)
    s = s.moved(cq.Location(cq.Vector(-cx, cy, 0)))                     # centro da placa na origem
    s = s.rotate((0, 0, 0), (0, 0, 1), -90)                              # (X, Y) -> (Y, -X)
    return s.moved(cq.Location(cq.Vector((b.xmin + b.xmax) / 2, (b.ymin + b.ymax) / 2, b.zmin)))

def placa_distribuicao(m):
    b = _bbox(m, 'placa_fusivel')
    cx, cy = CENTRO_DIST_KICAD
    s = _ler(STEP_DIST)
    s = s.moved(cq.Location(cq.Vector(-cx, cy, 0)))
    return s.moved(cq.Location(cq.Vector((b.xmin + b.xmax) / 2, (b.ymin + b.ymax) / 2, b.zmin)))

def motor(m, lado):
    """N20 do arquivo: eixo em y (tampa em -1,5, caixa de reducao 15-24,3, eixo ate 33,3), secao 10 (x) x 12 (z)."""
    r = _bbox(m, f'redutor_{lado}')
    s = _ler(STEP_N20).rotate((0, 0, 0), (0, 1, 0), 90)                 # secao 12 em x, 10 em z, como o modelo
    zc = (r.zmin + r.zmax) / 2
    if lado == 'esq':
        return s.moved(cq.Location(cq.Vector(0, r.ymin - 15.0, zc)))
    s = s.rotate((0, 0, 0), (0, 0, 1), 180)
    return s.moved(cq.Location(cq.Vector(0, r.ymax + 15.0, zc)))

def roda(m, lado):
    b = _bbox(m, f'roda_{lado}')
    D, L = b.zmax - b.zmin, b.ymax - b.ymin
    pneu = (cq.Workplane('XZ').circle(D / 2).circle(D / 2 - 5.0).extrude(-L).edges().fillet(1.5))
    aro = cq.Workplane('XZ').workplane(offset=-L / 2 + 4.0).circle(D / 2 - 5.0).circle(5.0).extrude(-3.0)
    cubo = (cq.Workplane('XZ').circle(5.0).extrude(-L + 2.0).translate((0, 1.0, 0))
            .cut(cq.Workplane('XZ').circle(1.5).extrude(-L).intersect(
                cq.Workplane('XZ').rect(3.0, 2.5).extrude(-L).translate((0, 0, -0.25)))))
    w = pneu.union(aro).union(cubo)
    s = w.val()
    return s.moved(cq.Location(cq.Vector((b.xmin + b.xmax) / 2, b.ymin, (b.zmin + b.zmax) / 2)))

def pecas(m):
    """[(nome, solido, cor)] e o conjunto de nomes de modelo.py que elas substituem."""
    out = [('placa_esp32_kicad', placa_esp32(m), (0.15, 0.45, 0.25)),
           ('placa_distribuicao_kicad', placa_distribuicao(m), (0.15, 0.4, 0.55)),
           ('motor_n20_esq', motor(m, 'esq'), (0.75, 0.75, 0.78)),
           ('motor_n20_dir', motor(m, 'dir'), (0.75, 0.75, 0.78)),
           ('roda_esq', roda(m, 'esq'), (0.08, 0.08, 0.08)),
           ('roda_dir', roda(m, 'dir'), (0.08, 0.08, 0.08))]
    tira = set()
    for v in SUBSTITUI.values():
        tira |= set(v)
    return out, tira

def conferir(m):
    """O modelo de verdade tem de ficar dentro (ou quase) da caixa que as verificacoes usam: lista de diferencas."""
    erros = []
    caixas = {'placa_esp32_kicad': ['placa_esp32', 'esp32_devkit', 'barras_esp32', 'c470_esq', 'c470_dir', 'drv8833_esq',
                                    'drv8833_dir', 'plugue_usb_esp32'],
              'placa_distribuicao_kicad': ['placa_fusivel', 'diodo_protecao', 'fusivel_5x20'],
              'motor_n20_esq': ['motor_esq', 'redutor_esq', 'eixo_esq', 'encoder_esq'],
              'motor_n20_dir': ['motor_dir', 'redutor_dir', 'eixo_dir', 'encoder_dir'],
              'roda_esq': ['roda_esq'], 'roda_dir': ['roda_dir']}
    novos, _ = pecas(m)
    for nome, s, _ in novos:
        bs = [_bbox(m, n) for n in caixas[nome]]
        lo = np.min([[b.xmin, b.ymin, b.zmin] for b in bs], axis=0)
        hi = np.max([[b.xmax, b.ymax, b.zmax] for b in bs], axis=0)
        b = s.BoundingBox()
        fora = max(np.max(lo - [b.xmin, b.ymin, b.zmin]), np.max([b.xmax, b.ymax, b.zmax] - hi))
        erros.append((nome, float(fora), (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax), tuple(lo), tuple(hi)))
    return erros
