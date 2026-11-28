# Verificacao automatica do chassi v4 (gerada por `fonte/gerar.py`)

Espessura T = 3.0 mm, rasgo = 2.90 mm. Resultado: **tudo ok** (70 ok, 0 falhas).

| | grupo | verificacao | detalhe |
|---|---|---|---|
| ok | regulamento | comprimento <= 250 mm | 175.7 mm (de x = -55.8 a 120.0, com plugues, cabos e camera em toda a faixa) |
| ok | regulamento | largura <= 150 mm | 143.0 mm (de y = -71.5 a 71.5) |
| ok | regulamento | chassi >= 50 x 60 mm | 168 x 121 mm |
| ok | regulamento | diametro do pneu 20-113 mm | 42 mm |
| ok | regulamento | largura do pneu 11-45 mm | 19 mm |
| ok | regulamento | tensao do motor 3-12 V | 7.2 V (XL4016 #2, D-019) |
| ok | regulamento | rotacao 500-7000 rpm | 750 rpm nominal (6 V), ~900 rpm em vazio a 7,2 V |
| ok | regulamento | 2 rodas tracionadas tocam o chao | z minimo das rodas: 0.00, 0.00 mm |
| ok | regulamento | esfera no chao (carro nivelado) | fundo da esfera a +0.00 mm do chao (piso dianteiro a 15.0 mm, esfera de 15 mm) |
| ok | regulamento | vao livre >= 8 mm (emendas do tapete) | 12.0 mm |
| ok | interferencia | nenhuma sobreposicao | 106 solidos (13 volumes de acesso) |
| ok | folga | encoder_esq | cresce 0.5/0.5/1/0/0/0.5 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | conector_motor_esq | cresce 0.5/0.5/1/0/0/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | encoder_dir | cresce 0.5/0.5/0/1/0/0.5 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | conector_motor_dir | cresce 0.5/0.5/0/1/0/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | xl4016_1_jetson | cresce 0/1/0/1/0/2 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | xl4016_2_motores | cresce 0/1/1/0/0/2 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | bateria | cresce 0.5/0.5/1/1/0/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | par_xt60 | cresce 1/1/1/1/1/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | jetson_dissipador | cresce 1/1/1/1/0/0 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | plugue_p4 | cresce 3/0/0.5/0.5/0.5/0.5 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | plugue_usb_a | cresce 3/0/1/1/1/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | chave_geral | cresce 0/2/0/0/0/0 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | fusivel_5x20 | cresce 0.5/0.5/0.5/0.5/0/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | esp32_devkit | cresce 0.5/0.5/0.5/0.5/0/1.5 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | drv8833_esq | cresce 0.5/0.5/0.5/0.5/0/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | drv8833_dir | cresce 0.5/0.5/0.5/0.5/0/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | c470_esq | cresce 0.5/0.5/0.5/0.5/0/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | c470_dir | cresce 0.5/0.5/0.5/0.5/0/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | plugue_usb_esp32 | cresce 3/0/1/1/1/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | botao_desligar | cresce 1/1/1/1/3/0 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | folga | botao_capa | cresce 1/1/1/1/0/1 mm (x-/x+/y-/y+/z-/z+): cabe |
| ok | camera | camera livre em toda a faixa | 25 a 65 graus, de 5 em 5 |
| ok | camera | a camera nao ve o proprio carro no angulo nominal | 45 graus; livre ate 50 graus (campo vertical estimado 56 graus) |
| ok | material | piso_traseiro | 13 furos, teia >= 2.0 mm, 1 peca |
| ok | material | piso_dianteiro | 18 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_berco_tras | 3 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_berco_frente | 3 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_berco_esq | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_frente | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | andar2 | 36 furos, teia >= 2.0 mm, 1 peca |
| ok | material | pilar_tras | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | pilar_frente | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | andar3 | 21 furos, teia >= 2.0 mm, 1 peca |
| ok | material | poste_mastro | 3 furos, teia >= 2.0 mm, 1 peca |
| ok | material | travessa_mastro | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | orelha_camera | 4 furos, teia >= 2.0 mm, 1 peca |
| ok | material | placa_camera | 4 furos, teia >= 2.0 mm, 1 peca |
| ok | material | placa_luz | 1 furos, teia >= 2.0 mm, 1 peca |
| ok | cg | massa total estimada | 671 g; CG x 21.6 / y -1.6 / z 50.5 mm |
| ok | cg | CG centrado (|y| <= 3 mm) | -1.6 mm |
| ok | cg | peso nas rodas entre 70 e 92 % | 77 % |
| ok | cg | tomba so acima de 1.15 x a aceleracao lateral permitida | tomba com 0.76 g; permitido 0.65 g (curva R100 a ate 0.80 m/s; atrito 0.90) |
| ok | cg | empina so acima de 0.40 g | 0.43 g -> rampa do firmware deve limitar a aceleracao abaixo disso |
| ok | cabos | pigtail_xt60_fusivel | rota 102 mm, corte 132 mm |
| ok | cabos | fusivel_chave | rota 64 mm, corte 91 mm |
| ok | cabos | chave_placa | rota 65 mm, corte 91 mm |
| ok | cabos | alim_xl1 | rota 119 mm, corte 151 mm |
| ok | cabos | alim_xl2 | rota 114 mm, corte 145 mm |
| ok | cabos | xl1_p4_jetson | rota 89 mm, corte 118 mm |
| ok | cabos | vm_e | rota 178 mm, corte 216 mm |
| ok | cabos | vm_d | rota 124 mm, corte 156 mm |
| ok | cabos | vbat | rota 143 mm, corte 177 mm |
| ok | cabos | motor_esq | rota 126 mm, corte 139 mm (tem 150) |
| ok | cabos | motor_dir | rota 129 mm, corte 141 mm (tem 150) |
| ok | cabos | usb_jetson_esp32 | rota 64 mm, corte 70 mm (tem 300) |
| ok | cabos | j41_desligar | rota 62 mm, corte 68 mm (tem 150) |
| ok | cabos | luz | rota 311 mm, corte 402 mm |
| ok | cabos | ffc_camera | rota 115 mm, corte 127 mm (tem 150) |
| ok | medidas | conferir antes de cortar: chave_recorte | KCD1-101: lojas pedem 19,2 x 13,2 (faixa 18-19,2 x 12-13,2). Cortamos 19 x 13: se apertar, lixar 0,2 mm; se cortasse maior, a chave ficaria solta. CONFERIR NO PENTE DE TESTE (teste_chave) |
| ok | dxf | furos da Jetson no DXF | 85.30 x 57.30 mm (1 esperado) |
| ok | dxf | furos da placa da ESP32 no DXF | 73.0 x 66.0 mm (1 esperado) |
| ok | dxf | furos dos 2 XL4016 no DXF | 57.0 x 40.0 mm (2 esperados) |
| ok | dxf | furos da camera no DXF | 21.0 x 12.5 mm |
| ok | dxf | furos da esfera no DXF | 16.0 mm |
| ok | dxf | furos do pino de trava no DXF | 2 esperados |
| ok | dxf | furos de fixacao das pecas compradas so gravados (furar a mao) | 0 cortados (Jetson 2,9 / camera 2,2 / esfera 2,8 mm); esperado 0 |

## Cabos: rota e comprimento de corte

Corte = rota x 1,10 + 20 mm (descascar, terminal, termorretratil). Cabos prontos (motor, USB, flat, Dupont) so sao conferidos.

| cabo | bitola | de | para | rota (mm) | corte (mm) | disponivel (mm) | maior trecho solto (mm) | obs |
|---|---|---|---|---|---|---|---|---|
| pigtail_xt60_fusivel | 0,75 mm2 vermelho + preto | XT60 do chassi (par solto, a direita da bateria) | BAT+ / BAT- da placa de distribuicao | 102 | 132 | do rolo | 70 | XT60 soldado nesta ponta; termorretratil |
| fusivel_chave | 0,75 mm2 vermelho | CHAVE 1 (FUS+) da placa de distribuicao | chave geral (terminal 1) | 64 | 91 | do rolo | 42 | soldar ou apertar nas duas pontas; termorretratil |
| chave_placa | 0,75 mm2 vermelho | chave geral (terminal 2) | CHAVE 2 (SW+) da placa de distribuicao | 65 | 91 | do rolo | 42 | soldar ou apertar nas duas pontas; termorretratil |
| alim_xl1 | 0,75 mm2 vermelho + preto | XL1 + / XL1 - da placa de distribuicao | IN+ / IN- do XL4016 #1 (Jetson) | 119 | 151 | do rolo | 69 | um par por conversor (sem jumper de um borne para o outro) |
| alim_xl2 | 0,75 mm2 vermelho + preto | XL2 + / XL2 - da placa de distribuicao | IN+ / IN- do XL4016 #2 (motores) | 114 | 145 | do rolo | 72 | um par por conversor (sem jumper de um borne para o outro) |
| xl1_p4_jetson | 0,75 mm2 vermelho + preto | OUT+ / OUT- do XL4016 #1 (5,2 V) | plugue P4 da Jetson (J25) | 89 | 118 | do rolo | 45 | P4 reto soldado; testar 5,2 V e polaridade antes de ligar |
| vm_e | 0,75 mm2 vermelho + preto | OUT+ / OUT- do XL4016 #2 (7,2 V) | J2 da placa da ESP32 | 178 | 216 | do rolo | 97 | ja soldado na placa: so conferir o comprimento |
| vm_d | 0,75 mm2 vermelho + preto | OUT+ / OUT- do XL4016 #2 (7,2 V) | J3 da placa da ESP32 | 124 | 156 | do rolo | 55 | ja soldado na placa: so conferir o comprimento |
| vbat | 0,2 mm2 (fio fino) | VBAT (SW+) da placa de distribuicao | J1 (VBAT) da placa da ESP32 | 143 | 177 | do rolo | 83 | conector de 1 via (Dupont) no meio para o andar 3 sair |
| motor_esq | cabo de 6 vias do motor | conector branco do encoder (esq) | J12 + J10 | 126 | cabo pronto | 150 | 84 | cabo original do motor; o comprimento disponivel e estimado |
| motor_dir | cabo de 6 vias do motor | conector branco do encoder (dir) | J13 + J11 | 129 | cabo pronto | 150 | 84 | cabo original do motor; o comprimento disponivel e estimado |
| usb_jetson_esp32 | cabo USB-A / USB-C de dados | USB-C da ESP32 (andar 3, tras) | USB-A da Jetson (andar 2, tras) | 64 | cabo pronto | 300 | 64 | cabo curto: 15-20 cm bastam |
| j41_desligar | 3 fios Dupont femea | J41 pinos 17 (3V3), 18 (botao) e 20 (GND) | botao de desligar (embaixo do andar 3) | 62 | cabo pronto | 150 | 62 | resistor de 10k soldado no botao, entre o 3V3 e o pino 18 (D-040) |
| luz | cabo USB da propria fita (sem o controle de toque) | porta USB da Jetson (tras) | fita COB (atras da placa da luz) | 311 | 402 | do rolo | 101 | tirar o controle de toque (PWM faz faixas na imagem) e emendar a fita direto no cabo USB (D-040) |
| ffc_camera | flat 15 vias | CSI da Jetson | camera | 115 | cabo pronto | 150 | 115 | pior angulo: 65 graus |

## Massas (para refazer o CG depois de pesar)

| item | g | x | y | z | origem |
|---|---|---|---|---|---|
| bateria | 70.0 | -37 | -2 | 22 | V |
| jetson_dissipador | 63.5 | 54 | -1 | 75 | M |
| jetson_placa | 49.3 | 40 | 0 | 59 | M |
| xl4016_1_jetson | 45.0 | 62 | 26 | 34 | E (PESAR) |
| xl4016_2_motores | 45.0 | 62 | -26 | 34 | E (PESAR) |
| placa_esp32 | 40.0 | 13 | -0 | 108 | E (PESAR) |
| andar2 | 39.8 | 25 | -0 | 52 | calculada |
| andar3 | 25.8 | 23 | 1 | 100 | calculada |
| piso_dianteiro | 23.4 | 59 | -0 | 16 | calculada |
| motor_esq | 20.0 | 0 | 34 | 21 | V |
| motor_dir | 20.0 | 0 | -34 | 21 | V |
| piso_traseiro | 19.7 | -13 | -0 | 14 | calculada |
| roda_esq | 19.0 | -0 | 62 | 21 | V |
| roda_dir | 19.0 | -0 | -62 | 21 | V |
| parafusos_porcas | 18.0 | 20 | 0 | 50 | calculada |
| placa_fusivel | 12.0 | -36 | 9 | 64 | E |
| parede_berco_tras | 9.3 | -48 | -2 | 32 | calculada |
| parede_berco_frente | 8.4 | -26 | -0 | 31 | calculada |
| par_xt60 | 8.0 | -36 | -61 | 29 | calculada |
| camera | 8.0 | 94 | 0 | 114 | E |
| jetson_usb | 7.1 | 7 | -22 | 68 | M |
| jetson_rj45 | 7.1 | 7 | -41 | 67 | M |
| jetson_hdmi_dp | 7.1 | 7 | 7 | 64 | M |
| botao_desligar | 6.0 | 40 | -50 | 88 | E |
| esfera_base | 6.0 | 94 | -0 | 12 | E |
| parede_frente_1 | 4.9 | 59 | 56 | 33 | calculada |
| parede_frente_2 | 4.9 | 59 | -56 | 33 | calculada |
| chave_geral | 4.0 | -41 | 28 | 41 | E |
| cola_e_abracadeiras | 4.0 | 20 | 0 | 50 | calculada |
| fio_vm_e | 3.2 | -2 | 29 | 72 | calculada |
| poste_mastro_1 | 3.0 | 76 | 18 | 128 | calculada |
| poste_mastro_2 | 3.0 | 76 | -18 | 128 | calculada |
| fio_vm_d | 2.2 | -2 | -36 | 72 | calculada |
| fio_alim_xl1 | 2.1 | -3 | 20 | 52 | calculada |
| placa_camera | 2.1 | 76 | -0 | 132 | calculada |
| pilar_tras_1 | 2.1 | -4 | 56 | 75 | calculada |
| pilar_tras_2 | 2.1 | -4 | -56 | 75 | calculada |
| pilar_frente_1 | 2.1 | 60 | 56 | 75 | calculada |
| pilar_frente_2 | 2.1 | 60 | -56 | 75 | calculada |
| fio_alim_xl2 | 2.1 | -3 | -6 | 52 | calculada |
| suporte_motor_esq | 2.0 | 0 | 45 | 21 | E |
| suporte_motor_dir | 2.0 | 0 | -45 | 21 | E |
| orelha_camera_esq | 2.0 | 87 | 15 | 146 | calculada |
| orelha_camera_dir | 2.0 | 87 | -16 | 146 | calculada |
| fio_pigtail_xt60_fusivel | 1.8 | -39 | -40 | 56 | calculada |
| parede_berco_esq | 1.8 | -37 | 56 | 32 | calculada |
| fio_xl1_p4_jetson | 1.6 | -5 | 35 | 49 | calculada |
| placa_luz | 1.3 | 105 | 0 | 161 | calculada |
| fio_luz | 1.2 | 27 | 13 | 114 | calculada |
| zener_vm | 1.2 | 24 | -31 | 21 | calculada |
| pino_trava | 1.0 | -40 | -55 | 19 | calculada |
| espacador_jetson_1 | 1.0 | 11 | 43 | 56 | calculada |
| espacador_jetson_2 | 1.0 | 69 | 43 | 56 | calculada |
| espacador_jetson_3 | 1.0 | 11 | -43 | 56 | calculada |
| espacador_jetson_4 | 1.0 | 69 | -43 | 56 | calculada |
| travessa_mastro | 0.7 | 64 | -0 | 109 | calculada |
| fio_motor_dir | 0.6 | 27 | -23 | 80 | calculada |
| fio_motor_esq | 0.6 | 27 | 24 | 80 | calculada |
| fio_chave_placa | 0.6 | -35 | 34 | 60 | calculada |
| fio_fusivel_chave | 0.6 | -40 | 34 | 60 | calculada |
| espacador_xl1_4_4 | 0.5 | 34 | 6 | 20 | calculada |
| espacador_xl1_61_4 | 0.5 | 91 | 6 | 20 | calculada |
| espacador_xl1_61_44 | 0.5 | 91 | 46 | 20 | calculada |
| espacador_xl1_4_44 | 0.5 | 34 | 46 | 20 | calculada |
| espacador_xl2_4_4 | 0.5 | 34 | -46 | 20 | calculada |
| espacador_xl2_61_4 | 0.5 | 91 | -46 | 20 | calculada |
| espacador_xl2_61_44 | 0.5 | 91 | -6 | 20 | calculada |
| espacador_xl2_4_44 | 0.5 | 34 | -6 | 20 | calculada |
| espacador_dist_14_4 | 0.5 | -37 | 27 | 58 | calculada |
| espacador_dist_15_39 | 0.5 | -37 | -8 | 58 | calculada |
| **total** | **671** | **21.6** | **-1.6** | **50.5** | |

## Fixadores (contados pelos furos)

| item | qtd |
|---|---|
| Espacador nylon M2.5 x 5 mm + parafuso M2.5 x 12 (NAO mais comprido: 2 deles ficam a 4 mm do XL4016) + porca (Jetson no andar 2) | 4 |
| Espacador nylon M3 x 10 mm femea-femea + 2 parafusos M3 x 6 (um por cima, um por baixo). O de tras fica 2,8 mm acima da chave: por baixo, cabeca chata escareada ou cola | 2 |
| Parafuso M2 x 12 + espacador nylon M2.5 x 5 mm (sobra do pacote da Jetson) + porca (camera na frente da placa) | 4 |
| Parafuso M2 x 16 + porca (vem com o suporte do N20) | 4 |
| Parafuso M2.5 x 10 + porca (esfera) | 2 |
| Parafuso M3 x 10 + porca (pivo da camera, um de cada lado) | 2 |
| Parafuso M3 x 10 + porca (une os 2 pisos) [3 + 3 + porca 2,4 = 8,4] | 2 |
| Parafuso M3 x 12 + porca + espacador nylon M3 x 4 mm (ou 2 porcas) [placa 1,6 + 4 + MDF 3 + porca 2,4 = 11] | 8 |
| Parafuso M3 x 12 + porca M3 presa no bolso da parede (andar 2) | 4 |
| Parafuso M3 x 12 + porca M3 presa no bolso do pilar (andar 3) | 4 |
| Parafuso M3 x 12 + porca borboleta (trava do angulo, um de cada lado) | 2 |
| Parafuso M3 x 14 + espacador nylon M3 x 5 mm + porca [1,6 + 5 + 3 + porca 2,4 = 12] | 4 |
| Pino de trava: arame/prego de 3 mm x 35 mm dobrado em L | 1 |
