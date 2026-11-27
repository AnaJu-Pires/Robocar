# 08 — Diário de engenharia (rodadas até a competição)

Uma entrada por rodada: hipótese → mudança → resultado → fonte. **FATO** = medido ou com fonte; **ESTIMATIVA** = conta ou
opinião. Os números de cada rodada saem de `make metricas` (log da corrida em `dados/logs/`).

Meta da competição (regulamento RoboCar Race 2026, §4.3 e §4.8): **completar a volta e parar no box** nas 2 tentativas
(§3.2.4); depois, menor tempo. Desempate: distância → menos erros → menor robô.

| Rodada | Data | Hipótese | Mudança | Resultado | Fonte |
|---|---|---|---|---|---|
| 1 | 27/11 | O gargalo é a confiabilidade da visão, não a velocidade: no teste de 22/11 a calibração tinha contraste de 40 níveis (branco 106, preto 66), 46 % dos quadros acusaram cruzamento falso e a linha sumia | Correções de software de 25/11 (razão do limiar limitada a 0,35–0,70, limiar suavizado, aviso de contraste < 60) + medidor `make metricas` + proposta de exposição fixa | **pendente**: sem volta completa registrada até hoje | FATO: log de 22/11 (CHANGELOG 25/11); regulamento §3.2.3–3.2.4 e §4.3 |
| 2 | 27/11 | Luz própria tira a dependência da iluminação do local e sobe o contraste (hoje 40 níveis) | Luz 5 V + IRLZ44N e LED amarelo na placa de interface (D-033); software pronto e testado com GPIO falso | **pendente**: comprar/montar a luz e rodar o T19 (contraste com e sem luz da sala) | FATO: log de 22/11; ESTIMATIVA: luz de ~1000–3000 lux na pista contra ~300–500 lux de sala |
