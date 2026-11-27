"""Placa de interface (D-028 + D-033): placa perfurada 16 x 7 furos, desenho furo a furo + verificacoes.

  python3 layout.py              # verifica, grava layout.json (lido pelo chassi v4) e as imagens
  python3 layout.py --negativos  # prova que cada verificacao pega um defeito plantado

Furo (c, r): c = 1 (borda de TRAS) .. 16 (borda da FRENTE, que da para o passa-fio do J41 e para o mastro);
r = 1 (borda de DENTRO, do lado da placa da ESP32) .. 7 (borda de FORA, lado direito do carro).
No carro: x = X0 + u, y = Y_DENTRO - w (u, w em mm a partir do canto de tras/dentro).

O que e verificado (falha = sai com erro):
  1. redes: cada fio/ponte liga exatamente o que o esquema pede (nenhuma ligacao a mais ou a menos)
  2. furos: cada furo com no maximo uma perna; furos reservados (parafusos) vazios
  3. pernas "so mecanicas" (2 pernas do botao) sem nenhuma ligacao
  4. corpos das pecas nao se sobrepoem; nada dentro da cabeca do parafuso
  5. pontes nuas so entre furos vizinhos; fio mais longo vai encapado
  6. conectores na borda certa: J1 na borda da frente (passa-fio do J41), J2 na borda de dentro (mastro)
"""
import json
import os
import sys

import shapely.geometry as sg

AQUI = os.path.dirname(os.path.abspath(__file__))
PASSO = 2.54
NC, NR = 16, 7
LARG, ALT = 40.0, 18.0                    # u (tras -> frente) x w (dentro -> fora), mm
U0, W0 = 0.95, 1.37                       # centro do furo (1, 1)


def mm(c, r):
    return (U0 + (c - 1) * PASSO, W0 + (r - 1) * PASSO)


# ------------------------------------------------------------------------------------------- pecas
# perna: (c, r, rede). rede None = so mecanica (nao ligar nada).
FUROS_M3 = {'MH1': (2, 6), 'MH2': (15, 2)}
R_CABECA = 2.9                            # cabeca do M3 / porca (mm)

PECAS = {
    # J1: 2 x 4 macho. Os 8 jumpers do J41 chegam pela frente. Ordem escolhida para os fios nao cruzarem.
    'J1': dict(tipo='barra', pernas=[(15, 4, 'P15'), (16, 4, '5V'), (15, 5, 'P19'), (16, 5, '3V3'),
                                     (15, 6, 'P16'), (16, 6, 'P18'), (15, 7, 'GND'), (16, 7, 'GND')],
               rotulos={(15, 4): '15', (16, 4): '2 (5V)', (15, 5): '19', (16, 5): '17 (3V3)', (15, 6): '16',
                        (16, 6): '18', (15, 7): '20 (GND)', (16, 7): '6 (GND)'}),
    # J2: 1 x 3 macho para o modulo da luz (no mastro): GND, controle (pino 15), 5 V
    'J2': dict(tipo='barra', pernas=[(11, 1, 'GND'), (12, 1, 'P15'), (13, 1, '5V')],
               rotulos={(11, 1): 'GND', (12, 1): 'LUZ', (13, 1): '5V'}),
    # botao 6x6: pernas em diagonal (4,3)-(6,5) sao as que chaveiam em qualquer posicao
    'S1': dict(tipo='botao', pernas=[(4, 3, 'BOT'), (6, 3, None), (4, 5, None), (6, 5, 'GND')]),
    'R1': dict(tipo='res', valor='10k', pernas=[(4, 1, '3V3'), (4, 2, 'BOT')], corpo=(4, 1)),
    'R2': dict(tipo='res', valor='1k', pernas=[(3, 3, 'BOT'), (3, 4, 'P18')], corpo=(3, 4)),
    # vermelho: "Jetson ligada / apagou = pode desligar a chave" (pino 16)
    'R5': dict(tipo='res', valor='150', pernas=[(7, 1, '3V3'), (7, 2, 'LEDV')], corpo=(7, 1)),
    'D1': dict(tipo='led', cor='vermelho', pernas=[(8, 2, 'LEDV'), (8, 3, 'C1')]),          # (anodo, catodo)
    'Q1': dict(tipo='to92', pernas=[(8, 4, 'C1'), (8, 5, 'B1'), (8, 6, 'GND')], face='tras'),  # C B E
    'R3': dict(tipo='res', valor='10k', pernas=[(10, 4, 'P16'), (10, 5, 'B1')], corpo=(10, 5)),
    'R4': dict(tipo='res', valor='100k', pernas=[(10, 6, 'B1'), (10, 7, 'GND')], corpo=(10, 7)),
    # amarelo: "codigo rodando" (pino 19)
    'R8': dict(tipo='res', valor='150', pernas=[(10, 3, '3V3'), (10, 2, 'LEDA')], corpo=(10, 3)),
    'D2': dict(tipo='led', cor='amarelo', pernas=[(13, 2, 'LEDA'), (13, 3, 'C2')]),
    'Q2': dict(tipo='to92', pernas=[(12, 4, 'C2'), (12, 5, 'B2'), (12, 6, 'GND')], face='tras'),
    'R6': dict(tipo='res', valor='10k', pernas=[(14, 4, 'P19'), (14, 5, 'B2')], corpo=(14, 4)),
    'R7': dict(tipo='res', valor='100k', pernas=[(14, 6, 'B2'), (14, 7, 'GND')], corpo=(14, 7)),
}

# ligacoes por baixo: ('ponte', a, b) = perna dobrada / ponte de solda entre furos vizinhos;
# ('fio', a, b) = fio encapado (30 AWG / cabinho), pode passar por cima de outros furos
LIGACOES = [
    # botao
    ('ponte', (4, 2), (4, 3)), ('ponte', (3, 3), (4, 3)),
    ('ponte', (6, 5), (6, 6)), ('ponte', (6, 6), (6, 7)),
    # barra de 3V3 (linha 1) ate o R5; R8 por fio
    ('ponte', (4, 1), (5, 1)), ('ponte', (5, 1), (6, 1)), ('ponte', (6, 1), (7, 1)),
    ('fio', (7, 1), (10, 3)),
    # barra de GND (linha 7)
    ('ponte', (6, 7), (7, 7)), ('ponte', (7, 7), (8, 7)), ('ponte', (8, 7), (9, 7)), ('ponte', (9, 7), (10, 7)),
    ('ponte', (10, 7), (11, 7)), ('ponte', (11, 7), (12, 7)), ('ponte', (12, 7), (13, 7)), ('ponte', (13, 7), (14, 7)),
    ('ponte', (14, 7), (15, 7)), ('ponte', (15, 7), (16, 7)),
    ('ponte', (8, 6), (8, 7)), ('ponte', (12, 6), (12, 7)),
    # vermelho
    ('ponte', (7, 2), (8, 2)), ('ponte', (8, 3), (8, 4)), ('ponte', (8, 5), (9, 5)), ('ponte', (9, 5), (10, 5)),
    ('ponte', (10, 5), (10, 6)),
    # amarelo
    ('ponte', (10, 2), (11, 2)), ('ponte', (11, 2), (12, 2)), ('ponte', (12, 2), (13, 2)), ('ponte', (13, 3), (12, 4)),
    ('ponte', (12, 5), (13, 5)), ('ponte', (13, 5), (14, 5)), ('ponte', (14, 5), (14, 6)),
    # J1 -> pecas
    ('fio', (16, 5), (7, 1)),        # 3V3
    ('fio', (15, 6), (10, 4)),       # P16 -> R3
    ('fio', (16, 6), (3, 4)),        # P18 -> R2
    ('ponte', (15, 5), (14, 4)),     # P19 -> R6 (perna do R6 dobrada ate o pino do J1, diagonal curta)
    # J1 -> J2 (luz)
    ('fio', (15, 4), (12, 1)),       # P15 -> LUZ
    ('fio', (16, 4), (13, 1)),       # 5V
    ('fio', (11, 7), (11, 1)),       # GND
]

# o que o esquema pede: rede -> conjunto de (peca, indice da perna)
REDES = {
    '3V3': {('J1', 3), ('R1', 0), ('R5', 0), ('R8', 0)},
    'GND': {('J1', 6), ('J1', 7), ('J2', 0), ('S1', 3), ('Q1', 2), ('Q2', 2), ('R4', 1), ('R7', 1)},
    '5V': {('J1', 1), ('J2', 2)},
    'P15': {('J1', 0), ('J2', 1)},
    'P16': {('J1', 4), ('R3', 0)},
    'P18': {('J1', 5), ('R2', 1)},
    'P19': {('J1', 2), ('R6', 0)},
    'BOT': {('S1', 0), ('R1', 1), ('R2', 0)},
    'LEDV': {('R5', 1), ('D1', 0)}, 'C1': {('D1', 1), ('Q1', 0)}, 'B1': {('Q1', 1), ('R3', 1), ('R4', 0)},
    'LEDA': {('R8', 1), ('D2', 0)}, 'C2': {('D2', 1), ('Q2', 0)}, 'B2': {('Q2', 1), ('R6', 1), ('R7', 0)},
}


# ------------------------------------------------------------------------------------------- corpos
def corpo(nome, p):
    t = p['tipo']
    pts = [mm(c, r) for c, r, _ in p['pernas']]
    if t == 'res':
        return sg.Point(*mm(*p['corpo'])).buffer(1.25)                 # resistor em pe: corpo em cima de uma perna
    if t == 'led':
        (a, b) = pts
        return sg.Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2).buffer(1.9)   # LED 3 mm (aba de 3,8 mm)
    if t == 'to92':
        (a, b, c) = pts
        lin = sg.LineString([a, c])
        lado = -1.0 if p['face'] == 'tras' else 1.0                    # face reta para tras: corpo redondo para a frente
        if abs(a[0] - c[0]) < 1e-6:                                    # pernas ao longo de w
            u0, u1 = (b[0] - 1.2, b[0] + 2.5) if lado < 0 else (b[0] - 2.5, b[0] + 1.2)
            return sg.box(u0, min(a[1], c[1]) - 0.0, u1, max(a[1], c[1]) + 0.0)
        raise ValueError(nome)
    if t == 'botao':
        cu = sum(q[0] for q in pts) / 4; cw = sum(q[1] for q in pts) / 4
        return sg.box(cu - 3.0, cw - 3.0, cu + 3.0, cw + 3.0)
    if t == 'barra':
        return sg.MultiPolygon([sg.box(u - 1.27, w - 1.27, u + 1.27, w + 1.27) for u, w in pts]).buffer(0)
    raise ValueError(t)


# ------------------------------------------------------------------------------------------- verificacoes
def verificar(pecas=PECAS, ligacoes=LIGACOES, redes=REDES, furos_m3=FUROS_M3):
    erros = []
    dono = {}
    for nome, p in pecas.items():
        for i, (c, r, _) in enumerate(p['pernas']):
            if not (1 <= c <= NC and 1 <= r <= NR):
                erros.append(f'{nome}: perna fora da placa em ({c},{r})')
            if (c, r) in dono:
                erros.append(f'furo ({c},{r}) com duas pernas: {dono[(c, r)][0]} e {nome}')
            dono[(c, r)] = (nome, i)
    for m3, (c, r) in furos_m3.items():
        centro = sg.Point(*mm(c, r))
        for (cc, rr), (nome, _) in dono.items():
            if centro.distance(sg.Point(*mm(cc, rr))) < 3.3:
                erros.append(f'{m3}: perna de {nome} em ({cc},{rr}) dentro da area do parafuso')
        for nome, p in pecas.items():
            if corpo(nome, p).intersects(centro.buffer(R_CABECA)):
                erros.append(f'{m3}: corpo de {nome} embaixo da cabeca do parafuso')
        u, w = mm(c, r)
        if min(u, w, LARG - u, ALT - w) < 2.6:
            erros.append(f'{m3}: furo de 3,2 mm a menos de 1 mm da borda')
    # ligacoes
    pai = {}
    def raiz(x):
        while pai.setdefault(x, x) != x:
            x = pai[x]
        return x
    pontas = {}
    for tipo, a, b in ligacoes:
        for q in (a, b):
            pontas[q] = pontas.get(q, 0) + 1
    reservados = {q for c in furos_m3.values() for q in [(c[0] + dc, c[1] + dr) for dc in (-1, 0, 1) for dr in (-1, 0, 1)]}
    for q, n in pontas.items():
        if not (1 <= q[0] <= NC and 1 <= q[1] <= NR):
            erros.append(f'ligacao em ({q[0]},{q[1]}) fora da placa')
        elif q not in dono and n < 2:
            erros.append(f'furo vazio ({q[0]},{q[1]}) com uma ligacao so (ponta solta)')
        if q in reservados:
            erros.append(f'ligacao no furo ({q[0]},{q[1]}), reservado para o parafuso')
    for tipo, a, b in ligacoes:
        if tipo == 'ponte' and max(abs(a[0] - b[0]), abs(a[1] - b[1])) > 1:
            erros.append(f'ponte nua {a}-{b} nao e entre vizinhos: use fio encapado')
        pai[raiz(a)] = raiz(b)
    for (c, r), (nome, i) in dono.items():
        if pecas[nome]['pernas'][i][2] is None and any((c, r) in (a, b) for _, a, b in ligacoes):
            erros.append(f'{nome}: perna so mecanica ({c},{r}) esta ligada')
    grupos = {}
    for q, (nome, i) in dono.items():
        if pecas[nome]['pernas'][i][2] is None:
            continue
        grupos.setdefault(raiz(q), set()).add((nome, i))
    for rede, membros in redes.items():
        achou = [g for g in grupos.values() if g & membros]
        if len(achou) != 1:
            erros.append(f'rede {rede}: separada em {len(achou)} pedacos (falta ligacao)')
        elif achou[0] != membros:
            extra = sorted(achou[0] - membros)
            erros.append(f'rede {rede}: ligada a mais coisas: {extra}')
    for nome, p in pecas.items():                                       # rotulo da perna = rede esperada
        for i, (c, r, rede) in enumerate(p['pernas']):
            if rede is not None and (rede not in redes or (nome, i) not in redes[rede]):
                erros.append(f'{nome} perna {i} ({c},{r}) rotulada {rede} mas nao esta nessa rede no esquema')
    # corpos
    nomes = list(pecas)
    for i, a in enumerate(nomes):
        for b in nomes[i + 1:]:
            ov = corpo(a, pecas[a]).intersection(corpo(b, pecas[b])).area
            if ov > 0.05:
                erros.append(f'corpos de {a} e {b} se sobrepoem ({ov:.1f} mm2)')
    # bordas dos conectores
    u_j1 = [mm(c, r)[0] for c, r, _ in pecas['J1']['pernas']]
    if max(u_j1) < LARG - 2.0:
        erros.append('J1 nao esta na borda da frente (os jumpers do J41 chegam pela frente)')
    w_j2 = [mm(c, r)[1] for c, r, _ in pecas['J2']['pernas']]
    if min(w_j2) > 2.0:
        erros.append('J2 nao esta na borda de dentro (o cabo da luz vai para o mastro)')
    return erros


# ------------------------------------------------------------------------------------------- saidas
def exportar():
    def pos(nome, k=None):
        p = PECAS[nome]
        pts = [mm(c, r) for c, r, _ in p['pernas']]
        u = sum(q[0] for q in pts) / len(pts); w = sum(q[1] for q in pts) / len(pts)
        return [round(u, 2), round(w, 2)]
    dados = dict(placa=[LARG, ALT, 1.6], furos_m3={k: [round(v, 2) for v in mm(*c)] for k, c in FUROS_M3.items()},
                 botao=pos('S1'), led_vermelho=pos('D1'), led_amarelo=pos('D2'),
                 j1=dict(centro=pos('J1'), lu=5.08, lw=10.16, altura=8.5), j2=dict(centro=pos('J2'), lu=7.62, lw=2.54, altura=8.5),
                 obs='u: da borda de tras para a frente; w: da borda de dentro (ESP32) para fora; mm. Gerado por layout.py')
    with open(os.path.join(AQUI, 'layout.json'), 'w') as f:
        json.dump(dados, f, indent=1)
    return dados


CORES = {'3V3': '#d62728', 'GND': '#222222', '5V': '#ff7f0e', 'P15': '#9467bd', 'P16': '#8c564b', 'P18': '#1f77b4',
         'P19': '#bcbd22', 'BOT': '#17becf', 'LEDV': '#e377c2', 'C1': '#7f7f7f', 'B1': '#2ca02c', 'LEDA': '#e377c2',
         'C2': '#7f7f7f', 'B2': '#2ca02c'}


def desenhar(arq):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle, Polygon
    rede_de = {}
    for nome, p in PECAS.items():
        for c, r, rede in p['pernas']:
            rede_de[(c, r)] = rede
    fig, axs = plt.subplots(2, 1, figsize=(11, 11.5), dpi=130)
    for k, ax in enumerate(axs):
        baixo = k == 1
        X = (lambda u: LARG - u) if baixo else (lambda u: u)           # vista de baixo: espelhada
        Y = lambda w: -w
        ax.add_patch(Rectangle((0, -ALT), LARG, ALT, fc='#e9d8a6', ec='k', lw=1.2))
        for c in range(1, NC + 1):
            for r in range(1, NR + 1):
                u, w = mm(c, r)
                ax.add_patch(Circle((X(u), Y(w)), 0.55, fc='#c8a060' if baixo else 'white', ec='#8a6d3b', lw=0.6))
        for m3, (c, r) in FUROS_M3.items():
            u, w = mm(c, r)
            ax.add_patch(Circle((X(u), Y(w)), 1.6, fc='#555', ec='k'))
            ax.add_patch(Circle((X(u), Y(w)), R_CABECA, fc='none', ec='#555', ls='--', lw=0.8))
            ax.text(X(u), Y(w) - 3.6, m3, ha='center', fontsize=7)
        if not baixo:
            for nome, p in PECAS.items():
                g = corpo(nome, p)
                cor = {'res': '#c4a484', 'led': '#ff4d4d' if p.get('cor') == 'vermelho' else '#ffd21f', 'to92': '#333',
                       'botao': '#444', 'barra': '#222'}[p['tipo']]
                for poly in (g.geoms if hasattr(g, 'geoms') else [g]):
                    ax.add_patch(Polygon([(X(a), Y(b)) for a, b in poly.exterior.coords], fc=cor, ec='k', lw=0.6, alpha=0.85))
                pts = [mm(c, r) for c, r, _ in p['pernas']]
                for (u, w), (c, r, rede) in zip(pts, p['pernas']):
                    ax.add_patch(Circle((X(u), Y(w)), 0.5, fc='#bbb' if rede is None else 'silver', ec='k', lw=0.5))
                cu = sum(q[0] for q in pts) / len(pts); cw = sum(q[1] for q in pts) / len(pts)
                txt = nome + (' ' + p['valor'] if 'valor' in p else '')
                ax.text(X(cu), Y(cw), txt, ha='center', va='center', fontsize=6.5,
                        color='white' if p['tipo'] in ('to92', 'botao', 'barra') else 'black', weight='bold')
                if nome == 'J2':
                    for (c, r), rot in p['rotulos'].items():
                        u, w = mm(c, r)
                        ax.text(X(u), Y(w) + 2.2, rot, fontsize=6.5, ha='center', color='navy', weight='bold')
                if nome == 'J1':
                    for r in range(4, 8):
                        a, b = p['rotulos'][(15, r)], p['rotulos'][(16, r)]
                        ax.text(X(LARG) + 1.0, Y(mm(16, r)[1]), f'{a} | {b}', fontsize=6.5, ha='left', va='center',
                                color='navy', weight='bold')
                    ax.text(X(LARG) + 1.0, Y(mm(16, 3)[1]) + 0.6, 'pino do J41:\ncol.15 | col.16', fontsize=6, ha='left',
                            color='navy')
                if p['tipo'] == 'to92':
                    (c, r, _) = p['pernas'][0]
                    ax.text(X(mm(c, r)[0]) - 2.2, Y(mm(c, r)[1]), 'C', fontsize=5.5, ha='right', va='center')
                if p['tipo'] == 'led':
                    (c, r, _) = p['pernas'][0]
                    ax.add_patch(Circle((X(mm(c, r)[0]), Y(mm(c, r)[1])), 0.75, fc='none', ec='red', lw=1.4))
                    ax.text(X(mm(c, r)[0]) - 1.0, Y(mm(c, r)[1]) + 1.0, '+', fontsize=8, ha='right', va='bottom',
                            weight='bold', color='red')
        for tipo, a, b in LIGACOES:
            (ua, wa), (ub, wb) = mm(*a), mm(*b)
            cor = CORES.get(rede_de.get(a) or '', 'k')
            ax.plot([X(ua), X(ub)], [Y(wa), Y(wb)], color=cor, lw=3.2 if tipo == 'ponte' else 1.6,
                    ls='-' if tipo == 'ponte' else (0, (4, 1.5)), alpha=1.0 if baixo else 0.25, solid_capstyle='round')
        for c in (1, 4, 8, 12, 16):
            ax.text(X(mm(c, 1)[0]), 1.0, str(c), ha='center', fontsize=6, color='gray')
        for r in range(1, NR + 1):
            ax.text(X(-1.2) if not baixo else X(LARG + 1.2), Y(mm(1, r)[1]), str(r), va='center', ha='center', fontsize=6,
                    color='gray')
        ax.set_xlim(-4, LARG + 16); ax.set_ylim(-ALT - 5, 3.5); ax.set_aspect('equal'); ax.axis('off')
        if baixo:
            ax.set_title('Lado da SOLDA (placa virada: a FRENTE do carro fica a ESQUERDA). Linha grossa = ponte nua entre '
                         'vizinhos; tracejada = fio encapado', fontsize=9)
        else:
            ax.set_title('Lado dos COMPONENTES (vista de cima, FRENTE do carro a DIREITA, lado de DENTRO/ESP32 em cima, '
                         'lado de FORA embaixo)\nS1: so as pernas cinza-claro ficam sem ligacao. Q1/Q2 (BC337): face reta '
                         'para TRAS. LED: perna longa (+) no furo marcado', fontsize=9)
    fig.text(0.5, 0.015, 'Furos (coluna, linha): coluna 1 = tras, 16 = frente; linha 1 = dentro, 7 = fora. '
             'Gerado por hardware/placa_desligar/layout.py (verificado: redes, furos, corpos, bordas).', ha='center', fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(arq, facecolor='white'); plt.close(fig)


# ------------------------------------------------------------------------------------------- negativos
def negativos():
    import copy
    casos = []
    def caso(nome, contendo, mut):
        pc, lg, rd, fm = copy.deepcopy(PECAS), list(LIGACOES), copy.deepcopy(REDES), dict(FUROS_M3)
        mut(pc, lg, rd, fm)
        err = verificar(pc, lg, rd, fm)
        pegou = any(contendo in e for e in err)
        casos.append((nome, pegou, err[:1]))
    caso('falta a ponte do emissor do Q1 ao GND', 'rede GND', lambda pc, lg, rd, fm: lg.remove(('ponte', (8, 6), (8, 7))))
    caso('fio do 5V soldado no pino do 3V3', 'rede', lambda pc, lg, rd, fm: (lg.remove(('fio', (16, 4), (13, 1))),
                                                                          lg.append(('fio', (16, 5), (13, 1)))))
    caso('ponte nua comprida (fio sem capa atravessando a placa)', 'ponte nua',
         lambda pc, lg, rd, fm: (lg.remove(('fio', (15, 6), (10, 4))), lg.append(('ponte', (15, 6), (10, 4)))))
    caso('perna mecanica do botao ligada na barra de GND', 'so mecanica',
         lambda pc, lg, rd, fm: lg.extend([('ponte', (4, 5), (5, 6)), ('ponte', (5, 6), (6, 6)), ('ponte', (6, 6), (6, 7))]))
    caso('ponte terminando num furo vazio (ponta solta)', 'ponta solta', lambda pc, lg, rd, fm: lg.append(('ponte', (14, 7), (13, 6))))
    caso('duas pernas no mesmo furo', 'duas pernas', lambda pc, lg, rd, fm: pc['R4']['pernas'].__setitem__(0, (10, 5, 'B1')))
    caso('LED em cima do transistor (corpos sobrepostos)', 'sobrepoem',
         lambda pc, lg, rd, fm: pc['D1'].__setitem__('pernas', [(9, 4, 'LEDV'), (9, 6, 'C1')]))
    caso('parafuso no meio dos resistores', 'parafuso', lambda pc, lg, rd, fm: fm.__setitem__('MH1', (10, 6)))
    caso('J1 no meio da placa (longe do passa-fio do J41)', 'J1 nao esta', lambda pc, lg, rd, fm:
         pc['J1'].__setitem__('pernas', [(c - 6, r, n) for c, r, n in pc['J1']['pernas']]))
    caso('resistor com rotulo de rede errado', 'rotulada', lambda pc, lg, rd, fm: pc['R3']['pernas'].__setitem__(0, (10, 4, 'P18')))
    return casos


def principal():
    if '--negativos' in sys.argv:
        casos = negativos()
        ok = all(p for _, p, _ in casos)
        for nome, pegou, err in casos:
            print('PEGOU    ' if pegou else 'NAO PEGOU', nome, '->', err[0] if err else '(nenhum erro)')
        base = verificar()
        if base:
            print('o desenho sem defeito NAO passa:', base); ok = False
        print('TODOS OS DEFEITOS FORAM PEGOS' if ok else 'FALHOU')
        return 0 if ok else 1
    erros = verificar()
    for e in erros:
        print('ERRO:', e)
    if erros:
        return 1
    exportar()
    os.makedirs(os.path.join(AQUI, 'imagens'), exist_ok=True)
    desenhar(os.path.join(AQUI, 'imagens', 'placa_perfurada.png'))
    n_p = sum(1 for t, _, _ in LIGACOES if t == 'ponte'); n_f = len(LIGACOES) - n_p
    print(f'placa de interface: {len(PECAS)} pecas, {len(REDES)} redes, {n_p} pontes nuas, {n_f} fios encapados: OK')
    return 0


if __name__ == '__main__':
    sys.exit(principal())
