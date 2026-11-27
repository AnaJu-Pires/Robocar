# firmware/

Firmware da ESP32 (controladora escrava): PWM dos DRV8833 com rampa, encoders, bateria, botão de largada e watchdog.
Os estados estão em [docs/02_arquitetura.md](../docs/02_arquitetura.md#3-estados) e o protocolo em [docs/05_protocolo_serial.md](../docs/05_protocolo_serial.md).

| Arquivo | Conteúdo |
|---|---|
| `robocar_esp32/config.h` | **Pinos e constantes** (fonte única da pinagem; reproduzida em docs/03_hardware.md) |
| `robocar_esp32/robocar_esp32.ino` | Lógica: estados, protocolo, motores, encoders, bateria |
| `simulacao/` | Arduino falso + roteiro que testa o firmware com o código da Jetson (`make sim-esp32`) |
| `teste_movimento/teste_movimento.ino` | Teste **sem a Jetson**: no botão de largada, anda para a frente, gira 360° no lugar e anda de ré |

> **Estado:** pinagem conferida pino a pino com o esquemático da placa v0.8 e **validado em simulação no PC**
> (`make sim-esp32`: o firmware roda com um Arduino falso e conversa com o código real da Jetson; 20 verificações:
> versão, estados, largada pelo J14, PWM e sentido dos dois motores, encoders, bateria pelo divisor 220k/47k,
> watchdog, $A/$S e corte por bateria baixa). Sintaxe conferida para os cores 2.x e 3.x. **Falta gravar numa ESP32
> real** (a compilação com o core da Espressif é feita na Arduino IDE).

## Compilar e gravar
1. Arduino IDE → Gerenciador de placas → "esp32" (Espressif), versão 2.x ou 3.x.
2. Abrir `robocar_esp32/robocar_esp32.ino`. A pasta precisa ter o mesmo nome do `.ino`.
3. Placa "ESP32 Dev Module"; porta `/dev/ttyUSB0` (Linux) ou `COMx` (Windows); gravar.
4. Monitor serial a 115200: aparece `$I,robocar_esp32,v2*..` e, a cada 20 ms, `$T,...`.

**Protocolo v2 (24/11/2026):** grave este firmware **junto** com a atualização da Jetson (`git pull`). Com versões diferentes, a Jetson avisa `ERRO: firmware usa protocolo v1`.

**Botão de largada (J14):** apertar e soltar = largada; apertar com o robô armado = para na hora; segurar 3 s com o robô parado = pede à Jetson para desligar. LED: pisca muito rápido enquanto a Jetson desliga (não corte a chave); **2 piscadas por segundo = pode desligar a chave** (25 s depois de a Jetson parar de mandar comandos, `ESPERA_DESLIGAR_MS`; se ela voltar, cancela). Não deixe um jumper fixo no J14 ([D-039](../docs/decisoes.md)).

## Primeiro teste, sem motores
1. Só a ESP32 ligada ao PC: LED apagado = SEM_JETSON (sem comandos).
2. Na Jetson: `make bancada PORTA=/dev/ttyUSB0` → LED piscando devagar (PRONTO), depois aceso (ARMADO).
3. Fechar o programa: freia em 250 ms; em 1 s o LED apaga (teste T08).
4. Só depois ligar os drivers e os motores, **com as rodas suspensas** (teste T05). Ajustar `INVERTER_E/INVERTER_D` em `config.h`.

## Teste de movimento sem a Jetson (`teste_movimento/`)
Programa separado, só para conferir motores, sentido das rodas e encoders. **Ele substitui o firmware do robô:
depois do teste, grave de novo `robocar_esp32/robocar_esp32.ino`.**

1. Arduino IDE → abrir `teste_movimento/teste_movimento.ino` → gravar (mesma placa e porta).
2. ESP32 alimentada pelo USB (Jetson ligada, carregador de celular ou PC) e bateria ligada (motores).
3. Monitor serial a 115200 (opcional). **Primeiro com as rodas no ar.**
4. Apertar o botão de largada: 1 s depois, FRENTE → pausa → GIRO de 360° para a direita → pausa → RÉ.
   Apertar o botão de novo durante o movimento **para na hora**.
5. No chão (≥ 1,5 m livres na frente e atrás), ajustar `TEMPO_GIRO_MS` até dar uma volta completa. O monitor
   mostra os pulsos dos encoders de cada etapa; com a média do giro em `PULSOS_GIRO_360`, o giro passa a ser
   medido pelos encoders.

Velocidades e tempos ficam no topo do arquivo. Os pinos são uma **cópia** de `robocar_esp32/config.h`: se a
pinagem ou `INVERTER_E/INVERTER_D` mudarem lá, mudar aqui também.
