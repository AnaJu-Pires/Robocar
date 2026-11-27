# Chassi v4 — fiação e montagem

Os comprimentos vêm do modelo (`make chassi` refaz a tabela em [verificacao.md](verificacao.md)). **Corte = rota × 1,10
+ 20 mm** (descascar, terminal, termorretrátil). Números de 26/11/2026.

## 0. Furar (antes de montar)

No DXF/PDF os furos das peças compradas vêm **gravados**: círculo do tamanho do furo + cruz no centro (azul no PDF).
1. Ponha a peça (ou o gabarito cortado do pente) em cima da marca e confira que os furos dela caem nos círculos.
2. Se cair: fure no centro da cruz. Se não cair (medida estimada diferente da peça): marque pelo furo da peça e fure ali.
3. Brocas: M2 (câmera, suportes dos motores) **2,0 mm**; M2.5 (Jetson, esfera) **2,8 mm**; M3 **3,2–3,5 mm**. MDF:
   broca de madeira com ponta, parafusadeira na velocidade baixa, um pedaço de madeira embaixo para não lascar.
4. Os suportes dos motores tinham furo oblongo (ajuste do alinhamento): fure no centro da marca; se o eixo ficar torto,
   alargue o furo para o lado com a broca inclinada.

## 1. Energia

```
 ANDAR 1 (atrás)                          ANDAR 2: placa de distribuição (D-036)        ANDAR 1 (frente)        ANDAR 3
 bateria ─XT60 (em pé, à direita)─ pigtail ──passa-fio──► BAT+ ─[fusível 7 A]─ FUS+ ─┐
                                                          BAT− ── GND                 │ CHAVE 1
 chave (parede de trás do berço) ◄────────────── passa-fio da chave ──────────────────┘
   └───────────────────────────── passa-fio da chave ──► CHAVE 2 ── SW+ ─┬ alim_xl1 ── passa-fio XL ──► IN do XL4016 #1
                                                                          ├ alim_xl2 ── passa-fio XL ──► IN do XL4016 #2
                                                                          └ vbat (fino, Dupont no meio) ─ passa-fio do andar 3 ─► J1
 XL4016 #1 OUT 5,2 V ── xl1_p4_jetson ── passa-fio esquerdo do andar 2 ──► P4 da Jetson (portas para trás)
 XL4016 #2 OUT 7,2 V ─┬ vm_e ── passa-fio esquerdo do andar 2 ── passa-fio do andar 3 ──────────────────► J2
                      └ vm_d ── passa-fio direito do andar 2 ─── passa-fio do andar 3 ──────────────────► J3
```

## 2. Cabos

| Cabo | Bitola / tipo | De → para | Corte | Rota e apoio |
|---|---|---|---|---|
| pigtail_xt60_fusivel | 0,75 mm² vermelho + preto | XT60 do chassi → BAT+ / BAT− da placa de distribuição | **132 mm** | do XT60 (em pé na ponta direita da bateria) sobe pelo passa-fio de trás do andar 2 |
| fusivel_chave | 0,75 mm² vermelho | CHAVE 1 (FUS+) → terminal 1 da chave | **92 mm** | desce pelo passa-fio da chave (andar 2) |
| chave_placa | 0,75 mm² vermelho | terminal 2 da chave → CHAVE 2 (SW+) | **93 mm** | sobe pelo mesmo passa-fio |
| alim_xl1 | 0,75 mm² vermelho + preto | XL1 + / XL1 − → IN do XL4016 #1 (Jetson) | **151 mm** | desce pelo passa-fio novo na frente da placa e passa por cima dos motores |
| alim_xl2 | 0,75 mm² vermelho + preto | XL2 + / XL2 − → IN do XL4016 #2 (motores) | **145 mm** | idem; um par para cada conversor, sem jumper entre os bornes |
| xl1_p4_jetson | 0,75 mm² vermelho + preto | OUT do XL4016 #1 → P4 | **118 mm** | sobe pelo passa-fio esquerdo do andar 2 até o P4 (centro = +; conferir 5,2 V antes) |
| vm_e | 0,75 mm² vermelho + preto | OUT do XL4016 #2 → J2 | rota 178 (precisa ≥ **216**) | passa-fio esquerdo do andar 2 → passa-fio esquerdo do andar 3 |
| vm_d | 0,75 mm² vermelho + preto | OUT do XL4016 #2 → J3 | rota 124 (precisa ≥ **156**) | passa-fio direito do andar 2 → passa-fio direito do andar 3 |
| vbat | 0,2 mm² | terminal 2 da chave → J1 | **206 mm** | passa-fio da chave → passa-fio do VM esquerdo no andar 3 (sobe antes de passar por cima da placa); **Dupont de 1 via** no meio |
| motor_esq / _dir | cabo de 6 vias original | encoder → J12 + J10 / J13 + J11 | precisa ≥ 141 mm (assumi 150) | passa-fio atrás da Jetson (andar 2) → passa-fio do andar 3, **na frente da placa da ESP32** (junto dos conectores dos motores) |
| usb_jetson_esp32 | USB-A ↔ USB-C | ESP32 (andar 3, trás) → Jetson (andar 2, trás) | precisa ≥ 70 mm | cabo de 15–20 cm |
| j41_desligar | 8 Dupont fêmea-fêmea 15 cm | J41 15–20, 2 e 6 → J1 da placa de interface | precisa ≥ 101 mm | sobe pelo passa-fio da direita do andar 3, na frente da placa; ver [pinos do J1](../../hardware/placa_desligar/README.md#montagem-furo-a-furo) |
| ffc_camera | flat 15 vias | CSI → câmera | precisa de 135 mm a 65° (temos 150) | contorna a frente do andar 3; folga para girar a câmera |

Regras conferidas pela verificação: nada a menos de 3 mm de roda ou redutor; nenhum cabo atravessa MDF sem
passa-fio; nenhum trecho solto acima de 110 mm.

## 3. Ordem de montagem

**0. Antes do corte grande:** como no v3 ([MONTAGEM do v3](../chassi_v3/MONTAGEM.md#3-ordem-de-montagem), passo 0):
medir o MDF, cortar `corte/TESTE_cortar_primeiro.dxf`, escolher a folga no pente, conferir as peças nos gabaritos,
pesar e rodar `T=… FOLGA=… make chassi-cortar` até passar.

**1. Cortar e colar** (cola branca; montar a seco antes)
1. Cortar `corte/chapa_1.dxf` e `corte/chapa_2.dxf`.
2. Andar 1: piso traseiro + paredes do berço (trás, frente, esquerda); piso dianteiro + paredes da frente. Encaixar o
   piso dianteiro sobre o traseiro e pôr os 2 parafusos M3 dos pisos.
3. Pilares no andar 2 (cola; abas nos rasgos). **Não** colar o andar 2 nas paredes nem o andar 3 nos pilares.
4. Mastro: postes + travessa no andar 3 (cola). Câmera: placa da câmera entre as orelhas.

**2. Mecânica:** esfera (parafusos M2.5 por baixo, porcas em cima, entre os XL4016); motores nos suportes; rodas;
conferir o nivelamento.

**3. Energia no andar 1 — soldar e apertar antes de fechar o andar 2**
1. Ajustar o XL4016 #1 em 5,2 V e o #2 em 7,2 V na bancada, sem carga (T03).
2. Soldar: XT60 no pigtail; na [placa de distribuição](../../hardware/placa_distribuicao/README.md): pigtail, fios da chave, `alim_xl1`, `alim_xl2` e VBAT; fios na chave; P4 no `xl1_p4_jetson`; Dupont do VBAT.
3. XL4016 no piso dianteiro (espaçadores de 4 mm), **bornes para trás** (#1 à esquerda).
4. Chave na parede de trás do berço. `alim_xl1` no IN do #1 e `alim_xl2` no IN do #2 (descem pelo passa-fio na frente da
   placa de distribuição); `xl1_p4_jetson` no OUT do #1; `vm_e` e `vm_d` no OUT do #2 (os fios do VM vêm da placa da ESP32: deixe-os
   soltos para cima por enquanto).

**4. Andar 2**
1. Placa de distribuição atrás, em 2 espaçadores M3 de 10 mm (furos no andar 2). Jetson nos espaçadores de 5 mm, portas para trás.
2. Passar pelos passa-fios do andar 2: pigtail e fios da chave (atrás), pares dos XL4016 (passa-fio na frente da placa de distribuição), P4 e VM esquerdo (esquerda), VM direito
   (direita), cabos dos motores (atrás da Jetson).
3. Encaixar o andar 2 nas abas das paredes e fechar com 4 parafusos M3 (porcas presas).
4. P4 na Jetson; flat no CSI (Jetson desligada).

**5. Andar 3:** placa da ESP32 (espaçadores de 5 mm) e placa de interface (3 mm); cabos dos motores, VM e VBAT pelos
passa-fios; encaixar nos pilares e fechar com 4 M3; USB; Dupont do J41; câmera no mastro em 45°.

**6. Conferência (T10/T18):** `make chassi-verificar` com as massas pesadas; medir com régua (≤ 250 × 150);
girar as rodas e a câmera (25°–65°) à mão; trocar a bateria cronometrando; regular um trimpot e tirar o microSD
com o carro montado; ligar, ver o LED vermelho acender, `tegrastats`, desligar pelo botão e esperar o LED apagar.
