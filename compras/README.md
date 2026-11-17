# compras/

| Arquivo | Conteúdo |
|---|---|
| `robocar_compras_2026.xlsx` | Lista revisada, 3 cotações por item, pedidos por loja, fretes, orçamento e comparação de cenários |
| `original/` | CSV original da equipe, **sem alteração** (também copiado na aba "CSV original" da planilha) |

## Planilha: como usar

* **Abas:** Resumo · Componentes · Cotacoes · Pedidos · CSV original.
* **Cores por loja na aba Componentes:**
  * azul = RoboCore;
  * verde = Smart Kits;
  * rosa = compra particular;
  * cinza = já possuímos;
  * verde-água = laboratório;
  * riscado = removido.
* **Editar só as células em azul:**
  * aba Componentes: Qtd, Situação, Pagador, Prioridade e "Cotação escolhida" (1, 2 ou 3);
  * aba Cotacoes: preços;
  * aba Pedidos: fretes.
* Trocar a cotação muda sozinho a loja, o preço, o link, a cor, os pedidos e os totais.
* Fórmulas validadas em 09/11/2026: 2.926 células, nenhum erro.

## Recomendação (cotações de 09/11/2026, CEP 01103-000 — confirmar o CEP)

| Pedido | Itens | Subtotal | Frete | Total |
|---|---|---|---|---|
| **RoboCore** | motores ×2, bateria 3S 1100, esfera, Lipo Sack, jumper J48, espaçador M2.5 | R$ 388,97 | R$ 29,99 *estimado* | R$ 418,96 |
| **Smart Kits** (Sedex) | DRV8833 ×3, XL4016 ×2, rodas ×4, carregador B3, XT60 ×2, plug P4 ×3, suporte N20 ×2, fusíveis e porta-fusível, chave, capacitores ×4, cabinho 0,75 mm² 2 m vermelho + 2 m preto | R$ 220,30 | R$ 54,76 *simulado* | R$ 275,06 |
| **Total institucional** | | **R$ 609,27** | **R$ 84,75** | **R$ 694,02** |
| **Saldo de R$ 800** | | | | **R$ 105,98** |

Sobre os fretes:
* **Smart Kits:** simulado no site para o CEP 01103-000. Sedex 1 dia útil: R$ 48,54–49,78 por item isolado; R$ 54,76 com peso maior que o do pedido (valor usado). PAC: R$ 25,40–31,64 em 6 dias úteis. O frete grátis só vale acima de R$ 300 na capital de SP, e a loja escolhe a transportadora.
* **RoboCore:** a simulação automática do carrinho não respondeu. Vale o valor do CSV original até confirmar no carrinho. A loja fica em Santana de Parnaíba-SP.

Outros cenários (aba Resumo):
* **Menor preço item a item:** R$ 692,97 (R$ 1,05 a menos), mas com 3 pedidos e bateria 52 g mais pesada.
* **Sem agrupar** (cada item num pedido): R$ 1.501,09.
* **Lista P0 original:** R$ 1.045,36.

Mudanças em relação ao CSV, com justificativas na coluna "Decisão" e em [docs/decisoes.md](../docs/decisoes.md):
* saem o UBEC Hobbywing (esgotado), a fonte 5 V (o laboratório tem fonte de bancada) e o alarme LiPo (a ESP32 monitora a bateria);
* trocam de modelo ou de loja: bateria, carregador, rodas, suportes e XT60;
* entram plug P4, cabinho 0,75 mm² e peças reservas.

Nota fiscal: pode ser no nome/CPF de um integrante (não precisa ser no CNPJ da faculdade).

**Se sobrar saldo** após confirmar os carrinhos (> R$ 70): 1 motor N20 reserva (item 01, mesmo pedido RoboCore).

## Situação dos pedidos

| Loja | Data do pedido | Nº do pedido | Frete pago | Previsão | Recebido |
|---|---|---|---|---|---|
| RoboCore | | | | | |
| Smart Kits | | | | | |
