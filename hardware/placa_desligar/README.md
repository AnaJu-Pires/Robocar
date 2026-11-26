# Placa de desligar a Jetson (placa extra, 30 × 18 mm)

Botão para desligar a Jetson com segurança e LED que diz **quando pode desligar a chave geral**. Fica no **andar 3**
do chassi v4, à direita da placa da ESP32, com 2 parafusos M3 (furos já no andar 3). A placa da ESP32 v0.8
**não muda**. Decisão: [D-028](../../docs/decisoes.md).

| LED vermelho | Significa |
|---|---|
| apagado logo depois de ligar a chave | Jetson iniciando (acende em ~20 s, quando o Linux sobe) |
| **aceso** | Jetson ligada: **não desligue a chave** |
| pisca rápido 1,5 s | o botão foi aceito: a Jetson está desligando |
| aceso de novo | ainda desligando (gravando o cartão) |
| **apagou** (com a chave ligada) | **pode desligar a chave** |

O LED é ligado pelo Linux e **nunca é apagado por software**: quem o apaga é o corte de energia do módulo da Jetson,
no fim do desligamento. Por isso "apagou" é uma informação confiável.

## Por que assim (comparação)

| Opção | Funciona com o programa do robô travado? | Indicador confiável de "pode desligar"? | Hardware novo |
|---|---|---|---|
| Largada segurada 3 s → ESP32 → flag → `shutdown` (já existe) | **não**: depende do `seguir_linha.py` e do USB | não (o LED da ESP32 continua aceso porque o USB da Jetson segue alimentando a ESP32) | nenhum |
| Botão de força do header J50 da Jetson + `HandlePowerKey` | sim | não (o LED verde da Jetson fica no 5 V e não apaga) | 2 fios, mas a pinagem do J50 da B01 **não pôde ser confirmada** (sites da NVIDIA bloqueados nesta sessão) e o J50 fica embaixo do módulo |
| Comando pela ESP32 via USB (outro botão na ESP32) | não (mesmo problema do 1º) | não | placa da ESP32 mudaria (vetado) |
| **GPIO do J41 + serviço próprio + LED pelo GPIO** (escolhida) | **sim**: serviço separado, como root | **sim**: o GPIO só cai quando o módulo desliga | esta plaquinha (peças de laboratório) |

A opção 1 continua valendo como **reserva** (nada foi tirado do firmware nem do `seguir_linha.py`).

## Esquema

```
J41 pino 17 (3V3) ──┬── R1 10k ──┬── R2 1k ──── J41 pino 18 (gpio15, entrada)
                    │            │
                    │           S1 botão (NA)
                    │            │
                    │           GND
                    │
                    └── R5 150 Ω ──► D1 LED vermelho ──── C  Q1 BC337
J41 pino 16 (gpio232) ── R3 10k ──┬─────────────────────── B
                                  R4 100k
                                  │
J41 pino 20 (GND) ────────────────┴─────────────────────── E
```

* R4 (100k) segura a base em 0 V quando o pino está solto (Jetson desligada ou iniciando): **LED apagado**.
* R2 (1k) protege o pino se ele for configurado como saída por engano.
* LED vermelho (Vf ≈ 1,9 V): (3,3 − 1,9 − 0,1) / 150 ≈ 9 mA. LED verde comum também serve; **não** use LED azul/branco
  (Vf ≈ 3 V não acende bem em 3,3 V).
* O pino 18 é o mesmo do exemplo de botão da NVIDIA (`jetson-gpio`, `button_led.py`: botão no pino 18 com pull-up
  externo para o 3V3). Os números do sysfs (gpio15, gpio232) foram conferidos em `gpio_pin_data.py` do `jetson-gpio`.

## Peças (todas do laboratório ou sobras)

| Ref | Peça | Obs |
|---|---|---|
| S1 | chave táctil 6 × 6 mm com haste de **13 mm** | haste alta = aperta com o dedo por cima sem tirar nada |
| D1 | LED vermelho 3 mm | |
| Q1 | BC337 (sobra da v0.4) | olhando a face chata, pernas da esquerda para a direita: C, B, E |
| R1, R3 | 10 kΩ | |
| R2 | 1 kΩ | |
| R4 | 100 kΩ | |
| R5 | 150 Ω (100–220 Ω) | |
| — | placa perfurada 30 × 18 mm (12 × 7 furos) | 2 furos de 3,2 mm em cantos opostos (ver desenho) |
| — | 4 jumpers Dupont fêmea de 15 cm (ou 1 conector fêmea 2 × 3) | pinos 16, 17, 18 e 20 do J41 |
| — | 2 parafusos M3 × 10 + 2 espaçadores M3 de 3 mm + porcas | fixação no tampo |

## Montagem na placa perfurada (vista dos componentes; a frente do carro fica à esquerda)

```
   1   2   3   4   5   6   7   8   9  10  11  12
A  (M3)  .   .   .   .   .   .   .   .   .   .   .
B  .   S1──S1  .   .   R1═══════R1  .   .   .   .
C  .   │ ▢ │   .   .   .   .   .   .   R2══R2  .
D  .   S1──S1  .   D1+ D1- .   Q1C Q1B Q1E .   .
E  .   .   .   .   R5══R5  .   R3═══R3  .   .   .
F  .   .   .   .   .   .   .   .   R4══R4  .   .
G  .   17  18  16  20  .   .   .   .   .   .  (M3)
```

* G2–G5: fios para o J41 (**17 = 3V3, 18 = botão, 16 = LED, 20 = GND**). Marque cada fio com fita.
* Faça a ligação por baixo com as próprias pernas dos componentes, seguindo o esquema.
* Na barra J41 da Jetson os pinos 15–20 ficam em 2 fileiras: 15, 17, 19 numa e 16, 18, 20 na outra.
  Com um conector fêmea 2 × 3 nos pinos 15–20, **marque o lado do pino 15**: ligado deslocado, ele não queima nada
  (só resistores no caminho), mas não funciona.

## Instalar e testar

1. **Na bancada, sem a Jetson:** fonte de 3,3 V entre os fios 17 (+) e 20 (−).
   * LED apagado. Encoste o fio 16 no 3,3 V: LED acende.
   * Multímetro no fio 18: 3,3 V solto, 0 V com o botão apertado.
2. **Na Jetson desligada**, ligue os 4 fios no J41. Ligue a chave e instale o serviço:
   `make servico` (instala o `robocar.service` e o `botao-desligar.service`). O LED acende quando o Linux sobe.
3. **Teste sem desligar:**
   ```bash
   sudo systemctl stop botao-desligar
   ```
   ```bash
   sudo python3 jetson/servico/botao_desligar.py --teste
   ```
   Aperte e solte: aparece `botao APERTADO` / `botao solto`. Segure 2 s: o LED pisca e aparece
   `desligando (TESTE: nao desliga)`. Ctrl+C e depois `sudo systemctl start botao-desligar`.
4. **Teste de verdade:** segure 2 s. Cronometre até o LED **apagar** (anote; esperado 10–25 s). Desligue a chave.
   Ligue de novo e confira que o desligamento foi limpo:
   ```bash
   journalctl -b -1 -n 30 --no-pager
   ```
   O fim deve mostrar `Reached target Power-Off` (ou `Shutdown`), sem erros de sistema de arquivos.
5. **Testes negativos** (anote o resultado em `docs/06_testes.md`, teste T15):
   * aperto curto (< 2 s): nada acontece;
   * ligar a Jetson **com o botão apertado**: não desliga (o serviço só arma depois de ver o botão solto 0,5 s);
   * `sudo systemctl stop robocar` e repetir o passo 4: tem de desligar igual (não depende do programa do robô).

Testes automáticos (sem Jetson, com um GPIO falso): `jetson/testes/test_botao_desligar.py` (rodam em `make testes`).

Se o SPI do J41 tiver sido ligado no `jetson-io`, os pinos 16 e 18 viram SPI e o serviço avisa
`ERRO no GPIO`. Nesse caso desligue o SPI no `jetson-io` ou troque para os pinos 31 (gpio200) e 33 (gpio38)
em `jetson/robocar/botao_desligar.py`.
