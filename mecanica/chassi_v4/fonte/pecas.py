"""Pecas compradas do Robocar Blitz: medidas, massas e de onde veio cada numero.

Fonte unica para o gerador do chassi (modelo.py), as verificacoes e a analise.
Cada medida tem uma ORIGEM:
  'M'  medida pela equipe (paquimetro, balanca) ou informada como fato no pedido de 25/11
  'V'  de documento confiavel (datasheet, KiCad da nossa placa, pagina da loja)
  'E'  estimada: CONFERIR antes de cortar se 'afeta_corte' for True
Para atualizar depois de medir: troque o valor e a origem para 'M'. O gerador lista o que ainda falta.
"""

def med(valor, origem, nota='', afeta_corte=False):
    return {'v': valor, 'o': origem, 'nota': nota, 'corte': afeta_corte}

# ------------------------------------------------------------------------------------------- medidas
M = {
    # Jetson Nano Developer Kit B01 (carrier P3449). u = ao longo dos 100 mm (u = 0 na ponta do P4/J25),
    # v = ao longo dos 80 mm (v = 0 na borda das portas), z = a partir da face de baixo da placa.
    'jet_placa':        med((100.0, 80.0, 1.6), 'V', 'placa P3449 100 x 80'),
    'jet_furos_borda':  med((88.0, 60.0), 'M', 'borda externa a borda externa dos furos (paquimetro)'),
    'jet_furo_d':       med(2.7, 'E', 'diametro do furo (M2.5); define centros = borda - d', afeta_corte=True),
    'jet_furo_u0':      med(None, 'E', 'distancia da ponta do P4 ao centro do 1o furo; None = furos centrados', afeta_corte=True),
    'jet_furo_v0':      med(None, 'E', 'distancia da borda das portas ao centro do furo; None = centrados', afeta_corte=True),
    'jet_altura':       med(29.0, 'V', 'da face de baixo da placa ao topo do dissipador (Arducam: 100 x 80 x 29)'),
    'jet_dissipador':   med((22.0, 80.0, 30.0, 79.0), 'E', 'caixa do dissipador em u0, u1, v0, v1'),
    'jet_p4_u':         med(9.0, 'E', 'centro do jack J25 ao longo da borda das portas'),
    'jet_usb_u':        med((64.0, 80.0), 'E', 'pilha de USB-A (u0, u1)'),
    'jet_rj45_u':       med((83.0, 99.0), 'E', 'RJ45 (u0, u1)'),
    'jet_hdmi_dp_u':    med((26.0, 60.0), 'E', 'HDMI + DP'),
    'jet_j41_u':        med((47.0, 98.0), 'E', 'barra de 40 pinos ao longo da borda oposta as portas'),
    'jet_csi_u':        med((1.0, 12.0), 'M', 'CSI na ponta oposta a barra de 40 pinos (fato do pedido); posicao exata E'),
    'jet_sd_u':         med((26.0, 42.0), 'E', 'microSD embaixo do modulo, sai pela borda v = 80'),
    'jet_massa':        med(141.0, 'M', 'Jetson + camera = 149 g medido; camera estimada em 8 g'),
    # Camera IMX219-160
    'cam_placa':        med((25.0, 24.0, 1.0), 'E', 'placa 25 x 24 (formato da camera do RPi)'),
    'cam_furos':        med((21.0, 12.5), 'E', 'furos M2 21 x 12,5 mm', afeta_corte=True),
    'cam_lente':        med((12.0, 19.0), 'E', 'diametro e comprimento da lente a partir da face da placa', afeta_corte=True),
    'cam_suporte_lente': med(14.0, 'E', 'base quadrada do suporte da lente (passa no furo da placa da camera)', afeta_corte=True),
    'cam_massa':        med(8.0, 'E'),
    'cam_vfov':         med(56.0, 'E', 'campo de visao vertical no modo 1280x720 (fracao do sensor x 160 graus)'),
    'ffc_compr':        med(150.0, 'E', 'cabo flat da camera'),
    # Motores N20 750 rpm com encoder (RoboCore)
    'motor_corpo':      med(35.0, 'M', 'do redutor ao fim do encoder, sem o eixo'),
    'motor_redutor':    med((12.0, 10.0, 9.0), 'V', 'secao 12 x 10, comprimento do redutor ~9'),
    'motor_eixo':       med(10.0, 'V', 'eixo D 3 mm com 10 mm'),
    'motor_massa':      med(20.0, 'V', 'RoboCore'),
    'motor_rpm_6v':     med(750.0, 'V'),
    'motor_stall_kgfcm': med(1.7, 'V', 'torque de travamento a 6 V'),
    'motor_stall_a':    med(1.6, 'V'),
    'motor_cabo':       med(150.0, 'E', 'comprimento do cabo de 6 vias do conector branco ate a ponta'),
    # Suporte branco do N20 (Smart Kits SK1915): funcionou bem na v1
    'sup_motor':        med((25.0, 12.0, 12.0), 'M', 'x (perpendicular ao eixo) x y x z'),
    'sup_motor_eixo_z': med(6.0, 'E', 'altura do eixo do motor acima da base do suporte', afeta_corte=False),
    'sup_motor_furos':  med((17.0, 21.6), 'E', 'faixa de distancia entre furos (por isso os rasgos oblongos da v1)'),
    # Rodas e esfera
    'roda':             med((42.0, 19.0), 'M', 'diametro x largura'),
    'roda_massa':       med(19.0, 'V'),
    'esfera_altura':    med(15.0, 'M', 'da face de fixacao ao chao'),
    'esfera_furos':     med(16.0, 'V', 'furos M2.5 a 16 mm (desenho RoboCore)', afeta_corte=True),
    'esfera_corpo':     med((22.0, 12.0), 'E', 'caixa em planta da base da esfera (x, y)'),
    'esfera_massa':     med(6.0, 'E'),
    # Bateria RoboCore 3S 1100 mAh
    'bat':              med((100.0, 18.0, 15.0), 'M'),
    'bat_massa':        med(70.0, 'V'),
    'bat_cabo':         med(70.0, 'E', 'comprimento dos fios do XT60 da bateria'),
    'xt60':             med((16.0, 15.5, 8.0), 'V', 'comprimento x largura x altura do corpo'),
    # XL4016 (2 unidades). l = ao longo dos 65 mm (l = 0 na ponta dos bornes), w = ao longo dos 48 mm
    'xl':               med((65.0, 48.0), 'M', 'com os dissipadores; bornes numa ponta, trimpots na outra'),
    'xl_altura':        med(24.0, 'E', 'altura total (placa + dissipador) - loja diz 65 x 46 x 24', afeta_corte=True),
    'xl_furos':         med(((4.0, 4.0), (61.0, 4.0), (61.0, 44.0), (4.0, 44.0)), 'E', 'centros dos 4 furos M3', afeta_corte=True),
    'xl_trimpots':      med(((60.0, 14.0), (60.0, 26.0)), 'E', 'parafusos dos trimpots (l, w), regulagem por CIMA', afeta_corte=True),
    'xl_bornes':        med((0.0, 9.0, 11.0), 'E', 'bloco de bornes: l0, l1, altura'),
    'xl_massa':         med(45.0, 'E', 'PESAR: planilha da equipe 35-70 g'),
    # Placa da ESP32 v0.8 (hardware/placa_esp32, KiCad): verificada
    'esp_placa':        med((80.0, 73.0, 1.6), 'V'),
    'esp_furos':        med(((3.5, 3.5), (76.5, 3.5), (76.5, 69.5), (3.5, 69.5)), 'V', 'M3 nos cantos (u, v)'),
    'esp_devkit':       med((25.9, 54.0, 15.3, 66.9), 'V', 'ESP32 DevKit em u0, u1, v0, v1 (USB em v1)'),
    'esp_altura':       med(15.0, 'E', 'da face de cima da placa ao topo da ESP32 (barra femea 8,5 + DevKit)'),
    'esp_usb_plugue':   med((22.0, 12.0, 7.0), 'E', 'plugue USB-C reto: comprimento x largura x altura'),
    'esp_massa':        med(40.0, 'E', 'PESAR montada com os fios'),
    # Placa do fusivel (ja feita) e placa extra de desligar
    'fus_placa':        med((32.0, 44.0, 22.0), 'V', 'placa de distribuicao (hardware/placa_distribuicao): 32 x 44; altura com espacador de 10 mm e fusivel'),
    'fus_massa':        med(12.0, 'E', 'placa + fusivel + diodo + 2 espacadores'),
    'desl_placa':       med((40.0, 18.0, 14.0), 'V', 'placa de interface: medidas e posicoes em hardware/placa_desligar/layout.json'),
    # Chave, plugues, cabos
    'chave_recorte':    med((19.0, 13.0), 'E', 'KCD1-101: recorte 19 x 13; conferir a sua', afeta_corte=True),
    'chave_corpo':      med((21.0, 15.0, 18.0), 'E', 'moldura x profundidade atras do painel'),
    'p4_plugue':        med((30.0, 10.0), 'E', 'P4 reto soldavel: comprimento x diametro'),
    'usb_a_plugue':     med((32.0, 16.0, 9.0), 'E', 'USB-A reto com capa'),
    'usb_cabo':         med(300.0, 'E', 'cabo USB Jetson-ESP32'),
    'massa_mdf_dens':   med(0.75, 'E', 'g/cm3: PESAR o pente de teste para confirmar'),
}

def v(nome):
    return M[nome]['v']

def pendencias():
    """Medidas estimadas que mudam o desenho de corte (devem ser conferidas antes de cortar)."""
    return [(k, d['nota']) for k, d in M.items() if d['o'] == 'E' and d['corte']]

# ------------------------------------------------------------------------------------------- massas
# (nome, gramas, origem, pesar?) - a posicao vem do modelo
MASSAS = {
    'jetson': (v('jet_massa'), 'M', False),
    'camera': (v('cam_massa'), 'E', False),
    'motor': (v('motor_massa'), 'V', False),
    'suporte_motor': (2.0, 'E', False),
    'roda': (v('roda_massa'), 'V', False),
    'esfera': (v('esfera_massa'), 'E', False),
    'bateria': (v('bat_massa'), 'V', False),
    'xl4016': (v('xl_massa'), 'E', True),
    'placa_esp32': (v('esp_massa'), 'E', True),
    'placa_fusivel': (v('fus_massa'), 'E', False),
    'placa_desligar': (4.0, 'E', False),
    'chave': (4.0, 'E', False),
    'xt60_chassi': (4.0, 'E', False),
    'cabo_usb': (12.0, 'E', True),
    'espacadores_parafusos': (20.0, 'E', True),
}
