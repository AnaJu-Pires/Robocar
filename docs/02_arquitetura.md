# 02 — Arquitetura do sistema

## 1. Visão geral

```
                Jetson Nano 4 GB (Python, ~60 Hz = taxa da câmera)                 ESP32 (C++, tempo real)
 IMX219-160 ─► camera ─► visao ─► controle ──► esp32 ═══ USB serial ═══► protocolo ─► rampa ─► PWM ─► 2× DRV8833 ─► N20
   (CSI)       320×180   faixas    PD +          $M,seq,esq,dir  (~60/s)          estados    1 kHz   20 kHz    (7,2 V)
               cinza     erros     velocidade   ◄── $T,... (50 Hz) ───────────── encoders, bateria (ADC), botão
```

| Componente | Responsabilidade | Não faz |
|---|---|---|
| **Jetson** ([jetson/](../jetson/)) | Enxergar a linha, decidir direção e velocidade, detectar cruzamento, perda de linha e chegada, registrar logs | Gerar PWM, contar pulsos, garantir segurança elétrica |
| **ESP32** ([firmware/](../firmware/)) | PWM com rampa, encoders, bateria, botão de largada, **watchdog** (para o robô se a Jetson falhar) | Decidir a trajetória |

Motivo da divisão: o Linux da Jetson não é tempo real. Pausas de dezenas de ms são possíveis e não podem deixar o motor sem controle. A lei de controle fica em Python porque é ajustada na pista sem regravar firmware. Ver [decisoes.md](decisoes.md) D-001 e D-006.

## 2. Fluxo por quadro (Jetson)

1. `camera.ler()` entrega o quadro **mais recente** (fila de 1), já em 320 × 180 e cinza.
2. `visao.processar()` calcula erro perto, erro longe, inclinação, cruzamento e marca.
3. `controle.atualizar()` calcula velocidade e direção e gera os comandos esquerda/direita em [−1, 1].
4. `esp32.enviar_motores()` envia o comando. É enviado **sempre**, mesmo zerado: isso mantém o link "vivo".
5. A telemetria recebida atualiza a largada (ARMADO → `iniciar`) e o log.

## 3. Estados

**Jetson** ([controle.py](../jetson/robocar/controle.py)):

```
AGUARDANDO ──largada──► SEGUINDO ◄──linha volta── BUSCANDO
                          │  └──linha some──────────►│
                          └──marca do box──► PARADO ◄─┴── perdida > tempo_busca_s
```

**ESP32** ([robocar_esp32.ino](../firmware/robocar_esp32/robocar_esp32.ino)):

| Estado | Entra quando | Motores |
|---|---|---|
| `SEM_JETSON` (0) | ligou; ou sem comando por > 1 s | desligados (driver dormindo) |
| `PRONTO` (1) | recebe comandos válidos | desligados; aguarda o botão |
| `ARMADO` (2) | botão (ou `$A`) com link ativo | obedecem à Jetson; sem comando por > 250 ms → **freia** |
| `FALHA_BATERIA` (3) | bateria < 3,2 V/célula por 2 s | desligados até reiniciar a placa |

## 4. Orçamento de tempo

| Etapa | Valor | Situação |
|---|---|---|
| Período da câmera | 16,7 ms (60 fps) | modo a validar [T] |
| Algoritmo de visão + controle | < 1 ms no PC; na Jetson, a medir | [V] PC / [T] Jetson |
| Comando serial (115200 baud, ~20 bytes) | ~2 ms | [E] |
| Rampa/PWM na ESP32 | 1 ms / 20 kHz | [E] |
| Latência total câmera → roda | dezenas de ms | **medir** [T] ([06_testes.md](06_testes.md)) |

A 1 m/s, cada 10 ms de latência equivalem a 1 cm percorrido "às cegas". O termo de antecipação (`k_frente`) e a redução de velocidade antes das curvas compensam parte disso.

## 5. Pontos fortes e fracos (avaliação honesta)

**Fortes:**
* a câmera vê à frente, o que permite antecipar curvas e manter a linha em cruzamentos em X e bifurcações;
* a IMX219-160 tem campo de visão largo, útil nas curvas de raio 100 mm;
* processamento sobra: algoritmo < 1 ms no PC.

**Fracos:**
* **latência** (a medir);
* **massa** estimada em ~520 g ([03_hardware.md](03_hardware.md#4-massa)), alta para N20;
* limite físico em curva de R100 em torno de 0,7–0,9 m/s [E];
* boot lento e risco de corromper o microSD se a chave for desligada com o Linux ligado;
* prazo curto.

**Alternativa avaliada:** ESP32 + barra de sensores IR. É mais leve e reage mais rápido, mas é mais frágil em interseções fora de 90° e exigiria refazer tudo. Fica como plano B ([decisoes.md](decisoes.md) D-001).

**Potencial competitivo:** sem dados dos adversários, não dá para afirmar vitória. Como completar a volta vem antes do tempo, a estratégia é **confiabilidade primeiro** (cruzamentos e parada no box). Depois, aumentar a velocidade com base nos logs.
