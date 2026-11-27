# Analise do chassi v4 (3 andares) - gerada por `fonte/analise.py`

Hipoteses: atrito pneu x tapete mu = 0.9 (medir no T12), motores em 7,2 V, pista sintetica de 20 m com curvas de R100 a R500.
Massas e posicoes: as do modelo (`pecas.py`); nas variantes B e C so mudam de andar a Jetson, a ESP32 e os XL4016. A linha da v3 vem de `chassi_v3/resumo.json`.

## 1. Arquiteturas

| | massa (g) | CG x / y / z (mm) | peso nas rodas | tomba a (g) | empina a (g) | curva R100 (m/s) | limite | volta 20 m (s) | comprimento (mm) |
|---|---|---|---|---|---|---|---|---|---|
| v3 (25/11): Jetson baixa sobre a bateria, 2 andares | 633 | 16.8 / -1.0 / 36.1 | 86 % | 1.11 | 0.47 | 0.94 | aderencia | 12.6 | 240 |
| A - v4: XL4016 + bateria no piso, Jetson no 2o, ESP32 no 3o (escolhida) | 669 | 21.5 / -1.6 / 50.6 | 77 % | 0.76 | 0.42 | 0.80 | software | 13.6 | 176 |
| B - Jetson no 3o, ESP32 no 2o (largada e USB da ESP32 ficam embaixo da Jetson) | 669 | 21.5 / -1.6 / 57.7 | 77 % | 0.67 | 0.37 | 0.77 | tombamento | 14.0 | 176 |
| C - Jetson no piso, XL4016 no 2o (XL quente em cima do dissipador; +15 mm) | 669 | 21.5 / -1.6 / 48.6 | 80 % | 0.86 | 0.44 | 0.80 | software | 13.6 | 191 |

Nas linhas da v4, a curva R100 ja respeita o limite por software de 0.65 g de aceleracao lateral (D-032).

* **tomba a**: aceleracao lateral que levanta uma roda (apoio em 3 pontos: o eixo de tombamento e a linha roda-esfera). Tem de ficar acima do que o carro faz na curva: o atrito (mu = 0.9) ou o limite por software, o que for menor.
* **empina a**: aceleracao para a frente que tira a esfera do chao (= x_CG / z_CG). Acima dela o carro levanta o nariz e a camera mexe.

## 2. Rodas (v4; trocar a roda sobe ou desce o carro inteiro)

| roda | v max em vazio (m/s) | forca de partida 2 motores (N) | z do CG (mm) | tomba a (g) | curva R100 (m/s) | limite | volta (s) | sem limite de empinar (s) | obs |
|---|---|---|---|---|---|---|---|---|---|
| 32 mm (mu 1.1) | 1.51 | 25.0 | 45.6 | 0.85 | 0.80 | software | 15.6 | 15.4 | StickyMAX: eixo a 16 mm; esfera de 15 mm fica 5 mm alta (precisa outra esfera) |
| 42 mm (mu 0.9) | 1.98 | 19.1 | 50.6 | 0.76 | 0.80 | software | 13.6 | 13.3 | atual (4 compradas); esfera de 15 mm encaixa sem calco |
| 48 mm (mu 0.9) | 2.26 | 16.7 | 53.6 | 0.72 | 0.80 | tombamento | 13.2 | 12.8 | eixo 3 mm mais alto; nao comprada |
| 65 mm (mu 0.9) | 3.06 | 12.3 | 62.1 | 0.62 | 0.74 | tombamento | 13.8 | 12.8 | eixo 11,5 mm mais alto; vao livre e CG sobem |

## 3. Limite real: controle e visao

Com a roda de 42 mm, tempo de volta conforme o teto de velocidade que a visao/controle aguentar:

| teto de velocidade (m/s) | volta 20 m (s) |
|---|---|
| 0.6 | 33.4 |
| 0.8 | 25.1 |
| 1.0 | 20.5 |
| 1.2 | 17.6 |
| 1.5 | 15.2 |
| sem teto | 13.6 |

Leitura: enquanto o carro nao passar de ~1,2 m/s com seguranca, a roda nao e o gargalo; a de 42 mm tem folga de velocidade (1.98 m/s em vazio) e de torque (forca de partida 19 N contra 4.6 N que o pneu consegue passar ao chao: 4x).

## 4. Sensibilidade ao atrito (medir no T12)

| mu | escorrega com (g) | tomba com (g) | margem | velocidade segura em R100 (m/s) | o que fazer |
|---|---|---|---|---|---|
| 0.7 | 0.70 | 0.76 | 1.09 | 0.80 (software) | limitar a velocidade na curva por software |
| 0.9 | 0.90 | 0.76 | 0.85 | 0.80 (software) | limitar a velocidade na curva por software (obrigatorio) |
| 1.0 | 1.00 | 0.76 | 0.76 | 0.80 (software) | limitar a velocidade na curva por software (obrigatorio) |
| 1.1 | 1.10 | 0.76 | 0.69 | 0.80 (software) | limitar a velocidade na curva por software (obrigatorio) |
| 1.3 | 1.30 | 0.76 | 0.59 | 0.80 (software) | limitar a velocidade na curva por software (obrigatorio) |

Se o pneu agarrar mais que mu ~ 1,0, o carro tomba antes de escorregar numa curva de R100 feita rapido demais. A protecao e de software: velocidade maxima na curva de ~0,9 m/s (o controle ja reduz a velocidade com o erro).
