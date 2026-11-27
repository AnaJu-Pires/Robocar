# Inspeção de 04/12 — checklist do regulamento contra o chassi v4

Fonte: [docs/01_regulamento.md](../../docs/01_regulamento.md) (§3.2 Micro, §4). Marque na bancada antes de ir ao evento.
"Verificado no modelo" = a verificação automática (`make chassi`) confere; "medir" = conferir no carro montado.

| # | Regra (Micro) | Projeto v3 | Como provar na inspeção | Situação |
|---|---|---|---|---|
| 1 | Chassi máx. **250,0 × 150,0 mm** | **161,6 × 143,0 mm** com plugues, cabos e câmera em toda a faixa (verificado no modelo) | régua/trena no carro montado, **com** os plugues P4 e USB e a câmera | [ ] medir |
| 2 | Chassi mín. 50,0 × 60,0 mm | 159 × 121 mm só de MDF | a mesma medida do item 1 | ok |
| 3 | Pneu Ø 20,0–113,0 mm | 42 mm | paquímetro | [ ] medir |
| 4 | Largura do pneu 11,0–45,0 mm | 19 mm | paquímetro | [ ] medir |
| 5 | Motor 3–12 V CC | 7,2 V regulados pelo XL4016 #2 (a bateria 3S nunca chega ao motor) | multímetro no borne OUT do XL4016 #2 e em J2/J3 | [ ] medir |
| 6 | Rotação 500–7.000 rpm | N20 750 rpm (6 V); ~900 rpm em vazio a 7,2 V | anúncio/etiqueta do motor (RoboCore) | [ ] levar o link impresso |
| 7 | 2 ou 4 rodas **tracionadas** que tocam a pista | 2 rodas tracionadas + esfera de apoio (bitola 124 mm); carro nivelado, as 2 rodas tocam (verificado no modelo) | mostrar no chão | ok; ver pergunta 3 à organização (esfera) |
| 8 | Veículo elétrico | LiPo 3S 1100 mAh | mostrar a bateria e a chave geral | ok |
| 9 | Seguidor de linha com câmera ou sensor óptico | câmera IMX219-160 + Jetson | mostrar a câmera no mastro | ok |
| 10 | Sensoriamento 100 % embarcado; sem computação externa | tudo no carro | **Wi-Fi desligado** nas voltas (`nmcli radio wifi off` ou tirar o adaptador) | [ ] na volta oficial |
| 11 | Sem controle remoto | largada por botão no carro (J14) | mostrar o botão de largada; Wi-Fi desligado | ok |
| 12 | Partida dada por membro da equipe; ninguém toca no robô durante a volta | botão de largada no andar 3, por cima; o robô só anda depois de soltar o botão | treinar: apertar e soltar, mão longe | ok |
| 13 | Entra no box e **para sozinho** | parada por linha perdida e por marca (`parada.usar_marca`) | treino de 04/12 na pista oficial | [ ] calibrar a marca do box |
| 14 | Autonomia para a missão | ~30–45 min estimados com 1100 mAh | bateria carregada + 1 reserva carregada | [ ] carregar na véspera |
| 15 | "Não serão aceitos robôs comprados" | chassi projetado e cortado pela equipe; placa da ESP32 feita pela equipe | levar o repositório (DXF, STEP e imagens do projeto) | ok |
| 16 | Ajustes e pequenos consertos permitidos; **sem troca substancial** de componentes | reparos previstos: roda, motor (conector), fusível, bateria, tampo | não trocar Jetson/câmera/ESP32 por outra no torneio | ok |
| 17 | Robô pronto e funcionando na chamada geral | tudo montado e testado no treino de 04/12 | checklist abaixo | [ ] |

## Antes de sair para o evento

* [ ] `make chassi-verificar` sem falhas com as massas pesadas; `make testes` e `make sim-esp32` ok.
* [ ] Parafusos apertados: andar 2 (4), andar 3 (4), Jetson (4), XL4016 (8), esfera (2), suportes dos motores (4), câmera (porcas borboleta).
* [ ] **Velocidade na curva R100 ≤ 0,80 m/s** (D-032): o carro tomba antes de escorregar. Conferir no treino de 04/12 que a roda de dentro não levanta.
* [ ] Abraçadeiras no lugar; nenhum fio encosta na roda (girar à mão).
* [ ] Pino de trava da bateria + 1 reserva. Fusível 7 A reserva. 2 baterias carregadas, Lipo Sack, carregador.
* [ ] LED de desligar: acende ao ligar, apaga depois do botão. Largada segurada 3 s também desliga (reserva).
* [ ] Ângulo da câmera anotado (número gravado na orelha) e calibração salva.
* [ ] Extensão e régua de tomada (box sem pino terra), notebook com o repositório, cabo USB de gravação.
* [ ] Ferramentas: chave Philips pequena, chave de fenda fina (trimpots), alicate, multímetro, fita, abraçadeiras, cola.
