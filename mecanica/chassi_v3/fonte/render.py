"""Imagens do chassi v3 (matplotlib, sem GPU): vistas 3D, vistas ortogonais e desenho das chapas."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

COR_MDF = (0.82, 0.68, 0.47, 1.0)

def triangulos(itens, tol=0.25):
    """itens: lista (solido, cor rgba). Devolve lista de (tri 3x3, cor)."""
    out = []
    for sol, cor in itens:
        vs, fs = sol.tessellate(tol, 0.3)
        P = np.array([(p.x, p.y, p.z) for p in vs])
        for f in fs:
            out.append((P[list(f)], cor))
    return out

def vista3d(tri, arq, elev, azim, titulo='', lim=None, tamanho=(10, 7.5), dpi=150, sombra=True):
    fig = plt.figure(figsize=tamanho, dpi=dpi)
    ax = fig.add_subplot(111, projection='3d')
    luz = np.array([0.35, -0.45, 0.82]); luz = luz / np.linalg.norm(luz)
    polys, cores = [], []
    for t, c in tri:
        n = np.cross(t[1] - t[0], t[2] - t[0]); nn = np.linalg.norm(n)
        k = 0.5 + 0.5 * abs(np.dot(n / nn, luz)) if nn > 1e-9 else 0.8
        polys.append(t); cores.append((c[0] * k, c[1] * k, c[2] * k, c[3] if len(c) > 3 else 1.0))
    ax.add_collection3d(Poly3DCollection(polys, facecolors=cores, edgecolors='none', linewidths=0))
    if lim is None:
        allp = np.concatenate([t for t, _ in tri])
        lo, hi = allp.min(axis=0), allp.max(axis=0)
    else:
        lo, hi = np.array(lim[0]), np.array(lim[1])
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(tuple(hi - lo))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    if titulo:
        ax.set_title(titulo, fontsize=11)
    fig.subplots_adjust(0, 0, 1, 0.95)
    fig.savefig(arq, facecolor='white'); plt.close(fig)
