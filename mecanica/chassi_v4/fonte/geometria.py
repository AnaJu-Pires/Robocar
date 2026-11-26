"""Utilitarios de geometria do chassi v3: chapas 2D (contorno, furos, textos), referenciais 3D e solidos.

Convencao do carro: x para a FRENTE (0 = eixo das rodas), y para a ESQUERDA, z para CIMA (0 = chao). mm.
Uma chapa e desenhada no plano local (a, b) e tem espessura w em [0, T]. O referencial leva (a, b, w) ao carro.
"""
import math
import numpy as np
import shapely.geometry as sg
import shapely.ops as so
import shapely.affinity as sa
import cadquery as cq
from OCP.gp import gp_Trsf

# ------------------------------------------------------------------------------------------- formas 2D
def ret(x0, y0, x1, y1):
    return sg.box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

def ret_c(xc, yc, w, h):
    return ret(xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2)

class Furo:
    """Furo de uma chapa. tipo 'circ' (vira circulo no DXF) ou 'poli'. nome serve para os testes e cabos."""
    def __init__(s, geom, nome='', tipo='poli', centro=None, d=None, funcao=''):
        s.geom, s.nome, s.tipo, s.centro, s.d, s.funcao = geom, nome, tipo, centro, d, funcao

def circ(x, y, d, nome='', funcao=''):
    return Furo(sg.Point(x, y).buffer(d / 2, quad_segs=32), nome, 'circ', (x, y), d, funcao)

def oblongo(p1, p2, d, nome='', funcao=''):
    return Furo(sg.LineString([p1, p2]).buffer(d / 2, quad_segs=16), nome, 'poli', funcao=funcao)

def rasgo(xc, yc, w, h, nome='', funcao='encaixe'):
    return Furo(ret_c(xc, yc, w, h), nome, 'poli', funcao=funcao)

def poli(pts, nome='', funcao=''):
    return Furo(sg.Polygon(pts), nome, 'poli', funcao=funcao)

def arco_rasgo(cx, cy, r, a0, a1, d, nome='', funcao=''):
    """Rasgo em arco (centro, raio, angulos em graus), largura d."""
    n = max(8, int(abs(a1 - a0) / 3))
    pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
           for k in range(n + 1)]
    return Furo(sg.LineString(pts).buffer(d / 2, quad_segs=16), nome, 'poli', funcao=funcao)

# ------------------------------------------------------------------------------------------- referenciais
def frame(ex, ey, origem):
    """Referencial com eixos locais a = ex, b = ey e w = ex x ey (mao direita)."""
    ex = np.array(ex, float); ey = np.array(ey, float)
    ez = np.cross(ex, ey)
    return (ex, ey, ez, np.array(origem, float))

def F_xy(z0):            # chapa horizontal: a = x, b = y, w = z a partir de z0
    return frame((1, 0, 0), (0, 1, 0), (0, 0, z0))

def F_xz(y_lado_de_cima):  # chapa vertical no plano x-z: a = x, b = z; ocupa y em [y - T, y]
    return frame((1, 0, 0), (0, 0, 1), (0, y_lado_de_cima, 0))

def F_yz(x0):            # chapa vertical no plano y-z: a = y, b = z; ocupa x em [x0, x0 + T]
    return frame((0, 1, 0), (0, 0, 1), (x0, 0, 0))

def aplicar(fr, a, b, w=0.0):
    ex, ey, ez, o = fr
    return o + a * ex + b * ey + w * ez

def loc(fr):
    ex, ey, ez, o = fr
    t = gp_Trsf()
    t.SetValues(ex[0], ey[0], ez[0], o[0], ex[1], ey[1], ez[1], o[1], ex[2], ey[2], ez[2], o[2])
    return cq.Location(t)

def F_rot_y(fr_base_xz, ang_graus, pivo):
    """Gira um referencial em torno de um eixo paralelo a y que passa pelo ponto pivo (x, z)."""
    a = math.radians(ang_graus)
    R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    ex, ey, ez, o = fr_base_xz
    p = np.array([pivo[0], o[1], pivo[1]])
    return (R @ ex, R @ ey, R @ ez, p + R @ (o - p))

# ------------------------------------------------------------------------------------------- chapas
class Chapa:
    def __init__(s, nome, base, furos=(), abas=(), entalhes=(), textos=(), frames=(), material='MDF', qtd=None,
                 descricao=''):
        """base: poligono shapely. abas: poligonos somados ao contorno. entalhes: poligonos tirados DO CONTORNO
        (intencionais, ex.: rasgo da porca presa na borda). furos: Furo (devem ficar dentro, com material em volta)."""
        geo = so.unary_union([base] + list(abas)) if abas else base
        for e in entalhes:
            geo = geo.difference(e)
        if geo.geom_type != 'Polygon':
            raise ValueError(f'{nome}: contorno nao e um poligono unico ({geo.geom_type})')
        s.nome, s.contorno, s.furos, s.textos = nome, sg.Polygon(geo.exterior), list(furos), list(textos)
        s.frames, s.material, s.descricao = list(frames), material, descricao
        s.qtd = qtd if qtd is not None else max(1, len(s.frames))
        s.entalhes = list(entalhes)

    def peca2d(s):
        """Chapa cortada: contorno menos furos."""
        g = s.contorno
        for f in s.furos:
            g = g.difference(f.geom)
        return g

    def area(s):
        return s.peca2d().area

    def solido(s, T):
        chave = round(T, 4)
        if getattr(s, '_cache', None) and s._cache[0] == chave:
            return s._cache[1]
        g = s.peca2d()
        if g.geom_type != 'Polygon':      # o verificador acusa; aqui so evita quebrar o desenho
            g = max(g.geoms, key=lambda q: q.area)
        def fio(anel):
            pts = [cq.Vector(x, y, 0) for x, y in list(anel.coords)[:-1]]
            return cq.Wire.makePolygon(pts, close=True)
        sol = None
        if g.geom_type == 'Polygon' and len(g.interiors) == len(s.furos):
            # furos redondos como circulos de verdade (STEP leve); so quando nenhum furo encosta em outro ou na borda
            internos = [cq.Wire.makeCircle(f.d / 2, cq.Vector(f.centro[0], f.centro[1], 0), cq.Vector(0, 0, 1))
                        if f.tipo == 'circ' else fio(f.geom.exterior) for f in s.furos]
            try:
                face = cq.Face.makeFromWires(fio(s.contorno.exterior), internos)
                if face.isValid():
                    sol = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, T))
            except Exception:
                sol = None
        if sol is None:
            face = cq.Face.makeFromWires(fio(g.exterior), [fio(i) for i in g.interiors])
            sol = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, T))
        s._cache = (chave, sol)
        return sol

# ------------------------------------------------------------------------------------------- solidos 3D
def caixa(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0)).val()

def cilindro(p0, p1, d):
    p0 = np.array(p0, float); p1 = np.array(p1, float)
    v = p1 - p0; h = float(np.linalg.norm(v))
    return cq.Solid.makeCylinder(d / 2, h, cq.Vector(*p0), cq.Vector(*(v / h)))

def caixa_local(fr, a0, a1, b0, b1, w0, w1):
    """Caixa definida nas coordenadas locais (a, b, w) de um referencial."""
    return cq.Workplane().box(a1 - a0, b1 - b0, w1 - w0, centered=False).translate((a0, b0, w0)).val().moved(loc(fr))

def tubo(pontos, d):
    """Cabo como uma sequencia de cilindros com esferas nas juncoes (para desenho e interferencia)."""
    partes = []
    for p, q in zip(pontos[:-1], pontos[1:]):
        if np.linalg.norm(np.array(q) - np.array(p)) > 0.01:
            partes.append(cilindro(p, q, d))
    for p in pontos[1:-1]:
        partes.append(cq.Solid.makeSphere(d / 2, cq.Vector(*p)))
    c = partes[0]
    for q in partes[1:]:
        c = c.fuse(q)
    return c

def comprimento(pontos):
    return float(sum(np.linalg.norm(np.array(q) - np.array(p)) for p, q in zip(pontos[:-1], pontos[1:])))
