# Testes negativos das verificacoes (gerado por `fonte/testes_negativos.py`)

Cada linha planta um defeito de proposito e confere que a verificacao FALHA (pega o defeito).

| defeito plantado | verificacao | pegou? | o que ela disse |
|---|---|---|---|
| (nenhum: projeto como esta) | todas | passou, como deve | 56 verificacoes |
| regulamento: comprimento > 250 mm (XL4016 16 mm mais para tras) | regulamento | sim | comprimento <= 250 mm: 254.2 mm (de x = -113.0 a 141.2, com plugues, cabos e camera em toda a faixa) |
| regulamento: largura > 150 mm (bitola de 140 mm) | regulamento | sim | largura <= 150 mm: 159.0 mm (de y = -79.5 a 79.5) |
| regulamento: pneu de 120 mm | regulamento | sim | diametro do pneu 20-113 mm: 120 mm |
| regulamento: esfera de 18 mm (carro torto) | regulamento | sim | esfera no chao (carro nivelado): fundo da esfera a -3.00 mm do chao (piso dianteiro a 15.0 mm, esfera de 18 mm) |
| interferencia: XL4016 da esquerda 12 mm para fora (bate na parede) | interferencia | sim | parede_lateral_1 x xl4016_1_jetson: 4494.8 mm3 |
| interferencia: Jetson 6 mm mais baixa (encosta na bateria) | interferencia | sim | trilho_bateria_1 x jetson_placa: 436.8 mm3 |
| acesso: placa da ESP32 cobre os trimpots (ESP 12 mm para tras) | interferencia | sim | placa_esp32 x chave_trimpot_xl1_1: 23.5 mm3 |
| acesso: parede direita ate a frente (tampa o fusivel) | interferencia | sim | parede_frente_dir x dedo_fusivel: 600.0 mm3 |
| acesso: fusivel 10 mm para a frente (bate no espacador da Jetson) | interferencia | sim | espacador_jetson_2 x placa_fusivel: 274.9 mm3 |
| camera: pivo 45 mm mais baixo (camera bate no mastro/Jetson em algum angulo) | camera | sim | 25 graus: orelha_camera_esq x travessa_mastro_2: 68.0 mm3 |
| camera: angulo nominal de 65 graus (a imagem pega o carro) | camera | sim | a camera nao ve o proprio carro no angulo nominal: 65 graus; livre ate 45 graus (campo vertical estimado 56 graus) |
| material: furo da esfera a 0,1 mm da borda (esfera em x = 139,5) | material | sim | piso_dianteiro: furo "esfera" a 0.10 mm da borda (min 2.0); furo "esfera" a 0.10 mm da borda (min 2.0) |
| material: furo da esfera passa da borda (vira entalhe) | material | sim | piso_dianteiro: ENTALHE: furo "esfera" encosta ou passa da borda (vira entalhe sem querer); ENTALHE: furo "esfera" encosta ou passa da borda (vira ent |
| material: chave em cima das abracadeiras (furos se juntam) | material | sim | parede_frente_dir: FUROS SE JUNTAM: "chave" x "ab_energia_parede" (0.00 mm, min 2.0); FUROS SE JUNTAM: "chave" x "ab_energia_parede" (0.00 mm, min 2.0 |
| material: chave passando da borda da parede (vira entalhe) | material | sim | parede_frente_dir: ENTALHE: furo "chave" encosta ou passa da borda (vira entalhe sem querer); 3 furos viraram 0 buracos (furos sobrepostos ou na borda |
| material: corte em anel (o miolo cai: peca que se solta) | material | sim | teste_ilha: a chapa se divide em 2 pedacos (peca que se solta) |
| material: aba de 1,5 mm (parte fina) | material | sim | teste_aba_fina: parte do contorno mais fina que 2.0 mm perto de (20.8, 35.0) |
| material: gravacao em cima de furo | material | sim | teste_gravacao: gravacao "TEXTO" cai em furo ou fora da peca |
| cg: Jetson 40 mm mais alta (CG alto e tomba antes de escorregar) | cg | sim | tomba so acima de 1.15 x mu (escorrega antes): tomba com 0.74 g; escorrega com 0.90 g |
| cg: 60 g de lastro de lado (CG fora do centro) | cg | sim | CG centrado (/y/ <= 3 mm): +3.4 mm |
| cg: 150 g de lastro atras (empina e tira peso da esfera) | cg | sim | empina so acima de 0.40 g: -0.10 g -> rampa do firmware deve limitar a aceleracao abaixo disso |
| cabos: cabo do motor de 60 mm (curto) | cabos | sim | motor_esq: precisa de 98 mm e tem 60 mm |
| cabos: bitola de 92 mm (cabos de energia encostam na roda) | cabos | sim | chave_xl: a menos de 3 mm de roda_dir |
| cabos: tampo 3 mm acima dos XL4016 (fio do VM atravessa o tampo) | cabos | sim | vm_e: atravessa a chapa tampo |
| cabos: abracadeira do passa-fio apagada | cabos | sim | vm_e: apoio "pf_vm_e" nao existe nas chapas; trecho solto de 114 mm (max 110: falta abracadeira) |
| cabos: cabo USB de 150 mm | cabos | sim | usb_jetson_esp32: precisa de 198 mm e tem 150 mm |
| medidas: --para-cortar com medidas estimadas | medidas | sim | conferir antes de cortar: jet_furo_d: diametro do furo (M2.5); define centros = borda - d |

Tempo: 113 s.
