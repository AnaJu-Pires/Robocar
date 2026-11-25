"""Analise de arquitetura e rodas do Robocar Blitz (chassi v3).

Compara, com as MESMAS pecas e massas do modelo:
  A  "v2.2 reconstruida": Jetson no andar de cima, acima da placa da ESP32 (o v2.2 nao esta no repositorio;
     montado a partir da D-024 e das licoes: placa sobre o eixo com ~20 mm de espacador, bateria no meio)
  B  v3 (escolhida): Jetson baixa sobre a bateria, caixa traseira com XL4016 e tampo da ESP32
  C  Jetson no piso (sem nada embaixo) e bateria atravessada na frente
e as rodas de 32, 42, 48 e 65 mm, num modelo de volta (aceleracao, frenagem, curvas).
Uso: python3 analise.py [arquivo_saida.md]
"""
import sys, math
import numpy as np
import modelo
from pecas import v

G = 9.81

# ------------------------------------------------------------------------------------------- estabilidade
def estabilidade(cg, L, bitola, mu):
    """cg (x, y, z) em mm; L = eixo -> esfera; apoio em 3 pontos (2 rodas + esfera no centro)."""
    x, y, h = cg
    b2 = bitola / 2
    # distancia do CG (em planta) a cada linha roda-esfera
    def dist(sy):
        p1, p2 = np.array([0.0, sy * b2]), np.array([L, 0.0])
        d = p2 - p1; n = np.array([-d[1], d[0]]) / np.linalg.norm(d)
        return abs(np.dot(np.array([x, y]) - p1, n))
    d_esq, d_dir = dist(1), dist(-1)
    a_tomb = min(d_esq, d_dir) / h                     # em g
    a_empina = x / h                                   # aceleracao que tira a esfera do chao (em g)
    carga_rodas = 1 - x / L
    a_trac = mu * carga_rodas                          # g
    a_freio = mu * carga_rodas / (1 + mu * h / L)      # transferencia de carga para a esfera ao frear
    return dict(d_tomb=min(d_esq, d_dir), a_tomb=a_tomb, a_empina=a_empina, carga_rodas=carga_rodas, a_trac=a_trac,
                a_freio=a_freio, assimetria=abs(d_esq - d_dir) / max(d_esq, d_dir))

# ------------------------------------------------------------------------------------------- motor e roda
def motor(d_roda_mm, volts=7.2):
    r = d_roda_mm / 2000
    w0 = v('motor_rpm_6v') * volts / 6 * 2 * math.pi / 60
    Ts = v('motor_stall_kgfcm') * 0.0980665 * volts / 6
    return dict(r=r, v0=w0 * r, F_stall=2 * Ts / r, rpm=w0 * 60 / 2 / math.pi)

def v_curva(R, mot, est, mu, bitola, v_ctrl=None):
    lim = dict(aderencia=math.sqrt(mu * G * R), tombamento=math.sqrt(0.9 * est['a_tomb'] * G * R),
               diferencial=0.97 * mot['v0'] / (1 + bitola / 2000 / R))
    if v_ctrl:
        lim['controle'] = v_ctrl
    k = min(lim, key=lim.get)
    return lim[k], k, lim

# ------------------------------------------------------------------------------------------- pista sintetica
def pista():
    """20 m: retas de 0,4 a 2 m e curvas de R100 a R500 (hipotese; a pista real e desconhecida)."""
    q = math.pi / 2
    seq = [(1.5, 0), (q * 0.1, 0.1), (0.6, 0), (q * 0.3, 0.3), (2.0, 0), (2 * q * 0.15, 0.15), (0.8, 0), (q * 0.1, 0.1),
           (0.4, 0), (q * 0.1, 0.1), (1.2, 0), (q * 0.5, 0.5), (1.0, 0), (2 * q * 0.2, 0.2), (0.5, 0), (q * 0.1, 0.1),
           (1.6, 0), (q * 0.25, 0.25), (0.7, 0), (2 * q * 0.1, 0.1), (1.1, 0), (q * 0.3, 0.3), (0.9, 0)]
    tot = sum(s[0] for s in seq)
    return [(L * 20 / tot, R) for L, R in seq]

def tempo_volta(massa_kg, mot, est, mu, bitola, v_ctrl=None, empinar=True, crr=0.05):
    ds = 0.005
    segs = pista()
    vlim = []
    for L, R in segs:
        n = max(1, int(L / ds))
        vmax = mot['v0'] * 0.97 if R == 0 else v_curva(R, mot, est, mu, bitola, v_ctrl)[0]
        if v_ctrl:
            vmax = min(vmax, v_ctrl)
        vlim += [vmax] * n
    vlim = np.array(vlim)
    a_lim = min(est['a_trac'], est['a_empina'] if empinar else 9) * G
    vel = np.zeros_like(vlim)
    for i in range(1, len(vlim)):                    # acelerando
        a = min(mot['F_stall'] * (1 - vel[i - 1] / mot['v0']) / massa_kg, a_lim) - crr * G
        vel[i] = min(vlim[i], math.sqrt(max(0, vel[i - 1] ** 2 + 2 * max(a, 0) * ds)))
    ab = est['a_freio'] * G
    for i in range(len(vlim) - 2, -1, -1):           # freando
        vel[i] = min(vel[i], math.sqrt(vel[i + 1] ** 2 + 2 * ab * ds))
    vel = np.maximum(vel, 0.05)
    return float(np.sum(ds / vel)), float(vel.max())

# ------------------------------------------------------------------------------------------- layouts
def layout_variantes(m):
    base = modelo.massas(m)
    P = m.P
    jet = {'jetson_placa', 'jetson_dissipador', 'jetson_usb', 'jetson_rj45', 'jetson_hdmi_dp'} | \
          {f'espacador_jetson_{i}' for i in range(1, 5)}
    def mover(lista, nomes, dx=0, dz=0, novo_x=None, novo_z=None):
        out = []
        for n, g, (x, y, z) in lista:
            if n in nomes or any(n.startswith(k) for k in nomes):
                x = novo_x if novo_x is not None else x + dx
                z = novo_z if novo_z is not None else z + dz
            out.append((n, g, (x, y, z)))
        return out
    var = {}
    # B: o modelo
    var['B'] = dict(massas=base, L=P['ESFERA_X'], compr=None, nome='B - v3: Jetson baixa sobre a bateria (escolhida)')
    # A: Jetson no andar de cima (acima da ESP32 sobre o eixo), bateria no piso no meio, XL atras
    zA = m.Z_ESP + 1.6 + v('esp_altura') + 3 + 3 + 6 - m.ZJ          # tampo acima da ESP32 + espacador
    a = mover(base, jet, dx=-25, dz=zA)
    a = mover(a, {'bateria'}, dz=-(m.Z2 - m.Z1), novo_x=55)
    a = mover(a, {'placa_esp32', 'esp32', 'barras', 'drv8833', 'c470', 'tampo', 'placa_desligar'}, dz=-6)
    var['A'] = dict(massas=a, L=137.0, compr=246.0, nome='A - v2.2 reconstruida: Jetson no andar de cima')
    # C: Jetson no piso (espacador de 6 mm), bateria atravessada na frente
    c = mover(base, jet, dz=-(P['JET_ESPACADOR'] - 6))
    c = mover(c, {'bateria'}, novo_x=146)
    var['C'] = dict(massas=c, L=P['ESFERA_X'] + 6, compr=None, nome='C - Jetson no piso, bateria atravessada na frente')
    return var

def relatorio(m, saida=None):
    P = m.P; mu = P['MU']; bit = P['BITOLA']
    linhas = []
    def w(s=''):
        linhas.append(s)
    from verificacoes import dimensoes
    dim = dimensoes(m)
    w('# Analise de arquitetura e rodas (gerada por `fonte/analise.py`)')
    w()
    w(f'Hipoteses: atrito pneu x tapete mu = {mu} (medir no T12), motores em 7,2 V, pista sintetica de 20 m com curvas de R100 a R500.')
    w('Massas e posicoes: as do modelo (`pecas.py`); nas variantes A e C so mudam de lugar a Jetson e a bateria.')
    w()
    w('## 1. Arquiteturas')
    w()
    w('| | massa (g) | CG x / y / z (mm) | peso nas rodas | tomba a (g) | empina a (g) | curva R100 (m/s) | limite | volta 20 m (s) | comprimento (mm) |')
    w('|---|---|---|---|---|---|---|---|---|---|')
    mot = motor(v('roda')[0])
    res = {}
    for k, var in sorted(layout_variantes(m).items()):
        M_, c = modelo.cg(var['massas'])
        est = estabilidade(c, var['L'], bit, mu)
        vc, lim, _ = v_curva(0.1, mot, est, mu, bit)
        t, vmax = tempo_volta(M_ / 1000, mot, est, mu, bit)
        compr = var['compr'] or (dim['comprimento'] + (12 if k == 'C' else 0))
        res[k] = (M_, c, est, vc, lim, t)
        w(f"| {var['nome']} | {M_:.0f} | {c[0]:.1f} / {c[1]:.1f} / {c[2]:.1f} | {est['carga_rodas'] * 100:.0f} % | "
          f"{est['a_tomb']:.2f} | {est['a_empina']:.2f} | {vc:.2f} | {lim} | {t:.1f} | {compr:.0f} |")
    w()
    w('* **tomba a**: aceleracao lateral que levanta uma roda (apoio em 3 pontos: o eixo de tombamento e a linha roda-esfera). '
      f'Tem de ficar acima de mu = {mu}; senao o carro tomba antes de escorregar.')
    w('* **empina a**: aceleracao para a frente que tira a esfera do chao (= x_CG / z_CG). Acima dela o carro levanta o nariz e a camera mexe.')
    w()
    w('## 2. Rodas (arquitetura B; trocar a roda sobe ou desce o carro inteiro)')
    w()
    w('| roda | v max em vazio (m/s) | forca de partida 2 motores (N) | z do CG (mm) | tomba a (g) | curva R100 (m/s) | limite | volta (s) | sem limite de empinar (s) | obs |')
    w('|---|---|---|---|---|---|---|---|---|---|')
    M_, c, est0 = res['B'][0], res['B'][1], res['B'][2]
    for d, mu_r, obs in ((32, 1.1, 'StickyMAX: eixo a 16 mm; esfera de 15 mm fica 5 mm alta (precisa outra esfera)'),
                         (42, mu, 'atual (4 compradas); esfera de 15 mm encaixa sem calco'),
                         (48, mu, 'eixo 3 mm mais alto; nao comprada'),
                         (65, mu, 'eixo 11,5 mm mais alto; vao livre e CG sobem')):
        mt = motor(d)
        cz = c.copy(); cz[2] += (d - 42) / 2
        e = estabilidade(cz, P['ESFERA_X'], bit, mu_r)
        vc, lim, _ = v_curva(0.1, mt, e, mu_r, bit)
        t, _ = tempo_volta(M_ / 1000, mt, e, mu_r, bit)
        t2, _ = tempo_volta(M_ / 1000, mt, e, mu_r, bit, empinar=False)
        w(f'| {d} mm (mu {mu_r}) | {mt["v0"]:.2f} | {mt["F_stall"]:.1f} | {cz[2]:.1f} | {e["a_tomb"]:.2f} | {vc:.2f} | {lim} | {t:.1f} | {t2:.1f} | {obs} |')
    w()
    w('## 3. Limite real: controle e visao')
    w()
    w('Com a roda de 42 mm, tempo de volta conforme o teto de velocidade que a visao/controle aguentar:')
    w()
    w('| teto de velocidade (m/s) | volta 20 m (s) |')
    w('|---|---|')
    for vct in (0.6, 0.8, 1.0, 1.2, 1.5, None):
        t, _ = tempo_volta(M_ / 1000, mot, est0, mu, bit, v_ctrl=vct)
        w(f'| {vct if vct else "sem teto"} | {t:.1f} |')
    w()
    f_ader = mu * M_ / 1000 * G * est0['carga_rodas']
    w(f'Leitura: enquanto o carro nao passar de ~1,2 m/s com seguranca, a roda nao e o gargalo; a de 42 mm tem folga '
      f'de velocidade ({mot["v0"]:.2f} m/s em vazio) e de torque (forca de partida {mot["F_stall"]:.0f} N contra '
      f'{f_ader:.1f} N que o pneu consegue passar ao chao: {mot["F_stall"] / f_ader:.0f}x).')
    w()
    w('## 4. Sensibilidade ao atrito (medir no T12)')
    w()
    w('| mu | escorrega com (g) | tomba com (g) | margem | velocidade segura em R100 (m/s) | o que fazer |')
    w('|---|---|---|---|---|---|')
    for mu_s in (0.7, 0.9, 1.0, 1.1, 1.3):
        e = estabilidade(c, P['ESFERA_X'], bit, mu_s)
        vc, lim, _ = v_curva(0.1, mot, e, mu_s, bit)
        marg = e['a_tomb'] / mu_s
        acao = 'nada' if marg >= 1.15 else ('limitar a velocidade na curva por software' if marg >= 0.95 else
                                            'limitar a velocidade na curva por software (obrigatorio)')
        w(f'| {mu_s} | {mu_s:.2f} | {e["a_tomb"]:.2f} | {marg:.2f} | {vc:.2f} ({lim}) | {acao} |')
    w()
    w('Se o pneu agarrar mais que mu ~ 1,0, o carro tomba antes de escorregar numa curva de R100 feita rapido demais. '
      'A protecao e de software: velocidade maxima na curva de ~0,9 m/s (o controle ja reduz a velocidade com o erro).')
    texto = '\n'.join(linhas) + '\n'
    if saida:
        open(saida, 'w').write(texto)
    return texto, res

if __name__ == '__main__':
    m = modelo.construir()
    print(relatorio(m, sys.argv[1] if len(sys.argv) > 1 else None)[0])
