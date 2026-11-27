# Histórico de versões

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versões no formato MAIOR.MENOR.CORREÇÃO.

## [Não lançado]
### Adicionado (27/11/2026, trabalhar só pelo SSH)
- `make fotos` / `seguir_linha.py --fotos [SEG]`: sem janela, salva imagem + máscara a cada SEG s e nos eventos (largada, linha sumiu, parou) em `dados/capturas/<data>/`.
- Log CSV com flush a cada 0,5 s e fsync numa thread a cada 2 s: o corte da chave não apaga mais a corrida (o log `20261121_204647.csv` do cartão ficou só com o cabeçalho).
- `camera.trava_balanco_branco` (awblock), junto da trava de exposição que já existia. 7 testes novos (`test_registro.py`).
### Alterado (27/11/2026, seguir a linha: fim da linha, cruzamento e freio)
- Controle: novo estado **AVANCANDO** (D-038). Linha some indo reto (`|erro|`, `|erro_longe|` ≤ `reto_max_erro` 0,25) ou num cruzamento: segue reto a no máximo `v_avanco` (0,25) por até `avanco_s` (0,35 s); a linha voltou → segue; não voltou → PARADO "fim da linha" (box). Na curva continua girando (BUSCANDO). `avanco_s` = 0 volta ao comportamento antigo.
- `seguir_linha.py`: ao parar, mantém zero armado (freio) por `parada.freio_s` (0,5 s) antes de desarmar; antes desarmava na hora e a roda ficava solta. `make metricas` conta "vezes que seguiu reto sem linha". 9 testes novos.
### Alterado (27/11/2026, rodada 2f: chassi para cortar)
- Chassi v4 é o escolhido (D-037). Furos de fixação das peças compradas viram **marcas gravadas** (círculo + cruz) para furar à mão; continuam cortados os que alinham chapas, encaixes e passa-fios. Auditoria do DXF confere e tem teste negativo novo.
- Placa da luz acima do pivô da câmera (orelhas mais altas), com a fita COB na frente e o módulo da luz atrás; cabo `luz` preso na travessa do mastro. 176 × 143 × 181 mm (162 mm com a câmera em 45°), 667 g.
- Placa de distribuição: aviso para **não usar 1N4728** (zener de 3,3 V) no D1; sem 1N5408/1N400x, o D1 fica vazio.
### Alterado (27/11/2026, rodada 2d: energia)
- `hardware/placa_distribuicao/` (`make placa-distribuicao`): placa de distribuição corroída, 32 × 44 mm, face simples (D-036). Bateria → fusível 7 A → chave → SW+ em estrela para os 2 XL4016, VBAT, LED "chave ligada" e diodo de proteção contra bateria invertida. Gerada pelo KiCad com DRC, conferência pino a pino, só B.Cu e largura mínima de 3 mm nos caminhos de corrente; 7 testes negativos; PDF 1:1 para transferência e furação.
- Chassi v4: a placa entra no lugar da placa de fusível de 30 × 30 (espaçadores de 10 mm, 2 furos e um passa-fio novo no andar 2); fios novos (`chave_placa`, `alim_xl1`, `alim_xl2`; sai o jumper de um borne para o outro).
- O botão de largada no painel foi desfeito: a equipe já tem um botão no J14 (placa da ESP32 sem mudança). A placa de interface volta a 16 × 7 furos.
### Alterado (27/11/2026, rodada 2c: painel do operador)
- Placa de interface vira o painel do operador (17 × 7 furos, 43 × 18 mm; D-035): botão de LARGADA (S3) no lugar do jumper J14, ligado por 2 fios Dupont, ao lado do botão de DESLIGAR e dos LEDs. 11 testes negativos no desenho (novo: botão de largada ligado ao GND da Jetson).
- Chassi v4: botão de largada, J3 e cabo `largada_j14` no modelo; o acesso ao botão de largada passa para o painel.
- Luz: instruções para a fita COB 5 V comprada (não usar o controle de toque, que regula por PWM e faz faixas na imagem; 3 pedaços de 5 cm; medir a corrente).
### Alterado (27/11/2026, rodada 2b: placa de interface)
- `hardware/placa_desligar/layout.py` (`make placa-interface`): placa de interface 16 × 7 furos desenhada furo a furo (lado dos componentes e da solda em `imagens/placa_perfurada.png`), com verificação de redes, furos, corpos, parafusos, pontes e bordas e 10 testes negativos. Grava `layout.json`, que o chassi v4 lê (D-034).
- O MOSFET da luz sai da placa e vai para um módulo junto da luz (J2 de 3 vias: 5V, LUZ, GND). Chicote do J41 com 8 fios (15–20, 2 e 6).
- Chassi v4: passa-fios dos motores no andar 3 para a frente da placa da ESP32 (o do motor direito ficava embaixo da placa de interface). Nova verificação "cabo não atravessa placa de circuito" (e teste negativo), que corrigiu também as rotas do VM esquerdo, do VBAT e do chicote do J41. Fios do VM: ≥ 216 / 156 mm.
### Adicionado (27/11/2026, rodada 2)
- Luz da câmera e LED amarelo "código rodando" na placa extra, que vira placa de interface (D-033): `jetson/robocar/leds.py`. A luz (J41 pino 15, IRLZ44N, 5 V regulados) acende antes de abrir a câmera no `seguir_linha.py` e no `calibrar.py`, apaga ao sair e com 5 quadros seguidos sem imagem; o amarelo (pino 19) pisca 1 Hz esperando e 4 Hz andando. `seguir_linha.py --sem-leds`. O serviço `botao-desligar` exporta os 2 pinos e libera a escrita para o programa do robô (`Before=robocar.service`). 7 testes novos (6 em `test_leds.py`, 1 no serviço).
- Chassi v4: placa extra de 30 × 18 para 40 × 18 mm, LED amarelo no modelo e chicote do J41 com 7 fios (pinos 15–20 + pino 2). 51 verificações e 30 testes negativos passam; DXF, PDF, STEP e imagens regerados.
### Adicionado (27/11/2026, rodada 1)
- `make metricas` (`jetson/metricas_log.py`, `robocar/metricas.py`): números da corrida a partir do log CSV (tempo andando, distância e velocidade pelos encoders, vezes que perdeu a linha, % de quadros com linha, |erro| p50/p95, cruzamentos, fps real, maior travada, processamento, queda da bateria). 4 testes.
- `docs/08_diario.md`: diário de engenharia das rodadas de otimização.
### Adicionado (26/11/2026, chassi v4)
- `mecanica/chassi_v4/`: chassi de **3 andares** (D-031), 162 × 143 × 160 mm (o v3 tinha 240): XL4016 e bateria no piso (bateria atravessada, sai pela direita), Jetson de través no 2º andar com as portas para trás, placa da ESP32, placa de desligar e mastro curto da câmera no 3º. Bitola 124 mm. Andares 2 e 3 removíveis com porcas presas.
- Curva limitada a 0,65 g (R100 a ≤ 0,80 m/s; D-032): o carro tomba com 0,77 g. A verificação de CG passa a comparar o tombamento com esse limite.
- 51 verificações e 30 testes negativos (novos: bateria saindo pela roda, ar em cima do dissipador, pilar sobre a porca, limite de curva); auditoria do DXF em todas as chapas. `make chassi*` passa a usar o v4; o v3 fica como referência.
### Adicionado (25/11/2026, chassi v3)
- `mecanica/chassi_v3/`: chassi definitivo em MDF 3 mm (D-026): Jetson baixa sobre a bateria (túnel com pino de trava, sai pela frente), caixa traseira com os 2 XL4016 e tampo removível com a placa da ESP32 sobre o eixo, quilha central, pisos sobrepostos que nivelam a esfera de 15 mm. 240 × 140 × 154 mm, 633 g, CG a 36 mm; 1 chapa de 390 × 270 mm.
- Gerador `fonte/gerar.py` (`make chassi`): STEP montado, DXF, pente de teste com gabaritos de furação da Jetson, do XL4016 e da placa da ESP32, PDF 1:1 em A3 com régua, imagens, `verificacao.md` (cabos com comprimento de corte, massas, fixadores) e `resumo.json`.
- 52 verificações automáticas que param o `make` (regulamento, interferência com volumes de acesso, câmera em toda a faixa de ângulo e o que ela vê do carro, material mínimo/entalhe/peça solta/gravação, CG e tombamento, cabos, e a releitura do DXF gravado) e 28 testes negativos (`make chassi-negativos`); `make chassi-cortar` barra o corte com medida estimada.
- `fonte/analise.py`: 3 arquiteturas e 4 rodas no mesmo modelo de volta; rodas de 42 mm mantidas (D-027).
- Botão de desligar a Jetson no J41 com LED "pode desligar a chave" (D-028): `hardware/placa_desligar/`, `jetson/robocar/botao_desligar.py`, `jetson/servico/botao_desligar.py` e `botao-desligar.service` (instalado por `make servico`); 8 testes.
- `docs/06_testes.md`: T15 (desligar), T16 (temperatura), T17 (massa e CG), T18 (chassi v3).
### Alterado (25/11/2026)
- Controle: `acel_max` = 2,0/s limita só a subida da velocidade (o chassi v3 empina acima de ~0,47 g; D-030). 2 testes novos; a simulação do firmware confere o PWM depois da rampa (26/26).
### Adicionado (25/11/2026)
- `make calibrar-auto` (`calibrar.py --auto`): calibração sem janela pelo SSH (o `ssh -X` derrubava a câmera). Otsu em 30 quadros depois de a exposição estabilizar; salva e grava uma foto (imagem + máscara) em `dados/capturas/`.
- `make diagnostico` (`jetson/servico/diagnostico.sh`): junta serviço, kernel, reinícios, configuração, logs CSV e fotos num `.tar.gz`.
### Corrigido (25/11/2026)
- Calibração automática (tecla A e `--auto`): com só o chão na imagem, o Otsu dividia o ruído em "branco" e "preto" (ex.: 204/195) e salvava uma calibração inútil; agora exige 25 de separação. 3 testes novos.
### Alterado (25/11/2026, a partir dos logs do teste no chão de 22/11)
- **Visão:** a razão do limiar vinda da calibração fica entre `razao_min` 0,35 e `razao_max` 0,70. A calibração de 22/11 (branco 106, preto 66) dava razão 0,81: o chão virava "escuro", e 46 % dos quadros acusavam cruzamento falso e a linha sumia. O limiar também é suavizado entre quadros (`suavizar_limiar` 0,3); no log ele pulava de 57 a 187. `calibrar.py` avisa contraste baixo abaixo de 60 (era 40). 5 testes novos, um deles reproduzindo o caso real.
- **Controle:** `v_busca` 0,25 → 0,45 e `tempo_busca_s` 0,6 → 1,0. Com 0,25 o carro não girava no chão e parava por "linha perdida".
- **Protocolo v2 / botão:** segurar o botão de largada 3 s com o robô parado liga a flag DESLIGAR na telemetria e a Jetson faz `shutdown` (regra do sudo instalada pelo `make servico`). A largada passa a ser ao **soltar** o botão; apertar com o robô armado continua parando na hora. LED pisca muito rápido ao desligar. Firmware e Jetson precisam ser atualizados juntos. Simulação do firmware: 26/26 (6 novas).
### Corrigido (24/11/2026, revisão do código)
- `abrir_porta`: espera a ESP32 reiniciar (1,5 s) depois de cada reabertura; antes a conferência podia falhar com o link bom e a última tentativa voltava sem limpar o buffer.
- `teste_movimento.py`: não fica preso para sempre se a ESP32 não aceitar comandos (SEM_JETSON) ou parar de mandar telemetria; com `--armar`, repete o `$A` a cada 0,5 s; recusa velocidades fora de 0–1 e tempos negativos. 4 testes novos.
- Docs: o botão de largada é o GPIO4 (J14), não o GPIO23.
### Adicionado (24/11/2026)
- `jetson/servico/` e `make servico`: início automático no boot (systemd). Abre o modo corrida e espera o botão de largada; espera a ESP32 aparecer, reinicia se o programa cair e para com SIGINT (desarma a ESP32). Unidade conferida com `systemd-analyze verify`; falta testar na Jetson.
### Corrigido (22/11/2026)
- `robocar/esp32.py`: `abrir_porta` confere se chega telemetria legível; se vier embaralhada (primeira abertura depois de ligar o USB, Jetson Nano + CP2102), reabre a porta em 9600 e volta para 115200, até 3 vezes. 4 testes novos.
- Porta serial aberta em modo exclusivo: um segundo programa na mesma porta (ex.: `make movimento` rodando duas vezes) dá erro em vez de misturar comandos e telemetria.
### Adicionado (22/11/2026)
- `jetson/teste_movimento.py` e `robocar/manobra.py` (`make movimento`): o mesmo teste (frente, giro de 360° e ré) comandado pela Jetson com o firmware do robô; largada pelo botão, botão de novo para na hora; mostra os pulsos dos encoders de cada etapa. Giro padrão 0,6 por 2,0 s (medido no chão). 5 testes novos (`test_manobra.py`, com uma ESP32 falsa) e conferido com o firmware simulado.
### Adicionado (21/11/2026)
- Sentido dos motores (T05 no carro): as duas rodas giravam ao contrário; `INVERTER_E = true` e `INVERTER_D = false` no `config.h` e no teste de movimento (roteiro da simulação ajustado, 20/20 OK). Giro do teste a 60 % por 1,2 s.
- `firmware/teste_movimento/`: teste sem a Jetson. No botão de largada, anda para a frente, gira 360° no lugar e anda de ré; botão de novo para na hora; mostra os pulsos dos encoders de cada etapa. Conferido numa simulação no PC (Arduino falso); falta testar no carro.
- Primeiros testes reais: firmware compilado (core 3.3.12) e gravado na ESP32; câmera a 60 fps (3,8 ms por quadro) e Jetson ↔ ESP32 funcionando (`make bancada`); Jetson na bateria pelo plug P4 (pelos pinos 5 V com fio jumper ela desligava no boot).
### Corrigido (placa v0.8, ajustes da equipe, 19/11/2026)
- `hardware/placa_esp32/`: incorporados os ajustes feitos no KiCad 10 (placa **80 × 73**, motor em Y, R2–R4 no meio da ESP32, J2 alinhado com o C1, texto BLITZ). Corrigido o GND dos drivers, que ia ao plano por um toco e passava por um trecho de 0,4 mm: voltou a ser trilha de 1,5 mm (D-025). Plano de volta para 0,6/1,0/1,0 mm. Borda exata, furos simétricos, degraus e curva de 90° tirados. DRC 0, paridade OK.
- Esquemático: PWR_FLAG em VM_E, VM_D e GND (3 erros do ERC) e tudo na grade de 1,27 mm (98 avisos). Ligações iguais.
- Novo `ferramentas/netlist_texto.py`: lê o esquemático do KiCad 10 sem o KiCad (usado pelo gerador e pelo `verificar.py` quando o kicad-cli é mais velho). `.history/` (VS Code) no `.gitignore`.
### Alterado (placa v0.8, 19/11/2026)
- `hardware/placa_esp32/`: **placa espelhada** (D-024), 80 × 70 mm: tudo do motor esquerdo à esquerda e do direito à direita, ESP32 no meio com o USB para trás e área sem cobre embaixo da antena. Ilhas retangulares arredondadas alongadas (furo e passo iguais), trilhas de 1,0 mm (sinal) e 1,5 mm (potência), curvas chanfradas a 45°, saída reta das ilhas, 62 gotas, plano de GND em volta de tudo. 3 jumpers (JP3 novo), resistores de passo 7,62 mm (R2–R4 embaixo da ESP32), encoders na ordem A, B, −, +. DRC 0, paridade OK.
- Esquemático: pinagem nova da ESP32 e JP3 (`SLEEP_D_JP`); `config.h` com os GPIOs novos; `docs/03_hardware.md` (pinagem) atualizado.
- Novo gerador `ferramentas/montar_placa_v08.py`; `verificar.py` mede a distância aos furos pela ilha inteira; regras novas no `.kicad_dru`.
- Novo `LISTA_DE_SOLDAGEM.md` (o que é cada peça e se já temos); BOM e `jumpers.json` refeitos; PDFs, furação, STEP e imagens refeitos.
- Pendente: chassi ainda com a placa v0.7.
### Alterado (placa v0.7, 18/11/2026)
- `hardware/placa_esp32/`: **USB da ESP32 para a frente do carro** (D-023): layout da v0.6 girado 90°, placa de **63 × 72,5 mm**; serigrafia refeita, BOM/jumpers com coordenadas novas. DRC 0, paridade OK, zona salva conferida.
- `verificar.py`: acusa zona de GND desatualizada no arquivo salvo.
- `mecanica/chassi/`: placa com a frente em x = 124 mm, furos novos no andar 1, paredes sem a janela de USB; DXF/PDF, STEP e imagens refeitos.
### Alterado (placa v0.6, 18/11/2026)
- `hardware/placa_esp32/`: roteamento refeito (D-022): **72,5 × 63 mm** (era 80 × 67), **furos M3 nos 4 cantos**, GND da ESP32 (pinos 14 e 29) ligado ao plano por **alívio térmico com 2 raios** em vez dos tocos de trilha. Esquemático e pinagem iguais. DRC 0, paridade OK, só 0/45/90°, cobre não-GND a ≥ 3,6 mm dos furos.
- `verificar.py` confere também ângulos, larguras e a distância do cobre aos furos; BOM e `jumpers.json` com as coordenadas novas.
- `mecanica/chassi/`: `chassi.py` com o tamanho e os furos novos da placa; `corte_MDF.dxf`/PDF, `chassi_montado.step` e imagens refeitos.
### Corrigido (placa v0.5.1, 18/11/2026)
- `hardware/placa_esp32/`: projeto KiCad só com cobre em **B.Cu** (D-021): os 2 jumpers deixaram de ser trilhas em F.Cu + 4 vias e viraram componentes JP1/JP2 (esquemático e placa, redes `ME_IN2_JP`/`MD_IN2_JP`); `placa_esp32.kicad_dru` faz o DRC acusar qualquer trilha/zona em F.Cu ou via. Cobre e furação iguais aos da v0.5.
- Pegadas ligadas aos símbolos (o "Atualizar PCB a partir do esquemático" não recria peças); furos de fixação marcados "só na placa"; símbolos da biblioteca apontando para as pegadas `_SoldaManual`.
- 3D: ESP32 com o STEP de 30 pinos baixado pela equipe; DRV8833 só com as barras fêmea nativas; apagados os `.wrl` desenhados à mão. `placa_esp32.step` e `imagens/vista_3d.png` refeitos.
- Serigrafia M−/M+ e JP1/JP2 afastada das ilhas. DRC: 0 violações; paridade esquema × placa: 19 peças, 23 redes.
- Avisos do DRC do KiCad 10: 17 ilhas sem a rede `unconnected-(…)` e 5 pegadas `Fio_0.75mm2_*` fora da lista de materiais (corrigidos; `verificar.py` agora confere os dois).
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
