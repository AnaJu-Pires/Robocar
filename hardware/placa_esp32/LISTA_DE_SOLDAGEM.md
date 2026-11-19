# Lista de soldagem da placa da ESP32 (v0.8)

O que precisa para montar a placa, o que é cada coisa e se **já temos** (conferido com a lista de compras,
[compras/robocar_compras_2026.xlsx](../../compras/robocar_compras_2026.xlsx), aba Componentes).

Situação: **Temos** = já possuímos ou o laboratório tem · **Comprado** = está nos pedidos (RoboCore/Smart Kits) ·
**FALTA** = não está em nenhuma lista, precisa conseguir.

## 1. Peças que vão soldadas na placa

| Qtd | Peça | Ref. | O que é / para que serve | Situação |
|---|---|---|---|---|
| 1 | **ESP32 DevKit V1, 30 pinos** | U1 | O "cérebro" de baixo nível: recebe os comandos da Jetson pelo USB, gera o PWM dos motores, lê os encoders e a tensão da bateria. Não é soldada: **encaixa nas barras fêmea** (dá para trocar se queimar) | **Temos** (L03). Medir: fileiras a **25,4 mm** (1") entre centros, 15 pinos por lado |
| 2 | **Módulo DRV8833** (+1 reserva) | U2, U3 | Ponte H: transforma os sinais de 3,3 V da ESP32 em tensão/corrente para o motor (até 2,4 A com os 2 canais em paralelo). Um por motor. Também encaixa em barras fêmea | **Comprado** (item 02, 3 un.). Os pinos macho costumam vir **soltos**: soldar no módulo, virados para baixo |
| 2 | **Barra de pinos fêmea 1x15**, 2,54 mm, altura 8,5 mm | soquete do U1 | Soquete da ESP32 | **FALTA** |
| 4 | **Barra de pinos fêmea 1x6**, 2,54 mm | soquete do U2/U3 | Soquete dos módulos DRV8833 | **FALTA** |
| 2 | **Capacitor eletrolítico 470 µF 16 V** | C1, C2 | "Reservatório" de energia junto de cada driver: segura os picos de corrente do motor e evita que o VM caia/oscile. Tem polaridade (perna maior = +, faixa = −) | **Comprado** (item 17, 4 un.). Medir: pegada para **Ø 8 mm, pernas a 3,5 mm**. Se for Ø 10 mm / 5 mm, avisar (não cabe no lugar) |
| 1 | **Resistor 150 kΩ** 1/4 W | R1 | Parte de cima do divisor da bateria: 12,6 V → ≈ 2,3 V, que a ESP32 consegue ler | **Temos** (laboratório, L08) |
| 1 | **Resistor 33 kΩ** 1/4 W | R2 | Parte de baixo do divisor da bateria | **Temos** (L08) |
| 2 | **Resistor 10 kΩ** 1/4 W | R3, R4 | Pull-down do nSLEEP: mantém os drivers **desligados** enquanto a ESP32 está ligando (motor não dá tranco no boot) | **Temos** (L08 tem 10k) |
| 1 | **Barra de pinos macho 1x2** + **jumper** | J14 | Largada: com o jumper, o GPIO4 vai para o GND. Pode trocar por um botão em 2 fios | Jumper: **Temos** (sobra do pacote de 4 do item 13). Pinos macho: **sobra** da barra que vem com o DRV8833 |
| ~15 cm | **Fio rígido 0,5–0,6 mm** (perna cortada de resistor serve) | JP1, JP2, JP3 | "Pontes" no lado dos componentes, porque a placa só tem cobre embaixo e 3 ligações não cabem sem cruzar | **Temos** (pernas cortadas) |

Resistores de **1/4 W** (corpo ≈ 6,3 mm): cabem deitados no passo de 7,62 mm. Se forem de 1/2 W (corpo ≈ 9 mm),
montar o R1 em pé; R2, R3 e R4 ficam embaixo da ESP32 e **precisam ser de 1/4 W, deitados e encostados na placa**.

## 2. Fios soldados nos pontos da placa

| Qtd | Fio | Pontos | Para que serve | Situação |
|---|---|---|---|---|
| 2 pares | **Cabinho 0,75 mm² vermelho + preto** | J2, J3 | Leva os 7,2 V do XL4016 #2 até o VM de cada driver (corrente dos motores) | **Comprado** (itens 19 e 20, 2 m de cada) |
| 2 cabos | **Cabo de 6 vias do motor com encoder** | J10 + J12 (esq.), J11 + J13 (dir.) | 2 fios do motor (M+, M−) e 4 do encoder (A, B, −, +) | Vem com o motor (**Comprado**, item 01). Se vier só o conector, cortar e soldar os fios direto |
| 1 | **Fio fino** (qualquer, ~26 AWG) | J1 | + da bateria **depois da chave**, para a ESP32 medir a tensão | **Temos** (jumper fêmea-fêmea cortado, L12) |
| 1 | **Cabo USB de dados** | USB da ESP32 | Alimenta a ESP32 e liga ela à Jetson | **Temos** (L05) |
| — | **Tubo termorretrátil** | emendas | Isolar emendas dos fios | **Temos** (L10) |

## 3. Fixação

| Qtd | Item | Para que serve | Situação |
|---|---|---|---|
| 4 | Parafuso M3 + porca | Furos dos 4 cantos | **Temos** (L13) |
| 4 | **Espaçador M3 ≈ 15 mm** | Placa por cima do eixo/motores (bateria no meio, placa atrás) | **Temos** (L13; conferir se tem de 15 mm) |
| ~10 | **Abraçadeira de nylon pequena** (≈ 2,5 × 100 mm) | Alívio de tração dos fios: prender cada cabo no chassi a 2–3 cm da placa, deixando uma folga (barriga) no trecho até a solda | **Temos?** (L13 lista abraçadeiras; senão, pacote em loja de ferragens/elétrica ou na Santa Ifigênia) |

**Alívio de tração:** quem segura o puxão é a abraçadeira no chassi, não a solda. A placa não tem furo de alívio: os
fios grossos ficam perto das bordas e dos furos M3, e um furo a mais ali enfraqueceria o fenolite. Ao soldar, passe o
fio por cima (lado das peças) e deixe o isolamento encostar na placa. Uma gota de cola quente no isolamento, do lado
das peças (nunca na solda), ajuda nos fios finos do encoder.

## 4. Para fazer a placa (corrosão) e soldar

| Item | Para que serve | Situação |
|---|---|---|
| **Placa de fenolite cobreada face simples**, ≥ 80 × 73 mm (10 × 10 cm serve) | A placa em si | **FALTA** (a "placa perfurada" L11 é outra coisa) |
| Impressão **laser** da arte do cobre (`fabricacao/1_cobre_transferencia_1x1.pdf`, 100 %) em papel couché/fotográfico | Transferência térmica do desenho | **FALTA** (impressora laser e papel) |
| Ferro de passar, palha de aço/esponja, álcool isopropílico | Transferir e limpar o cobre | **FALTA** (verificar no laboratório) |
| **Percloreto de ferro** + vasilha plástica | Corroer o cobre que não é trilha | **FALTA** |
| Caneta permanente | Retocar trilha falhada antes de corroer | **FALTA** (verificar) |
| Brocas **0,8 / 1,0 / 1,5 / 3,2 mm** + micro retífica ou furadeira | Furos | **FALTA** (verificar no laboratório) |
| Ferro de solda, estanho, fluxo | Soldar | **Temos** (L07) |
| Multímetro | Testar continuidade, curto e tensões antes de ligar | **Temos** (L06) |

## Resumo: o que falta conseguir

1. **Barra fêmea 2,54 mm**: 2 barras de **1x40** cortáveis já dão 2 × 15 + 4 × 6 (cada corte perde 1 posição).
2. **Fenolite face simples** ≥ 80 × 73 mm.
3. **Percloreto de ferro**, impressão laser e brocas (se o laboratório não tiver).

## Ordem de montagem

1. Corroer, limpar e **conferir com o multímetro**: nenhuma trilha encostando em outra nem no plano de GND.
2. Furar (0,8 mm resistores/capacitores/jumpers, 1,0 mm barras e J12–J14, 1,5 mm fios grossos, 3,2 mm cantos).
3. **JP1, JP2, JP3** (fio rígido, do lado dos componentes).
4. **R2, R3, R4** (ficam **embaixo da ESP32**: depois das barras fêmea não dá mais acesso) e R1.
5. **Barras fêmea** (2 × 1x15 e 4 × 1x6). Dica: encaixar a ESP32/módulo nelas antes de soldar para ficarem retas.
6. **C1, C2** (atenção à polaridade: + na ilha marcada).
7. Pinos do J14 e os fios (J1, J2, J3, J10–J13).
8. **Sem a ESP32 e sem os módulos**: medir resistência entre +3V3, VM_E, VM_D e GND (nada em curto); ligar só o
   XL4016 #2 e medir 7,2 V entre VCC e GND de cada soquete dos DRV8833. Depois encaixar e seguir T05–T07 de
   [docs/06_testes.md](../../docs/06_testes.md).

## Medir antes de corroer

| Medida | Esperado pela pegada | Se não bater |
|---|---|---|
| ESP32: distância entre as 2 fileiras de pinos | 25,4 mm | avisar: muda a pegada |
| DRV8833: distância entre as 2 fileiras (6 pinos cada) | 15,24 mm | avisar: muda a pegada |
| DRV8833: ordem dos pinos, começando pelo canto do EEP | fileira 1: EEP, OUT1, OUT2, OUT3, OUT4, ULT; fileira 2 (em frente): IN4, IN3, GND, VCC, IN2, IN1 | avisar: muda o roteamento |
| 470 µF: diâmetro / distância entre pernas | 8 mm / 3,5 mm | 10 mm / 5 mm não cabe |
| Resistores: tamanho do corpo | ≤ 6,5 mm (1/4 W) | ver nota acima |
