# firmware/

Firmware da ESP32 (controladora escrava): PWM dos DRV8833 com rampa, encoders, bateria, botão de largada e watchdog.
Os estados estão em [docs/02_arquitetura.md](../docs/02_arquitetura.md#3-estados) e o protocolo em [docs/05_protocolo_serial.md](../docs/05_protocolo_serial.md).

| Arquivo | Conteúdo |
|---|---|
| `robocar_esp32/config.h` | **Pinos e constantes** (fonte única da pinagem; reproduzida em docs/03_hardware.md) |
| `robocar_esp32/robocar_esp32.ino` | Lógica: estados, protocolo, motores, encoders, bateria |

> **Estado:** passou só por checagem de sintaxe, com cabeçalhos simulados dos cores 2.x e 3.x. **Não foi compilado com o core real nem testado na placa.**

## Compilar e gravar
1. Arduino IDE → Gerenciador de placas → "esp32" (Espressif), versão 2.x ou 3.x.
2. Abrir `robocar_esp32/robocar_esp32.ino`. A pasta precisa ter o mesmo nome do `.ino`.
3. Placa "ESP32 Dev Module"; porta `/dev/ttyUSB0` (Linux) ou `COMx` (Windows); gravar.
4. Monitor serial a 115200: aparece `$I,robocar_esp32,v1*..` e, a cada 20 ms, `$T,...`.

## Primeiro teste, sem motores
1. Só a ESP32 ligada ao PC: LED apagado = SEM_JETSON (sem comandos).
2. Na Jetson: `make bancada PORTA=/dev/ttyUSB0` → LED piscando devagar (PRONTO), depois aceso (ARMADO).
3. Fechar o programa: freia em 250 ms; em 1 s o LED apaga (teste T08).
4. Só depois ligar os drivers e os motores, **com as rodas suspensas** (teste T05). Ajustar `INVERTER_E/INVERTER_D` em `config.h`.
