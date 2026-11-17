// =====================================================================================
// Robocar Blitz - configuracao do firmware da ESP32 (pinos e constantes)
// Fonte unica da pinagem: docs/03_hardware.md reproduz esta tabela.
// =====================================================================================
#pragma once

// ----- Protocolo (deve ser igual a jetson/robocar/protocolo.py: VERSAO) --------------
#define PROTOCOLO_VERSAO 1

// ----- Pinagem (ESP32 DevKit) -------------------------------------------------------
// Baseada na aba "PINAGEM ESP32" da planilha da equipe. Unica mudanca: GPIO14 -> GPIO13
// no driver direito, porque o GPIO14 emite PWM durante o boot e poderia mexer o motor.
// DRV8833 em modo paralelo: um modulo por motor (IN1+IN3 juntos, IN2+IN4 juntos).
// Na placa (hardware/placa_esp32) a ponte e ligada ESPELHADA: PIN_x_IN1 vai em IN2+IN4 do
// modulo e o M+ do motor sai de OUT2+OUT4. A tabela-verdade do DRV8833 e simetrica, entao o
// comportamento e identico (IN1=1/IN2=0 continua sendo "para frente" no conector).
const int PIN_ME_IN1 = 25;   // motor esquerdo: IN2+IN4 do modulo esquerdo (U4)
const int PIN_ME_IN2 = 26;   // motor esquerdo: IN1+IN3
const int PIN_MD_IN1 = 27;   // motor direito:  IN2+IN4 do modulo direito (U5)
const int PIN_MD_IN2 = 13;   // motor direito:  IN1+IN3
const int PIN_SLEEP  = 18;   // nSLEEP das duas placas (HIGH = ligado). Nunca ligar ao VM!
const int PIN_ENC_E_A = 32;  // encoder esquerdo (na placa, vem do CD4050B: 0/3,3 V push-pull)
const int PIN_ENC_E_B = 33;
const int PIN_ENC_D_A = 34;  // encoder direito: GPIO34/35 sao SO entrada e SEM pull-up interno;
const int PIN_ENC_D_B = 35;  //   o CD4050B da placa ja entrega 0/3,3 V. Nunca ligar o encoder (5 V) direto aqui
const int PIN_VBAT   = 36;   // ADC1: divisor 150k (topo) / 33k (baixo) + 100 nF ao GND
const int PIN_BOTAO  = 23;   // botao de largada para o GND (INPUT_PULLUP)
const int PIN_BUZZER = 4;    // opcional
const int PIN_LED    = 2;    // LED da placa

// ----- Motores ----------------------------------------------------------------------
const bool INVERTER_E = false;      // ajuste com as rodas suspensas (teste T05)
const bool INVERTER_D = true;       // motores espelhados: normalmente um e invertido
const uint32_t PWM_FREQ = 20000;    // 20 kHz: fora da faixa audivel
const uint8_t  PWM_BITS = 10;
const int      DUTY_MAX_PCT = 100;  // VM ja regulado em 6,0 V pelo XL4016
const int      RAMPA_POR_MS = 10;   // unidades (de 1000) por ms: 0 -> 100% em 100 ms

// ----- Seguranca --------------------------------------------------------------------
const uint32_t WATCHDOG_FREIO_MS   = 250;   // sem comando: freia (continua armado)
const uint32_t WATCHDOG_DESARME_MS = 1000;  // sem comando: desarma (exige novo botao)
const uint32_t TELEMETRIA_MS = 20;          // 50 Hz

// ----- Bateria 3S -------------------------------------------------------------------
const float DIVISOR_VBAT = (150.0f + 33.0f) / 33.0f;
const int   VBAT_AVISO_MV = 9900;           // 3,3 V/celula: buzzer
const int   VBAT_CORTE_MV = 9600;           // 3,2 V/celula por 2 s: FALHA_BATERIA
const int   VBAT_MINIMA_VALIDA_MV = 5000;   // abaixo disso: divisor desligado (bancada via USB)
