# 06 — Testes

Três níveis, do mais barato ao mais caro. **Não avance de nível com falha no anterior.**

## Nível 1 — Automático (PC ou Jetson, sem hardware)

```bash
make testes       # unittest: visão, controle, protocolo, link serial (porta falsa), configuração
make benchmark    # tempo por quadro: algoritmo atual x original, nesta máquina
```

Rode **antes de levar qualquer mudança ao carro**. As imagens sintéticas pegam erros de lógica, mas não substituem a câmera real.

Situação em 09/11/2026 [V]:
* 35 testes passando no PC (Python 3.11, OpenCV 5);
* compatibilidade com Python 3.6 conferida com `vermin`;
* integração Jetson ↔ "ESP32 simulada" por pseudo-terminal: pedido de versão, armar em PRONTO, 145 comandos recebidos armado e desarme ao sair;
* firmware: só checagem de sintaxe (cabeçalhos simulados dos cores 2.x e 3.x). **Falta compilar na Arduino IDE.**

## Nível 2 — Bancada e nível 3 — Pista

Baseado na aba PLANO TESTES da planilha da equipe, atualizado para a lista de componentes atual.
Em cada ensaio, medir tensão, corrente e temperatura. Não ligar o robô completo no primeiro dia.

| ID | Fase | Procedimento | Critério de aprovação | Segurança |
|---|---|---|---|---|
| T00 | Compra | Conferir estoque dos itens 01–20 e o frete no carrinho | Pedidos feitos; prazos anotados em `compras/README.md` | Não trocar modelo sem atualizar a planilha |
| T01 | Jetson | Fonte de bancada 5,1–5,2 V (≥ 4 A) → P4 → J25 com J48 fechado; `make testes` e `make visao` | Boot sem reinícios; câmera abre; anotar fps e tempo de processamento | Conferir a polaridade do P4 (centro +) |
| T02 | Bateria | Carga no B3 pelo conector de balanceamento | 12,3–12,6 V e células equilibradas | Fora do robô, no Lipo Sack, supervisionada |
| T03 | Conversores | Ajustar os XL4016 (5,2 V e 7,2 V) com carga resistiva | Tensões estáveis sob carga | **Sem** Jetson e sem motores ligados |
| T04 | Alimentação | Jetson pelo XL4016 #1 com visão rodando | ≥ 4,75 V no jack; plug P4 sem aquecer | Senão: pinos 5 V do J41 ([03](03_hardware.md)) |
| T05 | Motores | `make bancada`, PWM baixo, uma placa DRV8833 em paralelo por motor | Rodas giram no sentido certo (`INVERTER_*`); driver sem aquecer | **Rodas suspensas** |
| T06 | Encoders | **Assim que os motores chegarem, antes de corroer a placa:** ligar o + e o − do encoder (preto e azul) em 3,3 V da fonte de bancada (ou do pino 3V3 da DevKit) e medir A e B (amarelo e verde) girando a roda à mão; depois, na placa montada, medir os furos dos GPIO 32/33/25/26 no soquete | A e B alternam entre ~0 e ~3,3 V | Nada acima de 3,3 V em GPIO; se não funcionar em 3,3 V, ver o plano B da D-018 |
| T07 | Encoders | Girar a roda 10 voltas e ler `enc_e`/`enc_d` no log | Pulsos/volta medidos e sinal coerente com o sentido | — |
| T08 | Segurança | Matar o programa da Jetson com o robô armado (rodas suspensas) | Freia em < 250 ms; desarma em 1 s; LED apagado | — |
| T09 | Carga | 50 acelerações e frenagens com a visão rodando | Jetson sem reinício; 7,2 V estáveis; DRV8833 e motores sem esquentar demais | Medir consumo |
| T10 | Mecânica | Chassi montado | Dentro de 250 × 150 mm; nada raspa; centro de massa entre as rodas | — |
| T11 | Visão | Calibrar na pista de teste; variar a iluminação; comparar modos da câmera | ≥ 30 fps reais; linha estável; anotar a **latência medida** | — |
| T12 | Controle | Pista com R100, cruzamento de 90°, X e bifurcação, em velocidade crescente | Não perde a linha; anotar velocidade máxima e μ estimado | — |
| T13 | Box | Marca de box de teste e linha terminando no box | Para dentro do box em **100 %** das tentativas | — |
| T14 | Competição | 20 voltas seguidas sem intervenção | Zero reinícios e zero erros em cruzamento; anotar tempo médio e melhor volta | — |
| T15 | Desligar | Botão de desligar (placa extra, [roteiro](../hardware/placa_desligar/README.md#instalar-e-testar)): `--teste`, depois de verdade; aperto curto; ligar com o botão apertado; com o `robocar.service` parado | Segurar 2 s desliga; LED pisca, fica aceso e **apaga** quando terminou (anotar o tempo); `journalctl -b -1` limpo; aperto curto e botão preso no boot não desligam | Só desligar a chave depois que o LED apagar |
| T16 | Temperatura | `sudo tegrastats --interval 1000 --logfile ~/teg.log` em 15 min de `make carro` (rodas suspensas), MAXN; dedo/termômetro nos XL4016, DRV8833 e bateria depois | CPU/GPU ≤ 70 °C a ~25 °C; XL4016 ≤ 60 °C; bateria ≤ 40 °C ([D-029](decisoes.md)) | Se passar: medir o modo 5 W antes de pôr ventoinha |
| T17 | Massa e CG | Pesar XL4016 (cada), placa da ESP32 montada e as peças do pente; atualizar `mecanica/chassi_v3/fonte/pecas.py`; `make chassi-verificar` | Verificação de CG sem falha; anotar massa, CG, "tomba com" e "empina com" | — |
| T18 | Chassi v3 | Pente e gabaritos ([MONTAGEM.md](../mecanica/chassi_v3/MONTAGEM.md#3-ordem-de-montagem)); depois do corte: medidas, folgas, troca de bateria, trimpot e microSD com o carro montado; câmera de 25° a 65° | Peças reais encaixam nos gabaritos; ≤ 250 × 150 mm medido; troca de bateria < 20 s; nada encosta | `make chassi-cortar` sem erro antes de cortar a chapa |
| T19 | Luz e LEDs | Placa de interface ([roteiro](../hardware/placa_desligar/README.md#instalar-e-testar)); depois `make calibrar-auto` 4 vezes: luz da sala acesa/apagada × luz do robô acesa/apagada (`--sem-leds` não vale para o calibrar: tirar o fio do pino 15) | Luz acende antes da câmera e apaga ao sair; amarelo 1 Hz parado, 4 Hz andando, parado se o programa fecha; com a luz do robô, **contraste (branco − preto) ≥ 60 e varia < 15 entre sala acesa e apagada**; sem reflexo estourado na faixa de baixo da imagem | Medir a corrente da luz (≤ 0,5 A) |
| T20 | Energia | Placa de distribuição ([roteiro](../hardware/placa_distribuicao/README.md#fazer)): continuidade sem bateria; bateria com chave desligada e ligada | Ilhas isoladas entre si; LED verde só com a chave ligada; tensão da bateria nos 2 XL4016 só com a chave ligada; nada esquenta em 5 min com o robô andando (rodas suspensas) | Conferir a faixa do D1 no lado do SW+ antes de pôr a bateria |

**Medir a latência (T11):** com a câmera apontada para o LED da ESP32, enviar o comando que acende o LED e contar quantos quadros se passam até a imagem mostrar o LED aceso. Outra forma: filmar o robô e a tela juntos com um celular em câmera lenta.

## Registro de resultados

Preencha uma linha por ensaio. O arquivo de log/vídeo fica em `dados/`; cite o nome.

| Data | ID | Resultado | Medições | Arquivo em dados/ | Responsável |
|---|---|---|---|---|---|
| 09/11/2026 | Nível 1 | OK (35/35) | algoritmo 0,5–0,75 ms no PC | — | — |
| 21/11/2026 | T01 | OK | câmera 60 fps, 3,8 ms por quadro; Jetson ↔ ESP32 OK (`make bancada`) | `dados/logs/` | — |
| 21/11/2026 | T04 | OK pelo P4 | pelos pinos 5 V do J41 com fio jumper a Jetson desligava no boot; pelo plug P4 funcionou | — | — |
| 21/11/2026 | T05 | OK | as duas rodas giravam ao contrário: `INVERTER_E = true`, `INVERTER_D = false` | — | — |
| 21/11/2026 | Movimento (só ESP32) | OK | giro de 360° no chão: 60 % por 2,0 s | — | — |

| | | | | | |
