# Analise de arquitetura e rodas (gerada por `fonte/analise.py`)

Hipoteses: atrito pneu x tapete mu = 0.9 (medir no T12), motores em 7,2 V, pista sintetica de 20 m com curvas de R100 a R500.
Massas e posicoes: as do modelo (`pecas.py`); nas variantes A e C so mudam de lugar a Jetson e a bateria.

## 1. Arquiteturas

| | massa (g) | CG x / y / z (mm) | peso nas rodas | tomba a (g) | empina a (g) | curva R100 (m/s) | limite | volta 20 m (s) | comprimento (mm) |
|---|---|---|---|---|---|---|---|---|---|
| A - v2.2 reconstruida: Jetson no andar de cima | 633 | 9.8 / -1.0 / 45.5 | 93 % | 0.97 | 0.22 | 0.93 | tombamento | 13.5 | 246 |
| B - v3: Jetson baixa sobre a bateria (escolhida) | 633 | 16.8 / -1.0 / 36.1 | 86 % | 1.11 | 0.47 | 0.94 | aderencia | 12.6 | 240 |
| C - Jetson no piso, bateria atravessada na frente | 633 | 25.3 / -1.0 / 33.1 | 80 % | 1.14 | 0.77 | 0.94 | aderencia | 12.4 | 252 |

* **tomba a**: aceleracao lateral que levanta uma roda (apoio em 3 pontos: o eixo de tombamento e a linha roda-esfera). Tem de ficar acima de mu = 0.9; senao o carro tomba antes de escorregar.
* **empina a**: aceleracao para a frente que tira a esfera do chao (= x_CG / z_CG). Acima dela o carro levanta o nariz e a camera mexe.

## 2. Rodas (arquitetura B; trocar a roda sobe ou desce o carro inteiro)

| roda | v max em vazio (m/s) | forca de partida 2 motores (N) | z do CG (mm) | tomba a (g) | curva R100 (m/s) | limite | volta (s) | sem limite de empinar (s) | obs |
|---|---|---|---|---|---|---|---|---|---|
| 32 mm (mu 1.1) | 1.51 | 25.0 | 31.1 | 1.29 | 0.96 | diferencial | 15.0 | 14.9 | StickyMAX: eixo a 16 mm; esfera de 15 mm fica 5 mm alta (precisa outra esfera) |
| 42 mm (mu 0.9) | 1.98 | 19.1 | 36.1 | 1.11 | 0.94 | aderencia | 12.6 | 12.3 | atual (4 compradas); esfera de 15 mm encaixa sem calco |
| 48 mm (mu 0.9) | 2.26 | 16.7 | 39.1 | 1.03 | 0.94 | aderencia | 12.0 | 11.6 | eixo 3 mm mais alto; nao comprada |
| 65 mm (mu 0.9) | 3.06 | 12.3 | 47.6 | 0.84 | 0.86 | tombamento | 12.4 | 11.4 | eixo 11,5 mm mais alto; vao livre e CG sobem |

## 3. Limite real: controle e visao

Com a roda de 42 mm, tempo de volta conforme o teto de velocidade que a visao/controle aguentar:

| teto de velocidade (m/s) | volta 20 m (s) |
|---|---|
| 0.6 | 33.4 |
| 0.8 | 25.1 |
| 1.0 | 20.2 |
| 1.2 | 17.2 |
| 1.5 | 14.4 |
| sem teto | 12.6 |

Leitura: enquanto o carro nao passar de ~1,2 m/s com seguranca, a roda nao e o gargalo; a de 42 mm tem folga de velocidade (1.98 m/s em vazio) e de torque (forca de partida 19 N contra 4.8 N que o pneu consegue passar ao chao: 4x).

## 4. Sensibilidade ao atrito (medir no T12)

| mu | escorrega com (g) | tomba com (g) | margem | velocidade segura em R100 (m/s) | o que fazer |
|---|---|---|---|---|---|
| 0.7 | 0.70 | 1.11 | 1.59 | 0.83 (aderencia) | nada |
| 0.9 | 0.90 | 1.11 | 1.24 | 0.94 (aderencia) | nada |
| 1.0 | 1.00 | 1.11 | 1.11 | 0.99 (aderencia) | limitar a velocidade na curva por software |
| 1.1 | 1.10 | 1.11 | 1.01 | 0.99 (tombamento) | limitar a velocidade na curva por software |
| 1.3 | 1.30 | 1.11 | 0.86 | 0.99 (tombamento) | limitar a velocidade na curva por software (obrigatorio) |

Se o pneu agarrar mais que mu ~ 1,0, o carro tomba antes de escorregar numa curva de R100 feita rapido demais. A protecao e de software: velocidade maxima na curva de ~0,9 m/s (o controle ja reduz a velocidade com o erro).
