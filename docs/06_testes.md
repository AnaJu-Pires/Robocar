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

**Medir a latência (T11):** com a câmera apontada para o LED da ESP32, enviar o comando que acende o LED e contar quantos quadros se passam até a imagem mostrar o LED aceso. Outra forma: filmar o robô e a tela juntos com um celular em câmera lenta.

## Registro de resultados

Preencha uma linha por ensaio. O arquivo de log/vídeo fica em `dados/`; cite o nome.

| Data | ID | Resultado | Medições | Arquivo em dados/ | Responsável |
|---|---|---|---|---|---|
| 09/11/2026 | Nível 1 | OK (35/35) | algoritmo 0,5–0,75 ms no PC | — | — |
| | | | | | |
