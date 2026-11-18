# Robocar Blitz

Carrinho autônomo seguidor de linha para a **RoboCar Race 2026, categoria Micro**. A pista tem linha preta de 20 mm sobre tapete claro, cruzamentos, interseções e bifurcações, e curvas de raio mínimo de 100 mm. Ao fim da volta, o robô tem de parar sozinho no box.
Inspeção e treino em **04/12/2026**; torneio em **05/12/2026** (SENAC Santo Amaro, São Paulo).

**Arquitetura:** câmera IMX219-160 → **Jetson Nano 4 GB** (visão + controle, Python) → USB serial → **ESP32** (PWM, encoders, bateria, largada, watchdog) → 2× DRV8833 → 2× N20 6 V (em 7,2 V). Detalhes em [docs/02_arquitetura.md](docs/02_arquitetura.md).

## Estado (09/11/2026)

| Parte | Situação |
|---|---|
| Software da Jetson | Implementado; **35 testes automáticos passando no PC**; integração com ESP32 **simulada** OK. Não testado na câmera real |
| Firmware da ESP32 | Implementado; **só checagem de sintaxe**, falta compilar e gravar |
| Hardware | Compras definidas (R$ 694,02 com fretes, dentro dos R$ 800); **pedidos a fazer** |
| Placa da ESP32 | **v0.6** enxuta, embaixo da Jetson: 72,5 × 63 mm com furos M3 nos cantos, face simples (só B.Cu, sem vias), trilha ≥ 1 mm, **2 jumpers** (JP1/JP2), só peças já compradas; DRC 0 violações e paridade esquema × placa OK (`make drc`); **testar o encoder em 3,3 V quando os motores chegarem, medir as peças, corroer e montar** ([hardware/placa_esp32/](hardware/placa_esp32/)) |
| Mecânica | Chassi a projetar (CAD) e imprimir |

Próximos passos e cronograma: [docs/07_plano.md](docs/07_plano.md).

## Início rápido

```bash
make ajuda                      # lista os comandos
make testes                     # testes automáticos (PC ou Jetson; sem hardware)
make calibrar                   # na Jetson: calibração preto/branco
make visao                      # na Jetson: câmera ao vivo, sem mover motores
make carro PORTA=/dev/ttyUSB0   # no carro: largada pelo botão da ESP32
```
Instalação na Jetson: [jetson/README.md](jetson/README.md). Gravação da ESP32: [firmware/README.md](firmware/README.md).

## Onde está cada coisa

| Quero… | Vá para |
|---|---|
| entender a regra e o que perguntar à organização | [docs/01_regulamento.md](docs/01_regulamento.md) |
| ver componentes, elétrica, **pinagem**, massa e cálculos | [docs/03_hardware.md](docs/03_hardware.md) |
| entender ou alterar o código | [docs/04_software.md](docs/04_software.md) · [jetson/](jetson/) |
| ver o esquemático e a placa (PCB) da ESP32 | [hardware/placa_esp32/](hardware/placa_esp32/) |
| ver o protocolo Jetson ↔ ESP32 | [docs/05_protocolo_serial.md](docs/05_protocolo_serial.md) |
| testar (bancada e pista) e registrar resultados | [docs/06_testes.md](docs/06_testes.md) |
| comprar / ver orçamento e fretes | [compras/README.md](compras/README.md) |
| saber por que algo foi decidido | [docs/decisoes.md](docs/decisoes.md) |
| contribuir (convenções, git, checklist) | [CONTRIBUTING.md](CONTRIBUTING.md) |
| ver o código original | [legado/](legado/) |

```
docs/        documentação numerada + decisões + regulamento (PDF)
compras/     planilha de compras + CSV original
jetson/      software da Jetson: programas, biblioteca robocar/, config/, testes/
firmware/    firmware da ESP32 (Arduino)
hardware/    placa da ESP32 (KiCad: esquemático, PCB, arquivos de fabricação)
dados/       vídeos, logs e capturas dos testes (fora do git)
legado/      peb.py e seguir_linha.py originais, intactos
```

## Implementado
- Captura de baixa latência (GRAY8 no hardware, fila de 1 quadro, 60 fps, alternativas automáticas).
- Calibração salva em arquivo, com modo automático; limiar adaptativo à iluminação.
- Detecção por faixas que mantém a linha em cruzamentos e interseções em X; erro perto, erro longe e inclinação.
- Controle PD com antecipação e redução de velocidade em curva; busca e parada com linha perdida; parada opcional por marca.
- Protocolo serial versionado com checksum; firmware com estados, watchdog em dois níveis, rampa, encoders, bateria e botão de largada.
- Parâmetros com fonte única e validação; log CSV, gravação de vídeo e reprocessamento offline; Makefile; testes.

## Falta
- [ ] Compras, montagem e chassi.
- [ ] Compilar e testar o firmware; validar encoders, ADC e sentido dos motores.
- [ ] Testar a câmera real: modo, campo de visão, exposição, **latência**, tempo na Jetson.
- [ ] Controle de velocidade com encoder (PI na ESP32, protocolo v2).
- [ ] Ajustar ganhos e velocidades na pista de teste; definir a detecção do box conforme a resposta da organização.
- [ ] Início automático no boot (systemd) e desligamento seguro.
