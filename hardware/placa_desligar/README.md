# Botão de desligar a Jetson (sem placa) e luz da câmera no USB

Decisões: [D-028](../../docs/decisoes.md) (desligar com segurança), [D-040](../../docs/decisoes.md) (montagem final: só o
botão, sem placa e sem LED; luz no USB). A pasta continua com este nome para não quebrar os links.

## O que tem e para que serve

| Peça | Para que | Onde |
|---|---|---|
| **Botão de pulso de painel, 12 mm** (aperta e volta; **não** o de trava) | segurar **2 s** = a Jetson desliga sozinha, com segurança (fecha os arquivos do cartão) | furo de 12 mm no andar 3, lado direito, perto do J41 da Jetson; preso com a porca |
| Resistor de **10 kΩ** | mantém o pino 18 em "solto" (3,3 V) quando o botão não está apertado | soldado nos terminais do botão |
| Resistor de **1 kΩ** | protege o pino 18 da Jetson | em série no fio do pino 18, com termorretrátil |
| Fita LED COB 5 V | luz da câmera | placa da luz, em cima da câmera; **cabo USB direto numa porta da Jetson** |

O LED vermelho e o amarelo saíram (D-040). Para saber se o programa roda, o LED da placa da ESP32 já mostra: apagado =
sem Jetson; pisca devagar = pronto; aceso = armado.

## Ligação do botão (3 jumpers Dupont fêmea até o J41)

```
J41 pino 17 (3V3) ──── 10k ────┬──── terminal A do botão
J41 pino 18 ──── 1k ───────────┘
J41 pino 20 (GND) ────────────────── terminal B do botão
```

* Solde o 10k entre o fio do 3V3 e o terminal A; o 1k fica no meio do fio do pino 18. Termorretrátil em cada emenda.
* O botão é de pulso **NA** (normalmente aberto), 12 mm, de painel, tipo **PBS-33B** (rosca M12 com porca; cabeça de
  ~18 mm; lojas: "push button 12 mm sem trava"). Entra por cima do andar 3; a porca aperta por baixo. Qualquer cor;
  vermelho ajuda a não confundir com a largada.
* O furo de 12 mm vem **gravado** no andar 3 (não cortado): conferir o botão comprado e furar com broca de 12 mm (ou
  fura menor e alarga com estilete/lima).

## Como desligar

1. Segure o botão **2 s** (o serviço `botao-desligar` manda a Jetson desligar).
2. Espere a Jetson terminar:
   * se, depois de desligar, a **luz da câmera e o LED de energia da ESP32 apagam** (a porta USB da Jetson deixa de dar
     5 V): apagou = **pode desligar a chave**. Teste uma vez (T15) e anote;
   * se continuam acesos: espere o LED de estado da ESP32 apagar e conte **mais 30 s**.
3. Desligue a chave geral (o LED verde da placa de distribuição apaga).

Reserva, se o botão falhar: com o robô parado, segure o botão de **largada** da ESP32 por 3 s.

## Luz no USB

Corte o controle de toque fora e emende a fita direto no cabo USB dela (vermelho no +, preto no −). O controle regula
por PWM, e a câmera, que lê a imagem linha por linha, transforma isso em faixas claras e escuras. Ligada direto, a fita
recebe 5 V fixos: brilho constante, calibração estável. Ela acende com a Jetson. O cabo sobe por trás da câmera e fica
preso na travessa do mastro (~40 cm de cabo; a fita vem com mais).

## Instalar e testar

1. `make servico` na Jetson (instala o `botao-desligar.service`).
2. Teste sem desligar:
   ```bash
   sudo systemctl stop botao-desligar
   ```
   ```bash
   sudo python3 jetson/servico/botao_desligar.py --teste
   ```
   Aperte e solte: aparece `botao APERTADO` / `botao solto`. Segure 2 s: aparece `desligando (TESTE: nao desliga)`.
   Ctrl+C e depois `sudo systemctl start botao-desligar`.
3. Desligue de verdade (2 s) e veja o que apaga e quando (passo 2 de "Como desligar"); anote no T15.
4. Ligue de novo e confira que o desligamento foi limpo:
   ```bash
   journalctl -b -1 -n 30 --no-pager
   ```
   O fim deve mostrar `Reached target Power-Off` (ou `Shutdown`).

O código do LED vermelho (gpio232) e o de luz/amarelo (`jetson/robocar/leds.py`, gpio194/gpio16) continuam, sem efeito
sem nada ligado; servem se um dia voltarem a ter LEDs.
