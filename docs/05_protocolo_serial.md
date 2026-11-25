# 05 — Protocolo serial Jetson ↔ ESP32 (versão 1)

**Implementações:** [jetson/robocar/protocolo.py](../jetson/robocar/protocolo.py) e [firmware/robocar_esp32/robocar_esp32.ino](../firmware/robocar_esp32/robocar_esp32.ino) (versão em `config.h`).
**Testes:** [jetson/testes/test_protocolo.py](../jetson/testes/test_protocolo.py) e [test_esp32.py](../jetson/testes/test_esp32.py).

## Camada física
USB serial (cabo de dados entre a Jetson e a ESP32), 115200 baud, 8N1. A porta costuma ser `/dev/ttyUSB0` (CP2102/CH340) ou `/dev/ttyACM0`.

## Enquadramento
```
$<CORPO>*<HH>\n
```
* `HH` = XOR de todos os bytes do `CORPO`, em hexadecimal maiúsculo (estilo NMEA).
* Linhas sem `$`, com checksum errado ou com formato inválido são **descartadas** e contadas em `linhas_invalidas`.
* Os campos são separados por vírgula; os números são inteiros decimais.

## Jetson → ESP32

| Mensagem | Exemplo | Efeito |
|---|---|---|
| `M,<seq>,<esq>,<dir>` | `$M,12,-500,800*42` | Alvos das rodas, −1000 a 1000 (fração do PWM máximo). `seq` vai de 0 a 9999 e é só diagnóstico. Também mantém o link vivo |
| `S` | `$S*53` | Parar e desarmar (ARMADO → PRONTO) |
| `A` | `$A*41` | Armar (só aceito em PRONTO, com comando há < 250 ms). **Somente bancada**; na pista usa-se o botão |
| `V` | `$V*56` | Pede a versão do firmware (resposta `I,...`) |

A Jetson envia `M` **a cada quadro**, inclusive zerado quando parada.

## ESP32 → Jetson

| Mensagem | Exemplo | Quando |
|---|---|---|
| `T,<ms>,<encE>,<encD>,<vbat_mV>,<estado>,<flags>` | `$T,1000,15,-3,11850,2,0*..` | A cada 20 ms (50 Hz) |
| `I,robocar_esp32,v<N>` | `$I,robocar_esp32,v1*..` | No boot e em resposta a `V` |

* `encE`/`encD`: contagem acumulada em quadratura x4 (int32). A RoboCore indica ~140 pulsos/volta, mas não diz em qual modo: **calibrar** (teste T07).
* `estado`: 0 `SEM_JETSON`, 1 `PRONTO`, 2 `ARMADO`, 3 `FALHA_BATERIA` ([02_arquitetura.md](02_arquitetura.md#3-estados)).
* `flags`: bit 0 = watchdog (armado e sem comando há > 250 ms, freando); bit 1 = bateria baixa (< 3,3 V/célula); bit 2 = **desligar** (v2: botão segurado 3 s com o robô parado; a Jetson faz `shutdown`).
* Botão (v2): com o robô **armado**, apertar **para na hora**; parado, **apertar e soltar** arma; **segurar 3 s** liga a flag desligar por 3 s e não arma.

## Temporização e segurança
* Sem `M` válido por **250 ms** com o robô ARMADO: alvos zerados (freio) e flag de watchdog ligada.
* Sem `M` por **1000 ms**: desarma (SEM_JETSON) e exige novo botão.
* Bateria abaixo de 3,2 V/célula por 2 s: FALHA_BATERIA até reiniciar a placa. Abaixo de 5 V medidos, considera-se que não há bateria ligada (bancada via USB).

## Como mudar o protocolo
1. Incrementar `VERSAO` em `protocolo.py` **e** `PROTOCOLO_VERSAO` em `config.h`.
2. Alterar os dois lados e este documento **no mesmo commit**.
3. Atualizar os testes. Ao conectar, a Jetson pede `V` e avisa se as versões diferirem.

Evolução prevista (v2): comando de velocidade das rodas em mm/s com controle PI de velocidade na ESP32, usando os encoders (ideia da aba SOFTWARE da planilha da equipe).
