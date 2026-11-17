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
*14/11/2026 · aceita*
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
*14/11/2026 · aceita*
**Contexto:** a equipe corrói a placa em casa, face simples, PTH. Em modo paralelo, as ilhas do DRV8833 alternam de rede, o que impede ligar tudo numa camada só.
**Decisão:**
* placa de 130 × 105 mm com cobre embaixo e plano de GND;
* trilhas de 2,5 mm (bateria), 1,5 mm (motores), 1,2 mm (GND) e 0,7 mm (sinais), com folga de 0,4–0,5 mm;
* 15 jumpers de fio do lado dos componentes;
* entrada sem uso do CD4050B no +3V3 em vez do GND, e 78L05/BC337 em TO-92 de pernas a 2,54 mm.
O roteamento foi automático e conferido pelo DRC do KiCad (com paridade com o esquemático).
**Consequências:** o DRC deu 0 violações, mas a placa não foi fabricada. Os jumpers do +6V_MOT usam cabinho de 0,75 mm². Uma revisão humana do traçado antes de corroer é recomendada.
