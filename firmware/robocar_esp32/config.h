// =====================================================================================
// Robocar Blitz - configuracao do firmware da ESP32 (pinos e constantes)
// Fonte unica da pinagem: docs/03_hardware.md reproduz esta tabela.
// =====================================================================================
#pragma once

// ----- Protocolo (deve ser igual a jetson/robocar/protocolo.py: VERSAO) --------------
#define PROTOCOLO_VERSAO 1

// ----- Pinagem (ESP32 DevKit) -------------------------------------------------------
// Placa v0.5 (hardware/placa_esp32, D-017): a pinagem saiu do traçado da placa de face simples,
// para nenhuma trilha cruzar. Pinos evitados: strapping (0, 2, 5, 12, 15), TX/RX (1, 3) e 14
// (PWM no boot). DRV8833 em modo paralelo, um modulo por motor (IN1+IN3 juntos, IN2+IN4 juntos).
// Ponte ESPELHADA (D-013): PIN_x_IN1 vai em IN2+IN4 do modulo e o M+ do motor sai de OUT2+OUT4.
// A tabela-verdade do DRV8833 e simetrica: IN1=1/IN2=0 continua sendo "M+ positivo".
const int PIN_ME_IN1 = 16;   // motor esquerdo: IN2+IN4 do modulo esquerdo (U2)
const int PIN_ME_IN2 = 17;   // motor esquerdo: IN1+IN3
const int PIN_MD_IN1 = 19;   // motor direito:  IN2+IN4 do modulo direito (U3)
const int PIN_MD_IN2 = 21;   // motor direito:  IN1+IN3
const int PIN_SLEEP_E = 4;   // EEP (nSLEEP) do modulo esquerdo; pull-down de 10k na placa. HIGH = ligado
const int PIN_SLEEP_D = 18;  // EEP (nSLEEP) do modulo direito;  pull-down de 10k na placa
const int PIN_ENC_E_A = 32;  // encoder esquerdo, alimentado em 3,3 V (D-018): saida 0/3,3 V direto no GPIO
const int PIN_ENC_E_B = 33;
const int PIN_ENC_D_A = 25;  // encoder direito, idem
const int PIN_ENC_D_B = 26;
const int PIN_VBAT   = 36;   // ADC1: divisor 150k (topo) / 33k (baixo)
const int PIN_BOTAO  = 23;   // largada: jumper (ou botao) para o GND, INPUT_PULLUP
const int PIN_BUZZER = -1;   // sem buzzer na placa v0.5 (-1 = desligado)
const int PIN_LED    = 2;    // LED da propria DevKit

// ----- Motores ----------------------------------------------------------------------
const bool INVERTER_E = false;      // ajuste com as rodas suspensas (teste T05)
const bool INVERTER_D = true;       // motores espelhados: normalmente um e invertido
const uint32_t PWM_FREQ = 20000;    // 20 kHz: fora da faixa audivel
const uint8_t  PWM_BITS = 10;
const int      DUTY_MAX_PCT = 100;  // VM regulado em 7,2 V pelo XL4016 #2 (D-019): 100% = 7,2 V no motor
const int      RAMPA_POR_MS = 10;   // unidades (de 1000) por ms: 0 -> 100% em 100 ms

// ----- Seguranca --------------------------------------------------------------------
const uint32_t WATCHDOG_FREIO_MS   = 250;   // sem comando: freia (continua armado)
const uint32_t WATCHDOG_DESARME_MS = 1000;  // sem comando: desarma (exige novo botao)
const uint32_t TELEMETRIA_MS = 20;          // 50 Hz

// ----- Bateria 3S -------------------------------------------------------------------
const float DIVISOR_VBAT = (150.0f + 33.0f) / 33.0f;
const int   VBAT_AVISO_MV = 9900;           // 3,3 V/celula: aviso na telemetria (e buzzer, se houver)
const int   VBAT_CORTE_MV = 9600;           // 3,2 V/celula por 2 s: FALHA_BATERIA
const int   VBAT_MINIMA_VALIDA_MV = 5000;   // abaixo disso: divisor desligado (bancada via USB)
