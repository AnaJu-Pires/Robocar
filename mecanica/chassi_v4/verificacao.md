# Verificacao automatica do chassi v4 (gerada por `fonte/gerar.py`)

Espessura T = 3.0 mm, rasgo = 2.90 mm. Resultado: **tudo ok** (55 ok, 0 falhas).

| | grupo | verificacao | detalhe |
|---|---|---|---|
| ok | regulamento | comprimento <= 250 mm | 161.7 mm (de x = -55.8 a 105.9, com plugues, cabos e camera em toda a faixa) |
| ok | regulamento | largura <= 150 mm | 143.0 mm (de y = -71.5 a 71.5) |
| ok | regulamento | chassi >= 50 x 60 mm | 159 x 121 mm |
| ok | regulamento | diametro do pneu 20-113 mm | 42 mm |
| ok | regulamento | largura do pneu 11-45 mm | 19 mm |
| ok | regulamento | tensao do motor 3-12 V | 7.2 V (XL4016 #2, D-019) |
| ok | regulamento | rotacao 500-7000 rpm | 750 rpm nominal (6 V), ~900 rpm em vazio a 7,2 V |
| ok | regulamento | 2 rodas tracionadas tocam o chao | z minimo das rodas: 0.00, 0.00 mm |
| ok | regulamento | esfera no chao (carro nivelado) | fundo da esfera a +0.00 mm do chao (piso dianteiro a 15.0 mm, esfera de 15 mm) |
| ok | regulamento | vao livre >= 8 mm (emendas do tapete) | 12.0 mm |
| ok | interferencia | nenhuma sobreposicao | 95 solidos (13 volumes de acesso) |
| ok | camera | camera livre em toda a faixa | 25 a 65 graus, de 5 em 5 |
| ok | camera | a camera nao ve o proprio carro no angulo nominal | 45 graus; livre ate 45 graus (campo vertical estimado 56 graus) |
| ok | material | piso_traseiro | 13 furos, teia >= 2.0 mm, 1 peca |
| ok | material | piso_dianteiro | 18 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_berco_tras | 3 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_berco_frente | 3 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_berco_esq | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_frente | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | andar2 | 33 furos, teia >= 2.0 mm, 1 peca |
| ok | material | pilar_tras | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | pilar_frente | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | andar3 | 23 furos, teia >= 2.0 mm, 1 peca |
| ok | material | poste_mastro | 3 furos, teia >= 2.0 mm, 1 peca |
| ok | material | travessa_mastro | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | orelha_camera | 3 furos, teia >= 2.0 mm, 1 peca |
| ok | material | placa_camera | 5 furos, teia >= 2.0 mm, 1 peca |
| ok | cg | massa total estimada | 657 g; CG x 21.7 / y -1.6 / z 49.8 mm |
| ok | cg | CG centrado (|y| <= 3 mm) | -1.6 mm |
| ok | cg | peso nas rodas entre 70 e 92 % | 77 % |
| ok | cg | tomba so acima de 1.15 x a aceleracao lateral permitida | tomba com 0.77 g; permitido 0.65 g (curva R100 a ate 0.80 m/s; atrito 0.90) |
| ok | cg | empina so acima de 0.40 g | 0.44 g -> rampa do firmware deve limitar a aceleracao abaixo disso |
| ok | cabos | pigtail_xt60_fusivel | rota 93 mm, corte 122 mm |
| ok | cabos | fusivel_chave | rota 54 mm, corte 80 mm |
| ok | cabos | chave_xl | rota 96 mm, corte 126 mm |
| ok | cabos | jumper_in_xl | rota 37 mm, corte 61 mm |
| ok | cabos | xl1_p4_jetson | rota 89 mm, corte 118 mm |
| ok | cabos | vm_e | rota 172 mm, corte 209 mm |
| ok | cabos | vm_d | rota 118 mm, corte 150 mm |
| ok | cabos | vbat | rota 162 mm, corte 199 mm |
| ok | cabos | motor_esq | rota 122 mm, corte 134 mm (tem 150) |
| ok | cabos | motor_dir | rota 125 mm, corte 138 mm (tem 150) |
| ok | cabos | usb_jetson_esp32 | rota 64 mm, corte 70 mm (tem 300) |
| ok | cabos | j41_desligar | rota 90 mm, corte 99 mm (tem 150) |
| ok | cabos | ffc_camera | rota 123 mm, corte 135 mm (tem 150) |
| ok | medidas | conferir antes de cortar: jet_furo_d | diametro do furo (M2.5); define centros = borda - d |
| ok | medidas | conferir antes de cortar: jet_furo_u0 | distancia da ponta do P4 ao centro do 1o furo; None = furos centrados |
| ok | medidas | conferir antes de cortar: jet_furo_v0 | distancia da borda das portas ao centro do furo; None = centrados |
| ok | medidas | conferir antes de cortar: cam_furos | furos M2 21 x 12,5 mm |
| ok | medidas | conferir antes de cortar: cam_lente | diametro e comprimento da lente a partir da face da placa |
| ok | medidas | conferir antes de cortar: cam_suporte_lente | base quadrada do suporte da lente (passa no furo da placa da camera) |
| ok | medidas | conferir antes de cortar: xl_altura | altura total (placa + dissipador) - loja diz 65 x 46 x 24 |
| ok | medidas | conferir antes de cortar: xl_furos | centros dos 4 furos M3 |
| ok | medidas | conferir antes de cortar: xl_trimpots | parafusos dos trimpots (l, w), regulagem por CIMA |
| ok | medidas | conferir antes de cortar: chave_recorte | KCD1-101: recorte 19 x 13; conferir a sua |

## Cabos: rota e comprimento de corte

Corte = rota x 1,10 + 20 mm (descascar, terminal, termorretratil). Cabos prontos (motor, USB, flat, Dupont) so sao conferidos.

| cabo | bitola | de | para | rota (mm) | corte (mm) | disponivel | maior trecho solto (mm) | obs |
|---|---|---|---|---|---|---|---|---|
| pigtail_xt60_fusivel | 0,75 mm2 vermelho + preto | XT60 do chassi (par solto, a direita da bateria) | entrada da placa do fusivel | 93 | 122 | — | 61 | XT60 soldado nesta ponta; termorretratil |
| fusivel_chave | 0,75 mm2 vermelho | saida do fusivel | chave geral (terminal 1) | 54 | 80 | — | 31 |  |
| chave_xl | 0,75 mm2 vermelho + preto | chave geral (terminal 2) + GND do fusivel | IN+ / IN- do XL4016 #1 | 96 | 126 | — | 65 | sai pela janela da parede do berco e passa por cima dos motores |
| jumper_in_xl | 0,75 mm2 vermelho + preto | IN+ / IN- do XL4016 #1 | IN+ / IN- do XL4016 #2 | 37 | 61 | — | 37 |  |
| xl1_p4_jetson | 0,75 mm2 vermelho + preto | OUT+ / OUT- do XL4016 #1 (5,2 V) | plugue P4 da Jetson (J25) | 89 | 118 | — | 45 | P4 reto soldado; testar 5,2 V e polaridade antes de ligar |
| vm_e | 0,75 mm2 vermelho + preto | OUT+ / OUT- do XL4016 #2 (7,2 V) | J2 da placa da ESP32 | 172 | 209 | — | 97 | ja soldado na placa: so conferir o comprimento |
| vm_d | 0,75 mm2 vermelho + preto | OUT+ / OUT- do XL4016 #2 (7,2 V) | J3 da placa da ESP32 | 118 | 150 | — | 55 | ja soldado na placa: so conferir o comprimento |
| vbat | 0,2 mm2 (fio fino) | chave geral (terminal 2) | J1 (VBAT) da placa da ESP32 | 162 | 199 | — | 84 | conector de 1 via (Dupont) no meio para o andar 3 sair |
| motor_esq | cabo de 6 vias do motor | conector branco do encoder (esq) | J12 + J10 | 122 | — | 150 | 67 | cabo original do motor; o comprimento disponivel e estimado |
| motor_dir | cabo de 6 vias do motor | conector branco do encoder (dir) | J13 + J11 | 125 | — | 150 | 67 | cabo original do motor; o comprimento disponivel e estimado |
| usb_jetson_esp32 | cabo USB-A / USB-C de dados | USB-C da ESP32 (andar 3, tras) | USB-A da Jetson (andar 2, tras) | 64 | — | 300 | 64 | cabo curto: 15-20 cm bastam |
| j41_desligar | 4 fios Dupont femea | J41 pinos 16, 17, 18 e 20 | placa de desligar (andar 3) | 90 | — | 150 | 60 | jumpers Dupont de 15 cm; sobem pela borda direita do andar 3 |
| ffc_camera | flat 15 vias | CSI da Jetson | camera | 123 | — | 150 | 123 | pior angulo: 65 graus |

## Massas (para refazer o CG depois de pesar)

| item | g | x | y | z | origem |
|---|---|---|---|---|---|
| bateria | 70.0 | -37 | -2 | 22 | V |
| jetson_dissipador | 63.5 | 54 | -1 | 75 | M |
| jetson_placa | 49.3 | 40 | 0 | 59 | M |
| xl4016_1_jetson | 45.0 | 62 | 26 | 34 | E (PESAR) |
| xl4016_2_motores | 45.0 | 62 | -26 | 34 | E (PESAR) |
| placa_esp32 | 40.0 | 13 | -0 | 108 | E (PESAR) |
| andar2 | 39.9 | 25 | -0 | 52 | calculada |
| andar3 | 26.0 | 23 | 0 | 100 | calculada |
| piso_dianteiro | 23.4 | 59 | -0 | 16 | calculada |
| motor_esq | 20.0 | 0 | 34 | 21 | V |
| motor_dir | 20.0 | 0 | -34 | 21 | V |
| piso_traseiro | 19.7 | -13 | -0 | 14 | calculada |
| roda_esq | 19.0 | -0 | 62 | 21 | V |
| roda_dir | 19.0 | -0 | -62 | 21 | V |
| parafusos_porcas | 18.0 | 20 | 0 | 50 | calculada |
| parede_berco_tras | 9.3 | -48 | -2 | 32 | calculada |
| parede_berco_frente | 8.4 | -26 | -0 | 31 | calculada |
| par_xt60 | 8.0 | -36 | -61 | 29 | calculada |
| placa_fusivel | 8.0 | -35 | 9 | 60 | E |
| camera | 8.0 | 88 | 0 | 120 | E |
| jetson_usb | 7.1 | 7 | -22 | 68 | M |
| jetson_rj45 | 7.1 | 7 | -41 | 67 | M |
| jetson_hdmi_dp | 7.1 | 7 | 7 | 64 | M |
| esfera_base | 6.0 | 94 | -0 | 12 | E |
| parede_frente_1 | 4.9 | 59 | 56 | 33 | calculada |
| parede_frente_2 | 4.9 | 59 | -56 | 33 | calculada |
| chave_geral | 4.0 | -39 | 28 | 41 | E |
| placa_desligar | 4.0 | 23 | -50 | 106 | E |
| cola_e_abracadeiras | 4.0 | 20 | 0 | 50 | calculada |
| fio_vm_e | 3.1 | -0 | 27 | 66 | calculada |
| poste_mastro_1 | 3.0 | 76 | 18 | 128 | calculada |
| poste_mastro_2 | 3.0 | 76 | -18 | 128 | calculada |
| fio_vm_d | 2.1 | -0 | -35 | 66 | calculada |
| pilar_tras_1 | 2.1 | -4 | 56 | 75 | calculada |
| pilar_tras_2 | 2.1 | -4 | -56 | 75 | calculada |
| pilar_frente_1 | 2.1 | 60 | 56 | 75 | calculada |
| pilar_frente_2 | 2.1 | 60 | -56 | 75 | calculada |
| suporte_motor_esq | 2.0 | 0 | 45 | 21 | E |
| suporte_motor_dir | 2.0 | 0 | -45 | 21 | E |
| parede_berco_esq | 1.8 | -37 | 56 | 32 | calculada |
| fio_chave_xl | 1.7 | -7 | 21 | 38 | calculada |
| fio_pigtail_xt60_fusivel | 1.7 | -38 | -45 | 48 | calculada |
| fio_xl1_p4_jetson | 1.6 | -5 | 35 | 49 | calculada |
| orelha_camera_esq | 1.6 | 83 | 16 | 142 | calculada |
| orelha_camera_dir | 1.6 | 83 | -16 | 142 | calculada |
| placa_camera | 1.6 | 76 | -0 | 132 | calculada |
| pino_trava | 1.0 | -40 | -55 | 19 | calculada |
| espacador_jetson_1 | 1.0 | 11 | 43 | 56 | calculada |
| espacador_jetson_2 | 1.0 | 69 | 43 | 56 | calculada |
| espacador_jetson_3 | 1.0 | 11 | -43 | 56 | calculada |
| espacador_jetson_4 | 1.0 | 69 | -43 | 56 | calculada |
| travessa_mastro | 0.7 | 64 | -0 | 109 | calculada |
| fio_jumper_in_xl | 0.7 | 26 | 0 | 28 | calculada |
| fio_motor_dir | 0.6 | 12 | -27 | 75 | calculada |
| fio_motor_esq | 0.6 | 12 | 28 | 75 | calculada |
| espacador_xl1_4_4 | 0.5 | 34 | 6 | 20 | calculada |
| espacador_xl1_61_4 | 0.5 | 91 | 6 | 20 | calculada |
| espacador_xl1_61_44 | 0.5 | 91 | 46 | 20 | calculada |
| espacador_xl1_4_44 | 0.5 | 34 | 46 | 20 | calculada |
| espacador_xl2_4_4 | 0.5 | 34 | -46 | 20 | calculada |
| espacador_xl2_61_4 | 0.5 | 91 | -46 | 20 | calculada |
| espacador_xl2_61_44 | 0.5 | 91 | -6 | 20 | calculada |
| espacador_xl2_4_44 | 0.5 | 34 | -6 | 20 | calculada |
| **total** | **657** | **21.7** | **-1.6** | **49.8** | |

## Fixadores (contados pelos furos)

| item | qtd |
|---|---|
| Espacador M2.5 x 5 mm + parafuso M2.5 x 12 + porca (Jetson no andar 2) | 4 |
| Parafuso M2 x 16 + porca (vem com o suporte do N20) | 4 |
| Parafuso M2 x 8 + porca + arruela fina (camera) | 4 |
| Parafuso M2.5 x 8 + porca (esfera) | 2 |
| Parafuso M3 x 10 + espacador M3 x 3 mm + porca | 2 |
| Parafuso M3 x 10 + espacador nylon M3 x 5 mm + porca | 4 |
| Parafuso M3 x 10 + porca (pivo da camera, um de cada lado) | 2 |
| Parafuso M3 x 10 + porca (une os 2 pisos) | 2 |
| Parafuso M3 x 10 + porca borboleta (trava do angulo, um de cada lado) | 2 |
| Parafuso M3 x 12 + porca + espacador nylon M3 x 4 mm (ou 2 porcas) | 8 |
| Parafuso M3 x 12 + porca M3 presa no bolso da parede (andar 2) | 4 |
| Parafuso M3 x 12 + porca M3 presa no bolso do pilar (andar 3) | 4 |
| Pino de trava: arame/prego de 3 mm x 35 mm dobrado em L | 1 |
