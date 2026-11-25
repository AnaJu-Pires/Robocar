# Verificacao automatica do chassi v3 (gerada por `fonte/gerar.py`)

Espessura T = 3.0 mm, rasgo = 2.90 mm. Resultado: **tudo ok** (56 ok, 0 falhas).

| | grupo | verificacao | detalhe |
|---|---|---|---|
| ok | regulamento | comprimento <= 250 mm | 240.2 mm (de x = -98.9 a 141.2, com plugues, cabos e camera em toda a faixa) |
| ok | regulamento | largura <= 150 mm | 139.5 mm (de y = -61.5 a 78.0) |
| ok | regulamento | chassi >= 50 x 60 mm | 238 x 121 mm |
| ok | regulamento | diametro do pneu 20-113 mm | 42 mm |
| ok | regulamento | largura do pneu 11-45 mm | 19 mm |
| ok | regulamento | tensao do motor 3-12 V | 7.2 V (XL4016 #2, D-019) |
| ok | regulamento | rotacao 500-7000 rpm | 750 rpm nominal (6 V), ~900 rpm em vazio a 7,2 V |
| ok | regulamento | 2 rodas tracionadas tocam o chao | z minimo das rodas: 0.00, 0.00 mm |
| ok | regulamento | esfera no chao (carro nivelado) | fundo da esfera a +0.00 mm do chao (piso dianteiro a 15.0 mm, esfera de 15 mm) |
| ok | regulamento | vao livre >= 8 mm (emendas do tapete) | 12.0 mm |
| ok | interferencia | nenhuma sobreposicao | 96 solidos (14 volumes de acesso) |
| ok | camera | camera livre em toda a faixa | 25 a 65 graus, de 5 em 5 |
| ok | camera | a camera nao ve o proprio carro no angulo nominal | 45 graus; livre ate 45 graus (campo vertical estimado 56 graus) |
| ok | material | piso_traseiro | 32 furos, teia >= 2.0 mm, 1 peca |
| ok | material | piso_dianteiro | 30 furos, teia >= 2.0 mm, 1 peca |
| ok | material | tampo | 32 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_lateral | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_traseira | 5 furos, teia >= 2.0 mm, 1 peca |
| ok | material | quilha | 3 furos, teia >= 2.0 mm, 1 peca |
| ok | material | trilho_bateria | 1 furos, teia >= 2.0 mm, 1 peca |
| ok | material | batente_bateria | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_frente_esq | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | parede_frente_dir | 3 furos, teia >= 2.0 mm, 1 peca |
| ok | material | poste_mastro | 5 furos, teia >= 2.0 mm, 1 peca |
| ok | material | travessa_mastro | 0 furos, teia >= 2.0 mm, 1 peca |
| ok | material | orelha_camera | 3 furos, teia >= 2.0 mm, 1 peca |
| ok | material | placa_camera | 5 furos, teia >= 2.0 mm, 1 peca |
| ok | cg | massa total estimada | 633 g; CG x 16.8 / y -1.0 / z 36.1 mm |
| ok | cg | altura do CG <= 40 mm | 36.1 mm |
| ok | cg | CG centrado (|y| <= 3 mm) | -1.0 mm |
| ok | cg | peso nas rodas entre 75 e 92 % | 86 % |
| ok | cg | tomba so acima de 1.15 x mu (escorrega antes) | tomba com 1.11 g; escorrega com 0.90 g |
| ok | cg | empina so acima de 0.40 g | 0.47 g -> rampa do firmware deve limitar a aceleracao abaixo disso |
| ok | cabos | pigtail_xt60_fusivel | rota 45 mm, corte 70 mm |
| ok | cabos | fusivel_chave | rota 26 mm, corte 49 mm |
| ok | cabos | chave_xl | rota 96 mm, corte 125 mm |
| ok | cabos | jumper_in_xl | rota 36 mm, corte 60 mm |
| ok | cabos | xl1_p4_jetson | rota 186 mm, corte 225 mm |
| ok | cabos | vm_e | rota 136 mm, corte 170 mm |
| ok | cabos | vm_d | rota 86 mm, corte 115 mm |
| ok | cabos | vbat | rota 106 mm, corte 136 mm |
| ok | cabos | motor_esq | rota 89 mm, corte 98 mm (tem 150) |
| ok | cabos | motor_dir | rota 90 mm, corte 99 mm (tem 150) |
| ok | cabos | usb_jetson_esp32 | rota 180 mm, corte 198 mm (tem 300) |
| ok | cabos | j41_desligar | rota 79 mm, corte 87 mm (tem 150) |
| ok | cabos | ffc_camera | rota 114 mm, corte 126 mm (tem 150) |
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
| pigtail_xt60_fusivel | 0,75 mm2 vermelho + preto | XT60 do chassi (par solto na frente) | entrada da placa do fusivel | 45 | 70 | — | 28 | XT60 soldado nesta ponta; termorretratil |
| fusivel_chave | 0,75 mm2 vermelho | saida do fusivel | chave geral (terminal 1) | 26 | 49 | — | 14 |  |
| chave_xl | 0,75 mm2 vermelho + preto | chave geral (terminal 2) + GND do fusivel | IN+ / IN- do XL4016 #2 | 96 | 125 | — | 71 | o GND vem direto da placa do fusivel, junto |
| jumper_in_xl | 0,75 mm2 vermelho + preto | IN+ / IN- do XL4016 #2 | IN+ / IN- do XL4016 #1 | 36 | 60 | — | 18 |  |
| xl1_p4_jetson | 0,75 mm2 vermelho + preto | OUT+ / OUT- do XL4016 #1 (5,2 V) | plugue P4 da Jetson (J25) | 186 | 225 | — | 100 | P4 reto soldado; testar 5,2 V e polaridade antes de ligar |
| vm_e | 0,75 mm2 vermelho + preto | OUT+ / OUT- do XL4016 #2 (7,2 V) | J2 da placa da ESP32 (VM esquerdo) | 136 | 170 | — | 93 | ja soldado na placa: so conferir o comprimento |
| vm_d | 0,75 mm2 vermelho + preto | OUT+ / OUT- do XL4016 #2 (7,2 V) | J3 da placa da ESP32 (VM direito) | 86 | 115 | — | 70 | ja soldado na placa: so conferir o comprimento |
| vbat | 0,2 mm2 (fio fino) | chave geral (terminal 2) | J1 (VBAT) da placa da ESP32 | 106 | 136 | — | 92 | conector de 1 via (Dupont) no meio para o tampo sair |
| motor_esq | cabo de 6 vias do motor | conector branco do encoder (esq) | J10 + J12 | 89 | — | 150 | 89 | cabo original do motor; o comprimento disponivel e estimado |
| motor_dir | cabo de 6 vias do motor | conector branco do encoder (dir) | J11 + J13 | 90 | — | 150 | 90 | cabo original do motor; o comprimento disponivel e estimado |
| usb_jetson_esp32 | cabo USB-A / USB-C de dados | USB-C da ESP32 | USB-A da Jetson | 180 | — | 300 | 112 | um cabo de 20 cm basta se as pontas forem em angulo |
| j41_desligar | 4 fios Dupont femea | J41 pinos 16, 17, 18 e 20 | placa de desligar | 79 | — | 150 | 64 | jumpers Dupont de 15 cm |
| ffc_camera | flat 15 vias | CSI da Jetson | camera | 114 | — | 150 | 114 | pior angulo: 65 graus |

## Massas (para refazer o CG depois de pesar)

| item | g | x | y | z | origem |
|---|---|---|---|---|---|
| bateria | 70.0 | 69 | -0 | 26 | V |
| jetson_dissipador | 63.5 | 61 | -14 | 55 | M |
| jetson_placa | 49.3 | 62 | 0 | 39 | M |
| xl4016_1_jetson | 45.0 | -56 | 26 | 31 | E (PESAR) |
| xl4016_2_motores | 45.0 | -56 | -26 | 31 | E (PESAR) |
| placa_esp32 | 40.0 | -38 | -0 | 58 | E (PESAR) |
| piso_traseiro | 29.7 | -37 | -0 | 13 | calculada |
| piso_dianteiro | 28.3 | 71 | -0 | 16 | calculada |
| tampo | 25.1 | -47 | 0 | 50 | calculada |
| motor_esq | 20.0 | 0 | 25 | 21 | V |
| motor_dir | 20.0 | 0 | -25 | 21 | V |
| roda_esq | 19.0 | -0 | 52 | 21 | V |
| roda_dir | 19.0 | -0 | -52 | 21 | V |
| parafusos_porcas | 15.0 | 0 | 0 | 30 | calculada |
| par_xt60 | 8.0 | 133 | 0 | 22 | calculada |
| placa_fusivel | 8.0 | 85 | -29 | 25 | E |
| camera | 8.0 | 122 | 0 | 114 | E |
| quilha | 7.6 | -43 | -0 | 32 | calculada |
| parede_traseira | 7.5 | -92 | 0 | 33 | calculada |
| jetson_usb | 7.1 | 40 | 33 | 48 | M |
| jetson_rj45 | 7.1 | 21 | 33 | 47 | M |
| jetson_hdmi_dp | 7.1 | 69 | 33 | 44 | M |
| esfera_base | 6.0 | 121 | 0 | 12 | E |
| parede_lateral_1 | 5.3 | -58 | 56 | 32 | calculada |
| parede_lateral_2 | 5.3 | -58 | -56 | 32 | calculada |
| poste_mastro_1 | 4.8 | 119 | 18 | 89 | calculada |
| poste_mastro_2 | 4.8 | 119 | -18 | 89 | calculada |
| placa_desligar | 4.0 | -19 | -50 | 56 | E |
| chave_geral | 4.0 | 44 | -48 | 27 | E |
| cola_e_abracadeiras | 4.0 | 0 | 0 | 30 | calculada |
| trilho_bateria_1 | 3.9 | 72 | 11 | 26 | calculada |
| trilho_bateria_2 | 3.9 | 72 | -11 | 26 | calculada |
| parede_frente_esq | 3.6 | 68 | 56 | 26 | calculada |
| fio_xl1_p4_jetson | 3.4 | 44 | 46 | 30 | calculada |
| fio_vm_e | 2.4 | -44 | 25 | 44 | calculada |
| suporte_motor_esq | 2.0 | 0 | 35 | 21 | E |
| suporte_motor_dir | 2.0 | 0 | -35 | 21 | E |
| fio_chave_xl | 1.7 | 9 | -38 | 27 | calculada |
| orelha_camera_esq | 1.6 | 117 | 16 | 136 | calculada |
| orelha_camera_dir | 1.6 | 117 | -15 | 136 | calculada |
| placa_camera | 1.6 | 110 | 0 | 126 | calculada |
| fio_vm_d | 1.6 | -44 | -40 | 45 | calculada |
| parede_frente_dir | 1.1 | 46 | -56 | 25 | calculada |
| espacador_jetson_1 | 1.0 | 105 | 29 | 28 | calculada |
| espacador_jetson_2 | 1.0 | 105 | -29 | 28 | calculada |
| espacador_jetson_3 | 1.0 | 19 | 29 | 28 | calculada |
| espacador_jetson_4 | 1.0 | 19 | -29 | 28 | calculada |
| pino_trava | 1.0 | 121 | 1 | 22 | calculada |
| fio_pigtail_xt60_fusivel | 0.8 | 116 | -19 | 22 | calculada |
| batente_bateria | 0.8 | 18 | -0 | 25 | calculada |
| fio_usb_jetson_esp32 | 0.7 | -33 | 39 | 61 | calculada |
| travessa_mastro_1 | 0.7 | 120 | -0 | 62 | calculada |
| travessa_mastro_2 | 0.7 | 120 | -0 | 100 | calculada |
| fio_jumper_in_xl | 0.7 | -19 | 0 | 26 | calculada |
| espacador_xl1_4_4 | 0.5 | -28 | 46 | 17 | calculada |
| espacador_xl1_61_4 | 0.5 | -85 | 46 | 17 | calculada |
| espacador_xl1_61_44 | 0.5 | -85 | 6 | 17 | calculada |
| espacador_xl1_4_44 | 0.5 | -28 | 6 | 17 | calculada |
| espacador_xl2_4_4 | 0.5 | -28 | -6 | 17 | calculada |
| espacador_xl2_61_4 | 0.5 | -85 | -6 | 17 | calculada |
| espacador_xl2_61_44 | 0.5 | -85 | -46 | 17 | calculada |
| espacador_xl2_4_44 | 0.5 | -28 | -46 | 17 | calculada |
| **total** | **633** | **16.8** | **-1.0** | **36.1** | |

## Fixadores (contados pelos furos)

| item | qtd |
|---|---|
| Espacador M2.5 x 20 mm (femea-femea) + parafuso M2.5 x 6 embaixo e em cima | 3 |
| Parafuso M2 x 16 + porca (vem com o suporte do N20) | 4 |
| Parafuso M2 x 8 + porca + arruela fina (camera) | 4 |
| Parafuso M2.5 x 8 CABECA CHATA (escareado) por cima + porca embaixo; escarear o furo a mao | 2 |
| Parafuso M3 x 10 + espacador M3 x 3 mm + porca | 2 |
| Parafuso M3 x 10 + espacador nylon M3 x 5 mm + porca | 4 |
| Parafuso M3 x 10 + porca | 4 |
| Parafuso M3 x 10 + porca (pivo da camera, um de cada lado) | 2 |
| Parafuso M3 x 10 + porca borboleta (trava do angulo, um de cada lado) | 2 |
| Parafuso M3 x 12 + porca + espacador nylon M3 x 4 mm (ou 2 porcas) | 8 |
| Parafuso M3 x 12 + porca M3 presa no bolso da parede | 4 |
| Pino de trava: arame/prego de 3 mm x 50 mm dobrado em L | 1 |
