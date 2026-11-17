# 01 — Regulamento (categoria Micro)

Fonte: [referencias/regulamento_robocar_race_2026.pdf](referencias/regulamento_robocar_race_2026.pdf).
Em 09/11/2026 o caderno de regras ligado no [site oficial](https://www.robocarrace.com.br/) foi baixado e comparado com o PDF palavra por palavra: **o conteúdo é idêntico** [V].

## 1. Datas e local [V]

* Inspeção e treino: **04/12/2026 (sexta), 14h–22h**. Torneio: **05/12/2026 (sábado)**, a partir das 9h.
* Local: SENAC Santo Amaro, São Paulo (site oficial).
* Prazo de inscrição informado no site: **04/11/2026** (não consta no PDF).

## 2. Requisitos que afetam o projeto

| Requisito (§3.2 e regras gerais) | Consequência no projeto |
|---|---|
| Seguidor de linha; **câmera ou sensor óptico, com ou sem microcontrolador** | Jetson + câmera é permitido |
| Linha **preta de 20 mm** em **fundo claro** (tapete de borracha) | Detectamos pixels escuros. A Nano é o contrário (linha clara) |
| **Cruzamentos, bifurcações e interseções com ângulos ≠ 90°** | Visão por faixas que segue a linha prevista ([04_software.md](04_software.md)) |
| Curvas de **raio mínimo 100 mm**; pista até **20 m** | Limita a velocidade em curva ([03_hardware.md](03_hardware.md#5-velocidade-e-curvas)) |
| Chassi **mín. 50 × 60 mm / máx. 250 × 150 mm** | Projetar o robô **inteiro** dentro de 250 × 150 mm em planta |
| Pneu **Ø 20–113 mm**, **largura 11–45 mm** | Roda de 42 × 19 mm atende. A roda de 34 mm × 6,5 mm **não** atende |
| Motores **3–12 V CC** e **500–7.000 rpm** | N20 6 V 750 rpm em trilho regulado de 6 V. A 3S direta (12,6 V) ultrapassaria 12 V |
| **2 ou 4 rodas tracionadas** que tocam a pista | Tração diferencial em 2 rodas |
| Sensoriamento **100 % embarcado**; sem controle remoto nem computação externa | Wi‑Fi/SSH só em testes, nunca nas voltas oficiais |
| Largada dada por um membro da equipe; ninguém toca no robô | Botão de largada na ESP32 (GPIO23) |
| **Ao fim, entra no box e para sozinho, senão a volta é inválida** | Parada por linha perdida e por marca escura (configurável) |
| Duas tentativas; saiu da linha = volta perdida | Confiabilidade antes de velocidade |
| Classificação: maior distância; entre quem completa, menor tempo (§4.3) | Completar a volta é o primeiro objetivo |
| "Não serão aceitos robôs comprados"; inspeção no 1º dia | Montagem a partir de componentes; robô pronto em 04/12 |
| Boxes: 220 VAC sem terra | Levar extensão e régua (carregador e fonte) |

## 3. Divergências entre fontes

| Assunto | Fonte A | Fonte B | Como tratamos |
|---|---|---|---|
| Voltas | §1.1: "3 voltas cronometradas; vale a melhor" | §3.2.4: "duas tentativas para completar uma volta" | Planejamos para **2 tentativas** (o caso mais restritivo) |
| Classificação | §1.1/§4.7: menor tempo | §4.3: maior distância e, entre quem completa, menor tempo | São compatíveis: completar vem primeiro |
| Data da regra | Site: "última atualização em 18/06/2026" | Histórico do documento termina em 22/05/2026 | Conteúdo idêntico; sem impacto |
| [github.com/fdmartins/RoboCarRace](https://github.com/fdmartins/RoboCarRace) | Carro 1/8 (servo, ESC, ultrassom, Pico, Jetson) | Não trata da Micro | Referência geral apenas |
| [robocarrace.com.br/category/aprenda](https://www.robocarrace.com.br/category/aprenda/) | Artigos de OpenCV ("Zona de Visão"), ultrassom, ESC | Nada específico da Micro | Sem regras adicionais |

## 4. Perguntas para a organização (robocar.race@gmail.com)

Não presumimos as respostas. Cada uma afeta um parâmetro ou o projeto:

1. **Como o box/chegada é marcado?** A Figura 4 é "meramente ilustrativa" e mostra um losango preto. Afeta `parada.usar_marca` e `visao.marca_frac_escura`.
2. **Bifurcações:** qual ramo seguir, ou ambos levam ao mesmo ponto? Afeta `visao.preferencia_bifurcacao`.
3. **Esfera ou rodízio de apoio passivo** é aceito junto com as 2 rodas tracionadas?
4. **250 × 150 mm** vale para o chassi ou para o robô inteiro? Há limite de altura (mastro da câmera)?
5. **500–7.000 rpm** é medido no eixo de saída do motorredutor? O N20 de 750 rpm é especificado na saída.
6. (Se ainda não feito) Confirmação da **inscrição** da equipe.
