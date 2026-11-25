"""Modelo parametrico do chassi v3 do Robocar Blitz (MDF 3 mm cortado a laser).

construir(P) devolve um Modelo com:
  chapas   - pecas de MDF (contorno 2D, furos, referenciais 3D)
  compradas - pecas compradas como solidos simplificados (com massa e categoria)
  acessos  - volumes que precisam ficar livres (dedo, chave de fenda, caminho da bateria, plugues)
  cabos    - cada fio com rota, bitola, apoios (abracadeiras) e comprimento disponivel
Arquitetura (decisao D-026, ver README):
  * eixo em x = 0; caixa traseira com os 2 XL4016 no chao e o TAMPO com a placa da ESP32 (sobre o eixo);
  * Jetson BAIXA, a frente do eixo, com os 100 mm ao longo do carro e as portas para a ESQUERDA;
  * bateria deitada no sentido do comprimento, num tunel EMBAIXO da Jetson, sai pela frente;
  * piso traseiro (z 12-15) e piso dianteiro (z 15-18) sobrepostos: motor em cima do traseiro e esfera
    embaixo do dianteiro -> carro nivelado com a esfera de 15 mm, sem calco;
  * quilha central liga a caixa traseira ao piso da frente (rigidez na regiao do eixo, que era o ponto fraco).
"""
import math, copy
import numpy as np
import shapely.geometry as sg
import shapely.ops as so
import cadquery as cq
import pecas
from pecas import v
from geometria import (ret, ret_c, circ, oblongo, rasgo, poli, arco_rasgo, Furo, Chapa, frame, F_xy, F_xz, F_yz,
                       F_rot_y, aplicar, loc, caixa, cilindro, caixa_local, comprimento)

# ======================================================================================== parametros
PADRAO = dict(
    T=3.0,                 # espessura MEDIDA da chapa
    FOLGA=-0.1,            # rasgo = T + FOLGA (escolher pelo pente de teste)
    BITOLA=104.0,          # centro a centro das rodas
    FOLGA_RODA_REDUTOR=1.5,
    J0=12.0,               # traseira da Jetson (x)
    JET_ESPACADOR=20.0,    # altura dos espacadores M2.5 da Jetson (bateria embaixo)
    BAT_X0=19.0,           # traseira da bateria (x); sai pela frente
    XL_XF=-24.0,           # ponta dos bornes dos XL4016 (x)
    XL_ESPACADOR=4.0,      # espacador M3 embaixo dos XL4016
    XL_AR=6.0,             # vao de ar entre o topo dos XL4016 e o tampo
    XL_Y=(2.0, -2.0),      # borda interna de cada XL (esquerdo, direito)
    ESP_X0=-2.0,           # borda da frente da placa da ESP32 (x)
    ESP_ESPACADOR=5.0,     # espacador M3 entre o tampo e a placa da ESP32
    ESFERA_X=121.0,
    PIVO=(120.0, 140.0),   # eixo de giro da camera (x, z)
    CAM_ANG=(25.0, 65.0),  # faixa de inclinacao da camera abaixo da horizontal (graus)
    CAM_ANG_NOMINAL=45.0,
    CAM_C=-17.0,           # centro da camera abaixo do pivo (no referencial da camera)
    CHAVE_X=44.0,          # centro do recorte da chave geral na parede direita
    FUS_X0=70.0,           # placa do fusivel (x0) embaixo da Jetson, lado direito
    XT60_X=133.5,          # centro do par XT60 (solto, deitado) na frente, entre os postes
    MESA=(390.0, 270.0),   # area util da chapa no laser (mm) -> folha A3 no PDF
    MIN_TEIA=2.0,          # material minimo entre furos e entre furo e borda
    MU=0.9,                # atrito pneu x tapete (hipotese; medir no T12)
    CABO_FOLGA=0.10,       # sobra de 10 % nos cabos
)

class Modelo:
    pass

# ======================================================================================== construcao
def construir(P=None, verif=False):
    """verif=True: rasgos com largura igual a T (para a checagem de interferencia nao acusar o aperto)."""
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

    # ---------------------------------------------------------------------------- rodas, motores
    RD, RL = v('roda'); EZ = RD / 2
    YR = P['BITOLA'] / 2
    Y_PNEU_IN = YR - RL / 2
    Y_RED = Y_PNEU_IN - P['FOLGA_RODA_REDUTOR']                 # face do redutor
    sx, sy, sz = v('sup_motor')
    Z1 = EZ - v('sup_motor_eixo_z')                             # topo do piso traseiro = base do suporte
    Z0 = Z1 - T                                                 # fundo do piso traseiro
    Z2 = Z1 + T                                                 # topo do piso dianteiro
    Y_SUP = Y_RED - sy / 2
    corpo = v('motor_corpo'); Y_FIM = Y_RED - corpo
    m.Z0, m.Z1, m.Z2, m.EZ, m.YR = Z0, Z1, Z2, EZ, YR
    for s, lado in ((1, 'esq'), (-1, 'dir')):
        def yy(a, b):
            return (min(s * a, s * b), max(s * a, s * b))
        comprada(f'roda_{lado}', cq.Workplane('XZ').circle(RD / 2).extrude(RL / 2, both=True).val().translate((0, s * YR, EZ)),
                 v('roda_massa'), 'roda', (0.12, 0.12, 0.12), f'motor_{lado}')
        y0, y1 = yy(Y_RED - 9, Y_RED)
        comprada(f'redutor_{lado}', caixa(-6, 6, y0, y1, EZ - 5, EZ + 5), 0, 'redutor', (0.8, 0.65, 0.2), f'motor_{lado}')
        comprada(f'eixo_{lado}', cilindro((0, s * Y_RED, EZ), (0, s * (Y_RED + v('motor_eixo')), EZ), 3), 0, 'redutor',
                 (0.7, 0.7, 0.7), f'motor_{lado}')
        comprada(f'motor_{lado}', cilindro((0, s * (Y_RED - 9), EZ), (0, s * (Y_FIM + 11), EZ), 12), v('motor_massa'),
                 'eletronica', (0.6, 0.6, 0.62))
        y0, y1 = yy(Y_FIM, Y_FIM + 11)
        comprada(f'encoder_{lado}', caixa(-6, 6, y0, y1, Z1 + 0.5, EZ + 6), 0, 'eletronica', (0.1, 0.4, 0.15), f'motor_{lado}')
        y0, y1 = yy(Y_FIM, Y_FIM + 5)
        comprada(f'conector_motor_{lado}', caixa(-5, 5, y0, y1, EZ + 6, EZ + 12), 0, 'conector', (0.95, 0.95, 0.95),
                 f'motor_{lado}')
        y0, y1 = yy(Y_SUP - sy / 2, Y_SUP + sy / 2)
        comprada(f'suporte_motor_{lado}', caixa(-sx / 2, sx / 2, y0, y1, Z1, Z1 + sz), 2.0, 'estrutura', (0.95, 0.95, 0.95),
                 f'motor_{lado}')
    m.Y_SUP, m.Y_RED, m.Y_FIM = Y_SUP, Y_RED, Y_FIM

    # ---------------------------------------------------------------------------- XL4016 (2x)
    XL_L, XL_W = v('xl'); XL_H = v('xl_altura')
    XL_XF = P['XL_XF']; XL_XT = XL_XF - XL_L
    Z_XL = Z1 + P['XL_ESPACADOR']
    xl_y0 = (P['XL_Y'][0] + XL_W, P['XL_Y'][1])        # y da borda w = 0 (w cresce para -y)
    def xl_pt(k, l, w):
        return (XL_XF - l, xl_y0[k] - w)
    m.xl_pt = xl_pt
    nomes_xl = ('xl4016_1_jetson', 'xl4016_2_motores')
    for k in range(2):
        ya, yb = xl_pt(k, 0, 0)[1], xl_pt(k, 0, XL_W)[1]
        comprada(nomes_xl[k], caixa(XL_XT, XL_XF, min(ya, yb), max(ya, yb), Z_XL, Z_XL + XL_H), v('xl_massa'), 'eletronica',
                 (0.2, 0.45, 0.3))
        l0, l1, hb = v('xl_bornes')
        comprada(f'bornes_xl{k + 1}', caixa(XL_XF - l1, XL_XF - l0, min(ya, yb) + 9, max(ya, yb) - 9, Z_XL + 1.6, Z_XL + 1.6 + hb),
                 0, 'conector', (0.1, 0.3, 0.8), nomes_xl[k])
        for j, (l, w) in enumerate(v('xl_trimpots')):
            x, y = xl_pt(k, l, w)
            acesso(f'chave_trimpot_xl{k + 1}_{j + 1}', cilindro((x, y, Z_XL + XL_H - 3), (x, y, Z_XL + XL_H + 70), 5.0),
                   'regular o trimpot com chave de fenda por cima, carro montado', ignora=(nomes_xl[k],))
        for (l, w) in v('xl_furos'):
            x, y = xl_pt(k, l, w)
            comprada(f'espacador_xl{k + 1}_{l:.0f}_{w:.0f}', cilindro((x, y, Z1), (x, y, Z_XL), 5.5), 0.5, 'fixacao',
                     (0.9, 0.9, 0.85), nomes_xl[k])
    m.Z_XL_TOPO = Z_XL + XL_H
    ZD = m.Z_XL_TOPO + P['XL_AR']                # fundo do tampo
    m.ZD = ZD

    # ---------------------------------------------------------------------------- caixa traseira: dimensoes
    X_TRAS = XL_XT - 2.0 - T          # face de fora da parede traseira
    X_PISO_TRAS = X_TRAS - 3.0         # borda do piso (material atras do rasgo)
    Y_PAR = 55.0                       # face interna das paredes laterais (traseira e dianteira)
    Y_PISO = Y_PAR + T + 2.5           # borda do piso
    X_PAR_FRENTE = -(EZ + 4.0)         # frente das paredes laterais traseiras: 4 mm do pneu
    m.X_TRAS, m.X_PISO_TRAS, m.Y_PAR, m.Y_PISO = X_TRAS, X_PISO_TRAS, Y_PAR, Y_PISO

    # ---------------------------------------------------------------------------- placa da ESP32 (v0.8)
    EW, EL, ET = v('esp_placa'); EX0 = P['ESP_X0']
    Z_ESP = ZD + T + P['ESP_ESPACADOR']
    def esp_pt(u, vv):
        return (EX0 - vv, EW / 2 - u)
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
    # USB-C da ESP32 (traseira) e plugue reto
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

    # ---------------------------------------------------------------------------- placa de desligar (no tampo, lado direito)
    dw, dl, dh = v('desl_placa')
    DX0, DY1 = -34.0, -(EW / 2 + 1.0)                  # do lado direito da placa da ESP32
    comprada('placa_desligar', caixa(DX0, DX0 + dw, DY1 - dl, DY1, ZD + T + 3, ZD + T + 3 + 1.6), 4.0, 'eletronica',
             (0.15, 0.4, 0.55))
    zbd = ZD + T + 3 + 1.6
    m.desl_botao = (DX0 + 8, DY1 - dl / 2, zbd)
    m.desl_led = (DX0 + 20, DY1 - dl / 2, zbd)
    comprada('botao_desligar', caixa(DX0 + 5, DX0 + 11, DY1 - dl / 2 - 3, DY1 - dl / 2 + 3, zbd, zbd + 13), 0, 'eletronica',
             (0.1, 0.1, 0.1), 'placa_desligar')
    comprada('led_pode_desligar', cilindro((DX0 + 20, DY1 - dl / 2, zbd), (DX0 + 20, DY1 - dl / 2, zbd + 8), 3), 0,
             'eletronica', (0.9, 0.1, 0.1), 'placa_desligar')
    acesso('dedo_botao_desligar', cilindro((DX0 + 8, DY1 - dl / 2, zbd + 13), (DX0 + 8, DY1 - dl / 2, zbd + 60), 12),
           'apertar o botao de desligar a Jetson')
    m.desl_furos = [(DX0 + 3.5, DY1 - 3.5), (DX0 + dw - 3.5, DY1 - dl + 3.5)]

    # ---------------------------------------------------------------------------- Jetson Nano B01
    JW, JD, JT = v('jet_placa'); J0 = P['J0']
    ZJ = Z2 + P['JET_ESPACADOR']
    def jet_pt(u, vv):                    # portas (v = 0) para a ESQUERDA, P4 (u = 0) para a FRENTE
        return (J0 + JW - u, JD / 2 - vv)
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
    # plugues usados: P4 (energia) e um USB-A (ESP32); retos, saem pela esquerda
    pl, pd = v('p4_plugue')
    xp, yp = jet_pt(pu, 0)
    comprada('plugue_p4', cilindro((xp, yp - 1.5, ZJ + JT + 6), (xp, yp + pl, ZJ + JT + 6), pd), 0, 'plugue', (0.3, 0.3, 0.3),
             'jetson')
    ul, uw, uh = v('usb_a_plugue')
    a, b = v('jet_usb_u')
    xu2, yu2 = jet_pt((a + b) / 2, 0)
    comprada('plugue_usb_a', caixa(xu2 - uw / 2, xu2 + uw / 2, yu2 - 1.5, yu2 + ul, ZJ + JT + 2, ZJ + JT + 2 + uh), 0, 'plugue',
             (0.3, 0.3, 0.3), 'jetson')
    m.p4_fim = (xp, yp + pl, ZJ + JT + 6); m.usb_a_fim = (xu2, yu2 + ul, ZJ + JT + 2 + uh / 2)
    # microSD: sai pela borda v = 80 (lado direito do carro)
    a, b = v('jet_sd_u')
    (xa, ya), (xb, yb) = jet_pt(a, JD), jet_pt(b, JD)
    acesso('dedo_microsd', caixa(min(xa, xb), max(xa, xb), -JD / 2 - 16, -JD / 2 + 1, ZJ + 1, ZJ + 9),
           'tirar e por o microSD da Jetson', ignora=('jetson_placa', 'jetson_solda', 'jetson_dissipador', 'jetson_j41'))
    acesso('ar_dissipador', caixa_jet(du0, du1, dv0, dv1, v('jet_altura'), v('jet_altura') + 25),
           'ar livre em cima do dissipador (sem ventoinha)')
    jfb = v('jet_furos_borda'); jfd = v('jet_furo_d')
    dxu, dxv = jfb[0] - jfd, jfb[1] - jfd
    fu0 = v('jet_furo_u0') if v('jet_furo_u0') is not None else (JW - dxu) / 2
    fv0 = v('jet_furo_v0') if v('jet_furo_v0') is not None else (JD - dxv) / 2
    m.jet_furos = [jet_pt(u, vv) for u in (fu0, fu0 + dxu) for vv in (fv0, fv0 + dxv)]
    for i, (x, y) in enumerate(m.jet_furos):
        comprada(f'espacador_jetson_{i + 1}', cilindro((x, y, Z2), (x, y, ZJ), 5.0), 1.0, 'fixacao', (0.9, 0.9, 0.85), 'jetson')

    # ---------------------------------------------------------------------------- bateria e tunel
    BL, BW, BH = v('bat')
    BX0 = P['BAT_X0']; BX1 = BX0 + BL
    comprada('bateria', caixa(BX0, BX1, -BW / 2, BW / 2, Z2, Z2 + BH), v('bat_massa'), 'eletronica', (0.95, 0.75, 0.15))
    Y_TRILHO = BW / 2 + 0.75                           # face interna do trilho
    acesso('caminho_bateria', caixa(BX0 + 1, BX1 + 60, -BW / 2 + 0.3, BW / 2 - 0.3, Z2 + 0.3, Z2 + BH - 0.3),
           'tirar a bateria pela frente (deslizando 60 mm alem da posicao)', ignora=('bateria', 'pino_trava', 'par_xt60'))
    m.BX0, m.BX1, m.Y_TRILHO = BX0, BX1, Y_TRILHO

    # ---------------------------------------------------------------------------- energia: XT60, fusivel, chave
    xl6, xw6, xh6 = v('xt60')
    XX = P['XT60_X']
    XT_L = 26.0                                        # par XT60 encaixado (comprimento), deitado, eixo em y
    comprada('par_xt60', caixa(XX - xw6 / 2, XX + xw6 / 2, -XT_L / 2, XT_L / 2, Z2, Z2 + xh6), 8.0,
             'conector', (0.95, 0.8, 0.1))
    acesso('mao_xt60', caixa(XX - 5, XX + 5, -XT_L / 2 + 2, XT_L / 2 - 2, Z2 + xh6, Z2 + xh6 + 30), 'segurar e soltar o par XT60',
           ignora=('par_xt60',))
    fw, fl, fh = v('fus_placa')
    FX0 = P['FUS_X0']; FY1 = -(Y_TRILHO + T + 1.5)
    comprada('placa_fusivel', caixa(FX0, FX0 + fw, FY1 - fl, FY1, Z2, Z2 + fh), v('fus_massa'), 'eletronica', (0.15, 0.4, 0.55))
    acesso('dedo_fusivel', caixa(FX0 + 5, FX0 + fw - 5, FY1 - fl - 14, FY1 - fl + 6, Z2 + 3, Z2 + 13),
           'trocar o fusivel pelo lado direito', ignora=('placa_fusivel',))
    m.fus = (FX0, FX0 + fw, FY1 - fl, FY1)
    cr_w, cr_h = v('chave_recorte'); c_w, c_h, c_d = v('chave_corpo')
    CX = P['CHAVE_X']; ZCH = Z2 + 9.5
    comprada('chave_geral', caixa(CX - cr_w / 2 + 0.3, CX + cr_w / 2 - 0.3, -Y_PAR - T, -Y_PAR + c_d,
                                  ZCH - cr_h / 2 + 0.3, ZCH + cr_h / 2 - 0.3), 4.0, 'eletronica', (0.1, 0.1, 0.1))
    comprada('chave_moldura', caixa(CX - c_w / 2, CX + c_w / 2, -Y_PAR - T - 3, -Y_PAR - T, ZCH - c_h / 2, ZCH + c_h / 2), 0,
             'eletronica', (0.1, 0.1, 0.1), 'chave_geral')
    acesso('dedo_chave', caixa(CX - 8, CX + 8, -Y_PAR - T - 18, -Y_PAR - T - 3, ZCH - 6, ZCH + 6), 'ligar e desligar a chave geral')
    m.chave = (CX, -Y_PAR, ZCH)

    # ---------------------------------------------------------------------------- esfera
    ex_, ey_ = v('esfera_corpo'); EH = v('esfera_altura'); EXX = P['ESFERA_X']
    comprada('esfera_base', caixa(EXX - ex_ / 2, EXX + ex_ / 2, -ey_ / 2, ey_ / 2, Z1 - EH + 9.525, Z1), v('esfera_massa'),
             'estrutura', (0.3, 0.3, 0.3), 'esfera')
    comprada('esfera_bola', cq.Solid.makeSphere(9.525 / 2, cq.Vector(EXX, 0, Z1 - EH + 9.525 / 2)), 0, 'estrutura',
             (0.75, 0.75, 0.75), 'esfera')
    m.esfera_z_chao = Z1 - EH

    # ======================================================================================== CHAPAS
    def nome_aba(*a):
        return '_'.join(str(q) for q in a)

    # ---------------------------------------------------------------------------- piso traseiro (z Z0..Z1)
    X_LAP0, X_LAP1 = 13.0, 35.0                        # sobreposicao dos pisos
    Y_EIXO = Y_PNEU_IN - 1.5                           # largura do piso entre as rodas
    X_PISO_LARGO = -(EZ + 2.0)                        # parte larga do piso: 2 mm atras do pneu (na altura do piso)
    base_t = so.unary_union([ret(X_PISO_TRAS, -Y_PISO, X_PISO_LARGO, Y_PISO), ret(X_PISO_LARGO - 1, -Y_EIXO, X_LAP1, Y_EIXO)])
    ft = []
    for sy_ in (1, -1):
        for sx_ in (1, -1):
            ft.append(oblongo((sx_ * 8.5, sy_ * Y_SUP), (sx_ * 10.8, sy_ * Y_SUP), 2.3, f'suporte_motor', 'parafuso M2 do suporte'))
    for k in range(2):
        for (l, w) in v('xl_furos'):
            x, y = xl_pt(k, l, w)
            ft.append(circ(x, y, 3.4, f'xl{k + 1}', 'parafuso M3 do XL4016'))
    # rasgos das paredes laterais, parede traseira e quilha
    xs_par = [X_TRAS + T + 12, (X_TRAS + X_PAR_FRENTE) / 2, X_PAR_FRENTE - 12]
    for sy_ in (1, -1):
        for xc in xs_par:
            ft.append(rasgo(xc, sy_ * (Y_PAR + T / 2), 10, S, 'parede_lateral'))
    ys_tras = [-40.0, 8.0, 40.0]                       # abas da parede traseira (a do meio desviada da quilha)
    for yc in ys_tras:
        ft.append(Furo(ret_c(X_TRAS + T / 2, yc, S, 10), 'parede_traseira', funcao='encaixe'))
    X_QUILHA0, X_QUILHA1 = X_TRAS + T, X_LAP0
    xs_quilha_t = [-75, -45, -12]
    for xc in xs_quilha_t:
        ft.append(rasgo(xc, 0, 10, S, 'quilha'))
    # sobreposicao: 2 parafusos M3 + os 2 espacadores de tras da Jetson atravessam os dois pisos
    lap_paraf = [(27.0, 20.0), (27.0, -20.0)]
    for (x, y) in lap_paraf:
        ft.append(circ(x, y, 3.4, 'parafuso_pisos', 'parafuso M3 que une os pisos'))
    for (x, y) in m.jet_furos:
        if x < X_LAP1 - 3:
            ft.append(circ(x, y, 2.9, 'jetson', 'parafuso M2.5 do espacador da Jetson'))
    # abracadeiras (pares de rasgos 1,5 x 3,5) nos pontos de apoio dos cabos
    def abracadeira(lista, nome, x, y, ang=0, dist=6.0):
        c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for d in (-dist / 2, dist / 2):
            lista.append(Furo(sg.Polygon([(x + d * c + p * 0.75 * -s_ + q * 1.75 * c, y + d * s_ + p * 0.75 * c + q * 1.75 * s_)
                                          for p, q in ((-1, -1), (1, -1), (1, 1), (-1, 1))]).convex_hull, nome,
                              funcao='abracadeira'))
    abracadeira(ft, 'ab_energia_dir', -17.0, -32.0, 90)
    abracadeira(ft, 'ab_p4_esq', -17.0, 32.0, 90)
    apoios['ab_energia_dir'] = (-17.0, -32.0, Z1)
    apoios['ab_p4_esq'] = (-17.0, 32.0, Z1)
    piso_t = Chapa('piso_traseiro', base_t, ft, frames=[F_xy(Z0)],
                   textos=[('PISO TRASEIRO  FRENTE >', -55, -40, 3.5), ('BLITZ v3', -55, 24, 6)],
                   descricao='motores, XL4016, caixa traseira')
    chapas.append(piso_t)

    # ---------------------------------------------------------------------------- piso dianteiro (z Z1..Z2)
    X_FRENTE = 141.0
    base_f = so.unary_union([ret(X_LAP0, -Y_EIXO, X_PAR_FRENTE * 0 + 24.5, Y_EIXO), ret(23.5, -Y_PISO, 110.0, Y_PISO),
                             sg.Polygon([(110, -Y_PISO), (117, -24), (X_FRENTE, -24), (X_FRENTE, 24), (117, 24), (110, Y_PISO)])])
    ff = []
    for (x, y) in lap_paraf:
        ff.append(circ(x, y, 3.4, 'parafuso_pisos', 'parafuso M3 que une os pisos'))
    for (x, y) in m.jet_furos:
        ff.append(circ(x, y, 2.9, 'jetson', 'parafuso M2.5 do espacador da Jetson'))
    # trilhos do tunel da bateria (x-z), paredes laterais da frente, batente, postes, esfera
    xs_tr = [BX0 + 12, BX0 + 47, 100.0]
    for sy_ in (1, -1):
        for xc in xs_tr:
            ff.append(rasgo(xc, sy_ * (Y_TRILHO + T / 2), 10, S, 'trilho'))
    X_PARF0, X_PARF1 = 26.0, 110.0
    X_PARF1_DIR = 64.0                                 # parede direita so ate depois da chave: fusivel e microSD livres
    xs_pf = [X_PARF0 + 9, 68.0, X_PARF1 - 9]
    xs_pf_dir = [X_PARF0 + 5, X_PARF1_DIR - 6]
    for sy_, xs_ in ((1, xs_pf), (-1, xs_pf_dir)):
        for xc in xs_:
            ff.append(rasgo(xc, sy_ * (Y_PAR + T / 2), 10, S, 'parede_frente'))
    ff.append(rasgo(BX0 - T / 2, 0, S, 10, 'batente_bateria'))
    PX0, PX1 = 113.0, 127.0; PY = 17.0                  # postes do mastro: x, face interna
    for sy_ in (1, -1):
        for xc in (PX0 + 3.5, PX1 - 3.5):
            ff.append(rasgo(xc, sy_ * (PY + T / 2), 5, S, 'poste'))
    eh = v('esfera_furos') / 2
    ff += [circ(EXX, eh, 2.8, 'esfera', 'parafuso M2.5 da esfera'), circ(EXX, -eh, 2.8, 'esfera', 'parafuso M2.5 da esfera')]
    abracadeira(ff, 'ab_energia_frente', 60.0, -46.0, 0)
    abracadeira(ff, 'ab_p4_frente', 60.0, 46.0, 0)
    abracadeira(ff, 'ab_pigtail', 106.0, -15.5, 0, 6.0)
    apoios['ab_energia_frente'] = (60.0, -46.0, Z2)
    apoios['ab_p4_frente'] = (60.0, 46.0, Z2)
    apoios['ab_pigtail'] = (106.0, -15.5, Z2)
    piso_f = Chapa('piso_dianteiro', base_f, ff, frames=[F_xy(Z1)],
                   textos=[('PISO DIANTEIRO  FRENTE >', 70, 40, 3.5), ('BATERIA', 70, 0, 4)],
                   descricao='Jetson, tunel da bateria, mastro, esfera')
    chapas.append(piso_f)
    m.X_FRENTE_PISO = X_FRENTE

    # ---------------------------------------------------------------------------- tampo (ESP32) z ZD..ZD+T
    X_TAMPO1 = EX0 + 3.0
    base_d = ret(X_PISO_TRAS, -Y_PISO, X_TAMPO1, Y_PISO)
    fd = []
    for (u, vv) in v('esp_furos'):
        fd.append(circ(*esp_pt(u, vv), 3.4, 'esp32', 'parafuso M3 da placa da ESP32'))
    for (x, y) in m.desl_furos:
        fd.append(circ(x, y, 3.4, 'desligar', 'parafuso M3 da placa de desligar'))
    for k in range(2):
        for (l, w) in v('xl_trimpots'):
            x, y = xl_pt(k, l, w)
            fd.append(circ(x, y, 7.0, 'trimpot', 'chave de fenda no trimpot do XL4016'))
    pf_vm = [(esp_pt(7.9, 63.5)[0], EW / 2 + 6.5), (esp_pt(76.8, 63.5)[0], -(EW / 2 + 6.5))]
    for (x, y) in pf_vm:
        fd.append(circ(x, y, 8.0, 'passa_fio_vm', 'fios do VM (XL4016 #2 -> J2/J3)'))
    m.pf_vm = pf_vm
    apoios['pf_vm_e'] = (pf_vm[0][0], pf_vm[0][1], ZD + T / 2)
    apoios['pf_vm_d'] = (pf_vm[1][0], pf_vm[1][1], ZD + T / 2)
    for sy_ in (1, -1):
        for xc in xs_par:
            fd.append(rasgo(xc, sy_ * (Y_PAR + T / 2), 10, S, 'parede_lateral'))
    for yc in ys_tras:
        fd.append(Furo(ret_c(X_TRAS + T / 2, yc, S, 10), 'parede_traseira', funcao='encaixe'))
    xs_quilha_d = [-75, -45, -12]
    for xc in xs_quilha_d:
        fd.append(rasgo(xc, 0, 10, S, 'quilha'))
    xs_porca = [(xs_par[0] + xs_par[1]) / 2, (xs_par[1] + xs_par[2]) / 2]
    for sy_ in (1, -1):
        for xc in xs_porca:
            fd.append(circ(xc, sy_ * (Y_PAR + T / 2), 3.4, 'tampo', 'parafuso M3 do tampo (porca presa na parede)'))
    abracadeira(fd, 'ab_usb_tampo', -20.0, 52.0, 0)
    abracadeira(fd, 'ab_j41_tampo', -8.0, -47.0, 90)
    apoios['ab_usb_tampo'] = (-20.0, 52.0, ZD + T)
    apoios['ab_j41_tampo'] = (-8.0, -47.0, ZD + T)
    tampo = Chapa('tampo', base_d, fd, frames=[F_xy(ZD)],
                  textos=[('TAMPO >', -78, -50, 2.5), ('XL1', -84, 46, 3), ('XL2', -84, -46, 3)],
                  descricao='placa da ESP32 e placa de desligar; sai com 4 parafusos')
    chapas.append(tampo)

    # ---------------------------------------------------------------------------- paredes laterais traseiras (x-z)
    H_CX = ZD - Z1
    LPx0, LPx1 = X_TRAS + T, X_PAR_FRENTE
    base_pl = ret(LPx0, Z1, LPx1, ZD)
    abas_pl = [ret_c(xc, Z1 - T / 2, 10, T) for xc in xs_par] + [ret_c(xc, ZD + T / 2, 10, T) for xc in xs_par]
    abas_pl.append(ret(LPx0 - T, Z1 + 8, LPx0, Z1 + 18))         # aba na parede traseira
    ent_pl = []
    for xc in xs_porca:   # porca presa: rasgo do parafuso desce da borda de cima e bolso da porca M3
        ent_pl.append(sg.Polygon([(xc - 1.6, ZD + 0.01), (xc - 1.6, ZD - 4.5), (xc - 2.9, ZD - 4.5), (xc - 2.9, ZD - 7.1),
                                  (xc - 1.6, ZD - 7.1), (xc - 1.6, ZD - 11), (xc + 1.6, ZD - 11), (xc + 1.6, ZD - 7.1),
                                  (xc + 2.9, ZD - 7.1), (xc + 2.9, ZD - 4.5), (xc + 1.6, ZD - 4.5), (xc + 1.6, ZD + 0.01)]))
    par_lat = Chapa('parede_lateral', base_pl, [], abas_pl, ent_pl, frames=[F_xz(Y_PAR + T), F_xz(-Y_PAR)],
                    textos=[('PAREDE', (LPx0 + LPx1) / 2, Z1 + 20, 3)], descricao='caixa traseira (2x)')
    chapas.append(par_lat)

    # ---------------------------------------------------------------------------- parede traseira (y-z)
    base_pt = ret(-Y_PISO, Z1, Y_PISO, ZD)
    abas_pt = [ret_c(yc, Z1 - T / 2, 10, T) for yc in ys_tras] + [ret_c(yc, ZD + T / 2, 10, T) for yc in ys_tras]
    fpt = [rasgo(sy_ * (Y_PAR + T / 2), Z1 + 13, S, 10, 'parede_lateral') for sy_ in (1, -1)]
    fpt.append(rasgo(0, Z1 + 13, S, 10, 'quilha'))
    for k in range(2):
        ya, yb = xl_pt(k, 0, 6)[1], xl_pt(k, 0, XL_W - 6)[1]
        fpt.append(Furo(ret(min(ya, yb), Z_XL + 4, max(ya, yb), Z_XL + 16), 'janela_ar', funcao='ventilacao do XL4016'))
    par_tras = Chapa('parede_traseira', base_pt, fpt, abas_pt, frames=[F_yz(X_TRAS)],
                     textos=[('TRAS', 0, ZD - 5, 3)], descricao='fecha a caixa; janelas = saida de ar dos XL4016')
    chapas.append(par_tras)

    # ---------------------------------------------------------------------------- quilha (x-z, y = 0)
    Z_QF = ZJ - 4.0                                     # topo da quilha embaixo da Jetson
    base_q = so.unary_union([ret(X_QUILHA0, Z1, X_TAMPO1 - 1, ZD), ret(X_TAMPO1 - 1, Z1, X_LAP0 - 0.5, Z_QF)])
    abas_q = [ret_c(xc, Z1 - T / 2, 10, T) for xc in xs_quilha_t] + [ret_c(xc, ZD + T / 2, 10, T) for xc in xs_quilha_d]
    abas_q.append(ret(X_QUILHA0 - T, Z1 + 8, X_QUILHA0, Z1 + 18))
    fq = [Furo(ret(-23.0, Z1 + 4, -12.0, Z1 + 18), 'janela_fios', funcao='fios de energia do XL4016 #1 e do VM para a esquerda')]
    abracadeira(fq, 'ab_quilha', -60.0, Z1 + 22, 0)
    apoios['ab_quilha_janela'] = (-17.5, 0.0, Z1 + 11)
    quilha = Chapa('quilha', base_q, fq, abas_q, frames=[F_xz(T / 2)], textos=[('QUILHA', -40, Z1 + 30, 3)],
                   descricao='espinha central: liga a caixa traseira ao piso da frente')
    chapas.append(quilha)

    # ---------------------------------------------------------------------------- trilhos do tunel (x-z), 2x
    Z_TR = Z2 + BH + 1.0
    TRx0, TRx1 = BX0 + 2.0, BX1 + 6.0
    PINO = (BX1 + 2.0, Z2 + 4.0)                         # pino de trava (arame/prego 3 mm) atravessa trilhos e postes
    base_tr = ret(TRx0, Z2, TRx1, Z_TR)
    abas_tr = [ret_c(xc, Z2 - T / 2, 10, T) for xc in xs_tr]
    ftr = [circ(*PINO, 3.3, 'pino_trava', 'pino que trava a bateria (tirar com a mao)')]
    trilho = Chapa('trilho_bateria', base_tr, ftr, abas_tr, frames=[F_xz(Y_TRILHO + T), F_xz(-Y_TRILHO)],
                   textos=[('TRILHO', 70, Z2 + 8, 3)], descricao='guia da bateria; nervura do piso da frente (2x)')
    chapas.append(trilho)
    # batente de tras da bateria (y-z)
    base_bt = ret(-Y_TRILHO, Z2, Y_TRILHO, Z_TR)
    batente = Chapa('batente_bateria', base_bt, [], [ret_c(0, Z2 - T / 2, 10, T)], frames=[F_yz(BX0 - T)],
                    descricao='para a bateria atras')
    chapas.append(batente)
    comprada('pino_trava', cilindro((PINO[0], -24.0, PINO[1]), (PINO[0], 27.0, PINO[1]), 3.0), 1.0,
             'fixacao', (0.7, 0.7, 0.7))
    acesso('dedo_pino_trava', caixa(PINO[0] - 5, PINO[0] + 5, 27.0, 50.0, Z2 + 0.5, PINO[1] + 8),
           'puxar o pino de trava da bateria (pelo lado esquerdo)', ignora=('pino_trava',))
    m.PINO = PINO

    # ---------------------------------------------------------------------------- paredes laterais da frente (x-z)
    Z_PF = ZJ - 2.0
    for lado, sy_ in (('esq', 1), ('dir', -1)):
        base_pf = ret(X_PARF0, Z2, X_PARF1 if sy_ > 0 else X_PARF1_DIR, Z_PF)
        fpf = []
        if sy_ < 0:   # parede direita: recorte da chave geral + abracadeira do feixe de energia
            fpf.append(Furo(ret_c(CX, ZCH, cr_w, cr_h), 'chave', funcao='chave geral'))
            for d in (-3.0, 3.0):
                fpf.append(Furo(ret_c(X_PARF0 + 4.5, Z2 + 7 + d, 1.5, 3.5), 'ab_energia_parede', funcao='abracadeira'))
        abas_pf = [ret_c(xc, Z2 - T / 2, 10, T) for xc in (xs_pf if sy_ > 0 else xs_pf_dir)]
        fr = F_xz(Y_PAR + T) if sy_ > 0 else F_xz(-Y_PAR)
        chapas.append(Chapa(f'parede_frente_{lado}', base_pf, fpf, abas_pf, frames=[fr],
                            textos=[('CHAVE' if sy_ < 0 else 'ESQ', CX + 14 if sy_ < 0 else 60, Z2 + 9, 2.5)],
                            descricao='lateral da frente' + (' com a chave geral' if sy_ < 0 else '')))

    # ---------------------------------------------------------------------------- mastro: postes (x-z), travessas, camera
    PVx, PVz = P['PIVO']
    R_ARCO = 9.0
    ZT1, ZT2 = 62.0, 100.0                               # travessas
    TRVx = 120.0
    base_po = so.unary_union([
        sg.Polygon([(PX0, Z2), (PX1, Z2), (PX1, PVz), (PVx - R_ARCO - 5, PVz), (PX0 - 5, 112), (PX0, 78)]),
        sg.Point(PVx, PVz).buffer(10.5), sg.Point(PVx - R_ARCO, PVz).buffer(5.0)])
    abas_po = [ret_c(xc, Z2 - T / 2, 5, T) for xc in (PX0 + 3.5, PX1 - 3.5)]
    fpo = [circ(PVx, PVz, 3.4, 'pivo', 'pivo da camera (M3)'), circ(PVx - R_ARCO, PVz, 3.4, 'trava_angulo', 'trava do angulo (M3)'),
           circ(PINO[0], PINO[1], 3.3, 'pino_trava', 'pino que trava a bateria')]
    for zt_ in (ZT1, ZT2):
        fpo.append(rasgo(TRVx, zt_, S, 8, 'travessa'))
    postes = Chapa('poste_mastro', base_po, fpo, abas_po, frames=[F_xz(PY + T), F_xz(-PY)],
                   textos=[('POSTE', PX0 + 7, 40, 2.5), ('v', PVx, PVz + 8.5, 2.0)], descricao='mastro da camera (2x)')
    chapas.append(postes)
    base_tv = ret(-PY, -4, PY, 4)
    abas_tv = [ret(PY, -4, PY + T, 4), ret(-PY - T, -4, -PY, 4)]
    trav = Chapa('travessa_mastro', base_tv, [], abas_tv,
                 frames=[frame((0, 1, 0), (0, 0, 1), (TRVx - T / 2, 0, zt_)) for zt_ in (ZT1, ZT2)],
                 descricao='degraus do mastro (2x)')
    chapas.append(trav)

    # camera: referencial da orelha (a = eixo otico, c = "cima" da imagem), girado do angulo
    def F_cam(ang, y_lado):
        base = frame((1, 0, 0), (0, 0, 1), (PVx, y_lado, PVz))      # a = x, b = c = z, w = -y
        return F_rot_y(base, ang, (PVx, PVz))
    m.F_cam = F_cam
    YO = PY - T                                          # face interna da orelha
    CA, CC = 2.0, P['CAM_C']                             # placa da camera em a = [CA, CA + T]
    R_OR = 14.0
    base_or = so.unary_union([sg.Point(0, 0).buffer(R_OR), ret(-2, CC - 16, CA + T + 2.5, 0)])
    th0, th1 = 180 + P['CAM_ANG'][0] - 4, 180 + P['CAM_ANG'][1] + 4
    for_ = [circ(0, 0, 3.4, 'pivo', 'pivo'), arco_rasgo(0, 0, R_ARCO, th0, th1, 3.4, 'arco', 'ajuste do angulo'),
            Furo(ret(CA, CC - 8, CA + T if False else CA + S, CC + 8), 'placa_camera', funcao='encaixe')]
    escala = []          # o numero do angulo atual aparece em cima do pivo, alinhado com a marca 'v' do poste
    for ang in range(int(P['CAM_ANG'][0]), int(P['CAM_ANG'][1]) + 1, 10):
        th = math.radians(90 + ang)
        escala.append((f'{ang}', 12.2 * math.cos(th), 12.2 * math.sin(th), 1.6))
    orelha = Chapa('orelha_camera', base_or, for_, textos=escala, frames=[], descricao='suporte giratorio (2x)')
    orelha.qtd = 2
    chapas.append(orelha)
    cw_ = YO                                             # meia largura da placa da camera (entre as orelhas)
    lente_q = v('cam_suporte_lente') + 0.6
    cfx, cfy = v('cam_furos')
    base_pc = ret(-cw_, CC - 15, cw_, CC + 15)
    abas_pc = [ret(cw_, CC - 8, cw_ + T, CC + 8), ret(-cw_ - T, CC - 8, -cw_, CC + 8)]
    fpc = [Furo(ret_c(0, CC, lente_q, lente_q), 'lente', funcao='suporte da lente passa pela placa')]
    fpc += [circ(sx_ * cfx / 2, CC + sy_ * cfy / 2, 2.2, 'camera', 'parafuso M2 da camera') for sx_ in (1, -1) for sy_ in (1, -1)]
    placa_cam = Chapa('placa_camera', base_pc, fpc, abas_pc, frames=[],
                      textos=[('CIMA ^', 0, CC + 12.5, 2.2)], descricao='camera presa por tras, lente para a frente')
    placa_cam.qtd = 1
    chapas.append(placa_cam)
    m.CA, m.CC, m.YO = CA, CC, YO

    def partes_camera(ang):
        """Solidos da camera e do suporte num angulo (para desenho e varredura de interferencia)."""
        out = []
        frL = F_cam(ang, YO + T)     # orelha esquerda: w de 0..T -> y de YO+T ate YO ... (w = -y)
        frR = F_cam(ang, -YO)
        out.append(('orelha_camera_esq', orelha.solido(T).moved(loc(frL)), 'chapa'))
        out.append(('orelha_camera_dir', orelha.solido(T).moved(loc(frR)), 'chapa'))
        # placa da camera: plano (y, c) em a = [CA, CA+T]; referencial a -> x_cam, b -> c, w
        base = F_cam(ang, 0)
        ex, ey, ez, o = base          # ex = a (eixo otico), ey = c (cima), ez = -y
        frp = (-ez, ey, ex, o + CA * ex)                     # local (y, c, a)
        out.append(('placa_camera', placa_cam.solido(T).moved(loc(frp)), 'chapa'))
        pw_, ph_, pt_ = v('cam_placa')
        out.append(('camera_placa', caixa_local(frp, -pw_ / 2, pw_ / 2, CC - ph_ / 2, CC + ph_ / 2, -1.5 - pt_, -1.5),
                    'camera'))
        ld, ll = v('cam_lente')
        p0 = aplicar(frp, 0, CC, -1.5); p1 = aplicar(frp, 0, CC, -1.5 + ll)
        out.append(('camera_lente', cilindro(p0, p1, ld), 'camera'))
        out.append(('camera_conector_ffc', caixa_local(frp, -10, 10, CC - ph_ / 2, CC - ph_ / 2 + 5.5, -1.5 - pt_ - 3, -1.5 - pt_),
                    'camera'))
        m.cam_ffc_pt = aplicar(frp, 0, CC - ph_ / 2 - 1, -1.5 - pt_ - 1.5)
        m.cam_ffc_baixo = aplicar(frp, 0, CC - 15 - 8, -1.5 - pt_ - 3)        # desce por tras da placa da camera
        m.cam_centro = aplicar(frp, 0, CC, -1.5 + ll)
        return out
    m.partes_camera = partes_camera

    # ======================================================================================== CABOS
    def cabo(nome, pontos, d, bitola, de, para, apoio=(), disponivel=None, extra=20.0, ramo=None, obs=''):
        cabos.append(dict(nome=nome, pontos=[tuple(map(float, p)) for p in pontos], d=d, bitola=bitola, de=de, para=para,
                          apoios=list(apoio), disponivel=disponivel, extra=extra, obs=obs))

    zi = Z_XL + 1.6 + 6                        # altura dos bornes
    (xb1, yb1) = xl_pt(0, 0, 24); (xb2, yb2) = xl_pt(1, 0, 24)
    sw = (CX, -Y_PAR + 4, ZCH)
    zb = EZ + 11                               # fios passando por cima do suporte do motor (topo em Z1 + 12)
    ff_ = m.fus
    cabo('pigtail_xt60_fusivel', [(XX, -xl6 - 1, Z2 + 4), (XX - 8, -14.5, Z2 + 3), (106, -14.5, Z2 + 3),
                                  (ff_[1] - 3, (ff_[2] + ff_[3]) / 2, Z2 + 5)],
          4.0, '0,75 mm2 vermelho + preto', 'XT60 do chassi (par solto na frente)', 'entrada da placa do fusivel',
          apoio=['ab_pigtail'], obs='XT60 soldado nesta ponta; termorretratil')
    apoios['ab_energia_parede'] = (X_PARF0 + 4.5, -Y_PAR, Z2 + 7)
    cabo('fusivel_chave', [(ff_[0] + 3, ff_[2] + 3, Z2 + 5), (60, -46, Z2 + 3), (CX + 6, -Y_PAR + 6, ZCH)],
         2.6, '0,75 mm2 vermelho', 'saida do fusivel', 'chave geral (terminal 1)', apoio=['ab_energia_frente'])
    cabo('chave_xl', [sw, (X_PARF0 + 4.5, -Y_PAR + 3, Z2 + 7), (24, -36, zb - 2), (16, -36, zb), (-14, -36, zb),
                      (-17, -32, Z1 + 3), (xb2 + 4, yb2, zi)],
         4.0, '0,75 mm2 vermelho + preto', 'chave geral (terminal 2) + GND do fusivel', 'IN+ / IN- do XL4016 #2',
         apoio=['ab_energia_parede', 'ab_energia_dir'], obs='o GND vem direto da placa do fusivel, junto')
    cabo('jumper_in_xl', [(xb2 + 4, yb2 + 8, zi), (-17.5, 0, Z1 + 11), (xb1 + 4, yb1 - 8, zi)],
         4.0, '0,75 mm2 vermelho + preto', 'IN+ / IN- do XL4016 #2', 'IN+ / IN- do XL4016 #1', apoio=['ab_quilha_janela'])
    cabo('xl1_p4_jetson', [(xb1 + 4, yb1 + 6, zi), (-17, 32, Z1 + 3), (-14, 36, zb), (16, 36, zb), (26, 38, Z2 + 10), (30, 50, Z2 + 4),
                           (60, 50, Z2 + 4), (100, 50, Z2 + 6), (101, 52, Z_PF + 3), (m.p4_fim[0], 62, m.p4_fim[2]),
                           (m.p4_fim[0], m.p4_fim[1] + 2, m.p4_fim[2])],
         4.0, '0,75 mm2 vermelho + preto', 'OUT+ / OUT- do XL4016 #1 (5,2 V)', 'plugue P4 da Jetson (J25)',
         apoio=['ab_p4_esq', 'ab_p4_frente'], obs='P4 reto soldado; testar 5,2 V e polaridade antes de ligar')
    zvm = m.Z_XL_TOPO + 3
    for lado, sy_, (xh, yh), padu in (('e', 1, pf_vm[0], 7.9), ('d', -1, pf_vm[1], 76.8)):
        alvo = esp_pt(padu, 63.5)
        pts = [(xb2 + 4, yb2 + 4 * sy_, zi), (-17.5, 0, Z1 + 11) if sy_ > 0 else (xb2 + 6, -34, zi + 6),
               (-28, sy_ * 46, zvm), (xh, yh, zvm), (xh, yh, ZD + T + 4), (alvo[0], alvo[1], Z_ESP + ET + 2)]
        cabo(f'vm_{lado}', pts, 4.0, '0,75 mm2 vermelho + preto', 'OUT+ / OUT- do XL4016 #2 (7,2 V)',
             f'J{2 if sy_ > 0 else 3} da placa da ESP32 (VM {"esquerdo" if sy_ > 0 else "direito"})',
             apoio=['ab_quilha_janela', 'pf_vm_e'] if sy_ > 0 else ['pf_vm_d'],
             obs='ja soldado na placa: so conferir o comprimento')
    j1 = esp_pt(39.5, 8.5)
    cabo('vbat', [sw, (X_PARF0 + 4.5, -Y_PAR + 3, Z2 + 7), (24, -36, zb - 2), (16, -36, zb), (6, -20, zb + 4), (6, -6, ZD + 6),
                  (EX0 + 4, -2, Z_ESP + 6), (j1[0], j1[1], Z_ESP + ET + 2)],
         1.6, '0,2 mm2 (fio fino)', 'chave geral (terminal 2)', 'J1 (VBAT) da placa da ESP32', apoio=['ab_energia_parede'],
         obs='conector de 1 via (Dupont) no meio para o tampo sair')
    for lado, sy_ in (('esq', 1), ('dir', -1)):
        yc = sy_ * (Y_FIM + 2.5)
        j10 = esp_pt(11.5 if sy_ > 0 else 63.0, 5.75)
        j12 = esp_pt(11 if sy_ > 0 else 72, 45.4)
        cabo(f'motor_{lado}', [(0, yc, EZ + 12), (3, yc + sy_ * 3, ZD - 2), (EX0 + 5, sy_ * 26, Z_ESP + ET + 6),
                               (j10[0], j10[1], Z_ESP + ET + 2), (j10[0] - 6, j10[1] + sy_ * 1, Z_ESP + ET + 3),
                               (j12[0], j12[1], Z_ESP + ET + 2)],
             3.0, 'cabo de 6 vias do motor', f'conector branco do encoder ({lado})', f'J{10 if sy_ > 0 else 11} + J{12 if sy_ > 0 else 13}',
             disponivel=v('motor_cabo'), extra=0.0, obs='cabo original do motor; o comprimento disponivel e estimado')
    xu_, yu_, zu_ = m.esp_usb
    cabo('usb_jetson_esp32', [(xu_ - upl, yu_, zu_), (xu_ - upl - 6, yu_, zu_ + 8), (xu_ - 10, 24, Z_ESP + 22),
                              (-40, 50, ZD + T + 5), (-20, 52, ZD + T + 3), (0, 54, ZD + T + 4), (20, 58, ZJ + 12),
                              (m.usb_a_fim[0], m.usb_a_fim[1] + 4, m.usb_a_fim[2])],
         4.0, 'cabo USB-A / USB-C de dados', 'USB-C da ESP32', 'USB-A da Jetson', apoio=['ab_usb_tampo'],
         disponivel=v('usb_cabo'), extra=0.0, obs='um cabo de 20 cm basta se as pontas forem em angulo')
    pts_j41 = [jet_pt(v('jet_j41_u')[0] + 10, JD - 4) + (ZJ + JT + 10,)]
    pts_j41 += [(8, -44, ZJ + JT + 14), (-8, -47, ZD + T + 3), (m.desl_botao[0] + 4, m.desl_botao[1] + 4, m.desl_botao[2] + 3)]
    cabo('j41_desligar', pts_j41, 3.0, '4 fios Dupont femea', 'J41 pinos 16, 17, 18 e 20', 'placa de desligar',
         apoio=['ab_j41_tampo'], disponivel=150.0, extra=0.0, obs='jumpers Dupont de 15 cm')
    m.cabos_ffc = (jet_pt(np.mean(v('jet_csi_u')), 58) + (ZJ + JT + 4,))
    return m

# ======================================================================================== utilidades
def chapas_3d(m, ang=None):
    """Lista (nome, solido, chapa) de todas as chapas montadas (camera no angulo pedido)."""
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
    """Lista (nome, massa g, centro (x, y, z)) de tudo: chapas (pela densidade) + compradas + fios + miudezas."""
    T = m.T
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
    out.append(('parafusos_porcas', 15.0, (0.0, 0.0, 30.0)))
    out.append(('cola_e_abracadeiras', 4.0, (0.0, 0.0, 30.0)))
    return out

def cg(lista):
    M_ = sum(q[1] for q in lista)
    c = sum(np.array(q[2]) * q[1] for q in lista) / M_
    return M_, c
