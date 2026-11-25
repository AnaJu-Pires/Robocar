# Registro de decisões técnicas

Formato curto (inspirado em ADR): contexto → decisão → consequências. Decisão nova = nova entrada; decisão revista = marque a antiga como **substituída por D-xxx**.

---

### D-001 — Câmera na Jetson, ESP32 como controladora escrava
*09/11/2026 · aceita*
**Contexto:** a categoria Micro tem cruzamentos, interseções fora de 90°, bifurcações, curvas de raio 100 mm e exige parar no box. A equipe já tinha Jetson, câmera e código.
**Decisão:** a visão e a decisão de trajetória ficam na Jetson; o PWM, os encoders, a bateria, a largada e o watchdog ficam na ESP32.
**Alternativa descartada (por ora):** só ESP32 + barra IR. É mais leve e rápida, mas pior em interseções e bifurcações, e exigiria refazer tudo. Plano B se a latência medida inviabilizar velocidades úteis.
**Consequências:** mais massa e latência; ganho em antecipação de curvas e robustez em cruzamentos.

### D-002 — 3S com dois conversores XL4016 (5,2 V Jetson / 6,0 V motores)
*09/11/2026 · aceita*
**Contexto:** o DRV8833 aceita no máximo 10,8 V; a regra limita o motor a 12 V; a 3S cheia tem 12,6 V. O UBEC Hobbywing do CSV custava R$ 199,90 e estava fora de estoque.
**Decisão:** 2× XL4016 (R$ 29,90 cada), um por trilho, com limite de corrente ajustado.
**Consequências:** são volumosos (65 × 46 × 24 mm) e de massa não declarada; têm peças intercambiáveis. Se a medição mostrar corrente baixa nos motores, um LM2596 pode substituir o do trilho de 6 V.
**Revisão:** o trilho dos motores passou para 7,2 V em D-019.

### D-003 — Detecção por faixas com previsão e limiar adaptativo
*09/11/2026 · aceita*
**Contexto:** o original (maior contorno + centroide, limiar fixo) errava em interseções em X (erro de −0,203 no teste) e falhava com outra iluminação.
**Decisão:** faixas horizontais, segmento mais próximo da posição prevista, rejeição de faixas largas e de saltos, limiar = razão calibrada × percentil 90 da ROI.
**Consequências:** robusto nos casos testados (sintéticos). Sombra forte e reflexos ainda precisam de teste real. O modo `otsu` fica disponível.

### D-004 — Pipeline de câmera de baixa latência
*09/11/2026 · aceita*
**Decisão:** 1280 × 720 @ 60 → 320 × 180 GRAY8 no nvvidconv; appsink com fila de 1 quadro; fallbacks automáticos.
**Consequências:** o modo 60 fps pode ter campo de visão diferente do 1640 × 1232 @ 30. Validar no teste T11.

### D-005 — Protocolo texto com checksum e watchdog em dois níveis
*09/11/2026 · aceita*
**Decisão:** mensagens `$...*HH` legíveis no monitor serial; versão negociada (`V`); watchdog freia em 250 ms e desarma em 1 s.
**Consequências:** ~20 bytes por comando, o que é suficiente a 115200 baud. Uma pausa curta da Jetson só freia o robô; uma pausa longa exige nova largada.

### D-006 — Controle de direção na Jetson; ESP32 em malha aberta (fase 1)
*09/11/2026 · aceita*
**Decisão:** o PD fica em Python (ajuste rápido na pista). A ESP32 aplica o PWM com rampa e informa os encoders.
**Próximo passo:** PI de velocidade por roda na ESP32 (protocolo v2), quando os encoders estiverem validados (T07).

### D-007 — Bateria RoboCore 3S 1100 mAh em vez da Tattu 1300 mAh
*09/11/2026 · aceita*
**Contexto:** a autonomia necessária é baixa (volta < 1 min; estimativa de 30–45 min por carga). Pico de ~4,3 A.
**Decisão:** RoboCore 3S 1100 mAh 20C, com 70 g contra 122 g, no mesmo pedido dos motores.
**Consequências:** a Tattu (Helitec) sairia R$ 1,05 mais barata no total, mas com um terceiro pedido e +52 g.

### D-008 — Pinagem da ESP32 (base: planilha da equipe)
*09/11/2026 · aceita*
**Decisão:** adotada a pinagem da equipe, com uma mudança: motor direito IN2 no **GPIO13** em vez do GPIO14, que emite PWM durante o boot. A fonte única é `firmware/robocar_esp32/config.h`.

### D-009 — Compras em 2 lojas, Smart Kits por Sedex
*09/11/2026 · aceita*
**Decisão:** RoboCore (motores, bateria, segurança) + Smart Kits (eletrônica, rodas, carregador, fios). Sedex na Smart Kits, a ~R$ 23 a mais que o PAC, por chegar ~5 dias úteis antes num cronograma em que a montagem é o caminho crítico. Fonte de bancada do laboratório no lugar da fonte 5 V.
**Consequências:** R$ 694,02 com fretes (Smart Kits simulado; RoboCore estimado) e saldo de R$ 105,98. Detalhes em [compras/README.md](../compras/README.md).

### D-010 — Estrutura do repositório
*09/11/2026 · aceita*
**Decisão:**
* biblioteca `jetson/robocar/` separada dos programas;
* parâmetros com fonte única (`PADRAO`) e validação;
* testes `unittest` (rodam no Python 3.6 sem dependências extras);
* `Makefile` como ponto de entrada;
* documentação numerada e este registro de decisões;
* originais em `legado/`;
* dados de teste fora do git.
**Convenções:** [CONTRIBUTING.md](../CONTRIBUTING.md).

### D-011 — Encoders em 5 V com conversor CD4050B
*14/11/2026 · substituída por D-018*
**Contexto:** a RoboCore não informa a tensão do encoder; a única medida dela é a saída a ~5 V (5,28 Vpp no osciloscópio). Encoders N20 Hall de outros fabricantes (Waveshare, ficha BJ-N20 da SparkFun) aceitam 3,3 ou 5 V e saem com nível igual à alimentação. A ESP32 não tolera 5 V nos GPIOs.
**Decisão:** alimentar os encoders com 5 V de um 78L05 na placa e converter A/B para 3,3 V com um CD4050B alimentado em 3,3 V (a TI garante entrada acima do VCC). Pull-up de 10 k no lado de 5 V.
**Consequências:** o encoder trabalha na condição medida pela loja e a ESP32 nunca recebe mais que 3,3 V, seja qual for o tipo de saída do encoder. Divisor resistivo foi descartado porque o pull-up interno do encoder é desconhecido e poderia derrubar o nível alto abaixo de 2,48 V (0,75 × VDD). Custo: CD4050B, soquete DIP-16, 78L05 e 4 resistores.

### D-012 — Biblioteca KiCad própria para ESP32 DevKit V1 e DRV8833
*14/11/2026 · aceita*
**Contexto:** a DevKit V1 de 30 pinos e o módulo DRV8833 não existem nas bibliotecas nativas do KiCad 10 (a da Espressif só tem a DevKitC de 38 pinos). O SnapEDA tem a DevKit V1 da DOIT, mas exige login e bloqueia acesso automático; bibliotecas da comunidade têm erro conhecido de distância entre fileiras.
**Decisão:** `hardware/placa_esp32/lib/` com símbolo, footprint e 3D simplificado feitos a partir de medidas com fonte citada (README da placa); soquetes com modelos 3D nativos. Sem scripts no repositório: a biblioteca é editada pelos editores do KiCad.
**Consequências:** a distância entre fileiras (ESP32 25,40 mm pelo desenho DOIT; DRV8833 15,24 mm estimada) precisa ser medida nas peças antes de fabricar.

### D-013 — Ponte espelhada nos DRV8833
*14/11/2026 · aceita*
**Contexto:** no módulo, a fileira de entradas é IN4, IN3, GND, VCC, IN2, IN1 (de cima para baixo). Com IN1 da ESP32 (GPIO25, acima do GPIO26) indo para IN1/IN3, as duas linhas se cruzariam na placa de face simples.
**Decisão:** `PIN_x_IN1` vai em IN2+IN4 e `PIN_x_IN2` em IN1+IN3; o M+ do conector sai de OUT2+OUT4. Nenhum GPIO mudou.
**Consequências:** pela tabela-verdade do DRV8833 (TI), trocar entradas e saídas juntas é só renomear a ponte: o sentido de giro continua o mesmo. O ajuste fino do sentido continua sendo `INVERTER_E/INVERTER_D` no teste T05.

### D-014 — Placa de face simples com plano de GND e jumpers
*14/11/2026 · substituída por D-015*
**Contexto:** a equipe corrói a placa em casa, face simples, PTH. Em modo paralelo, as ilhas do DRV8833 alternam de rede, o que impede ligar tudo numa camada só.
**Decisão:**
* placa de 130 × 105 mm com cobre embaixo e plano de GND;
* trilhas de 2,5 mm (bateria), 1,5 mm (motores), 1,2 mm (GND) e 0,7 mm (sinais), com folga de 0,4–0,5 mm;
* 15 jumpers de fio do lado dos componentes;
* entrada sem uso do CD4050B no +3V3 em vez do GND, e 78L05/BC337 em TO-92 de pernas a 2,54 mm.
O roteamento foi automático e conferido pelo DRC do KiCad (com paridade com o esquemático).
**Consequências:** o DRC deu 0 violações, mas a placa não foi fabricada. Os jumpers do +6V_MOT usam cabinho de 0,75 mm². Uma revisão humana do traçado antes de corroer é recomendada.

### D-015 — Placa v0.4 para corrosão manual: trilha mínima de 1 mm e ilhas grandes
*17/11/2026 · substituída por D-017* (as regras de corrosão manual continuam valendo)
**Contexto:** a placa vai ser corroída à mão (transferência térmica), em face simples. Trilhas de 0,7 mm com folga de 0,4 mm e ilhas da biblioteca padrão são arriscadas nesse processo, e 15 jumpers dão trabalho.
**Decisão:** refazer o traçado com trilha mínima de 1,0 mm (motores 1,5 mm, bateria 2,5 mm), folga de 0,5 mm, pegadas `_SoldaManual` (ilha maior, mesmo furo e passo), TO-92 triangular e só curvas de 45°. O traçado usa o cobre por baixo dos módulos (ESP32 e DRV8833 ficam elevados nos soquetes) e por dentro do soquete do CD4050, e resistores como ponte. J2 (4 pontos do XL4016 #2) virou J2 (entrada) + J4 (saída de 6 V, entre os DRV8833).
**Consequências:** placa de 103 × 95 mm (era 130 × 105) e 11 jumpers (eram 15; só um de cabinho). DRC sem erros de cobre e paridade esquema × placa conferida pino a pino; ERC a rodar no KiCad 10. Não fabricada. Detalhes em [hardware/placa_esp32/](../hardware/placa_esp32/).

### D-016 — Encoder esquerdo: A no GPIO33, B no GPIO32
*17/11/2026 · substituída por D-017*
**Contexto:** na face simples, com a ordem dos pinos do conector do motor e do CD4050, o par A/B do encoder esquerdo chegaria à ESP32 cruzado.
**Decisão:** trocar os dois GPIOs no `config.h` (`PIN_ENC_E_A = 33`, `PIN_ENC_E_B = 32`) em vez de gastar um jumper.
**Consequências:** comportamento igual (o firmware lê A e B pelos nomes). Quem usar a placa v0.3 precisa voltar aos valores antigos.

### D-017 — Placa v0.5: só ESP32 + drivers, embaixo da Jetson
*18/11/2026 · aceita*
**Contexto:** a v0.4 (103 × 95 mm, 11 jumpers) juntava distribuição de energia, conversor de nível e buzzer. No carro, a placa fica no 1º andar, embaixo da Jetson (100 × 80 mm), enquanto a bateria e os XL4016 ficam perto do eixo traseiro. A equipe quer o carro rápido e simples, sem comprar peças de novo.
**Decisão:**
* na placa, só o que liga na ESP32 ou nos drivers: ESP32, 2 DRV8833 com 470 µF cada, pontos de solda dos motores, encoders, VBAT e largada, divisor da bateria e pull-downs do nSLEEP;
* fusível, chave e XT60 no chicote, numa plaquinha perfurada perto da bateria (com os clips de porta-fusível já comprados);
* ESP32 com o USB para a borda esquerda; a fileira de baixo (GPIO23…3V3) desce para os drivers e a de cima passa por baixo da ESP32 até o bloco dos encoders, junto com o 3V3;
* pinagem escolhida pelo traçado: motores 16/17 e 19/21, nSLEEP 4 e 18, encoders 32/33 e 25/26, bateria 36, largada 23;
* mesmas regras de corrosão manual da D-015 (trilha ≥ 1 mm, folga 0,5 mm, ilhas `_SoldaManual`, curvas de 45°).
**Consequências:** 80 × 67 mm e só 2 jumpers (IN1+IN3 de cada driver, embaixo do módulo; inevitáveis porque GND e VCC ficam entre os pares na fileira do módulo). DRC sem erros de cobre e paridade esquema × placa OK. O firmware mudou de pinos (`config.h`). Sobram CD4050B, 78L05, BC337, buzzer e KF2510 da lista da v0.4. Não fabricada.

### D-018 — Encoders em 3,3 V, direto na ESP32
*18/11/2026 · aceita*
**Contexto:** a D-011 previa 78L05 + CD4050B porque a única medida da RoboCore é com o encoder em 5 V. Encoders Hall de N20 do mesmo tipo são vendidos para 3,3–5 V (Waveshare, Olimex, Abra), com a saída no nível da alimentação; a placa do encoder da RoboCore tem 2 sensores Hall e 2 resistores (pull-ups).
**Decisão:** alimentar os encoders pelo 3V3 da DevKit (J12, J13) e ligar A/B direto nos GPIOs 32/33 e 25/26 (com INPUT_PULLUP).
**Consequências:** sai o conversor de nível e o 78L05 (menos peças e jumpers). Risco: o sensor não funcionar em 3,3 V. Teste T06 assim que os motores chegarem, **antes de corroer a placa**. Plano B: alimentar o encoder em 5 V (pino VIN da DevKit) e voltar ao CD4050B numa plaquinha perfurada entre o cabo e J12/J13.

### D-019 — Motores em 7,2 V
*18/11/2026 · aceita*
**Contexto:** o N20 é de 6 V, mas a RoboCore informa faixa de 3–9 V; a regra permite até 12 V; o DRV8833 aceita até 10,8 V. A rotação é proporcional à tensão.
**Decisão:** XL4016 #2 ajustado em 7,2 V (limite de corrente ~4 A), um DRV8833 em paralelo por motor.
**Consequências:** +20 % de velocidade (≈ 1,37 m/s em carga, estimado) e o limite diferencial na curva de R100 fica no mesmo nível do de aderência. Stall sobe para ≈ 1,9 A por motor, abaixo dos 2,4 A do DRV8833 em paralelo. Desgaste maior das escovas: levar motor reserva se sobrar saldo. `DUTY_MAX_PCT` continua 100 % (dá para limitar por software se esquentar).

### D-020 — Um GPIO de nSLEEP por driver, com pull-down de 10k
*18/11/2026 · aceita*
**Contexto:** na face simples, os pinos EEP dos dois módulos ficam em cantos opostos do traçado e ligar os dois no mesmo GPIO custaria um jumper. Alguns módulos DRV8833 trazem pull-up do EEP para o VCC (7,2 V), o que levaria tensão acima de 3,3 V ao GPIO com a ESP32 desligada ou no boot.
**Decisão:** EEP do driver esquerdo no GPIO4 e do direito no GPIO18, cada um com 10k para o GND; o firmware escreve os dois juntos.
**Consequências:** com um pull-up de 47k no módulo, o EEP fica em ≈ 1,3 V no boot (seguro para a ESP32, abaixo do nível alto de 2 V do DRV8833); com o jumper de solda EEP–VCC do módulo fechado, é preciso abri-lo (medir antes). O buzzer saiu da placa (`PIN_BUZZER = -1`).

### D-021 — Placa face simples "de verdade" no KiCad e 3D só nativo ou baixado
*18/11/2026 · aceita*
**Contexto:** a placa é de fenolite com cobre só embaixo, mas o projeto tinha os 2 jumpers desenhados como trilhas em F.Cu com 4 vias, as pegadas não estavam ligadas aos símbolos do esquemático e o 3D da ESP32 e do DRV8833 eram caixas desenhadas à mão. Uma revisão feita por outra IA apontou problemas parecidos (e outros que não procedem; ver [hardware/placa_esp32/README.md](../hardware/placa_esp32/README.md#revisão-de-1811-v051)).
**Decisão:**
* jumpers de fio viram componentes (símbolo nativo `Jumper:Jumper_2_Bridged`, pegada `Jumper_Fio_P8.86mm_SoldaManual`); o lado do IN3 ganha rede própria (`ME_IN2_JP`, `MD_IN2_JP`);
* regras no `placa_esp32.kicad_dru` proíbem trilha/zona em F.Cu e qualquer via (o KiCad exige 2 camadas no projeto);
* toda pegada ligada ao seu símbolo pelo UUID; furos de fixação "só na placa";
* modelos 3D: só nativos do KiCad ou baixados do fabricante. ESP32 = STEP de 30 pinos baixado pela equipe (a pegada de 38 pinos que veio junto não é usada); DRV8833 = só as barras fêmea nativas.
**Consequências:** cobre e furação iguais aos da v0.5 (a arte de transferência não muda). DRC 0 violações e paridade esquema × placa OK, conferidos por `make drc`; saídas refeitas por `make placa`. O STEP da placa ficou maior (~19 MB) por causa do modelo detalhado da ESP32.

### D-022 — Placa v0.6: 72,5 × 63 mm, furos nos cantos, GND da ESP32 por alívio térmico
*18/11/2026 · aceita*
**Contexto:** na v0.5 os pinos GND da ESP32 (14 e 29) só chegavam ao plano por tocos de trilha fora do centro, porque o plano não tinha espaço para formar 2 raios de alívio térmico. Os furos de fixação estavam em posições irregulares (dois deles longe dos cantos) e a placa tinha espaço sobrando.
**Decisão:** refazer posicionamento e roteamento mantendo as ligações: fileira de cima da ESP32 em y = 3,8 mm (faixa de plano por cima) e SLEEP_E 1 mm mais baixo (faixa de plano por baixo), raios a 0°/90° nos pinos 14 e 29; furos M3 nos 4 cantos a 3,5 mm das bordas; módulos, capacitores e fios aproximados até o limite das regras de corrosão manual da D-015.
**Consequências:** 72,5 × 63 mm (−15 % de área). DRC 0 violações sem tocos (mínimo de 2 raios conferido), paridade esquema × placa OK, só 0/45/90°. O H4 fica embaixo da ponta USB da ESP32: apertar os parafusos antes de encaixá-la. Chassi refeito com os furos novos (só o andar 1 muda). Coordenadas dos jumpers e da BOM mudaram.

### D-023 — Placa v0.7: USB da ESP32 para a frente do carro
*18/11/2026 · aceita*
**Contexto:** na v0.6 o USB da ESP32 apontava para a lateral esquerda, a ~6 mm da parede; o plugue só entrava passando pela janela da parede.
**Decisão:** girar o layout inteiro da v0.6 em 90° (sentido horário): a ESP32 fica em pé com o USB na borda de cima (frente do carro), placa de 63 × 72,5 mm; no chassi a frente da placa vai a x = 124 mm e a janela de USB das paredes sai. Girar o layout validado, em vez de rotear de novo, mantém o cobre que já passava em todas as verificações.
**Consequências:** fios dos motores chegam pela lateral esquerda da placa e encoders/VBAT pela traseira. A traseira da placa fica a 2,5 mm da bateria (medida estimada: conferir). Coordenadas da BOM e dos jumpers mudaram; furos do andar 1 mudaram (cortar de novo se já cortado).


### D-024 — Placa v0.8 espelhada: lado esquerdo = motor esquerdo, lado direito = motor direito
*19/11/2026 · aceita*
**Contexto:** a equipe vai pôr a bateria no meio do carro (peso entre as rodas) e a placa atrás, em cima do eixo. Na v0.7 os fios dos dois motores chegavam pela mesma lateral e os encoders pela traseira, cruzando o carro. Também foi pedido: ilhas maiores para soldar (sem mudar furo nem passo), trilhas ≥ 1 mm calculadas para a corrente, saída reta das ilhas, gotas (teardrops), ilhas cercadas pelo plano de GND e nenhuma curva de 90°.
**Decisão:**
* placa de **80 × 70 mm** (depois 80 × 73, ajuste da equipe) espelhada: ESP32 em pé no meio (USB para trás, antena para a frente com área sem cobre embaixo); U2, J10, J12, C1 e J2 à esquerda; U3, J11, J13, C2 e J3 à direita;
* **pinagem nova da ESP32** para cada coluna atender um lado: motor E 33/25, nSLEEP E 32, encoder E 26/27; motor D 19/21, nSLEEP D 18, encoder D 17/16; bateria 36; largada 4; LED 2 (`config.h` atualizado);
* encoders na ordem **A, B, −, +** (J12/J13); **3º jumper** (JP3, nSLEEP do U3); resistores de passo 7,62 mm, R2–R4 embaixo da ESP32;
* ilhas retangulares arredondadas, alongadas só no sentido que não aproxima o pino vizinho; sinal 1,0 mm (≈ 2,4 A) e potência 1,5 mm (≈ 3,2 A contra 1,9 A de pico; IPC-2221, 35 µm, +10 °C); curvas chanfradas a 45°; 62 gotas; alívio térmico com ≥ 2 raios;
* a placa é gerada por `ferramentas/montar_placa_v08.py` a partir do esquemático (tabelas de posição e de rotas).
**Consequências:** DRC 0 e paridade OK (`make drc`). 3 jumpers de fio (eram 2). R2, R3 e R4 têm de ser soldados antes das barras fêmea (ficam embaixo da ESP32) e ser de 1/4 W. O chassi (`mecanica/chassi/`) ainda está com a placa v0.7: refazer quando a posição da bateria e da placa estiver fechada (placa sobre o eixo com espaçadores de ~15 mm). Faltam comprar barras fêmea e fenolite ([LISTA_DE_SOLDAGEM.md](../hardware/placa_esp32/LISTA_DE_SOLDAGEM.md)).

### D-025 — GND dos drivers por trilha, não pelo plano
*19/11/2026 · aceita*
**Contexto:** no ajuste da equipe, o GND dos módulos DRV8833 foi ligado ao plano por um toco de trilha (o pino fica entre VCC e IN3 e não recebe 2 raios de alívio térmico). Medido no plano, o caminho do driver até o fio de GND e o 470 µF ficava com 0,4–0,5 mm de largura no trecho mais estreito.
**Decisão:** o GND de cada driver é uma trilha de 1,5 mm até o 470 µF e o fio de GND do XL4016, por fora do VM. O plano volta para folga de 0,6 mm, largura mínima de 1,0 mm e raios de 1,0 mm. Mantidos os outros ajustes da equipe (80 × 73 mm, Y do motor, resistores no meio da ESP32, J2 alinhado com o C1).
**Consequências:** a corrente do motor (até 1,9 A) volta direto ao fio sem passar pelo plano embaixo da ESP32. O trecho mais estreito do GND, do driver até o fio, ficou com 1,5 mm. DRC 0 e paridade OK. Esquemático com PWR_FLAG em VM_E, VM_D e GND e tudo na grade de 1,27 mm (ERC do KiCad 10 sem os 3 erros e os 98 avisos; rodar de novo para confirmar).

### D-026 — Chassi v3: Jetson baixa sobre a bateria, caixa traseira com tampo da ESP32 e quilha central
*25/11/2026 · aceita* (substitui o arranjo da v1 em `mecanica/chassi/`; o estudo v2.2 não está no repositório)
**Contexto:** a v1 ficou bamba (paredes paralelas sem travessa, sem parafuso embaixo, rasgo folgado), maior que o
necessário e com furos errados; a Jetson (141 g, a peça mais pesada) ia no 2º andar. Com apoio em 3 pontos, o carro
tomba em torno da linha roda–esfera: a ~46 mm de altura de CG, ele tombaria (0,97 g) antes de escorregar (μ ≈ 0,9)
numa curva de R100 feita rápido demais.
**Decisão:** ([mecanica/chassi_v3/](../mecanica/chassi_v3/))
* Jetson baixa (placa a 38 mm do chão), à frente do eixo, com os 100 mm no sentido do carro e as portas para a esquerda;
* bateria embaixo da Jetson, num túnel que sai pela frente, travada por um pino;
* caixa traseira fechada com os 2 XL4016 no chão (bornes para o eixo, trimpots reguláveis por cima através do tampo)
  e tampo removível com a placa da ESP32 sobre o eixo e a placa de desligar;
* quilha central (espinha de MDF em pé) ligando a caixa ao piso da frente; pisos sobrepostos (traseiro z 12–15,
  dianteiro z 15–18) que nivelam o carro com a esfera de 15 mm;
* fusível logo depois do XT60 (na frente) e chave na parede direita; o XT60 do chassi fica num pigtail curto (par solto).
**Alternativas comparadas** (mesmas peças e massas, `fonte/analise.py`): Jetson no andar de cima (CG 45,5 mm, tomba
com 0,97 g, 246 mm) e Jetson no piso com a bateria atravessada na frente (CG 33,1 mm, mas 252 mm > 250).
**Consequências:** 240 × 140 × 154 mm, 633 g estimados, CG a 36 mm, 86 % do peso nas rodas, tomba só com 1,11 g.
Empina acima de 0,47 g (D-030). 52 verificações automáticas e 28 testes negativos. Cortar o pente primeiro: 10
medidas estimadas ainda mudam o corte (`make chassi-cortar` barra até serem conferidas).

### D-027 — Rodas de 42 mm mantidas; bitola de 104 mm
*25/11/2026 · aceita*
**Contexto:** foi pedido rever a roda (velocidade, torque, vão livre, aderência, esfera, limite em curva).
**Decisão:** manter as 42 × 19 mm (já compradas) e a bitola de 104 mm.
**Por quê:** em R100 o limite é o pneu no tapete (~0,94 m/s com μ = 0,9), não o motor; a de 42 mm dá 1,98 m/s em vazio
e 19 N de partida (4× o que o pneu passa ao chão). A de 32 mm (StickyMAX) fica limitada pelo diferencial (0,96 m/s em
R100) e deixa a esfera de 15 mm 5 mm alta; a de 48 mm só ganha nas retas acima de ~1,6 m/s (hoje o controle roda a ~0,7 m/s)
e a de 65 mm passa a tombar antes de escorregar. Pneu mais aderente (μ > 1,0) também faria tombar antes de escorregar.
**Consequências:** nada a comprar. Se o T12 medir μ > 1,0, limitar a velocidade na curva por software (~0,9 m/s em R100).

### D-028 — Botão de desligar a Jetson no J41 e LED "pode desligar a chave"
*25/11/2026 · aceita*
**Contexto:** o desligamento pela largada segurada 3 s depende do `seguir_linha.py` e do USB da ESP32; nenhum LED
indica com certeza que a Jetson terminou (o LED verde da Jetson fica no 5 V; a ESP32 segue alimentada pelo USB).
Desligar a chave cedo demais corrompe o microSD.
**Decisão:** placa extra pequena ([hardware/placa_desligar/](../hardware/placa_desligar/)) no tampo: botão no J41 pino 18
(gpio15, pull-up externo) e LED vermelho por BC337 no pino 16 (gpio232). Serviço próprio `botao-desligar.service`
(root, sysfs): segurar 2 s → `poweroff`. O LED acende quando o Linux sobe e **nunca é apagado por software**: só apaga
quando o módulo corta a própria energia → "apagou = pode desligar a chave". Só arma depois de ver o botão solto 0,5 s
(fio em curto não desliga a Jetson no boot). A largada segurada 3 s continua como reserva.
**Descartadas:** header J50 (pinagem da B01 não confirmada; fica embaixo do módulo), botão extra na ESP32 (mudaria a
placa v0.8, que fica como está).
**Consequências:** 8 testes automáticos com GPIO falso; `make servico` instala os dois serviços. Falta o teste na Jetson (T15).

### D-029 — Temperatura: sem ventoinha por padrão; decidir pelo `tegrastats`
*25/11/2026 · aceita*
**Contexto:** dissipador passivo da Jetson aguenta 10 W a 25 °C; o pipeline atual gasta ~4 ms por quadro. XL4016 #1
perde ~1,4 W a 2 A.
**Decisão:** nada em cima do dissipador (25 mm livres, verificado); MAXN se o `tegrastats` ficar ≤ 70 °C em 15 min de
`make carro`; senão medir o modo 5 W e, só se não servir, ventoinha 4010 de 5 V no J15. Caixa dos XL4016 com entrada de
ar pela frente e saída pelas 2 janelas da parede traseira (as únicas aberturas "de ar" do chassi).
**Consequências:** teste T16. A ventoinha não exige mudar o chassi.

### D-030 — Limite de aceleração na Jetson (`controle.acel_max`)
*25/11/2026 · aceita*
**Contexto:** com o CG do v3 (x 16,8 mm à frente do eixo, z 36,1 mm) a esfera sai do chão acima de 0,47 g; a largada
pedia 0 → `v_max` num quadro (tração limitada a ~0,77 g).
**Decisão:** limitar só a **subida** da velocidade comum no controlador: `acel_max` = 2,0 por segundo (≈ 0,4 g com a roda
de 42 mm). Frear e virar continuam imediatos. A rampa do firmware (por roda) não foi mexida: apertá-la deixaria a
direção lenta.
**Consequências:** na largada, 0 → 0,35 leva 0,18 s. 2 testes novos; a simulação do firmware passa a conferir o PWM depois
da rampa. Se a pesagem mudar o CG, recalcular (`make chassi-verificar` mostra o "empina com").
