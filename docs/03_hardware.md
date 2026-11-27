# 03 — Hardware

Lista de compras com preços, links e fretes: [../compras/](../compras/). Aqui ficam a função de cada parte, os cálculos e a ligação.
Também usamos dados da planilha de especificações da equipe (abas LIGACOES ELETRICAS, PINAGEM ESP32, MASSA E DINAMICA, CALCULOS); a origem está citada onde aparece.

## 1. Componentes

| Parte | Modelo | Situação | Dados-chave |
|---|---|---|---|
| Computador | Jetson Nano Developer Kit **4 GB** | possuímos | entrada J25 (5,5 × 2,1 mm, centro +) com jumper J48; 5 V / 4 A |
| Câmera | **IMX219-160** (lente ~160°) | possuímos | CSI; Jetson + câmera = **149 g (medido pela equipe)** [V] |
| Microcontrolador | ESP32 DevKit V1, 30 pinos, USB-C, CP2102 | possuímos | identificado por foto (13/11/2026) |
| Motores | N20 6 V 750 rpm com encoder (RoboCore) ×2 | comprar | 120 mA vazio; **stall 1,6 A**; 1,7 kgf·cm; eixo D 3 mm; 20 g; ~140 pulsos/volta (medido pela loja) [V] |
| Drivers | DRV8833 ×3 (2 em uso + 1 reserva) | comprar | VM 2,7–10,8 V; 1,2 A/canal, **2,4 A em paralelo** [V]; um módulo por motor, VM em 7,2 V ([D-019](decisoes.md)) |
| Bateria | LiPo 3S 1100 mAh 20C (RoboCore) | comprar | XT60 + JST-XH; **70 g** [V] |
| Conversores | XL4016 ×2 | comprar | entrada 8–40 V; tensão e corrente ajustáveis; 65 × 46 × 24 mm [V]; #1 = 5,2 V (Jetson), #2 = 7,2 V (motores) |
| Rodas | 42 × 19 mm borracha, eixo D 3 mm ×4 (2 reservas) | comprar | 19 g cada [V] |
| Apoio | esfera deslizante 3/8" | comprar | regra não cita apoio passivo ([01](01_regulamento.md), pergunta 3) |
| Carga | carregador B3 2S/3S + Lipo Sack | comprar | o laboratório não tem carregador LiPo |
| Bancada | fonte de bancada | laboratório | ajustar 5,1–5,2 V e limite ≥ 4 A para a Jetson |

## 2. Alimentação

```
              ┌──────── placa de distribuição (hardware/placa_distribuicao, andar 2) ────────┐
LiPo 3S 11,1 V ─XT60─► fusível 7 A ─► chave ─┬─► XL4016 #1 → 5,2 V (limite ~5 A) ─► plug P4 ─► Jetson J25 (J48 fechado)
  (9,9–12,6 V)                               ├─► XL4016 #2 → 7,2 V (limite ~4 A) ─┬─► J2 da placa (DRV8833 esquerdo, 470 µF)
                                             │   zener 9,1 V 5 W no OUT (D-042)   └─► J3 da placa (DRV8833 direito, 470 µF)
                                             ├─► fio fino ─► J1 da placa ─► divisor 220 k / 47 k ─► GPIO36 (ADC)
                                             └─► LED verde (chave ligada); diodo 1N5408 contra bateria invertida
Jetson USB-A ─► ESP32 (dados + 5 V) ─► 3V3 da DevKit ─► encoders (J12, J13)
Jetson USB-A ─► fita COB da câmera (sem o controle de toque, D-040)
GND comum em estrela na placa de distribuição. A corrente dos motores volta pelos fios pretos de J2/J3 até o XL4016 #2;
o cabo USB fecha um laço de terra e leva ~8 % dela nos picos (~0,3 A com os 2 motores travados): aceitável.
```

**Por que assim** ([decisoes.md](decisoes.md) D-002): o DRV8833 aceita no máximo 10,8 V e a regra limita o motor a 12 V. Com a 3S cheia (12,6 V), os motores precisam de trilho regulado. O UBEC previsto no CSV (R$ 199,90) estava fora de estoque. Dois XL4016 iguais custam R$ 59,80 e um serve de reserva para o outro.

**Plug P4 e 4 A:** a planilha da equipe alerta que plugs P4 genéricos podem ser limitados a 2 A, e o plug comprado não informa a corrente. Critério de aceite (teste T04): **≥ 4,75 V medidos no jack com a Jetson em carga e plug sem aquecer**. Se falhar, alimentar pelos pinos 5 V do conector J41 (2 pinos de 5 V e 2 de GND, fios curtos), conforme o guia da NVIDIA.

## 3. Cálculos elétricos

| Grandeza | Cálculo | Resultado |
|---|---|---|
| Jetson em 10 W | ≈ 12 W com periféricos; η ≈ 0,9; 11,1 V | ≈ 1,2 A na bateria [E] |
| Motores rodando | 2 × (0,25–0,6 A) × 7,2 V / 0,9 / 11,1 V | ≈ 0,35–0,9 A [E, medir] |
| Pico | 2 motores travados (2 × 1,9 A × 7,2 V) + Jetson a 20 W, bateria em 10 V | ≈ 5,3 A [E] (fusível de 7 A ok) |
| Bateria 20C | 1,1 Ah × 20 = 22 A contínuos | folga ≫ 4,3 A |
| Autonomia | 0,88 Ah úteis (80 %) ÷ 1,2–1,7 A | **≈ 30–45 min** [E]; uma volta < 1 min |
| Fusível | entre o pico (4,3 A) e o limite do fio | **7 A**; cabinho 0,75 mm² (~18 AWG) |
| Stall em 7,2 V | 1,6 A × 7,2 / 6 (corrente proporcional à tensão no motor travado) | ≈ 1,9 A [E] |
| DRV8833 em paralelo | 2,4 A > 1,9 A de stall | margem de 25 % [V] |
| Divisor da bateria | 12,6 V × 47 / 267 | 2,22 V no ADC; consome 47 µA (depois da chave: zero com a chave desligada) |

## 4. Massa

**Chassi v3:** massa, CG e tombamento calculados peça a peça pelo modelo ([mecanica/chassi_v3/verificacao.md](../mecanica/chassi_v3/verificacao.md#massas-para-refazer-o-cg-depois-de-pesar)): **633 g**, CG a 16,8 mm à frente do eixo e 36,1 mm de altura. A tabela abaixo é a estimativa inicial da planilha.

Planilha da equipe (aba MASSA E DINAMICA), ajustada para a lista atual.

| Item | Mín. (g) | Base (g) | Máx. (g) | Origem |
|---|---|---|---|---|
| Jetson + IMX219-160 | 149 | 149 | 149 | medido pela equipe [V] |
| Motores N20 ×2 | 40 | 40 | 40 | RoboCore [V] |
| Bateria 3S 1100 mAh | 70 | 70 | 70 | RoboCore [V] |
| XL4016 ×2 | 70 | 100 | 140 | não declarado; planilha da equipe: 35–70 g cada [E] |
| DRV8833 ×2 | 3 | 3 | 3 | Smart Kits [V] |
| Rodas 42 mm ×2 | 38 | 38 | 38 | Smart Kits [V] |
| ESP32 DevKit | 12 | 18 | 28 | estimativa da equipe [E] |
| Esfera | 5 | 10 | 20 | [E] |
| Chassi PLA | 35 | 60 | 95 | [E] |
| Cabos e parafusos | 15 | 30 | 50 | [E] |
| **Total** | **437** | **518** | **633** | pesar ao montar |

## 5. Velocidade e curvas

Fórmulas da aba CALCULOS da planilha da equipe.

| Grandeza | Fórmula | Resultado |
|---|---|---|
| Velocidade em vazio (roda 42 mm, 750 rpm) | π · 0,042 · 750 / 60 | 1,65 m/s |
| Velocidade estimada em carga (520 rpm) | π · 0,042 · 520 / 60 | 1,14 m/s [E] |
| Limite de aderência em R = 100 mm (μ = 0,8, hipótese) | √(μ · g · R) | 0,89 m/s [E] |
| Limite diferencial em R = 100 mm (bitola 110 mm) | v_roda_externa / (1 + b/2R) = 1,14 / 1,55 | **0,74 m/s** [E] |
| Em 7,2 V ([D-019](decisoes.md)): vazio / em carga | rpm proporcional à tensão: 900 / 624 rpm | 1,98 / **1,37 m/s** [E] |
| Limite diferencial em 7,2 V, R = 100 mm, bitola 104 mm | 1,37 / (1 + 104/200) | **0,90 m/s** ≈ limite de aderência [E] |

Consequências:
* nas curvas fechadas, o limite vem da mecânica e não do sensor;
* bitola menor aumenta o limite diferencial (b = 90 mm → 0,79 m/s), mas reduz a estabilidade;
* medir μ do pneu no tapete (teste T12).

## 6. Pinagem da ESP32

**Fonte única: [firmware/robocar_esp32/config.h](../firmware/robocar_esp32/config.h).** Esta tabela a reproduz. O esquemático e a placa (PCB) estão em [hardware/placa_esp32/](../hardware/placa_esp32/).

| Função | GPIO | Pino da DevKit | Observação |
|---|---|---|---|
| Motor esquerdo IN1 | **33** | 7 | coluna **esquerda** da ESP32 = motor esquerdo; na placa vai em IN2+IN4 do U2 (ponte espelhada: [D-013](decisoes.md)) |
| Motor esquerdo IN2 | **25** | 8 | IN1+IN3 do U2 (IN3 pelo JP1) |
| nSLEEP driver esquerdo | **32** | 6 | pull-down de 10k (R3) ([D-020](decisoes.md)); 3,3 V liga |
| Encoder esquerdo A/B | **26 / 27** | 9 / 10 | encoder em 3,3 V, saída direto no GPIO ([D-018](decisoes.md)); INPUT_PULLUP |
| Motor direito IN1 | **19** | 21 | coluna **direita** da ESP32 = motor direito; IN2+IN4 do U3 |
| Motor direito IN2 | **21** | 20 | IN1+IN3 do U3 (IN3 pelo JP2) |
| nSLEEP driver direito | **18** | 22 | pull-down de 10k (R4); passa pelo jumper JP3 até o EEP do U3 |
| Encoder direito A/B | **17 / 16** | 24 / 25 | idem |
| Bateria (ADC1) | 36 | 2 | divisor 220 k / 47 k (R1/R2) |
| Largada | **4** | 26 | **botão** para o GND (INPUT_PULLUP). Apertar e soltar = largada; apertar armado = para; segurar 3 s parado = desliga a Jetson. Não usar jumper fixo |
| Buzzer | — | — | fora da placa (`PIN_BUZZER = -1`); o aviso de bateria baixa vai na telemetria |
| LED | 2 | 27 | LED da própria DevKit: aceso = armado; pisca devagar = pronto; pisca rápido = falha; pisca muito rápido = desligando a Jetson |

Por que a pinagem mudou na v0.8 ([D-024](decisoes.md)): a placa ficou **espelhada** — a coluna esquerda da ESP32
atende só o motor esquerdo e a direita só o direito, para que cada cabo de motor (6 fios) e cada par de VM chegue no
lado certo da placa. Pinos evitados: 0, 2, 5, 12, 15 (strapping), 1 e 3 (USB serial), 14 (PWM no boot) e 39.

## 7. Regras de ligação (resumo da aba LIGACOES ELETRICAS da equipe)

* Ajustar cada XL4016 **sem carga** e medir com multímetro: 5,2 V e 7,2 V. Só então conectar a Jetson e os drivers.
* Nunca ligar a 3S direto no VM do DRV8833. Nunca aplicar mais de 3,3 V em GPIO da ESP32: os encoders são alimentados pelo 3V3 da DevKit (J12, J13); **nunca ligar o + do encoder em 5 V ou no VM**.
* Não usar protoboard nem fio Dupont na potência. Fios de potência curtos e soldados, com termorretrátil.
* Não alimentar a ESP32 pelo pino 5 V e pelo USB ao mesmo tempo.
* Não conectar nem desconectar o cabo CSI com a Jetson energizada.
* Carregar a LiPo **fora do robô**, dentro do Lipo Sack, supervisionada.
* **Zener de 9,1 V 5 W no OUT do XL4016 #2** antes de andar rápido: na frenagem os motores devolvem energia ao VM, e o
  XL4016 não a absorve (D-042).
* **Chave desligada sempre que o robô não estiver em uso** (o LED verde da placa de distribuição avisa). Com a chave
  ligada, a ESP32 para os motores em 9,6 V, mas a Jetson e os XL4016 continuam gastando a LiPo.
