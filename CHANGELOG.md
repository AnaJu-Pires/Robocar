# Histórico de versões

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versões no formato MAIOR.MENOR.CORREÇÃO.

## [Não lançado]
### Corrigido (placa v0.5.1, 18/11/2026)
- `hardware/placa_esp32/`: projeto KiCad só com cobre em **B.Cu** (D-021): os 2 jumpers deixaram de ser trilhas em F.Cu + 4 vias e viraram componentes JP1/JP2 (esquemático e placa, redes `ME_IN2_JP`/`MD_IN2_JP`); `placa_esp32.kicad_dru` faz o DRC acusar qualquer trilha/zona em F.Cu ou via. Cobre e furação iguais aos da v0.5.
- Pegadas ligadas aos símbolos (o "Atualizar PCB a partir do esquemático" não recria peças); furos de fixação marcados "só na placa"; símbolos da biblioteca apontando para as pegadas `_SoldaManual`.
- 3D: ESP32 com o STEP de 30 pinos baixado pela equipe; DRV8833 só com as barras fêmea nativas; apagados os `.wrl` desenhados à mão. `placa_esp32.step` e `imagens/vista_3d.png` refeitos.
- Serigrafia M−/M+ e JP1/JP2 afastada das ilhas. DRC: 0 violações; paridade esquema × placa: 19 peças, 23 redes.
- Novos `gerar_saidas.sh` (`make placa`) e `verificar.py` (`make drc`). README da placa com a conferência da revisão feita por outra IA.
### Alterado (placa v0.5, 18/11/2026)
- `hardware/placa_esp32/`: placa refeita **enxuta, para ficar embaixo da Jetson** (D-017): 80 × 67 mm, face simples, trilha ≥ 1 mm, **2 jumpers** (eram 11). Na placa ficam só a ESP32, os 2 DRV8833 com 470 µF, os pontos de solda dos fios, o divisor da bateria e os pull-downs do nSLEEP; fusível, chave e XT60 vão para o chicote. Esquemático novo gerado da mesma tabela de ligações da placa; DRC sem erros de cobre; paridade esquema × placa OK.
- Encoders em 3,3 V direto na ESP32, sem CD4050B e 78L05 (D-018, substitui D-011).
- Motores em 7,2 V (D-019); `docs/03_hardware.md` (energia, cálculos, velocidade, pinagem) e `docs/06_testes.md` (T03, T06, T09) atualizados.
- `config.h`: pinagem nova (motores 16/17 e 19/21, nSLEEP 4 e 18, encoders 32/33 e 25/26); `PIN_BUZZER = -1`. Firmware: um nSLEEP por driver (D-020), buzzer opcional, encoder direito com INPUT_PULLUP. Checagem de sintaxe OK.
### Alterado (placa v0.4, 17/11/2026)
- `hardware/placa_esp32/`: placa refeita para corrosão manual (D-015): face simples, trilha mínima de 1 mm, folga 0,5 mm, ilhas grandes (`lib/robocar_sm.pretty`), 103 × 95 mm e 11 jumpers. J2 dividido em J2 (entrada do XL4016 #2) e J4 (saída de 6 V). DRC sem erros de cobre; paridade esquema × placa OK; ERC a rodar no KiCad 10.
- `config.h`: encoder esquerdo com A no GPIO33 e B no GPIO32 (D-016); `docs/03_hardware.md` atualizado.
### Adicionado
- `hardware/placa_esp32/`: esquemático KiCad 10 da placa da ESP32, numa folha só com blocos ligados por fios, e **placa (PCB) de face simples** de 130 × 105 mm com plano de GND e 15 jumpers (D-014). ERC 0 violações; DRC 0 violações, 0 ligações faltando, paridade com o esquemático OK.
- `hardware/placa_esp32/fabricacao/`: arte do cobre 1:1 para transferência térmica, folha de montagem com jumpers, furação e mapa de brocas.
- Ponte espelhada nos DRV8833 (D-013), canais do CD4050B escolhidos pela posição na placa e TO-92 de pernas largas.
- Encoders em 5 V (78L05) com conversão para 3,3 V por CD4050B; pull-down no nSLEEP dos drivers; buzzer por transistor (D-011).
- `hardware/placa_esp32/lib/`: símbolo, footprint e 3D simplificado da ESP32 DevKit V1 (30 pinos) e do módulo DRV8833, a partir de medidas com fonte (D-012).
### Alterado
- `docs/03_hardware.md`: ESP32 identificada como DevKit V1 de 30 pinos; encoders via CD4050B.
- `docs/06_testes.md`: teste T06 refeito para a placa com CD4050B.
- `config.h`: só comentários (encoders e ponte espelhada); nenhum pino mudou.

## [0.2.0] — 2026-11-09
### Reestruturado
- Código da Jetson virou a biblioteca `jetson/robocar/` + programas finos (`seguir_linha.py`, `calibrar.py`; `peb.py` renomeado para `calibrar.py`).
- Parâmetros com fonte única (`PADRAO`) e validação de chaves; `config/` separado do código; calibração fora do git.
- Testes migrados para `unittest` (35 testes), com link serial testado contra uma porta falsa.
- `Makefile` como ponto de entrada; documentação dividida em `docs/01…07` + `docs/decisoes.md`; `CONTRIBUTING.md`.
- Firmware movido para `firmware/`, com pinos em `config.h`.
### Alterado
- Firmware: máquina de estados (SEM_JETSON/PRONTO/ARMADO/FALHA_BATERIA); arma só com a Jetson ativa; watchdog em dois níveis (freia em 250 ms, desarma em 1 s); botão de largada no GPIO23; pinagem alinhada à planilha da equipe (GPIO13 em vez de 14).
- Protocolo v1: telemetria com `estado` e `flags`; comando `V` (versão) com checagem na Jetson.
- `--armar` aguarda a ESP32 ficar PRONTO.
- Compras: fonte 5 V removida (há fonte de bancada no laboratório); cabinho 0,75 mm² acrescentado; plug P4 ×3; frete Smart Kits simulado para o CEP; câmera IMX219-160 e Jetson 4 GB registradas.

## [0.1.0] — 2026-11-09
### Adicionado
- Pipeline de câmera de baixa latência, detecção por faixas, limiar adaptativo, controle PD com antecipação, parada por linha perdida e por marca.
- Calibração salva em arquivo, protocolo serial com checksum, primeira versão do firmware.
- Planilha de compras com 3 cotações, fretes e orçamento.

## [0.0.1] — anterior a 2026-11-09
- `peb.py` e `seguir_linha.py` originais (preservados em `legado/`).
