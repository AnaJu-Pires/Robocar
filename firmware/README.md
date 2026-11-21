# firmware/

Firmware da ESP32 (controladora escrava): PWM dos DRV8833 com rampa, encoders, bateria, botão de largada e watchdog.
Os estados estão em [docs/02_arquitetura.md](../docs/02_arquitetura.md#3-estados) e o protocolo em [docs/05_protocolo_serial.md](../docs/05_protocolo_serial.md).

| Arquivo | Conteúdo |
|---|---|
| `robocar_esp32/config.h` | **Pinos e constantes** (fonte única da pinagem; reproduzida em docs/03_hardware.md) |
| `robocar_esp32/robocar_esp32.ino` | Lógica: estados, protocolo, motores, encoders, bateria |
| `simulacao/` | Arduino falso + roteiro que testa o firmware com o código da Jetson (`make sim-esp32`) |

> **Estado:** pinagem conferida pino a pino com o esquemático da placa v0.8 e **validado em simulação no PC**
> (`make sim-esp32`: o firmware roda com um Arduino falso e conversa com o código real da Jetson; 20 verificações:
> versão, estados, largada pelo J14, PWM e sentido dos dois motores, encoders, bateria pelo divisor 220k/47k,
> watchdog, $A/$S e corte por bateria baixa). Sintaxe conferida para os cores 2.x e 3.x. **Falta gravar numa ESP32
> real** (a compilação com o core da Espressif é feita na Arduino IDE).

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
