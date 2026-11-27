"""Modelo parametrico do chassi v4 do Robocar Blitz: 3 andares, MDF 3 mm cortado a laser.

  ANDAR 1 (piso): motores no eixo, os 2 XL4016 a frente do eixo, bateria atravessada atras (sai pela direita)
  ANDAR 2: Jetson de travessa (100 mm na largura), portas para TRAS; faixa de tras com chave, fusivel e
           placa de desligar
  ANDAR 3: placa da ESP32 (botao de largada, USB e LEDs em cima); mastro curto da camera na frente
Por que (D-031): comprimento. Empilhar tira ~70 mm do carro e os plugues da Jetson saem para tras, dentro do
comprimento, em vez de alargar o carro. Custo: CG mais alto (ver analise.md e a verificacao de tombamento).

construir(P) devolve um Modelo com chapas, compradas, acessos, cabos e apoios (mesma interface do v3).
Eixos: x para a FRENTE (0 = eixo das rodas), y para a ESQUERDA, z para CIMA (0 = chao). mm.
"""
import json
import os
import math
import numpy as np
import shapely.geometry as sg
import shapely.ops as so
import cadquery as cq
from pecas import v
from geometria import (ret, ret_c, circ, oblongo, rasgo, arco_rasgo, Furo, Chapa, frame, F_xy, F_xz, F_yz,
                       F_rot_y, aplicar, loc, caixa, cilindro, caixa_local, comprimento)

# ======================================================================================== parametros
PADRAO = dict(
    T=3.0,                 # espessura MEDIDA da chapa
    FOLGA=-0.1,            # rasgo = T + FOLGA (escolher pelo pente de teste)
    BITOLA=124.0,          # centro a centro das rodas (mais larga que no v3: CG mais alto pede base mais larga)
    FOLGA_RODA_REDUTOR=1.5,
    XL_X0=30.0,            # ponta dos bornes dos XL4016 (virada para o eixo); trimpots na ponta da frente
    XL_ESPACADOR=4.0,
    XL_Y=(2.0, -2.0),      # borda interna de cada XL (esquerdo, direito)
    AR_ANDAR2=4.0,         # vao entre o topo dos XL4016 e o andar 2
    BAT_X0=-46.0,          # bateria atras da roda: ela sai pela direita sem passar pelo pneu          # bateria atravessada: x de tras (a frente fica a 1,5 mm do suporte do motor)
    J0=0.0,                # borda das portas da Jetson (tras) em x
    JET_ESPACADOR=5.0,     # espacador M2.5 entre o andar 2 e a Jetson
    AR_DISSIPADOR=12.0,    # vao entre o topo do dissipador e o andar 3 (cabe ventoinha 4010)
    ESP_X1=50.0,           # borda da frente da placa da ESP32 (pontos dos motores) em x
    ESP_ESPACADOR=5.0,
    ESFERA_X=94.0,         # esfera girada 90 graus: parafusos alinhados com x, entre os 2 XL4016
    PIVO=(86.0, 146.0),    # eixo de giro da camera (x, z)
    CAM_ANG=(25.0, 65.0),
    CAM_ANG_NOMINAL=45.0,
    CAM_C=-17.0,
    MESA=(390.0, 270.0),
    MIN_TEIA=2.0,
    MU=0.9,
    CABO_FOLGA=0.10,
    LASTRO=None,
    TRIMPOT_CHAVE=40.0,
    PF3_MOTOR=(53.5, 30.0),  # passa-fio dos motores no andar 3 (x, |y|): na frente da placa da ESP32, longe da placa de interface    # comprimento livre para a chave de fenda acima do andar 2 (chave curta)
    PILARES=((-14.0, 6.0), (50.0, 70.0)),   # x dos pilares andar 2 -> 3 (aba numa ponta, porca presa na outra)
    ESFERA_MARGEM=2.5,     # material entre o furo da esfera e a borda da frente
    CHAVE_Y=28.0,          # centro do recorte da chave na parede de tras do berco
    A_LAT_MAX=0.65,        # aceleracao lateral maxima permitida por software (g): R100 a <= 0,80 m/s (D-032)
)

class Modelo:
    pass

def construir(P=None, verif=False):
    P = dict(PADRAO, **(P or {}))
    T = P['T']
    S = T if verif else T + P['FOLGA']
    m = Modelo(); m.P = P; m.T = T; m.S = S
    chapas, compradas, acessos, cabos, apoios = [], [], [], [], {}
    m.chapas, m.compradas, m.acessos, m.cabos, m.apoios = chapas, compradas, acessos, cabos, apoios

    def comprada(nome, solido, massa=0.0, cat='eletronica', cor=(0.5, 0.5, 0.5), grupo=None):
        compradas.append(dict(nome=nome, solido=solido, massa=massa, cat=cat, cor=cor, grupo=grupo or nome))

    def acesso(nome, solido, funcao, ignora=()):
        acessos.append(dict(nome=nome, solido=solido, funcao=funcao, ignora=set(ignora)))

    def abracadeira(lista, nome, x, y, ang=0, dist=6.0):
        c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for d in (-dist / 2, dist / 2):
            lista.append(Furo(sg.Polygon([(x + d * c + p * 0.75 * -s_ + q * 1.75 * c, y + d * s_ + p * 0.75 * c + q * 1.75 * s_)
                                          for p, q in ((-1, -1), (1, -1), (1, 1), (-1, 1))]).convex_hull, nome,
                              funcao='abracadeira'))

    # ---------------------------------------------------------------------------- rodas, motores
    RD, RL = v('roda'); EZ = RD / 2
    YR = P['BITOLA'] / 2
    Y_PNEU_IN = YR - RL / 2
    Y_RED = Y_PNEU_IN - P['FOLGA_RODA_REDUTOR']
    sx, sy, sz = v('sup_motor')
    Z1 = EZ - v('sup_motor_eixo_z'); Z0 = Z1 - T; Z2 = Z1 + T
    Y_SUP = Y_RED - sy / 2
    Y_FIM = Y_RED - v('motor_corpo')
    m.Z0, m.Z1, m.Z2, m.EZ, m.YR = Z0, Z1, Z2, EZ, YR
    for s, lado in ((1, 'esq'), (-1, 'dir')):
        def yy(a, b):
            return (min(s * a, s * b), max(s * a, s * b))
        g = f'motor_{lado}'
        comprada(f'roda_{lado}', cq.Workplane('XZ').circle(RD / 2).extrude(RL / 2, both=True).val().translate((0, s * YR, EZ)),
                 v('roda_massa'), 'roda', (0.12, 0.12, 0.12), g)
        y0, y1 = yy(Y_RED - 9, Y_RED)
        comprada(f'redutor_{lado}', caixa(-6, 6, y0, y1, EZ - 5, EZ + 5), 0, 'redutor', (0.8, 0.65, 0.2), g)
        comprada(f'eixo_{lado}', cilindro((0, s * Y_RED, EZ), (0, s * (Y_RED + v('motor_eixo')), EZ), 3), 0, 'redutor',
                 (0.7, 0.7, 0.7), g)
        comprada(f'motor_{lado}', cilindro((0, s * (Y_RED - 9), EZ), (0, s * (Y_FIM + 11), EZ), 12), v('motor_massa'),
                 'eletronica', (0.6, 0.6, 0.62))
        y0, y1 = yy(Y_FIM, Y_FIM + 11)
        comprada(f'encoder_{lado}', caixa(-6, 6, y0, y1, Z1 + 0.5, EZ + 6), 0, 'eletronica', (0.1, 0.4, 0.15), g)
        y0, y1 = yy(Y_FIM, Y_FIM + 5)
        comprada(f'conector_motor_{lado}', caixa(-5, 5, y0, y1, EZ + 6, EZ + 12), 0, 'conector', (0.95, 0.95, 0.95), g)
        y0, y1 = yy(Y_SUP - sy / 2, Y_SUP + sy / 2)
        comprada(f'suporte_motor_{lado}', caixa(-sx / 2, sx / 2, y0, y1, Z1, Z1 + sz), 2.0, 'estrutura', (0.95, 0.95, 0.95), g)

    # ---------------------------------------------------------------------------- ANDAR 1: XL4016 (2x) a frente do eixo
    XL_L, XL_W = v('xl'); XL_H = v('xl_altura')
    XL0 = P['XL_X0']
    Z_XL = Z2 + P['XL_ESPACADOR']
    xl_y0 = (P['XL_Y'][0], P['XL_Y'][1] - XL_W)          # y da borda w = 0 (l para +x, w para +y)
    def xl_pt(k, l, w):
        return (XL0 + l, xl_y0[k] + w)
    m.xl_pt = xl_pt
    nomes_xl = ('xl4016_1_jetson', 'xl4016_2_motores')
    for k in range(2):
        ya, yb = xl_y0[k], xl_y0[k] + XL_W
        comprada(nomes_xl[k], caixa(XL0, XL0 + XL_L, ya, yb, Z_XL, Z_XL + XL_H), v('xl_massa'), 'eletronica', (0.2, 0.45, 0.3))
        l0, l1, hb = v('xl_bornes')
        comprada(f'bornes_xl{k + 1}', caixa(XL0 + l0, XL0 + l1, ya + 9, yb - 9, Z_XL + 1.6, Z_XL + 1.6 + hb), 0, 'conector',
                 (0.1, 0.3, 0.8), nomes_xl[k])
        for (l, w) in v('xl_furos'):
            x, y = xl_pt(k, l, w)
            comprada(f'espacador_xl{k + 1}_{l:.0f}_{w:.0f}', cilindro((x, y, Z2), (x, y, Z_XL), 5.5), 0.5, 'fixacao',
                     (0.9, 0.9, 0.85), nomes_xl[k])
    m.Z_XL_TOPO = Z_XL + XL_H
    ZA2 = m.Z_XL_TOPO + P['AR_ANDAR2']                   # fundo do andar 2
    ZA2t = ZA2 + T
    m.ZA2 = ZA2
    for k in range(2):
        for j, (l, w) in enumerate(v('xl_trimpots')):
            x, y = xl_pt(k, l, w)
            acesso(f'chave_trimpot_xl{k + 1}_{j + 1}', cilindro((x, y, Z_XL + XL_H - 3), (x, y, ZA2t + P['TRIMPOT_CHAVE']), 5.0),
                   'regular o trimpot com chave de fenda curta pelo furo do andar 2', ignora=(nomes_xl[k],))

    # ---------------------------------------------------------------------------- ANDAR 1: bateria atravessada atras
    BL, BW, BH = v('bat')
    BX0 = P['BAT_X0']; BX1 = BX0 + BW
    BY0, BY1 = -BL / 2 - 2.0, BL / 2 - 2.0                    # sai pela DIREITA (-y)
    comprada('bateria', caixa(BX0, BX1, BY0, BY1, Z1, Z1 + BH), v('bat_massa'), 'eletronica', (0.95, 0.75, 0.15))
    acesso('caminho_bateria', caixa(BX0 + 0.3, BX1 - 0.3, BY0 - 90, BY1 - 1, Z1 + 0.3, Z1 + BH - 0.3),
           'tirar a bateria pela direita (deslizando 90 mm)', ignora=('bateria', 'pino_trava', 'par_xt60'))
    PAR_T0 = BX0 - 0.75 - T                                  # parede de tras do berco (y-z), ate o andar 2
    PAR_F0 = BX1 + 0.75                                      # parede da frente do berco (y-z)
    m.BX0, m.BX1 = BX0, BX1
    PINO = (BY0 - 2.5, Z1 + 4.0)                             # (y, z): pino atravessa as 2 paredes do berco
    comprada('pino_trava', cilindro((PAR_T0 - 6, PINO[0], PINO[1]), (PAR_F0 + T + 1, PINO[0], PINO[1]), 3.0), 1.0, 'fixacao',
             (0.7, 0.7, 0.7))
    acesso('dedo_pino_trava', caixa(PAR_T0 - 18, PAR_T0 - 6, PINO[0] - 5, PINO[0] + 5, Z1 + 0.5, PINO[1] + 8),
           'puxar o pino de trava da bateria (por tras)', ignora=('pino_trava',))
    xl6, xw6, xh6 = v('xt60')
    XT_L = 26.0                                              # par XT60 encaixado EM PE na ponta direita da bateria
    XTY0 = BY0 - 5.0 - xh6
    comprada('par_xt60', caixa(BX0 + 2, BX0 + 2 + xw6, XTY0, XTY0 + xh6, Z1 + 1, Z1 + 1 + XT_L), 8.0, 'conector', (0.95, 0.8, 0.1))
    m.XTY0 = XTY0

    # ---------------------------------------------------------------------------- dimensoes gerais
    Y_PAR = 55.0                       # face interna das paredes laterais
    Y_PISO = Y_PAR + T + 2.5
    X_TRAS = PAR_T0 - 3.0              # borda de tras do piso traseiro
    X_FRENTE = P['ESFERA_X'] + v('esfera_furos') / 2 + 1.4 + P['ESFERA_MARGEM']   # borda da frente logo alem do furo da esfera
    Y_EIXO = Y_PNEU_IN - 1.5
    m.X_TRAS, m.X_FRENTE = X_TRAS, X_FRENTE

    # ---------------------------------------------------------------------------- ANDAR 2: Jetson de travessa, portas para tras
    JW, JD, JT = v('jet_placa'); J0 = P['J0']
    ZJ = ZA2t + P['JET_ESPACADOR']
    def jet_pt(u, vv):                 # v = 0 (portas) em x = J0 (tras); u = 0 (P4) a ESQUERDA (y = +50)
        return (J0 + vv, JW / 2 - u)
    m.jet_pt, m.ZJ = jet_pt, ZJ
    def caixa_jet(u0, u1, v0, v1, z0, z1):
        (xa, ya), (xb, yb) = jet_pt(u0, v0), jet_pt(u1, v1)
        return caixa(min(xa, xb), max(xa, xb), min(ya, yb), max(ya, yb), ZJ + z0, ZJ + z1)
    comprada('jetson_placa', caixa_jet(0, JW, 0, JD, 0, JT), v('jet_massa') * 0.35, 'eletronica', (0.25, 0.5, 0.3), 'jetson')
    comprada('jetson_solda', caixa_jet(2, JW - 2, 2, JD - 2, -2.5, 0), 0, 'eletronica', (0.25, 0.5, 0.3), 'jetson')
    du0, du1, dv0, dv1 = v('jet_dissipador')
    comprada('jetson_dissipador', caixa_jet(du0, du1, dv0, dv1, 6, v('jet_altura')), v('jet_massa') * 0.45, 'eletronica',
             (0.3, 0.32, 0.35), 'jetson')
    for nome, (a, b), h in (('jetson_usb', v('jet_usb_u'), 17), ('jetson_rj45', v('jet_rj45_u'), 14),
                            ('jetson_hdmi_dp', v('jet_hdmi_dp_u'), 8)):
        comprada(nome, caixa_jet(a, b, -1.5, 15, JT, JT + h), v('jet_massa') * 0.05, 'conector', (0.7, 0.7, 0.72), 'jetson')
    pu = v('jet_p4_u')
    comprada('jetson_j25', caixa_jet(pu - 4.5, pu + 4.5, -1.5, 13, JT, JT + 11), 0, 'conector', (0.1, 0.1, 0.1), 'jetson')
    a, b = v('jet_j41_u')
    comprada('jetson_j41', caixa_jet(a, b, JD - 6.5, JD - 1.5, JT, JT + 8.5), 0, 'conector', (0.1, 0.1, 0.1), 'jetson')
    a, b = v('jet_csi_u')
    comprada('jetson_csi', caixa_jet(a, b, 45, 72, JT, JT + 5), 0, 'conector', (0.9, 0.9, 0.9), 'jetson')
    pl, pd = v('p4_plugue')
    xp, yp = jet_pt(pu, 0)
    zp4 = ZJ + JT + 6
    comprada('plugue_p4', cilindro((xp + 1.5, yp, zp4), (xp - pl, yp, zp4), pd), 0, 'plugue', (0.3, 0.3, 0.3), 'jetson')
    ul, uw, uh = v('usb_a_plugue')
    a, b = v('jet_usb_u')
    xu2, yu2 = jet_pt((a + b) / 2, 0)
    comprada('plugue_usb_a', caixa(xu2 - ul, xu2 + 1.5, yu2 - uw / 2, yu2 + uw / 2, ZJ + JT + 2, ZJ + JT + 2 + uh), 0, 'plugue',
             (0.3, 0.3, 0.3), 'jetson')
    m.p4_fim = (xp - pl, yp, zp4); m.usb_a_fim = (xu2 - ul, yu2, ZJ + JT + 2 + uh / 2)
    a, b = v('jet_sd_u')
    (xa, ya), (xb, yb) = jet_pt(a, JD), jet_pt(b, JD)
    acesso('dedo_microsd', caixa(J0 + JD - 1, J0 + JD + 16, min(ya, yb), max(ya, yb), ZJ + 1, ZJ + 9),
           'tirar e por o microSD da Jetson (pela frente, entre os andares 2 e 3)',
           ignora=('jetson_placa', 'jetson_solda', 'jetson_dissipador', 'jetson_j41', 'jetson_csi'))
    jfb = v('jet_furos_borda'); jfd = v('jet_furo_d')
    dxu, dxv = jfb[0] - jfd, jfb[1] - jfd
    fu0 = v('jet_furo_u0') if v('jet_furo_u0') is not None else (JW - dxu) / 2
    fv0 = v('jet_furo_v0') if v('jet_furo_v0') is not None else (JD - dxv) / 2
    m.jet_uv_furos = [(u, vv) for u in (fu0, fu0 + dxu) for vv in (fv0, fv0 + dxv)]
    m.jet_furos = [jet_pt(u, vv) for u, vv in m.jet_uv_furos]
    for i, (x, y) in enumerate(m.jet_furos):
        comprada(f'espacador_jetson_{i + 1}', cilindro((x, y, ZA2t), (x, y, ZJ), 5.0), 1.0, 'fixacao', (0.9, 0.9, 0.85), 'jetson')
    Z_DISS = ZJ + v('jet_altura')
    ZA3 = Z_DISS + P['AR_DISSIPADOR']                   # fundo do andar 3
    ZA3t = ZA3 + T
    m.ZA3 = ZA3
    acesso('ar_dissipador', caixa_jet(du0, du1, dv0, dv1, v('jet_altura'), v('jet_altura') + 11.0),
           'vao de 11 mm em cima do dissipador: ar e espaco para ventoinha 4010 (10 mm)')

    # faixa de tras do andar 2: chave, fusivel, placa de desligar
    cr_w, cr_h = v('chave_recorte'); c_w, c_h, c_d = v('chave_corpo')
    # chave na parede de TRAS do berco, virada para tras; o corpo fica dentro do berco, por cima da bateria
    CHY = P['CHAVE_Y']; CHZ = ZA2 - 2.5 - cr_h / 2
    CHX = PAR_T0 + T + c_d / 2
    comprada('chave_geral', caixa(PAR_T0 - 0.01, PAR_T0 + T + c_d, CHY - cr_w / 2 + 0.3, CHY + cr_w / 2 - 0.3, CHZ - cr_h / 2 + 0.3,
                                  CHZ + cr_h / 2 - 0.3), 4.0, 'eletronica', (0.1, 0.1, 0.1))
    comprada('chave_moldura', caixa(PAR_T0 - 3, PAR_T0, CHY - c_w / 2, CHY + c_w / 2, CHZ - c_h / 2, CHZ + c_h / 2), 0,
             'eletronica', (0.1, 0.1, 0.1), 'chave_geral')
    acesso('dedo_chave', caixa(PAR_T0 - 15, PAR_T0 - 3, CHY - 8, CHY + 8, CHZ - 6, CHZ + 6), 'ligar e desligar a chave geral (por tras)',
           ignora=('chave_geral',))
    fw, fl, fh = v('fus_placa')
    FX0, FY0 = X_TRAS + 3.0, -6.0                        # entre os plugues USB (y < -14) e P4 (y > 36)
    comprada('placa_fusivel', caixa(FX0, FX0 + fw, FY0, FY0 + fl, ZA2t, ZA2t + fh), v('fus_massa'), 'eletronica',
             (0.15, 0.4, 0.55))
    acesso('dedo_fusivel', caixa(FX0 + 3, FX0 + 15, FY0 + 5, FY0 + fl - 5, ZA2t + fh, ZA2t + fh + 25),
           'trocar o fusivel por cima, atras do andar 3', ignora=('placa_fusivel',))
    m._desl_pendente = True

    # ---------------------------------------------------------------------------- ANDAR 3: placa da ESP32
    EW, EL, ET = v('esp_placa'); EX1 = P['ESP_X1']
    Z_ESP = ZA3t + P['ESP_ESPACADOR']
    def esp_pt(u, vv):                 # orientacao da D-024: borda v = 0 (motores) para a frente
        return (EX1 - vv, EW / 2 - u)
    m.esp_pt, m.Z_ESP = esp_pt, Z_ESP
    def caixa_esp(u0, u1, v0, v1, z0, z1):
        (xa, ya), (xb, yb) = esp_pt(u0, v0), esp_pt(u1, v1)
        return caixa(min(xa, xb), max(xa, xb), min(ya, yb), max(ya, yb), z0, z1)
    comprada('placa_esp32', caixa_esp(0, EW, 0, EL, Z_ESP, Z_ESP + ET), v('esp_massa'), 'eletronica', (0.2, 0.45, 0.25))
    zt = Z_ESP + ET
    u0, u1, v0, v1 = v('esp_devkit')
    comprada('esp32_devkit', caixa_esp(u0, u1, v0, v1, zt + 8.5, zt + v('esp_altura')), 0, 'eletronica', (0.1, 0.1, 0.12),
             'placa_esp32')
    comprada('barras_esp32', caixa_esp(u0 + 1, u1 - 1, v0 + 6, v1 - 10, zt, zt + 8.5), 0, 'eletronica', (0.15, 0.15, 0.15),
             'placa_esp32')
    for nome, (a0, a1, b0, b1) in (('drv8833_esq', (4.5, 20.8, 10.4, 28.8)), ('drv8833_dir', (55.9, 72.2, 10.4, 28.8))):
        comprada(nome, caixa_esp(a0, a1, b0, b1, zt, zt + 11.5), 0, 'eletronica', (0.6, 0.1, 0.1), 'placa_esp32')
    for nome, (cu, cv) in (('c470_esq', (7.9, 56.3)), ('c470_dir', (76.8, 56.3))):
        x, y = esp_pt(cu, cv)
        comprada(nome, cilindro((x, y, zt), (x, y, zt + 12), 8), 0, 'eletronica', (0.2, 0.2, 0.6), 'placa_esp32')
    xu, yu = esp_pt((u0 + u1) / 2, v1)
    zu = zt + 8.5 + 1.6 + 1.6
    upl, upw, uph = v('esp_usb_plugue')
    comprada('plugue_usb_esp32', caixa(xu - upl, xu, yu - upw / 2, yu + upw / 2, zu - uph / 2, zu + uph / 2), 0, 'plugue',
             (0.3, 0.3, 0.3), 'placa_esp32')
    acesso('dedo_botao_largada', cilindro((*esp_pt(60, 48), zt + 6), (*esp_pt(60, 48), zt + 60), 14),
           'apertar o botao de largada (J14) por cima', ignora=('placa_esp32',))
    acesso('dedo_en_boot_esp32', cilindro((xu + 6, yu, zt + 11), (xu + 6, yu, zt + 60), 12),
           'botoes EN/BOOT da ESP32 (gravacao)', ignora=('esp32_devkit', 'barras_esp32'))
    m.esp_usb = (xu, yu, zu)
    # placa de interface (D-028/D-033): andar 3, faixa direita ao lado da ESP32. Posicao de cada peca e dos furos vem do
    # desenho furo a furo (hardware/placa_desligar/layout.json, gerado e verificado por layout.py)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'hardware', 'placa_desligar',
                           'layout.json')) as f_:
        LY = json.load(f_)
    dw, dl, _ = LY['placa']
    DX0, DY1 = 8.0, -(EW / 2 + 1.0)                      # canto de tras / de dentro
    lp = lambda uw: (DX0 + uw[0], DY1 - uw[1])           # (u, w) do layout -> (x, y) no carro
    comprada('placa_desligar', caixa(DX0, DX0 + dw, DY1 - dl, DY1, ZA3t + 3, ZA3t + 4.6), 4.0, 'eletronica', (0.15, 0.4, 0.55))
    zbd = ZA3t + 4.6
    bx, by = lp(LY['botao'])
    m.desl_botao = (bx, by, zbd)
    comprada('botao_desligar', caixa(bx - 3, bx + 3, by - 3, by + 3, zbd, zbd + 13), 0, 'eletronica', (0.1, 0.1, 0.1),
             'placa_desligar')
    for nome_, chave_, cor_ in (('led_pode_desligar', 'led_vermelho', (0.9, 0.1, 0.1)),
                                ('led_codigo_rodando', 'led_amarelo', (0.95, 0.75, 0.1))):
        lx, ly_ = lp(LY[chave_])
        comprada(nome_, cilindro((lx, ly_, zbd), (lx, ly_, zbd + 8), 3), 0, 'eletronica', cor_, 'placa_desligar')
    for nome_, chave_, cor_ in (('j1_interface', 'j1', (0.1, 0.1, 0.1)), ('j2_luz', 'j2', (0.9, 0.9, 0.9))):
        jj = LY[chave_]; jx, jy = lp(jj['centro'])
        comprada(nome_, caixa(jx - jj['lu'] / 2, jx + jj['lu'] / 2, jy - jj['lw'] / 2, jy + jj['lw'] / 2, zbd,
                              zbd + jj['altura']), 0, 'eletronica', cor_, 'placa_desligar')
    jx, jy = lp(LY['j1']['centro'])
    m.desl_j1 = (jx, jy, zbd + LY['j1']['altura'] + 3.0)
    acesso('dedo_botao_desligar', cilindro((bx, by, zbd + 13), (bx, by, zbd + 50), 12), 'apertar o botao de desligar a Jetson')
    m.desl_furos = [lp(LY['furos_m3'][k]) for k in ('MH1', 'MH2')]

    # ---------------------------------------------------------------------------- esfera
    ex_, ey_ = v('esfera_corpo'); EH = v('esfera_altura'); EXX = P['ESFERA_X']
    comprada('esfera_base', caixa(EXX - ey_ / 2, EXX + ey_ / 2, -ex_ / 2, ex_ / 2, Z1 - EH + 9.525, Z1), v('esfera_massa'),
             'estrutura', (0.3, 0.3, 0.3), 'esfera')
    comprada('esfera_bola', cq.Solid.makeSphere(9.525 / 2, cq.Vector(EXX, 0, Z1 - EH + 9.525 / 2)), 0, 'estrutura',
             (0.75, 0.75, 0.75), 'esfera')
    m.esfera_z_chao = Z1 - EH

    # ======================================================================================== CHAPAS
    X_LAP0, X_LAP1 = 13.0, 30.0
    X_LARGO = -(EZ + 2.0)
    # ---------------------------------------------------------------------------- piso traseiro (z Z0..Z1)
    base_t = so.unary_union([ret(X_TRAS, -Y_PISO, X_LARGO, Y_PISO), ret(X_LARGO - 1, -Y_EIXO, X_LAP1, Y_EIXO)])
    ft = []
    for sy_ in (1, -1):
        for sx_ in (1, -1):
            ft.append(oblongo((sx_ * 8.5, sy_ * Y_SUP), (sx_ * 10.8, sy_ * Y_SUP), 2.3, 'suporte_motor', 'parafuso M2 do suporte'))
    ys_berco = [-40.0, 0.0, 40.0]
    for xw in (PAR_T0, PAR_F0):
        for yc in ys_berco:
            ft.append(Furo(ret_c(xw + T / 2, yc, S, 10), 'parede_berco', funcao='encaixe'))
    xs_pl_t = [PAR_T0 + T + 6.0]
    ft.append(rasgo(xs_pl_t[0], Y_PAR + T / 2, 10, S, 'parede_lateral'))           # so a esquerda: a bateria sai pela direita
    lap_paraf = [(22.0, 24.0), (22.0, -24.0)]
    for (x, y) in lap_paraf:
        ft.append(circ(x, y, 3.4, 'parafuso_pisos', 'passagem (o mesmo parafuso do piso dianteiro)'))
    chapas.append(Chapa('piso_traseiro', base_t, ft, frames=[F_xy(Z0)],
                        textos=[('PISO TRASEIRO >', (PAR_T0 + PAR_F0) / 2 + 1.5, -20, 2.5)], descricao='motores e berco da bateria'))

    # ---------------------------------------------------------------------------- piso dianteiro (z Z1..Z2)
    base_f = so.unary_union([ret(X_LAP0, -Y_EIXO, 24.5, Y_EIXO), ret(23.5, -Y_PISO, X_FRENTE - 12, Y_PISO),
                             sg.Polygon([(X_FRENTE - 12, -Y_PISO), (X_FRENTE, -30), (X_FRENTE, 30), (X_FRENTE - 12, Y_PISO)])])
    ff = []
    for (x, y) in lap_paraf:
        ff.append(circ(x, y, 3.4, 'parafuso_pisos', 'parafuso M3 que une os pisos'))
    for k in range(2):
        for (l, w) in v('xl_furos'):
            x, y = xl_pt(k, l, w)
            ff.append(circ(x, y, 3.4, f'xl{k + 1}', 'parafuso M3 do XL4016'))
    XPF0, XPF1 = 26.0, X_FRENTE - 14.0
    xs_pf = [XPF0 + 8, (XPF0 + XPF1) / 2, XPF1 - 8]
    xs_topo_pf = [XPF0 + 10, XPF1 - 6.5]                # abas de cima das paredes da frente
    for sy_ in (1, -1):
        for xc in xs_pf:
            ff.append(rasgo(xc, sy_ * (Y_PAR + T / 2), 10, S, 'parede_frente'))
    eh = v('esfera_furos') / 2
    ff += [circ(EXX - eh, 0, 2.8, 'esfera', 'parafuso M2.5 da esfera'), circ(EXX + eh, 0, 2.8, 'esfera', 'parafuso M2.5 da esfera')]
    chapas.append(Chapa('piso_dianteiro', base_f, ff, frames=[F_xy(Z1)],
                        textos=[('PISO DIANTEIRO  FRENTE >', 60, 0, 3.0)], descricao='XL4016 e esfera'))

    # ---------------------------------------------------------------------------- paredes do andar 1 (sustentam o andar 2)
    H1 = ZA2 - Z1
    # paredes do berco (y-z), largura total; a de tras e a de frente tem o furo do pino de trava
    ys_tab_topo = [-40.0, 0.0, 40.0]
    for nome, xw in (('parede_berco_tras', PAR_T0), ('parede_berco_frente', PAR_F0)):
        yb_ = Y_PISO
        base_pb = ret(-yb_, Z1, yb_, ZA2)
        abas = [ret_c(yc, Z1 - T / 2, 10, T) for yc in ys_berco] + [ret_c(yc, ZA2 + T / 2, 10, T) for yc in ys_tab_topo]
        fpb = [circ(PINO[0], PINO[1], 3.3, 'pino_trava', 'pino que trava a bateria (tirar com a mao)')]
        fpb.append(rasgo(Y_PAR + T / 2, Z1 + H1 / 2, S, 10, 'parede_lateral'))
        if 'tras' in nome:
            fpb.append(Furo(ret_c(CHY, CHZ, cr_w, cr_h), 'chave', funcao='chave geral'))
        if nome == 'parede_berco_frente':
            fpb.append(Furo(ret(-24.0, Z1 + BH + 3, 24.0, ZA2 - 4), 'janela_fios', funcao='fios do andar 1 para tras (chave, fusivel)'))
            apoios['janela_berco'] = (PAR_F0 + T / 2, 0.0, (Z1 + BH + 3 + ZA2 - 4) / 2)
        chapas.append(Chapa(nome, base_pb, fpb, abas, frames=[F_yz(xw)], textos=[('TRAS' if 'tras' in nome else 'BERCO', 0, Z1 + 6, 2.5)],
                            descricao='berco da bateria e apoio do andar 2'))
    # parede lateral esquerda do berco (x-z) - fecha a bateria a esquerda
    base_pl = ret(PAR_T0 + T, Z1, PAR_F0, ZA2)
    abas_pl = [ret_c(xs_pl_t[0], Z1 - T / 2, 10, T), ret_c(xs_pl_t[0], ZA2 + T / 2, 10, T),
               ret(PAR_T0, Z1 + H1 / 2 - 5, PAR_T0 + T, Z1 + H1 / 2 + 5), ret(PAR_F0, Z1 + H1 / 2 - 5, PAR_F0 + T, Z1 + H1 / 2 + 5)]
    chapas.append(Chapa('parede_berco_esq', base_pl, [], abas_pl, frames=[F_xz(Y_PAR + T)], descricao='batente esquerdo da bateria'))
    # paredes laterais da frente (x-z), 2x
    base_pf = ret(XPF0, Z2, XPF1, ZA2)
    abas_pf = [ret_c(xc, Z2 - T / 2, 10, T) for xc in xs_pf] + [ret_c(xc, ZA2 + T / 2, 10, T) for xc in xs_topo_pf]
    ent_pf = []
    xs_porca2 = [46.0, 74.0]                             # porcas presas do andar 2 (longe das abas e dos pilares)
    def porca(xc, ztop):
        return sg.Polygon([(xc - 1.6, ztop + 0.01), (xc - 1.6, ztop - 4.5), (xc - 2.9, ztop - 4.5), (xc - 2.9, ztop - 7.1),
                           (xc - 1.6, ztop - 7.1), (xc - 1.6, ztop - 11), (xc + 1.6, ztop - 11), (xc + 1.6, ztop - 7.1),
                           (xc + 2.9, ztop - 7.1), (xc + 2.9, ztop - 4.5), (xc + 1.6, ztop - 4.5), (xc + 1.6, ztop + 0.01)])
    for xc in xs_porca2:
        ent_pf.append(porca(xc, ZA2))
    chapas.append(Chapa('parede_frente', base_pf, [], abas_pf, ent_pf, frames=[F_xz(Y_PAR + T), F_xz(-Y_PAR)],
                        textos=[('ANDAR 1', (XPF0 + XPF1) / 2, Z2 + 8, 2.5)], descricao='laterais do andar 1 (2x); porcas presas do andar 2'))

    # ---------------------------------------------------------------------------- ANDAR 2 (z ZA2..ZA2+T)
    X2_0, X2_1 = X_TRAS, X_FRENTE - 4.0
    base_a2 = ret(X2_0, -Y_PISO, X2_1, Y_PISO)
    f2 = []
    for (x, y) in m.jet_furos:
        f2.append(circ(x, y, 2.9, 'jetson', 'parafuso M2.5 do espacador da Jetson'))
    for xw in (PAR_T0, PAR_F0):
        for yc in ys_tab_topo:
            f2.append(Furo(ret_c(xw + T / 2, yc, S, 10), 'parede_berco', funcao='encaixe'))
    f2.append(rasgo(xs_pl_t[0], Y_PAR + T / 2, 10, S, 'parede_lateral'))
    for sy_ in (1, -1):
        for xc in xs_topo_pf:
            f2.append(rasgo(xc, sy_ * (Y_PAR + T / 2), 10, S, 'parede_frente'))
        for xc in xs_porca2:
            f2.append(circ(xc, sy_ * (Y_PAR + T / 2), 3.4, 'andar2', 'parafuso M3 do andar 2 (porca presa na parede)'))
    for k in range(2):
        for (l, w) in v('xl_trimpots'):
            x, y = xl_pt(k, l, w)
            f2.append(circ(x, y, 7.0, 'trimpot', 'chave de fenda no trimpot do XL4016'))
    PF_MOTOR = [(-7.0, 14.0), (-7.0, -14.0)]            # passa-fios dos cabos dos motores (atras da Jetson)
    PF_VM = (-6.0, -32.0); PF_P4 = (-6.0, 32.0)
    for (x, y) in PF_MOTOR:
        f2.append(circ(x, y, 9.0, 'passa_fio_motor', 'cabo do motor sobe para o andar 3'))
    f2.append(circ(*PF_VM, 8.0, 'passa_fio_vm', 'fios do VM (XL4016 #2) sobem para o andar 3'))
    f2.append(circ(*PF_P4, 10.0, 'passa_fio_p4', 'fios do P4 e do VM esquerdo sobem'))
    PF_CH = (PAR_T0 + T + 8.0, CHY + cr_w / 2 + 6.0)
    f2.append(circ(*PF_CH, 8.0, 'passa_fio_chave', 'fios da chave sobem para o fusivel'))
    apoios['pf_chave'] = (PF_CH[0], PF_CH[1], ZA2 + T / 2)
    PF_XT = (BX0 + 2.0 + xw6 / 2, -54.0)
    f2.append(circ(*PF_XT, 8.0, 'passa_fio_xt60', 'pigtail do XT60 sobe para o fusivel'))
    for nome_, (x, y) in (('pf_motor_e', PF_MOTOR[0]), ('pf_motor_d', PF_MOTOR[1]), ('pf_vm', PF_VM), ('pf_p4', PF_P4),
                          ('pf_xt60', PF_XT)):
        apoios[nome_] = (x, y, ZA2 + T / 2)
    # pilares do andar 3 (x-z, 4x): rasgos
    PIL_X = [tuple(q) for q in P['PILARES']]
    def pil_aba(k):                                       # aba (6 mm) na ponta de tras do pilar de tras / da frente do da frente
        a_, b_ = PIL_X[k]
        return (a_ + 4.0) if k == 0 else (b_ - 4.0)
    def pil_porca(k):
        a_, b_ = PIL_X[k]
        return (b_ - 6.0) if k == 0 else (a_ + 6.0)
    Y_PIL = Y_PAR                                        # pilares na mesma linha das paredes do andar 1
    for sy_ in (1, -1):
        for k in range(2):
            f2.append(rasgo(pil_aba(k), sy_ * (Y_PIL + T / 2), 6, S, 'pilar'))
    chapas.append(Chapa('andar2', base_a2, f2, frames=[F_xy(ZA2)],
                        textos=[('ANDAR 2  FRENTE >', 30, -48, 2.5), ('XL1', 92, 46, 2.5), ('XL2', 92, -46, 2.5)],
                        descricao='Jetson, chave, fusivel, placa de desligar; sai com 4 parafusos'))

    # ---------------------------------------------------------------------------- pilares andar 2 -> andar 3 (x-z), 4x
    H2 = ZA3 - ZA2t
    xs_porca3 = []
    for k, (a_, b_) in enumerate(PIL_X):
        base_p = ret(a_, ZA2t, b_, ZA3)
        abas_p = [ret_c(pil_aba(k), ZA2t - T / 2, 6, T), ret_c(pil_aba(k), ZA3 + T / 2, 6, T)]
        chapas.append(Chapa(f'pilar_{"tras" if k == 0 else "frente"}', base_p, [], abas_p, [porca(pil_porca(k), ZA3)],
                            frames=[F_xz(Y_PIL + T), F_xz(-Y_PIL)], descricao='sustenta o andar 3 (2x); porca presa em cima'))

    # ---------------------------------------------------------------------------- ANDAR 3 (z ZA3..ZA3+T)
    X3_0, X3_1 = min(esp_pt(0, EL)[0] - 3.0, PIL_X[0][0] - 3.0), max(EX1 + 3.0, PIL_X[1][1] + 3.0)
    PX0, PX1 = X3_1 - 16.0, X3_1 - 2.0                    # base dos postes da camera
    Y3 = Y_PIL + T + 2.5
    base_a3 = ret(X3_0, -Y3, X3_1, Y3)
    f3 = []
    for (u, vv) in v('esp_furos'):
        f3.append(circ(*esp_pt(u, vv), 3.4, 'esp32', 'parafuso M3 da placa da ESP32'))
    for (x, y) in m.desl_furos:
        f3.append(circ(x, y, 3.4, 'desligar', 'parafuso M3 da placa de desligar'))
    for sy_ in (1, -1):
        for k in range(2):
            f3.append(rasgo(pil_aba(k), sy_ * (Y_PIL + T / 2), 6, S, 'pilar'))
            f3.append(circ(pil_porca(k), sy_ * (Y_PIL + T / 2), 3.4, 'andar3', 'parafuso M3 do andar 3 (porca presa no pilar)'))
    PF3_MOTOR = [(P['PF3_MOTOR'][0], P['PF3_MOTOR'][1]), (P['PF3_MOTOR'][0], -P['PF3_MOTOR'][1])]
    PF3_VM = [(esp_pt(7.9, 63.5)[0], EW / 2 + 5.5), (esp_pt(76.8, 63.5)[0], -EW / 2 - 5.5)]
    for (x, y) in PF3_MOTOR:
        f3.append(circ(x, y, 8.0, 'passa_fio_motor3', 'cabo do motor chega na placa'))
    for (x, y) in PF3_VM:
        f3.append(circ(x, y, 7.0, 'passa_fio_vm3', 'fios do VM chegam em J2/J3'))
    for nome_, (x, y) in (('pf3_motor_e', PF3_MOTOR[0]), ('pf3_motor_d', PF3_MOTOR[1]), ('pf3_vm_e', PF3_VM[0]),
                          ('pf3_vm_d', PF3_VM[1])):
        apoios[nome_] = (x, y, ZA3 + T / 2)
    PF3_J41 = (52.0, -EW / 2 - 9.0)                   # na frente da placa de interface, ao lado do J1
    f3.append(circ(*PF3_J41, 7.0, 'passa_fio_j41', 'jumpers do J41 sobem para a placa de desligar'))
    apoios['pf3_j41'] = (PF3_J41[0], PF3_J41[1], ZA3 + T / 2)
    PY = 17.0
    for sy_ in (1, -1):
        for xc in (PX0 + 3.5, PX1 - 3.5):
            f3.append(rasgo(xc, sy_ * (PY + T / 2), 5, S, 'poste'))
    chapas.append(Chapa('andar3', base_a3, f3, frames=[F_xy(ZA3)], textos=[('ANDAR 3', X3_0 + 12, 0, 2.5)],
                        descricao='placa da ESP32 e mastro da camera; sai com 4 parafusos'))
    m.X3 = (X3_0, X3_1)

    # ---------------------------------------------------------------------------- mastro curto da camera (em cima do andar 3)
    PVx, PVz = P['PIVO']
    R_ARCO = 9.0
    z_b = max(ZA3t + 8, PVz - 24)
    base_po = so.unary_union([sg.MultiPoint([(PX0, ZA3t), (PX1, ZA3t), (PVx + 6, max(z_b, ZA3t + 1)), (PVx + 6, PVz),
                                             (PVx - R_ARCO - 5, PVz), (PX0, max(z_b, ZA3t + 1))]).convex_hull,
                              sg.Point(PVx, PVz).buffer(10.5), sg.Point(PVx - R_ARCO, PVz).buffer(5.0)])
    abas_po = [ret_c(xc, ZA3t - T / 2, 5, T) for xc in (PX0 + 3.5, PX1 - 3.5)]
    fpo = [circ(PVx, PVz, 3.4, 'pivo', 'pivo da camera (M3)'), circ(PVx - R_ARCO, PVz, 3.4, 'trava_angulo', 'trava do angulo (M3)')]
    postes = Chapa('poste_mastro', base_po, fpo, abas_po, frames=[F_xz(PY + T), F_xz(-PY)],
                   textos=[('v', PVx, PVz + 8.5, 2.0)], descricao='mastro curto da camera (2x)')
    chapas.append(postes)
    ZTR = ZA3t + 7.0                                     # travessa baixa: longe das orelhas da camera
    TRVx = (PX0 + PX1) / 2
    trav = Chapa('travessa_mastro', ret(-PY, -4, PY, 4), [], [ret(PY, -4, PY + T, 4), ret(-PY - T, -4, -PY, 4)],
                 frames=[frame((0, 1, 0), (0, 0, 1), (TRVx - T / 2, 0, ZTR))], descricao='trava os postes')
    chapas.append(trav)
    postes.furos.append(rasgo(TRVx, ZTR, S, 8, 'travessa'))

    def F_cam(ang, y_lado):
        base = frame((1, 0, 0), (0, 0, 1), (PVx, y_lado, PVz))
        return F_rot_y(base, ang, (PVx, PVz))
    m.F_cam = F_cam
    YO = PY - T
    CA, CC = 2.0, P['CAM_C']
    base_or = so.unary_union([sg.Point(0, 0).buffer(14.0), ret(-2, CC - 16, CA + T + 2.5, 0)])
    th0, th1 = 180 + P['CAM_ANG'][0] - 4, 180 + P['CAM_ANG'][1] + 4
    for_ = [circ(0, 0, 3.4, 'pivo', 'pivo'), arco_rasgo(0, 0, R_ARCO, th0, th1, 3.4, 'arco', 'ajuste do angulo'),
            Furo(ret(CA, CC - 8, CA + S, CC + 8), 'placa_camera', funcao='encaixe')]
    escala = []
    for ang in range(int(P['CAM_ANG'][0]), int(P['CAM_ANG'][1]) + 1, 10):
        th = math.radians(90 + ang)
        escala.append((f'{ang}', 12.2 * math.cos(th), 12.2 * math.sin(th), 1.6))
    orelha = Chapa('orelha_camera', base_or, for_, textos=escala, frames=[], descricao='suporte giratorio (2x)')
    orelha.qtd = 2
    chapas.append(orelha)
    cfx, cfy = v('cam_furos')
    lente_q = v('cam_suporte_lente') + 0.6
    base_pc = ret(-YO, CC - 15, YO, CC + 15)
    abas_pc = [ret(YO, CC - 8, YO + T, CC + 8), ret(-YO - T, CC - 8, -YO, CC + 8)]
    fpc = [Furo(ret_c(0, CC, lente_q, lente_q), 'lente', funcao='suporte da lente passa pela placa')]
    fpc += [circ(sx_ * cfx / 2, CC + sy_ * cfy / 2, 2.2, 'camera', 'parafuso M2 da camera') for sx_ in (1, -1) for sy_ in (1, -1)]
    placa_cam = Chapa('placa_camera', base_pc, fpc, abas_pc, frames=[], textos=[('CIMA ^', 0, CC + 12.5, 2.2)],
                      descricao='camera presa por tras, lente para a frente')
    placa_cam.qtd = 1
    chapas.append(placa_cam)

    def partes_camera(ang):
        out = []
        out.append(('orelha_camera_esq', orelha.solido(T).moved(loc(F_cam(ang, YO + T))), 'chapa'))
        out.append(('orelha_camera_dir', orelha.solido(T).moved(loc(F_cam(ang, -YO))), 'chapa'))
        ex, ey, ez, o = F_cam(ang, 0)
        frp = (-ez, ey, ex, o + CA * ex)
        out.append(('placa_camera', placa_cam.solido(T).moved(loc(frp)), 'chapa'))
        pw_, ph_, pt_ = v('cam_placa')
        out.append(('camera_placa', caixa_local(frp, -pw_ / 2, pw_ / 2, CC - ph_ / 2, CC + ph_ / 2, -1.5 - pt_, -1.5), 'camera'))
        ld, ll = v('cam_lente')
        out.append(('camera_lente', cilindro(aplicar(frp, 0, CC, -1.5), aplicar(frp, 0, CC, -1.5 + ll), ld), 'camera'))
        out.append(('camera_conector_ffc', caixa_local(frp, -10, 10, CC - ph_ / 2, CC - ph_ / 2 + 5.5, -1.5 - pt_ - 3, -1.5 - pt_),
                    'camera'))
        m.cam_ffc_pt = aplicar(frp, 0, CC - ph_ / 2 - 1, -1.5 - pt_ - 1.5)
        m.cam_ffc_baixo = aplicar(frp, 0, CC - 15 - 8, -1.5 - pt_ - 3)
        m.cam_centro = aplicar(frp, 0, CC, -1.5 + ll)
        return out
    m.partes_camera = partes_camera

    # ======================================================================================== CABOS
    def cabo(nome, pontos, d, bitola, de, para, apoio=(), disponivel=None, extra=20.0, obs=''):
        cabos.append(dict(nome=nome, pontos=[tuple(map(float, p)) for p in pontos], d=d, bitola=bitola, de=de, para=para,
                          apoios=list(apoio), disponivel=disponivel, extra=extra, obs=obs))
    zi = Z_XL + 1.6 + 6
    (xb1, yb1) = xl_pt(0, 0, 24); (xb2, yb2) = xl_pt(1, 0, 24)
    zb = EZ + 11                                  # por cima do suporte do motor
    zm = (ZA2t + ZA3) / 2                         # entre os andares 2 e 3
    fus_in = (FX0 + 5, FY0 + 5, ZA2t + 4); fus_out = (FX0 + 5, FY0 + fl - 5, ZA2t + 4)
    pfz = ZA2 + T / 2
    cabo('pigtail_xt60_fusivel', [(BX0 + 2 + xw6 / 2, XTY0 + xh6 / 2, Z1 + 1 + XT_L), (PF_XT[0], PF_XT[1], Z1 + BH + 2),
                                  (PF_XT[0], PF_XT[1], pfz), (PF_XT[0], PF_XT[1], ZA2t + 6), fus_in],
         4.0, '0,75 mm2 vermelho + preto', 'XT60 do chassi (par solto, a direita da bateria)', 'entrada da placa do fusivel',
         apoio=['pf_xt60'], obs='XT60 soldado nesta ponta; termorretratil')
    chave = (PAR_T0 + T + c_d - 2, CHY, CHZ)
    cabo('fusivel_chave', [fus_out, (PF_CH[0], PF_CH[1], ZA2t + 4), (PF_CH[0], PF_CH[1], ZA2 - 4), chave],
         2.6, '0,75 mm2 vermelho', 'saida do fusivel', 'chave geral (terminal 1)', apoio=['pf_chave'])
    jb = apoios['janela_berco']
    cabo('chave_xl', [chave, (CHX, 10.0, jb[2]), (jb[0], 8.0, jb[2]), (6.0, 30.0, ZA2 - 6), (XL0 - 8, yb1, zi + 4), (xb1 - 3, yb1, zi)],
         4.0, '0,75 mm2 vermelho + preto', 'chave geral (terminal 2) + GND do fusivel', 'IN+ / IN- do XL4016 #1',
         apoio=['janela_berco'], obs='sai pela janela da parede do berco e passa por cima dos motores')
    cabo('jumper_in_xl', [(xb1 - 3, yb1 - 8, zi), (XL0 - 6, 0, Z2 + 8), (xb2 - 3, yb2 + 8, zi)],
         4.0, '0,75 mm2 vermelho + preto', 'IN+ / IN- do XL4016 #1', 'IN+ / IN- do XL4016 #2', apoio=[])
    p4f = m.p4_fim
    cabo('xl1_p4_jetson', [(xb1 - 3, yb1 + 6, zi), (XL0 - 8, 30, zi + 6), (PF_P4[0], PF_P4[1], ZA2 - 6), (PF_P4[0], PF_P4[1], ZA2t + 6),
                           (p4f[0] - 6, p4f[1], p4f[2] - 4), (p4f[0] - 2, p4f[1], p4f[2])],
         4.0, '0,75 mm2 vermelho + preto', 'OUT+ / OUT- do XL4016 #1 (5,2 V)', 'plugue P4 da Jetson (J25)',
         apoio=['pf_p4'], obs='P4 reto soldado; testar 5,2 V e polaridade antes de ligar')
    for lado, sy_, padu, pf3 in (('e', 1, 7.9, 'pf3_vm_e'), ('d', -1, 76.8, 'pf3_vm_d')):
        alvo = esp_pt(padu, 63.5)
        x3, y3 = apoios[pf3][:2]
        pf2 = PF_P4 if sy_ > 0 else PF_VM
        cabo(f'vm_{lado}', [(xb2 - 3, yb2 - 4 * sy_, zi), (XL0 - 8, 30 * sy_, zi + 6), (pf2[0], pf2[1], ZA2 - 6), (pf2[0], pf2[1], ZA2t + 6),
                            (x3, y3, zm), (x3, y3, ZA3t + 4), (x3, y3, zt + 4), (alvo[0], alvo[1], zt + 2)],
             4.0, '0,75 mm2 vermelho + preto', 'OUT+ / OUT- do XL4016 #2 (7,2 V)', f'J{2 if sy_ > 0 else 3} da placa da ESP32',
             apoio=['pf_p4' if sy_ > 0 else 'pf_vm', pf3], obs='ja soldado na placa: so conferir o comprimento')
    j1 = esp_pt(39.5, 8.5)
    pv3 = apoios['pf3_vm_e']
    cabo('vbat', [chave, (PF_CH[0], PF_CH[1], ZA2 - 4), (PF_CH[0], PF_CH[1], ZA2t + 6), (pv3[0], pv3[1], zm),
                  (pv3[0], pv3[1], ZA3t + 3), (pv3[0], pv3[1], zt + 4), (j1[0], j1[1], zt + 2)],
         1.6, '0,2 mm2 (fio fino)', 'chave geral (terminal 2)', 'J1 (VBAT) da placa da ESP32', apoio=['pf_chave', 'pf3_vm_e'],
         obs='conector de 1 via (Dupont) no meio para o andar 3 sair')
    for lado, sy_ in (('esq', 1), ('dir', -1)):
        yc = sy_ * (Y_FIM + 2.5)
        j10 = esp_pt(11.5 if sy_ > 0 else 63.0, 5.75)
        j12 = esp_pt(11 if sy_ > 0 else 72, 45.4)
        pfm = PF_MOTOR[0 if sy_ > 0 else 1]; pf3 = apoios['pf3_motor_' + ('e' if sy_ > 0 else 'd')]
        cabo(f'motor_{lado}', [(0, yc, EZ + 12), (pfm[0], pfm[1], ZA2 - 4), (pfm[0], pfm[1], ZA2t + 4), (pf3[0], pf3[1], ZA3 - 3),
                               (pf3[0], pf3[1], ZA3t + 3), (pf3[0], pf3[1], zt + 4), (j10[0], j10[1], zt + 2)],
             3.0, 'cabo de 6 vias do motor', f'conector branco do encoder ({lado})',
             f'J{12 if sy_ > 0 else 13} + J{10 if sy_ > 0 else 11}', apoio=['pf_motor_' + lado[0], 'pf3_motor_' + lado[0]],
             disponivel=v('motor_cabo'), extra=0.0, obs='cabo original do motor; o comprimento disponivel e estimado')
    xu_, yu_, zu_ = m.esp_usb
    uf = m.usb_a_fim
    cabo('usb_jetson_esp32', [(xu_ - upl, yu_, zu_), (xu_ - upl - 3, yu_, zu_ - 8), (xu_ - upl - 3, uf[1], zm + 5),
                              (uf[0] - 4, uf[1], uf[2] + 6), (uf[0] - 2, uf[1], uf[2])],
         4.0, 'cabo USB-A / USB-C de dados', 'USB-C da ESP32 (andar 3, tras)', 'USB-A da Jetson (andar 2, tras)',
         apoio=[], disponivel=v('usb_cabo'), extra=0.0, obs='cabo curto: 15-20 cm bastam')
    xj41, yj41 = jet_pt(v('jet_j41_u')[0] + 10, JD - 4)
    pj = apoios['pf3_j41']
    cabo('j41_desligar', [(xj41, yj41, ZJ + JT + 10), (pj[0], pj[1], ZA3 - 4), (pj[0], pj[1], ZA3t + 4),
                          (pj[0], pj[1], m.desl_j1[2] + 4), (m.desl_j1[0], m.desl_j1[1], m.desl_j1[2])],
         3.5, '8 fios Dupont femea', 'J41 pinos 15 a 20, 2 (5 V) e 6 (GND)', 'placa de interface (andar 3)',
         apoio=['pf3_j41'], disponivel=150.0, extra=0.0,
         obs='jumpers Dupont de 15 cm; sobem pela borda direita do andar 3 (D-033)')
    m.cabos_ffc = (jet_pt(np.mean(v('jet_csi_u')), 58) + (ZJ + JT + 4,))
    def ffc_rota(ang):
        partes_camera(ang)
        c0 = np.array(m.cabos_ffc)
        return [tuple(c0), (c0[0] + 6, c0[1] - 8, ZA3 - 5), (m.X3[1] + 3, 12.0, ZA3 - 5), (m.X3[1] + 3, 12.0, ZA3t + 10),
                tuple(m.cam_ffc_baixo), tuple(m.cam_ffc_pt)]
    m.ffc_rota = ffc_rota
    return m

# ======================================================================================== utilidades (iguais ao v3)
def chapas_3d(m, ang=None):
    out = []
    for c in m.chapas:
        if c.nome in ('orelha_camera', 'placa_camera'):
            continue
        sol = c.solido(m.T)
        for k, fr in enumerate(c.frames):
            out.append((f'{c.nome}_{k + 1}' if len(c.frames) > 1 else c.nome, sol.moved(loc(fr)), c))
    ang = m.P['CAM_ANG_NOMINAL'] if ang is None else ang
    cams = {c.nome: c for c in m.chapas}
    for nome, sol, tipo in m.partes_camera(ang):
        if tipo == 'chapa':
            out.append((nome, sol, cams['orelha_camera' if 'orelha' in nome else 'placa_camera']))
    return out

def camera_compradas(m, ang):
    return [dict(nome=n, solido=s, massa=0.0, cat='camera', cor=(0.1, 0.1, 0.1), grupo='camera')
            for n, s, t in m.partes_camera(ang) if t == 'camera']

def massas(m):
    dens = v('massa_mdf_dens') / 1000.0
    out = []
    for nome, sol, ch in chapas_3d(m):
        c = sol.Center()
        out.append((nome, sol.Volume() * dens, (c.x, c.y, c.z)))
    for p in m.compradas + camera_compradas(m, m.P['CAM_ANG_NOMINAL']):
        if p['massa'] > 0:
            c = p['solido'].Center()
            out.append((p['nome'], p['massa'], (c.x, c.y, c.z)))
    out.append(('camera', v('cam_massa'), tuple(m.cam_centro)))
    for cb in m.cabos:
        pts = np.array(cb['pontos'])
        L = sum(np.linalg.norm(b - a) for a, b in zip(pts[:-1], pts[1:]))
        g_m = 9.0 if '0,75' in cb['bitola'] else 4.0 if 'USB' in cb['bitola'] else 2.5
        n = 2 if ('+' in cb['bitola'] or 'vias' in cb['bitola']) else 1
        out.append(('fio_' + cb['nome'], L / 1000 * g_m * n, tuple(pts.mean(axis=0))))
    out.append(('parafusos_porcas', 18.0, (20.0, 0.0, 50.0)))
    out.append(('cola_e_abracadeiras', 4.0, (20.0, 0.0, 50.0)))
    if m.P.get('LASTRO'):
        g, x, y, z = m.P['LASTRO']
        out.append(('lastro', float(g), (float(x), float(y), float(z))))
    return out

def cg(lista):
    M_ = sum(q[1] for q in lista)
    c = sum(np.array(q[2]) * q[1] for q in lista) / M_
    return M_, c
