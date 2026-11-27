# Testes negativos das verificacoes (gerado por `fonte/testes_negativos.py`)

Cada linha planta um defeito de proposito e confere que a verificacao FALHA (pega o defeito).

| defeito plantado | verificacao | pegou? | o que ela disse |
|---|---|---|---|
| (nenhum: projeto como esta) | todas | passou, como deve | 55 verificacoes |
| regulamento: comprimento > 250 mm (esfera 100 mm mais para a frente) | regulamento | sim | comprimento <= 250 mm: 261.6 mm (de x = -55.8 a 205.9, com plugues, cabos e camera em toda a faixa) |
| regulamento: largura > 150 mm (bitola de 140 mm) | regulamento | sim | largura <= 150 mm: 159.0 mm (de y = -79.5 a 79.5) |
| regulamento: pneu de 120 mm | regulamento | sim | diametro do pneu 20-113 mm: 120 mm |
| regulamento: esfera de 18 mm (carro torto) | regulamento | sim | esfera no chao (carro nivelado): fundo da esfera a -3.00 mm do chao (piso dianteiro a 15.0 mm, esfera de 18 mm) |
| interferencia: XL4016 da esquerda 12 mm para fora (bate na parede) | interferencia | sim | parede_frente_1 x xl4016_1_jetson: 4281.8 mm3 |
| interferencia: Jetson sem espacador (solda encosta no andar 2) | interferencia | sim | andar2 x jetson_solda: 14539.2 mm3 |
| interferencia: bateria 20 mm para a frente (sai pela direita passando pela roda) | interferencia | sim | parede_berco_frente x roda_esq: 538.3 mm3 |
| acesso: XL4016 10 mm para tras (trimpots embaixo da Jetson) | interferencia | sim | jetson_placa x chave_trimpot_xl1_1: 15.7 mm3 |
| acesso: Jetson 20 mm para tras (em cima do fusivel) | interferencia | sim | jetson_placa x placa_fusivel: 12.0 mm3 |
| acesso: vao de 3 mm em cima do dissipador (sem ar) | interferencia | sim | andar3 x ar_dissipador: 7197.1 mm3 |
| camera: pivo 30 mm mais baixo (camera bate no andar 3 em algum angulo) | camera | sim | 25 graus: orelha_camera_esq x jetson_dissipador: 55.2 mm3 |
| camera: angulo nominal de 65 graus (a imagem pega o carro) | camera | sim | a camera nao ve o proprio carro no angulo nominal: 65 graus; livre ate 45 graus (campo vertical estimado 56 graus) |
| material: furo da esfera a 0,5 mm da borda | material | sim | piso_dianteiro: furo "esfera" a 0.50 mm da borda (min 2.0) |
| material: furo da esfera passa da borda (vira entalhe) | material | sim | piso_dianteiro: ENTALHE: furo "esfera" encosta ou passa da borda (vira entalhe sem querer); 18 furos viraram 17 buracos (furos sobrepostos ou na borda |
| material: pilar em cima da porca do andar 2 (furos se juntam) | material | sim | andar2: pouco material entre furos: "parede_frente" x "pilar" (1.40 mm, min 2.0); FUROS SE JUNTAM: "andar2" x "pilar" (0.00 mm, min 2.0); pouco materi |
| material: chave passando da borda da parede (vira entalhe) | material | sim | parede_berco_tras: FUROS SE JUNTAM: "parede_lateral" x "chave" (0.00 mm, min 2.0); ENTALHE: furo "chave" encosta ou passa da borda (vira entalhe sem q |
| material: corte em anel (o miolo cai: peca que se solta) | material | sim | teste_ilha: a chapa se divide em 2 pedacos (peca que se solta) |
| material: aba de 1,5 mm (parte fina) | material | sim | teste_aba_fina: parte do contorno mais fina que 2.0 mm perto de (20.8, 35.0) |
| material: gravacao em cima de furo | material | sim | teste_gravacao: gravacao "TEXTO" cai em furo ou fora da peca |
| cg: 120 g no alto (tomba antes do limite de curva) | cg | sim | tomba so acima de 1.15 x a aceleracao lateral permitida: tomba com 0.61 g; permitido 0.65 g (curva R100 a ate 0.80 m/s; atrito 0.90) |
| cg: sem limite de curva por software (tomba antes de escorregar) | cg | sim | tomba so acima de 1.15 x a aceleracao lateral permitida: tomba com 0.77 g; permitido 0.90 g (curva R100 a ate 0.94 m/s; atrito 0.90) |
| cg: 80 g de lastro de lado (CG fora do centro) | cg | sim | CG centrado (/y/ <= 3 mm): +4.6 mm |
| cg: 150 g de lastro atras (empina) | cg | sim | empina so acima de 0.40 g: 0.14 g -> rampa do firmware deve limitar a aceleracao abaixo disso |
| cabos: cabo do motor de 90 mm (curto) | cabos | sim | motor_esq: precisa de 139 mm e tem 90 mm |
| cabos: bitola de 86 mm (fios passam a menos de 3 mm da roda) | cabos | sim | chave_xl: a menos de 3 mm de roda_esq |
| cabos: passa-fio do P4 apagado (fio atravessa o andar 2) | cabos | sim | xl1_p4_jetson: atravessa a chapa andar2 |
| cabos: passa-fio apagado da lista de apoios | cabos | sim | xl1_p4_jetson: apoio "pf_p4" nao existe nas chapas |
| cabos: passa-fio do motor de volta embaixo da placa de interface (cabo atravessa a placa) | cabos | sim | motor_dir: atravessa a placa_desligar |
| cabos: cabo USB de 50 mm | cabos | sim | usb_jetson_esp32: precisa de 70 mm e tem 50 mm |
| medidas: --para-cortar com medidas estimadas | medidas | sim | conferir antes de cortar: jet_furo_d: diametro do furo (M2.5); define centros = borda - d |
| dxf: DXF gravado com a Jetson 1 mm diferente da medida | dxf | sim | furos da Jetson no DXF: 86.30 x 57.30 mm (1 esperado) |

Tempo: 152 s.
