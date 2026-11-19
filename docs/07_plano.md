# 07 — Plano até a competição

Hoje: 09/11/2026. Inspeção e treino: **04/12** (sexta). Torneio: **05/12** (sábado). São ~25 dias úteis de trabalho.
Feriado em 20/11 (sexta); Black Friday em 27/11 (entregas mais lentas).

## 1. Ações imediatas

- [ ] **Inscrição:** o site indica prazo em 04/11. Se não foi feita, escrever hoje para robocar.race@gmail.com.
- [ ] **Fazer os 2 pedidos** ([compras/README.md](../compras/README.md)): RoboCore e Smart Kits (Sedex). Confirmar o frete da RoboCore no carrinho.
- [ ] Enviar as perguntas da [01_regulamento.md §4](01_regulamento.md).
- [ ] Confirmar o CEP (recebido como "0110300"; usado 01103-000).
- [ ] `git init` e primeiro commit ([CONTRIBUTING.md](../CONTRIBUTING.md)).

## 2. O que fazer já, sem esperar as compras

Dá para avançar bastante só com Jetson, câmera e ESP32:

1. **Jetson** (T01): JetPack 4.6.x, `sudo apt install python3-serial`, fonte de bancada no J25. Rodar `make testes` e `make benchmark` na Jetson e anotar os tempos.
2. **Câmera** (T11, parcial): `make visao` com fita preta sobre papel ou EVA claro.
   * Comparar 1280 × 720 @ 60 com 1640 × 1232 @ 30 (campo de visão).
   * Escolher altura e inclinação para enxergar a curva de raio 100 mm.
   * `make gravar` para criar vídeos de teste.
3. **Calibração:** `make calibrar`. Comparar exposição automática com exposição fixa (`exposicao_ns`).
4. **ESP32:** compilar e gravar o firmware ([firmware/README.md](../firmware/README.md)). Depois:
   * `make bancada PORTA=/dev/ttyUSB0` → conferir a telemetria;
   * botão no GPIO23 → LARGADA;
   * matar o programa → freia e desarma (T08, sem motores).
5. **Latência** (T11): medir agora; o número define a velocidade possível.
6. **CAD:** chassi e suporte de câmera com as dimensões de [03_hardware.md](03_hardware.md). Montar a **pista de teste**: R100, cruzamento de 90°, X, bifurcação e box.

## 3. Cronograma

| Semana | Mecânica / elétrica | Software / testes | Marco |
|---|---|---|---|
| 09–13/11 | Pedidos; CAD; pista de teste | Itens da seção 2 | Visão rodando na Jetson; link com a ESP32 OK |
| 16–20/11 | Recebimento; T02–T06; chassi v1 impresso | T07–T08; mapear PWM → velocidade (encoders) | Robô anda em reta comandado pela Jetson |
| 23–27/11 | Montagem completa; fixação ajustável da câmera | T09–T12 em baixa velocidade; ajuste de ganhos; T13 | **Volta completa autônoma na pista de teste** |
| 30/11–03/12 | Chassi v2 se preciso; peças reservas | Aumentar a velocidade aos poucos; T14; serviço de início automático; **congelar o código em 02/12** | 20 voltas seguidas sem falha |
| 04/12 | Inspeção | Calibrar na pista oficial; testar a parada no box | — |
| 05/12 | Torneio | — | — |

**Caminho crítico:** pedido → entrega → chassi → robô andando → ajuste na pista. O software anda em paralelo. Cada dia de atraso na entrega sai do tempo de ajuste.

## 4. Pendências

| Pendência | Quem resolve | Impacto |
|---|---|---|
| Frete real da RoboCore (simulação automática falhou) | equipe, no carrinho | orçamento |
| Respostas da organização (box, bifurcação, esfera, dimensões, rpm) | organização | parâmetros de parada/visão; projeto mecânico |
| Modelo exato da ESP32 | equipe | cabo USB, peso |
| Fio 18 AWG no laboratório | equipe | se houver, retirar os itens 19–20 da compra |
| Corrente máxima da fonte de bancada | equipe | ≥ 4 A para o modo 10 W |
| Compilar o firmware | equipe | ligação com o hardware |

## 5. Riscos principais

| Risco | Mitigação |
|---|---|
| Atraso na compra ou entrega | Pedir hoje, por Sedex; miudezas na Santa Ifigênia (perto do CEP) |
| Latência alta | Medir cedo; reduzir `v_max`; aumentar `k_frente`; plano B com sensores IR ([decisoes.md](decisoes.md) D-001) |
| Jetson desliga por queda de tensão | Teste T04; fio curto; J41 como alternativa |
| microSD corrompido | Desligar com `shutdown`; levar cópia do cartão |
| Marca do box diferente do previsto | Perguntar à organização; testar no treino de 04/12 |
| Motor N20 danificado | Saldo do orçamento permite 1 motor reserva após confirmar o carrinho |
