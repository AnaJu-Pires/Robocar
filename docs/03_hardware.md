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
| Drivers | DRV8833 ×3 (2 em uso + 1 reserva) | comprar | VM 2,7–10,8 V; 1,2 A/canal, **2,4 A em paralelo** [V] |
| Bateria | LiPo 3S 1100 mAh 20C (RoboCore) | comprar | XT60 + JST-XH; **70 g** [V] |
| Conversores | XL4016 ×2 | comprar | entrada 8–40 V; tensão e corrente ajustáveis; 65 × 46 × 24 mm [V] |
| Rodas | 42 × 19 mm borracha, eixo D 3 mm ×4 (2 reservas) | comprar | 19 g cada [V] |
| Apoio | esfera deslizante 3/8" | comprar | regra não cita apoio passivo ([01](01_regulamento.md), pergunta 3) |
| Carga | carregador B3 2S/3S + Lipo Sack | comprar | o laboratório não tem carregador LiPo |
| Bancada | fonte de bancada | laboratório | ajustar 5,1–5,2 V e limite ≥ 4 A para a Jetson |

## 2. Alimentação

```
LiPo 3S 11,1 V ─XT60─► fusível 7 A ─► chave ─┬─► XL4016 #1 → 5,2 V (limite ~5 A) ─► plug P4 ─► Jetson J25 (J48 fechado)
  (9,9–12,6 V)                               ├─► XL4016 #2 → 6,0 V (limite ~3,5 A) ─► VM das 2 placas DRV8833 (+470 µF cada)
                                             ├─► 78L05 → 5 V (encoders e buzzer, na placa da ESP32)
                                             └─► divisor 150 k / 33 k (+100 nF) ─► GPIO36 (ADC) da ESP32
Jetson USB-A ─► ESP32 (dados + 5 V)      GND comum ligado em estrela; a potência não retorna pelo cabo USB
```

**Por que assim** ([decisoes.md](decisoes.md) D-002): o DRV8833 aceita no máximo 10,8 V e a regra limita o motor a 12 V. Com a 3S cheia (12,6 V), os motores precisam de trilho regulado. O UBEC previsto no CSV (R$ 199,90) estava fora de estoque. Dois XL4016 iguais custam R$ 59,80 e um serve de reserva para o outro.

**Plug P4 e 4 A:** a planilha da equipe alerta que plugs P4 genéricos podem ser limitados a 2 A, e o plug comprado não informa a corrente. Critério de aceite (teste T04): **≥ 4,75 V medidos no jack com a Jetson em carga e plug sem aquecer**. Se falhar, alimentar pelos pinos 5 V do conector J41 (2 pinos de 5 V e 2 de GND, fios curtos), conforme o guia da NVIDIA.

## 3. Cálculos elétricos

| Grandeza | Cálculo | Resultado |
|---|---|---|
| Jetson em 10 W | ≈ 12 W com periféricos; η ≈ 0,9; 11,1 V | ≈ 1,2 A na bateria [E] |
| Motores rodando | 2 × (0,2–0,5 A) × 6 V / 0,9 / 11,1 V | ≈ 0,25–0,6 A [E, medir] |
| Pico | 2 motores travados (2 × 1,6 A × 6 V) + Jetson a 20 W, bateria em 10 V | ≈ 4,3 A [E] |
| Bateria 20C | 1,1 Ah × 20 = 22 A contínuos | folga ≫ 4,3 A |
| Autonomia | 0,88 Ah úteis (80 %) ÷ 1,2–1,7 A | **≈ 30–45 min** [E]; uma volta < 1 min |
| Fusível | entre o pico (4,3 A) e o limite do fio | **7 A**; cabinho 0,75 mm² (~18 AWG) |
| DRV8833 em paralelo | 2,4 A > 1,6 A de stall | margem de 50 % [V] |
| Divisor da bateria | 12,6 V × 33 / 183 | 2,27 V no ADC; consome 69 µA → **desconectar a bateria ao guardar** |

## 4. Massa

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

Consequências:
* nas curvas fechadas, o limite vem da mecânica e não do sensor;
* bitola menor aumenta o limite diferencial (b = 90 mm → 0,79 m/s), mas reduz a estabilidade;
* medir μ do pneu no tapete (teste T12).

## 6. Pinagem da ESP32

**Fonte única: [firmware/robocar_esp32/config.h](../firmware/robocar_esp32/config.h).** Esta tabela a reproduz. O esquemático e a placa (PCB) estão em [hardware/placa_esp32/](../hardware/placa_esp32/).

| Função | GPIO | Planilha da equipe | Observação |
|---|---|---|---|
| Motor esquerdo IN1 | 25 | 25 | DRV8833 em modo paralelo; na placa vai em IN2+IN4 do módulo (ponte espelhada, mesmo comportamento: [D-013](decisoes.md)) |
| Motor esquerdo IN2 | 26 | 26 | na placa: IN1+IN3 |
| Motor direito IN1 | 27 | 27 | |
| Motor direito IN2 | **13** | 14 | o GPIO14 emite PWM no boot e poderia mexer o motor |
| nSLEEP das duas placas | 18 | 18 | 3,3 V liga; nunca ligar ao VM |
| Encoder esquerdo A/B | 32 / 33 | 32 / 33 | via CD4050B (5 V → 3,3 V), saída push-pull |
| Encoder direito A/B | 34 / 35 | 34 / 35 | só entrada e sem pull-up interno; via CD4050B, que já entrega 0/3,3 V push-pull |
| Bateria (ADC1) | 36 | 36 | divisor 150 k / 33 k + 100 nF |
| Botão de largada | 23 | 23 | para o GND (INPUT_PULLUP) |
| Buzzer (opcional) | 4 | — | aviso de bateria baixa |
| LED | 2 | — | aceso = armado; pisca devagar = pronto; pisca rápido = falha |

## 7. Regras de ligação (resumo da aba LIGACOES ELETRICAS da equipe)

* Ajustar cada XL4016 **sem carga** e medir com multímetro: 5,2 V e 6,0 V. Só então conectar a Jetson e os drivers.
* Nunca ligar a 3S direto no VM do DRV8833. Nunca aplicar mais de 3,3 V em GPIO da ESP32: os encoders são alimentados em 5 V e passam pelo conversor CD4050B da placa ([hardware/placa_esp32/](../hardware/placa_esp32/)); não ligar encoder direto num GPIO.
* Não usar protoboard nem fio Dupont na potência. Fios de potência curtos e soldados, com termorretrátil.
* Não alimentar a ESP32 pelo pino 5 V e pelo USB ao mesmo tempo.
* Não conectar nem desconectar o cabo CSI com a Jetson energizada.
* Carregar a LiPo **fora do robô**, dentro do Lipo Sack, supervisionada.
