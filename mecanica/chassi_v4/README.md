# Robocar Blitz — chassi v4 (3 andares)

MDF 3 mm cortado a laser, 2 chapas de 390 × 270 mm. Substitui o [v3](../chassi_v3/) (240 mm de comprimento, muito
perto do limite de 250). Tudo sai de `fonte/` (Python + CadQuery + ezdxf): o `make chassi` gera os arquivos e
**para com erro se qualquer verificação falhar**.

![Frente e lado direito](imagens/vista_3d.png)

| | **v4 (3 andares)** | v3 |
|---|---|---|
| Tamanho total (com plugues, cabos e câmera em toda a faixa) | **162 × 143 × 160 mm** | 240 × 140 × 154 mm |
| Folga até o limite de 250 × 150 | **88 mm** no comprimento, 7 mm na largura | 10 mm / 10 mm |
| Massa estimada | 657 g | 633 g |
| Centro de massa (x à frente do eixo / y / altura) | 21,7 / −1,6 / **49,8 mm** | 16,8 / −1,0 / 36,1 mm |
| Peso nas rodas de tração | 77 % | 86 % |
| Tomba com | **0,77 g** → curva R100 a no máximo **0,80 m/s** ([D-032](../../docs/decisoes.md)) | 1,11 g |
| Levanta a esfera com | 0,44 g (`controle.acel_max` = 2,0/s ≈ 0,4 g) | 0,47 g |
| Peças de MDF | 19 (14 desenhos) | 18 |
| Verificações | 51 ok (interferência com 14 volumes de acesso; câmera em 9 ângulos; 6 releem o DXF) · **30 testes negativos, todos pegos** · 10 medidas a conferir | 52 · 28 |

## Peças compradas como estão no modelo

Não são fotos: é o desenho que o chassi usa para cada peça, com as medidas e de onde veio cada uma (medido, documento ou **ESTIMADO**). Ponha a peça real ao lado: o que estiver estimado e for diferente, corrija em `fonte/pecas.py` e rode `make chassi`. A placa da ESP32 é o render do KiCad da placa de vocês.

![Peças no modelo](imagens/pecas_no_modelo.png)

## 1. Quem fica em cada andar ([D-031](../../docs/decisoes.md))

```
 z (mm)
 99-102   ANDAR 3  placa da ESP32 (largada, USB, LED e EN/BOOT por cima) + placa de interface + mastro curto da câmera
 50-53    ANDAR 2  Jetson de través (100 mm na largura), portas para TRÁS; atrás dela: placa do fusível
 12-18    ANDAR 1  motores no eixo · 2 XL4016 à frente do eixo · bateria atravessada atrás (sai pela direita) + chave
          trás ◄── x = −56 ─────── 0 (eixo) ─────────────────────────── 106 ──► frente
```

| Andar | Por quê |
|---|---|
| 1: XL4016 + bateria | são ~160 g: o mais baixo possível. Os XL4016 ficam à frente do eixo, com os bornes virados para ele e os trimpots para a frente, onde o andar 2 tem furos de 7 mm para a chave de fenda. A bateria fica atravessada atrás da roda e sai pela direita em segundos |
| 2: Jetson | é a peça mais pesada (141 g): no meio, não em cima. Com 100 mm na largura e as portas para trás, os plugues P4 e USB ficam **dentro do comprimento** e o carro não alarga |
| 3: ESP32 | é a mais leve (40 g) e a que se usa na corrida: largada, LED, USB de gravação e EN/BOOT ficam por cima, sem tirar nada. Os cabos para a Jetson, os motores e a placa de interface são curtos |

Comparação das ordens possíveis, com as mesmas peças ([analise.md](analise.md)):

| Ordem | CG | Tomba com | Comprimento | Problema |
|---|---|---|---|---|
| **XL4016 + bateria / Jetson / ESP32 (escolhida)** | 49,8 mm | 0,77 g | 162 mm | precisa de limite de curva por software |
| XL4016 + bateria / ESP32 / Jetson | 57,1 mm | 0,67 g | 162 mm | tomba ainda antes; largada e USB da ESP32 embaixo da Jetson |
| Jetson / XL4016 / ESP32 | 47,8 mm | 0,87 g | 177 mm | XL4016 aquecendo em cima do dissipador da Jetson; mais longo |

**O custo dos 3 andares é o CG mais alto.** O carro tomba (levanta uma roda) com 0,77 g de aceleração lateral, antes
dos 0,9 g em que o pneu escorrega. Por isso a curva de R100 tem de ser feita a **no máximo 0,80 m/s** (0,65 g), o que
dá ~0,40 de `v` na escala do controle. Hoje o controle anda a `v_max` = 0,35 (≈ 0,7 m/s): está dentro. Ao subir a
velocidade, a regra é a da [D-032](../../docs/decisoes.md). Bitola de 124 mm (era 104): a base mais larga compensa
parte da altura e a largura total (143 mm) continua dentro dos 150.

## 2. Rodas

Ficam as de 42 mm ([D-027](../../docs/decisoes.md)): a análise da v4 dá o mesmo resultado
(seção 2 de [analise.md](analise.md)). Na v4 a curva é limitada pelo software (0,80 m/s) e não pelo motor.

## 3. Placa de interface (botão de desligar, LEDs e luz da câmera)

[hardware/placa_desligar/](../../hardware/placa_desligar/) ([D-028](../../docs/decisoes.md) e D-033). Na v4 a
painel do operador (**43 × 18 mm** desde 27/11, D-035) fica no **andar 3, à direita da placa da ESP32**: botão, LED vermelho
("Jetson ligada / apagou = pode desligar a chave") e LED amarelo ("código rodando") ficam por cima, e o J41 da
Jetson fica logo abaixo (8 jumpers de 15 cm). A posição da placa, dos 2 furos e das peças vem de
`hardware/placa_desligar/layout.json` (D-034). **Falta no modelo:** a luz e o módulo da luz no mastro, que entram
quando soubermos qual luz foi comprada.

## 4. Temperatura

* Jetson: **11 mm livres em cima do dissipador** (verificado), com o andar 3 por cima e os lados abertos; andando, o ar
  passa de frente para trás. É menos ar que no v3 (dissipador aberto): **medir antes de correr** (T16:
  `tegrastats` ≤ 70 °C em 15 min de `make carro`). Se passar, a ventoinha 4010 de 5 V cabe nos 11 mm (J15) sem mudar
  o chassi; outra opção é o modo 5 W.
* XL4016: no andar 1, com 4 mm até o andar 2; frente e lados abertos.
* Bateria: atrás, longe dos XL4016.

## 5. Ergonomia de corrida

| Operação | Como | Onde |
|---|---|---|
| **Trocar a bateria** | chave OFF → separar o par XT60 (em pé, na ponta direita da bateria) → puxar o pino de trava por trás → deslizar a bateria para a direita | lado direito, atrás da roda |
| Chave geral | gangorra na parede de trás do berço | traseira, à esquerda |
| Largada | botão LARGADA do painel do operador (S3, fita colorida), por cima | andar 3, direita |
| Desligar a Jetson | botão da placa de interface, 2 s; esperar o LED vermelho **apagar**; só então a chave geral | andar 3, direita |
| Trimpots dos XL4016 | chave de fenda **curta** (≤ 40 mm) pelos 4 furos de 7 mm do andar 2, na frente da Jetson | frente, entre os andares 2 e 3 |
| Ângulo da câmera (25–65°) | soltar as 2 porcas borboleta, girar, ler o número gravado em cima do pivô, apertar | topo do mastro |
| Gravar a ESP32 | USB-C na traseira da placa | andar 3, trás |
| SSH | Wi-Fi (adaptador na USB livre) ou Ethernet: as portas da Jetson ficam viradas para trás | andar 2, trás |
| microSD | sai pela borda da frente da Jetson, entre os andares 2 e 3 (verificado) | frente |
| Fusível | por cima, atrás do andar 3 (verificado) | andar 2, trás |
| Tirar o andar 3 sem mexer na Jetson | 4 parafusos M3 (porcas presas nos pilares) + Dupont do VBAT + conectores dos motores + USB | andar 3 |
| Tirar a Jetson com o andar 2 | 4 parafusos M3 do andar 2 (porcas presas nas paredes do andar 1) + P4 + flat; a Jetson sai parafusada no andar 2 | andar 2 |

## 6. Fiação, montagem e inspeção

[MONTAGEM.md](MONTAGEM.md) traz os cabos (rota, corte, apoio) e a ordem de montagem. A tabela é gerada pelo modelo em
[verificacao.md](verificacao.md). [INSPECAO.md](INSPECAO.md) traz o checklist do regulamento.

**Atenção:** os fios do VM já soldados na placa da ESP32 precisam ter **≥ 216 mm (esquerdo) e ≥ 156 mm (direito)** na v4 (D-034),
porque a placa está no andar 3. Se forem mais curtos, emende com 0,75 mm² e termorretrátil.

## 7. Pesos

O mesmo do v3: pesar os XL4016, a placa da ESP32 montada e as peças do pente de teste; trocar em `fonte/pecas.py`;
`make chassi-verificar`. Na v4 o que mais pesa no tombamento é a altura: a ESP32 e a Jetson. Mande o resultado.

## Arquivos e comandos

Mesma organização do v3 (ver [o README do v3](../chassi_v3/README.md#arquivos)). Peças:

| Peça | Qtd | Função |
|---|---|---|
| piso_traseiro / piso_dianteiro | 1 + 1 | motores e berço / XL4016 e esfera (sobrepostos: esfera de 15 mm sem calço) |
| parede_berco_tras | 1 | berço da bateria, apoio do andar 2, chave geral, furo do pino |
| parede_berco_frente | 1 | berço, apoio do andar 2, furo do pino, janela dos fios da chave |
| parede_berco_esq | 1 | batente esquerdo da bateria |
| parede_frente | 2 | laterais do andar 1; porcas presas do andar 2 |
| andar2 | 1 | Jetson, placa do fusível, furos dos trimpots e passa-fios |
| pilar_tras / pilar_frente | 2 + 2 | sustentam o andar 3; porcas presas |
| andar3 | 1 | placa da ESP32, placa de interface, mastro |
| poste_mastro, travessa_mastro | 2 + 1 | mastro curto da câmera |
| orelha_camera, placa_camera | 2 + 1 | giro da câmera |

Fixadores contados pelos furos: [verificacao.md](verificacao.md#fixadores-contados-pelos-furos). Em relação ao v3, a v4
**não precisa** de espaçadores M2.5 de 20 mm nem de parafusos de cabeça chata: são 4 espaçadores M2.5 de 5 mm, 8 porcas
presas (andares 2 e 3) e um pino de trava de 35 mm.

Medidas que ainda dependem de você: as mesmas do v3 (`make chassi-cortar` barra até conferir), e ficou mais
importante o **comprimento do cabo dos motores** (a v4 precisa de ~125 mm até a placa no andar 3; assumi 150).
