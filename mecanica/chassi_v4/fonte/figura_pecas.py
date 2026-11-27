"""Figura 'pecas como estao no modelo': render de cada peca comprada + as medidas usadas e de onde vieram.

Nao e foto: e o desenho que o chassi usa. Serve para conferir com a peca real (se algo nao bater, corrigir em pecas.py).
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import modelo, render
from pecas import M

def _origem(chave):
    o = M[chave]['o']
    return {'M': 'medido', 'V': 'documento', 'E': 'ESTIMADO'}[o]

def _fmt(chave, rotulo, unidade='mm', faixa=False):
    val = M[chave]['v']
    if isinstance(val, tuple) and val and isinstance(val[0], tuple):
        txt = ' '.join('(' + ', '.join(f'{q:g}' for q in par) + ')' for par in val)
    elif isinstance(val, tuple) and val and isinstance(val[0], (int, float)):
        txt = (' a '.join(f'{q:g}' for q in val)) if faixa else ' x '.join(f'{q:g}' for q in val)
    elif isinstance(val, (int, float)):
        txt = f'{val:g}'
    else:
        txt = 'ver pecas.py'
    return f'{rotulo}: {txt} {unidade} ({_origem(chave)})'

GRUPOS = [
    ('Jetson Nano B01 (portas para tras no v4)', lambda n, g: g == 'jetson',
     [('jet_placa', 'placa'), ('jet_furos_borda', 'furos, borda a borda'), ('jet_furo_d', 'diametro do furo'),
      ('jet_altura', 'altura com dissipador'), ('jet_p4_u', 'centro do P4 desde a ponta'), ('jet_usb_u', 'pilha USB-A, desde a ponta do P4', 'faixa')]),
    ('XL4016 (bornes para o eixo, trimpots para a frente)', lambda n, g: g == 'xl4016_1_jetson' or n == 'xl4016_1_jetson',
     [('xl', 'placa com dissipadores'), ('xl_altura', 'altura'), ('xl_furos', 'furos (l, w)'), ('xl_trimpots', 'trimpots (l, w)'),
      ('xl_bornes', 'bornes (l0, l1, altura)')]),
    ('Motor N20 + suporte + roda (lado esquerdo)', lambda n, g: g == 'motor_esq' or n == 'motor_esq',
     [('motor_corpo', 'corpo sem o eixo'), ('sup_motor', 'suporte branco'), ('sup_motor_eixo_z', 'eixo acima da base'),
      ('roda', 'roda'), ('motor_cabo', 'cabo de 6 vias')]),
    ('Bateria 3S 1100 + par XT60 + pino de trava', lambda n, g: n in ('bateria', 'par_xt60', 'pino_trava'),
     [('bat', 'bateria'), ('bat_cabo', 'fios do XT60'), ('xt60', 'corpo do XT60')]),
    ('Camera IMX219-160 no suporte (45 graus)', None,
     [('cam_placa', 'placa'), ('cam_furos', 'furos M2'), ('cam_lente', 'lente (diametro, comprimento)'),
      ('cam_suporte_lente', 'base do suporte da lente'), ('ffc_compr', 'cabo flat')]),
]

def figura(m, arq, img_esp=None):
    pasta = os.path.dirname(arq)
    tmp = []
    paineis = []
    for titulo, filtro, medidas in GRUPOS:
        if filtro is None:
            itens = [(s, (0.15, 0.15, 0.15, 1.0) if t == 'camera' else render.COR_MDF)
                     for n, s, t in m.partes_camera(m.P['CAM_ANG_NOMINAL'])]
        else:
            itens = [(p['solido'], tuple(p['cor']) + (1.0,)) for p in m.compradas if filtro(p['nome'], p['grupo'])]
        tri = render.triangulos(itens, 0.2)
        P = np.concatenate([t for t, _ in tri])
        lo, hi = P.min(axis=0), P.max(axis=0)
        c, r = (lo + hi) / 2, (hi - lo).max() / 2 * 1.05
        f = os.path.join(pasta, f'_peca_{len(tmp)}.png')
        render.vista3d(tri, f, 28, -55, '', (c - r, c + r), tamanho=(4.2, 4.2), dpi=110)
        tmp.append(f)
        paineis.append((titulo, f, [_fmt(q[0], q[1], faixa=len(q) > 2) for q in medidas]))
    if img_esp and os.path.exists(img_esp):
        paineis.append(('Placa da ESP32 v0.8 (render do KiCad da placa real)', img_esp,
                        [_fmt('esp_placa', 'placa'), 'furos M3: 73 x 66 mm entre centros (documento)', _fmt('esp_altura', 'altura da ESP32'),
                         _fmt('esp_usb_plugue', 'plugue USB-C')]))
    fig, axs = plt.subplots(2, 3, figsize=(15, 11.5), dpi=110)
    for ax, (titulo, f, linhas) in zip(axs.flat, paineis):
        ax.imshow(plt.imread(f)); ax.axis('off')
        ax.set_title(titulo, fontsize=10, weight='bold')
        txt = '\n'.join(linhas)
        ax.text(0.0, -0.02, txt, transform=ax.transAxes, va='top', fontsize=7.8, family='monospace',
                color='black')
    for ax in list(axs.flat)[len(paineis):]:
        ax.axis('off')
    fig.suptitle('Pecas compradas como estao no modelo (desenho, nao foto). Confira com a peca real: o que estiver ESTIMADO '
                 'e diferente, corrija em fonte/pecas.py', fontsize=11)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.08, hspace=0.45, wspace=0.08)
    fig.savefig(arq, facecolor='white'); plt.close(fig)
    for f in tmp:
        os.remove(f)
