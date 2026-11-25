# Chassi v3 — fiação e montagem

Os comprimentos vêm do modelo (`make chassi` refaz a tabela em [verificacao.md](verificacao.md)). **Corte = rota × 1,10
+ 20 mm** (descascar, terminal, termorretrátil). Números de 25/11/2026.

## 1. Esquema de energia (como fica no carro)

```
 FRENTE                                           │ meio (embaixo da Jetson, lado direito) │ TRÁS (caixa)
 bateria ─XT60 (par solto, na frente)─ pigtail ──► placa do fusível 7 A ──► chave (parede direita)
                                                                              │ (+ chaveado)      GND (da placa do fusível)
                                                                              ├──────────── chave_xl ────────────► IN+ / IN− do XL4016 #2 (direita)
                                                                              │                                     └─ jumper_in_xl (janela da quilha) ─► IN do XL4016 #1 (esquerda)
                                                                              └─ vbat (fio fino) ─ Dupont ─► J1 da placa da ESP32 (tampo)
 XL4016 #1 OUT (5,2 V) ──── xl1_p4_jetson (por cima do suporte esquerdo, ao longo da parede esquerda) ───► P4 da Jetson
 XL4016 #2 OUT (7,2 V) ──┬─ vm_e (janela da quilha, por cima do XL #1, passa-fio esquerdo do tampo) ───► J2 (VM esquerdo)
                         └─ vm_d (passa-fio direito do tampo) ──────────────────────────────────────────► J3 (VM direito)
```

## 2. Cabos

| Cabo | Bitola / tipo | De → para | Corte | Rota e apoio | Conector |
|---|---|---|---|---|---|
| pigtail_xt60_fusivel | 0,75 mm² vermelho + preto | XT60 do chassi → entrada da placa do fusível | **70 mm** | da frente, entre o trilho direito e o poste direito, por baixo da borda da Jetson; abraçadeira `ab_pigtail` no piso | XT60 soldado na ponta (termorretrátil); par solto na frente |
| fusivel_chave | 0,75 mm² vermelho | saída do fusível → terminal 1 da chave | **49 mm** | ao longo da parede direita | terminal da chave (solda ou faston) |
| chave_xl | 0,75 mm² vermelho + preto | terminal 2 da chave (+) e GND da placa do fusível (−) → IN+ / IN− do XL4016 #2 | **125 mm** | abraçadeira na parede direita (`ab_energia_parede`); por cima do suporte do motor direito (y = −36, 4 mm acima dele, 6 mm do pneu); desce até a abraçadeira do piso (`ab_energia_dir`) e entra nos bornes | borne |
| jumper_in_xl | 0,75 mm² vermelho + preto | IN do XL4016 #2 → IN do XL4016 #1 | **60 mm** | pela janela da quilha | borne (2 fios por borne: use terminal ilhós ou estanhe juntos) |
| xl1_p4_jetson | 0,75 mm² vermelho + preto | OUT+ / OUT− do XL4016 #1 (5,2 V) → plugue P4 | **225 mm** | abraçadeira `ab_p4_esq` no piso; por cima do suporte esquerdo (y = +36); ao longo da parede esquerda por dentro (abraçadeira `ab_p4_frente`); sobe e passa por cima da parede em x ≈ 100 até o P4 | P4 soldado (**centro = +**); conferir 5,2 V e polaridade antes de ligar na Jetson |
| vm_e | 0,75 mm² vermelho + preto | OUT do XL4016 #2 (7,2 V) → J2 | rota 136 mm (já soldado: precisa ter ≥ 170) | janela da quilha → por cima do XL #1, embaixo do tampo (3 mm de folga) → passa-fio esquerdo do tampo → J2 | borne no XL; solda na placa |
| vm_d | 0,75 mm² vermelho + preto | OUT do XL4016 #2 → J3 | rota 86 mm (já soldado: precisa ter ≥ 115) | sobe pelo passa-fio direito do tampo | idem |
| vbat | 0,2 mm² | terminal 2 da chave → J1 (VBAT) | **136 mm** | junto do feixe chave_xl até x = 16; sobe no vão entre o tampo e a Jetson (x ≈ 6); passa por cima da borda da frente do tampo até o J1 | **Dupont de 1 via no meio** (para o tampo sair) |
| motor_esq / motor_dir | cabo de 6 vias original | conector branco do encoder → J10 + J12 / J11 + J13 | rota 90 mm (precisa ter ≥ 100) | sobe no vão entre o tampo e a Jetson (x ≈ 3), passa pela borda da frente do tampo e vai pela borda da placa até os pontos | conector branco no motor (destacável); solda na placa |
| usb_jetson_esp32 | USB-A ↔ USB-C de dados | USB-C da ESP32 (traseira do tampo) → USB-A da Jetson (meio do lado esquerdo) | precisa de ≥ 200 mm (temos 300) | volta para cima na traseira, ao longo da borda esquerda do tampo (abraçadeira `ab_usb_tampo`), por cima da roda esquerda (≥ 10 mm acima do pneu) | plugues |
| j41_desligar | 4 jumpers Dupont fêmea 15 cm | J41 pinos 16, 17, 18, 20 → placa de desligar | precisa de ≥ 90 mm | da borda direita da Jetson para o tampo; abraçadeira `ab_j41_tampo` | Dupont (marcar cada fio) |
| ffc_camera | flat 15 vias | CSI da Jetson → câmera | precisa de 126 mm no pior ângulo (65°); temos 150 | sobe entre os postes, por trás das travessas; deixar a folga para girar a câmera | conectores CSI (**nunca** encaixar com a Jetson ligada) |

Regras (conferidas pela verificação de cabos):
* **Nada a menos de 3 mm da roda ou do redutor** (as engrenagens do N20 são abertas).
* **Nenhum trecho solto maior que 110 mm**: cada feixe passa por uma abraçadeira, um passa-fio ou a janela da quilha.
* **Alívio de tensão:** todo fio soldado tem abraçadeira ou passa-fio a menos de ~40 mm da solda; os fios do VM e
  dos motores ficam presos na borda do tampo antes de chegar à placa.
* Bitola: 0,75 mm² (≈ 18 AWG) aguenta ~10 A ao ar; o fusível de 7 A protege. Queda no P4 (2 A, 0,45 m ida e volta):
  ~0,02 V.

## 3. Ordem de montagem

**0. Antes de cortar a chapa grande**
1. Medir a espessura do MDF com paquímetro (3 pontos).
2. Cortar `corte/TESTE_cortar_primeiro.dxf`. No pente, escolher o rasgo em que a borda da chapa entra **justa, com
   pressão do dedo**. Folga = (rasgo escolhido) − T. Testar a porca presa (a porca M3 entra no bolso e o parafuso
   pega) e os furos M2/M2.5/M3/pino.
3. Pôr a Jetson, o XL4016 e a placa da ESP32 **em cima dos gabaritos**: cada parafuso tem de passar sem forçar. Pôr
   a gangorra no recorte da chave. Se algo não bater, corrigir em `fonte/pecas.py`.
4. Pesar todas as peças do teste juntas (densidade do MDF) e os XL4016.
5. `T=… FOLGA=… make chassi-cortar` até passar sem erro (ele barra enquanto houver medida estimada que muda o corte).

**1. Cortar e colar (cola branca, prendedores, 30–60 min)**
1. Cortar `corte/chapa_1.dxf`. Montar tudo a seco antes de colar.
2. Caixa traseira: piso traseiro + quilha + paredes laterais + parede traseira. **Não** colar o tampo.
3. Frente: piso dianteiro + 2 trilhos + batente + paredes da frente.
4. Mastro: 2 travessas entre os 2 postes; postes no piso dianteiro. Câmera: placa da câmera entre as 2 orelhas.
5. Encaixar o piso dianteiro sobre o traseiro (a frente da quilha encosta na borda dele), colar a sobreposição e
   pôr os 2 parafusos M3 dos pisos.

**2. Mecânica**
1. Escarear os 2 furos da esfera por cima (broca de 6 mm, à mão) e montar a esfera (parafusos de cabeça chata por cima).
2. Motores nos suportes brancos e suportes no piso traseiro (rasgos oblongos: alinhar o eixo e apertar). Rodas.
3. Conferir que o carro fica nivelado com a esfera (régua no piso dianteiro).

**3. Energia — o que soldar ANTES de fechar a caixa**
1. Na bancada, **sem carga**: ajustar o XL4016 #1 em 5,2 V e o #2 em 7,2 V (T03). Marcar "#1 JETSON" e "#2 MOTORES".
2. Soldar: XT60 no pigtail; pigtail e saída na placa do fusível; fios na chave; P4 no cabo `xl1_p4_jetson`;
   o Dupont de 1 via no meio do fio do VBAT. Termorretrátil em tudo.
3. Montar os XL4016 no piso traseiro (espaçadores de 4 mm, parafusos por baixo), **bornes para a frente** (#1 à esquerda).
4. Apertar nos bornes, nesta ordem, enquanto o tampo está fora:
   * `chave_xl` no IN do #2; `jumper_in_xl` do IN do #2 para o IN do #1, **pela janela da quilha**;
   * `xl1_p4_jetson` no OUT do #1;
   * `vm_e` (pela janela da quilha) e `vm_d` no OUT do #2 (2 fios por borne).
5. Placa do fusível no piso dianteiro (fita dupla face), lado direito, embaixo de onde fica a Jetson; chave na
   parede direita.
6. Abraçadeiras do piso (`ab_energia_dir`, `ab_p4_esq`, `ab_p4_frente`, `ab_pigtail`) e da parede direita.

**4. Tampo (fora do carro)**
1. Placa da ESP32 nos espaçadores de 5 mm; placa de desligar nos de 3 mm.
2. Passar `vm_e` e `vm_d` pelos passa-fios. Fechar o tampo: abas nos rasgos e 4 parafusos M3 nas porcas presas.
3. Ligar os conectores brancos dos motores, o Dupont do VBAT e o USB.

**5. Jetson e câmera**
1. Bateria no túnel (fios para a frente), pino de trava.
2. Espaçadores de 20 mm (os 2 de trás atravessam os dois pisos). Jetson por cima (portas para a esquerda), 4 parafusos.
3. Flat na Jetson e na câmera (**Jetson desligada**). Câmera na placa por trás (lente pelo furo; "CIMA ^" para cima).
   Orelhas nos postes: pivô M3 + trava com porca borboleta. Começar em 45°.
4. P4, USB e os 4 Dupont do J41.

**6. Conferência (T10)**
* `make chassi-verificar` com as massas pesadas.
* Medir comprimento e largura com régua, com os plugues e a câmera no lugar: ≤ 250 × 150 mm.
* Girar cada roda à mão: nada encosta. Girar a câmera de 25° a 65°: nada encosta.
* Trocar a bateria cronometrando (meta: < 20 s). Regular um trimpot e tirar o microSD com o carro montado.
* Ligar: LED vermelho acende (~20 s); `tegrastats` (§4 do README); desligar pelo botão; LED apaga; chave.
