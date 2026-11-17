# Robocar Blitz — placa da ESP32, v0.4 (face simples, corrosão caseira)

Placa-base do carrinho da RoboCar Race 2026 (categoria Micro), refeita para **corrosão manual**: um lado de cobre,
**trilha mínima de 1,0 mm**, folga mínima de 0,5 mm e ilhas grandes para soldar à mão. Mesmo circuito da v0.3
(bateria → fusível → chave → XL4016; dois DRV8833 em paralelo; encoders em 5 V com CD4050B; botão de largada e
buzzer), mesma ESP32 DevKit V1 de 30 pinos, só com peças PTH.

| v0.3 (anterior) | **v0.4 (esta)** |
|---|---|
| 130 × 105 mm | **103 × 95 mm** |
| trilha de sinal 0,7 mm | **1,0 mm** (motores 1,5 mm, bateria 2,5 mm) |
| ilhas da biblioteca padrão | **ilhas ampliadas**, mesmos furos e passos |
| 15 jumpers | **11 jumpers** (só 1 de cabinho) |

![Cobre visto de cima (azul = cobre, vermelho = jumper do lado dos componentes)](imagens/cobre_vista_de_cima.png)

## O que tem aqui

| Arquivo | Conteúdo |
|---|---|
| `placa_esp32.kicad_pro` / `.kicad_sch` / `.kicad_pcb` | Projeto KiCad (abrir no KiCad 10; ver "Como abrir") |
| `placa_esp32.pdf` | Esquemático em PDF |
| `fabricacao/1_cobre_transferencia_1x1.pdf` | **Arte do cobre**, 1:1, preto = cobre, com marca de centro nas ilhas |
| `fabricacao/2_montagem_e_jumpers.pdf` | Lado dos componentes: peças, referências e jumpers (vermelho) |
| `fabricacao/placa_esp32-PTH.drl`, `-NPTH.drl` e `*-drl_map.pdf` | Furação (Excellon) e mapa de brocas |
| `fabricacao/BOM.csv` | Lista de peças da placa |
| `imagens/` | Cobre visto de cima, lado do cobre (como fica na placa) e folha de montagem |
| `verificacao/` | Relatório do DRC, conferência esquema × placa, ângulos/larguras e lista dos jumpers |
| `lib/robocar_sm.pretty` | Pegadas `_SoldaManual` (ilha maior, furo e passo originais) |
| `lib/robocar.kicad_sym`, `lib/robocar.3dshapes` | Símbolos e 3D da ESP32 DevKit V1 e do DRV8833 (os mesmos da v0.3) |

## Ideia do desenho

Mesma lógica de arrumação do Projeto-PCB: **a energia entra por cima, a ESP32 fica à direita com o USB para fora da
borda de baixo, os motores ficam à esquerda e o CD4050 no meio, entre os encoders e a ESP32.**

| Faixa | O que tem | Regra |
|---|---|---|
| Borda de cima | Bateria (J1) → fusível (F1) → chave (SW1) → entradas dos dois XL4016 (J3, J2) | "Linha de montagem" da esquerda para a direita; a trilha da bateria é de 2,5 mm e fica reta |
| Canto de cima à direita | 78L05 (U3), divisor da bateria (R1, R2, C1), buzzer (BZ1, Q1, D1, R8, R9) | Cada peça perto de quem ela alimenta |
| Esquerda | Conectores dos motores na borda (J10 em cima, J11 embaixo), DRV8833 ao lado de cada um | Um "canal" por motor: conector → driver → ESP32, sem cruzar o outro motor |
| Entre os dois DRV8833 | C2 (do U4), C3 (do U5) e os fios da saída de 6 V (J4) | O capacitor fica colado no VCC/GND do seu driver |
| Meio, em cima | CD4050 (U2) e os pull-ups dos encoders (R4–R7) | Entradas de 5 V chegam pela esquerda, saídas de 3,3 V saem pela direita |
| Direita | ESP32 (U1), botão de largada (SW2) e R3 | A fileira esquerda da ESP32 atende motores e encoders; a direita, botão, buzzer, SLEEP e 3V3 |

**Como a face simples foi resolvida sem passar trilha entre pinos de 2,54 mm** (não cabe trilha de 1 mm):
* **Por baixo dos módulos.** A ESP32 e os DRV8833 ficam elevados nas barras fêmea, então o cobre entre as duas
  fileiras de cada um é usado como corredor: o SLEEP atravessa os dois DRV8833 por dentro; o 3V3 e o BUZZER sobem por
  dentro da ESP32; o +6V e o GND de cada driver saem por dentro do módulo até o capacitor dele.
* **Por dentro do soquete do CD4050.** As entradas do encoder do motor direito descem entre as fileiras do soquete e
  as saídas do encoder esquerdo saem por baixo dele, em três faixas de 1 mm.
* **Resistor como ponte.** O R1 (150k) passa por cima das trilhas de +5V e 3V3, e os pull-ups R4 e R6 passam por cima
  de outras linhas de encoder (como o R20/R22 no Projeto-PCB).
* **Encoder do motor direito pela borda.** As linhas A/B do J11 sobem pela borda esquerda, por fora de tudo.
* **Plano de GND** em todo o cobre livre (folga 0,6 mm, alívio térmico com raios de 1 mm). Onde o plano ficou
  fechado entre trilhas, um jumper de fio religa (JP5–JP11).

## Mudanças em relação à v0.3 (decisões)

1. **[D-015](../../docs/decisoes.md) — Placa refeita para corrosão manual (face simples, trilha ≥ 1 mm, ilhas grandes).** 103 × 95 mm,
   11 jumpers. O roteamento foi desenhado faixa por faixa (corredores por baixo dos módulos e do CD4050) para cortar
   jumpers, e conferido no DRC.
2. **[D-016](../../docs/decisoes.md) — Encoder esquerdo: GPIO32 ↔ GPIO33.** Na v0.4 o canal A do encoder esquerdo entra no **GPIO33** e o B no
   **GPIO32** (era o contrário). Com a ordem dos pinos do conector e do CD4050, essa troca evita um cruzamento (um
   jumper a mais). Não muda o comportamento, só a definição em `config.h` — **atualizar o firmware**:
   ```c
   const int PIN_ENC_E_A = 33;  // v0.4: era 32
   const int PIN_ENC_E_B = 32;  // v0.4: era 33
   ```
   Já aplicado em [config.h](../../firmware/robocar_esp32/config.h) e na tabela de
   [docs/03_hardware.md](../../docs/03_hardware.md#6-pinagem-da-esp32). Nenhum outro pino mudou.
3. **J2 (4 pontos) virou J2 + J4.** Os mesmos 4 fios do XL4016 #2, agora em dois lugares: a **entrada** (J2: VBAT e
   GND) fica na faixa de energia de cima e a **saída de 6 V** (J4: +6V e GND) fica entre os dois DRV8833, colada nos
   capacitores. Assim o +6V não precisa atravessar a placa.
4. **Pegadas `_SoldaManual`.** Ilhas maiores, **mesmo furo e mesmo passo** da peça (tabela abaixo). Não use
   "Atualizar pegadas a partir da biblioteca" com a biblioteca padrão: as ilhas voltariam ao tamanho original.
5. **TO-92 triangular** (78L05 e BC337): pernas das pontas a 5,08 mm e a do meio deslocada 2,54 mm, como no
   Projeto-PCB. As pernas do TO-92 abrem sem esforço para esse formato.
6. Ligações, valores e peças: **iguais à v0.3** (paridade conferida pino a pino, ver "Verificações").

## Regras usadas

| Item | Valor |
|---|---|
| Trilha de sinal (mínima) | **1,0 mm** |
| Motores (M+/M−), +6V e GND entre os módulos | 1,5 mm |
| Bateria (VBAT_IN, VBAT_FUS, VBAT_SW) | 2,5 mm (IPC-2221, 35 µm, +10 °C: ~4,3 A — o pico estimado do robô) |
| Folga cobre–cobre (trilha, ilha, via) | 0,5 mm |
| Folga do plano de GND | 0,6 mm; alívio térmico com raios de 1,0 mm; largura mínima do plano 1,0 mm |
| Cobre até a borda | 0,6 mm |
| Ângulos | só trechos a 0°, 45° e 90°; **nenhuma curva fechada** (toda curva é de 45°) e nenhum encontro agudo; 15 derivações em T a 90° |

**Ilhas (furo → ilha)** — o furo e o passo não mudaram:

| Peça | Furo | Ilha |
|---|---|---|
| Resistores, cerâmicos, 1N4148, eletrolíticos 470 µF | 0,8 mm | 2,4 mm |
| TO-92 (78L05, BC337) | 0,8 mm | 2,1 mm (triangular, ~3,6 mm entre pernas) |
| Soquete DIP-16 (CD4050) | 0,8 mm | 2,4 × 1,9 mm (oval) |
| Barras fêmea da ESP32 e dos DRV8833 | 1,0 mm | 2,6 × 1,9 mm (oval, quadrada no pino 1) |
| KF2510 dos motores | 1,19 mm | 1,9 × 3,0 mm |
| Clips do fusível / buzzer / botão | 1,05 / 1,0 / 1,1 mm | 3,0 / 3,0 / 2,8 mm |
| Pontos de solda dos fios 0,75 mm² | 1,55 mm | 3,6 mm |
| Furos dos jumpers | 0,8 mm (JP5: 1,2 mm) | 2,2 mm (JP5: 2,6 mm) |

**Polaridade:** ilha **quadrada = pino 1** (+ dos eletrolíticos e do buzzer, catodo do 1N4148, pino 1 do CD4050, pino
1 da ESP32 = EN, EEP dos DRV8833, M+ dos conectores dos motores, + da bateria em J1).

## Jumpers (11)

Cada jumper é um **fio do lado dos componentes**, soldado em dois furos. Coordenadas em mm a partir do **canto
superior esquerdo da placa, vista de cima** (a mesma vista da folha de montagem). No KiCad aparecem como trilha
vermelha (camada F.Cu).

| # | Rede | De | Até | Compr. | Para quê | Fio |
|---|---|---|---|---|---|---|
| JP1 | ME_IN2 | (32,3; 45,5) | (32,3; 54,4) | 9 mm | liga IN1+IN3 do DRV8833 esquerdo (por baixo do módulo) | rígido 0,5–0,6 mm |
| JP2 | MD_IN2 | (32,3; 80,5) | (32,3; 89,4) | 9 mm | o mesmo no DRV8833 direito | rígido |
| JP3 | +3V3 | (40,0; 21,3) | (53,0; 21,3) | 13 mm | alimentação do CD4050 | rígido, **isolado** |
| JP4 | +5V_ENC | (39,0; 17,7) | (53,0; 17,7) | 14 mm | 5 V dos encoders e pull-ups | rígido, **isolado** |
| JP5 | GND | (38,0; 65,0) | (38,0; 71,3) | 6 mm | retorno do DRV8833 esquerdo até o J4 | **cabinho 0,75 mm²** |
| JP6 | GND | (16,5; 21,0) | (16,5; 9,5) | 12 mm | GND do encoder esquerdo → GND da bateria | rígido |
| JP7 | GND | (41,0; 71,3) | (41,0; 47,0) | 24 mm | VSS do CD4050 → GND entre os módulos | rígido, **isolado** |
| JP8 | GND | (48,6; 44,6) | (41,0; 44,6) | 8 mm | entrada sem uso do CD4050 (pino 9) → VSS | rígido |
| JP9 | GND | (47,0; 72,8) | (47,0; 87,0) | 14 mm | GND entre os módulos → GND da ESP32 | rígido, **isolado** |
| JP10 | GND | (70,5; 33,5) | (70,5; 23,0) | 11 mm | GND de baixo da ESP32 → GND de cima | rígido |
| JP11 | GND | (22,4; 57,4) | (26,7; 57,4) | 4 mm | GND do encoder direito (J11) → GND entre os módulos | rígido |

JP1 e JP2 ficam entre as fileiras dos DRV8833 (o módulo encaixa por cima). Solde **todos os jumpers primeiro**,
antes de qualquer peça. A corrente dos motores volta pelo fio do J4 até o XL4016; o JP5 é de cabinho porque também
leva parte dessa corrente.

## Fabricação caseira (transferência térmica)

1. **Imprimir** `fabricacao/1_cobre_transferencia_1x1.pdf` em impressora **laser**, escala **100 %** (sem "ajustar
   à página"). A placa está no centro da folha A4. Conferir com régua: **103 × 95 mm**.
2. **Conferir a orientação.** Na folha, o texto "LADO DO COBRE v0.4" (embaixo, à direita) aparece **espelhado**.
   Depois de transferido ele fica **legível** olhando o lado do cobre (`imagens/lado_do_cobre.png` mostra como deve
   ficar). Se não ficar legível, a placa saiu espelhada.
3. **Transferir, corroer e limpar.** As marquinhas no centro das ilhas guiam a broca.
4. **Furar** (mapa: `placa_esp32-PTH-drl_map.pdf`):

| Broca | Onde |
|---|---|
| 0,8 mm | resistores, capacitores, 1N4148, TO-92, soquete DIP, furos dos jumpers (exceto JP5) |
| 1,0 mm | barras fêmea da ESP32 e dos DRV8833, buzzer, clips do fusível (1,05), KF2510 (o arquivo pede 1,19; os pinos são de 0,64 mm, 1,0 mm deixa mais cobre) |
| 1,1–1,2 mm | botão de largada; JP5 (cabinho) |
| 1,5–1,6 mm | pontos de solda dos fios de 0,75 mm² (J1, SW1, J2, J3, J4) |
| 3,2 mm | 4 furos de fixação M3 |

5. **Montar em ordem de altura:** jumpers → resistores → 1N4148 → cerâmicos → soquete DIP → TO-92 → botão → barras
   fêmea → KF2510 → eletrolíticos → clips do fusível → buzzer. Por último os fios de potência (bateria, chave, XL4016).
6. **Antes de encaixar a ESP32, os DRV8833 e o CD4050:**
   - procurar curto entre VBAT_SW, +6V_MOT, +5V_ENC, +3V3 e GND (multímetro em continuidade);
   - alimentar pela fonte de bancada com limite de corrente baixo;
   - medir **6,0 V** entre os pinos VCC e GND dos soquetes dos DRV8833 e **5 V** na saída do 78L05;
   - seguir o teste T06 de [docs/06_testes.md](../../docs/06_testes.md).

## O que falta comprar (fora da planilha de compras)

A planilha ([compras/robocar_compras_2026.xlsx](../../compras/)) já tem: DRV8833 ×3, XL4016 ×2, fusível 7 A e porta-fusível 5×20,
chave gangorra, 470 µF ×4, cabinho 0,75 mm², XT60. O laboratório tem os resistores 150k/33k/10k, multímetro, ferro de
solda e espaçadores M3. **Para esta placa ainda faltam:**

| Item | Qtd | Observação |
|---|---|---|
| CD4050B (DIP-16) | 1 (+1 reserva) | conversor 5 V → 3,3 V dos encoders |
| Soquete DIP-16 | 1 | |
| 78L05 (TO-92) | 1 | 5 V dos encoders |
| BC337 (TO-92) | 1 | aciona o buzzer |
| 1N4148 | 1 | |
| Buzzer **ativo** 5 V, 12 mm, PTH (passo 7,6 mm) | 1 | opcional; conferir se o do laboratório (item L14) é ativo |
| Chave táctil 6 × 6 mm, 4 terminais, PTH | 1 | botão de largada |
| Conector KF2510 6 vias: macho de placa 180° + fêmea + terminais de crimpar | 2 jogos | um por motor; ver "Medir antes" |
| Barra de pinos fêmea 1 × 15, 2,54 mm | 2 | ESP32 |
| Barra de pinos fêmea 1 × 6, 2,54 mm (ou 1 × 40 cortada) | 4 | dois DRV8833 |
| Resistores 1/4 W: 100k ×1, 1k ×1 | 2 | 150k, 33k e 10k ×5 o laboratório fornece |
| Capacitores cerâmicos: 100 nF ×3, 330 nF ×1 | 4 | |
| Placa de fenolite (ou fibra) **face simples**, mín. 110 × 100 mm | 1 (+1 para errar) | |
| Percloreto de ferro (ou persulfato de sódio), papel para transferência | 1 | se o laboratório não tiver |
| Brocas 0,8 / 1,0 / 1,2 / 1,5 / 3,2 mm | 1 de cada | se o laboratório não tiver |
| Fio rígido 0,5–0,6 mm (ex.: um pedaço de cabo de rede) | ~30 cm | jumpers |
| Termorretrátil fino ou espaguete | ~20 cm | isolar JP3, JP4, JP7 e JP9 |

Preços não cotados.

## Medir antes de fabricar

| Item | O que medir | Valor usado |
|---|---|---|
| ESP32 DevKit V1 | distância entre as fileiras (centro a centro) | 25,40 mm (desenho DOIT) |
| Módulo DRV8833 | distância entre as fileiras e a ordem dos pinos na serigrafia | 15,24 mm **estimado**; pino 1 = EEP |
| Módulo DRV8833 | continuidade EEP–VCC (jumper J2 do módulo) | tem de estar **aberto** (senão o GPIO18 recebe 6 V) |
| Clips do porta-fusível comprados | se cada clip tem 2 pernas a 5 mm e os clips ficam a 20 mm | Littelfuse 111 |
| Cabo do motor | conector da ponta e ordem 1 M+, 2 M−, 3 A, 4 B, 5 Vcc, 6 GND | KF2510 de 6 vias |
| 470 µF | diâmetro e passo | 8 mm, 3,5 mm |

Se algo mudar, edite a pegada em `lib/robocar_sm.pretty`, atualize a placa a partir do esquemático e refaça só as
trilhas daquela peça, rodando o DRC de novo.

## Verificações

| Verificação | Resultado |
|---|---|
| DRC (KiCad 7.0.11), todas as severidades | **0 erros de cobre, 0 ligações faltando**; sobram só 4 avisos "biblioteca MountingHole não configurada" (é a tabela de bibliotecas desta máquina; some no KiCad 10) — `verificacao/drc.rpt` |
| Esquema × placa (netlist exportada do esquemático pelo `kicad-cli`, comparada pino a pino com as ilhas) | **32 peças, 29 redes, 0 diferenças**, inclusive pegadas — `verificacao/paridade_esquema_placa.txt` |
| Ângulos e larguras (lidos do arquivo da placa) | 235 trechos, 0 fora de 0/45/90°, 0 curvas fechadas, 0 encontros agudos; trilha mais fina 1,00 mm — `verificacao/angulos_e_larguras.txt` |
| ERC do esquemático | **não rodado aqui** (o esquemático é do KiCad 10 e esta máquina só tem o KiCad 7). As mudanças no esquema são pequenas (J2/J4 e os rótulos do GPIO32/33); **rode o ERC no KiCad 10** antes de fabricar |
| Fabricada, montada ou testada | **não** |

## Como abrir

Abra `placa_esp32.kicad_pro` no **KiCad 10**. A placa foi gerada no formato do KiCad 7: o KiCad 10 abre e pede para
atualizar o arquivo ao salvar (pode aceitar). As tabelas `fp-lib-table` e `sym-lib-table` da pasta já apontam para
`lib/`. A v0.3 (130 × 105 mm, trilha de 0,7 mm, 15 jumpers) continua no histórico do git.

## Limitações e pendências

* Nada foi fabricado nem testado.
* O plano de GND tem trechos ligados só por jumper (JP6–JP11): se esquecer um, parte da placa fica sem GND. Depois
  de soldar, conferir continuidade de GND entre J1 (BAT−), J4 (6V−), o pino GND da ESP32 e o pino 8 do CD4050.
* As faixas por dentro do soquete do CD4050 têm 0,5 mm de folga para as ilhas (o mínimo da regra): capriche na
  transferência nessa região.
* Vista 3D não foi gerada aqui (o KiCad 7 de linha de comando não renderiza); o KiCad 10 mostra a placa em 3D com os
  modelos de `lib/robocar.3dshapes` e da biblioteca padrão.
