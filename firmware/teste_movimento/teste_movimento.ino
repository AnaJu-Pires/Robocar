/*
 * Robocar Blitz - TESTE DE MOVIMENTO (so a ESP32, sem a Jetson)
 * -------------------------------------------------------------
 * Aperte o botao de largada (J14): em 1 s o carro anda para a FRENTE, para, GIRA 360 graus no
 * lugar (para a direita), para e anda de RE. Apertar o botao durante o movimento PARA NA HORA.
 *
 * ATENCAO: este programa SUBSTITUI o firmware do robo. Depois do teste, grave de novo
 * firmware/robocar_esp32/robocar_esp32.ino, senao a Jetson nao consegue controlar o carro.
 *
 * Alimentacao: a ESP32 continua sendo alimentada pelo USB (Jetson ligada, carregador/power bank
 * de celular ou o PC). Os motores precisam da bateria ligada (XL4016 #2 em 7,2 V).
 * Monitor serial a 115200: mostra a bateria e os pulsos dos encoders de cada etapa.
 *
 * Primeiro teste com as RODAS NO AR. Depois, no chao, com pelo menos 1,5 m livre na frente e atras.
 */

#include <Arduino.h>
#include <stdarg.h>
#include "soc/soc.h"        // REG_READ (leitura direta dos GPIOs na interrupcao)
#include "soc/gpio_reg.h"

// ===================== AJUSTES DO TESTE (mude aqui) ===================================
const int      VEL_RETA        = 400;    // frente e re: 0..1000 (400 = 40 % de 7,2 V)
const uint32_t TEMPO_FRENTE_MS = 1500;
const uint32_t TEMPO_TRAS_MS   = 1500;
const int      VEL_GIRO        = 400;    // giro no lugar: roda esquerda para frente, direita para tras
const uint32_t TEMPO_GIRO_MS   = 900;    // tempo de UMA volta: ajustar no chao (girou pouco -> aumente)
const long     PULSOS_GIRO_360 = 0;      // > 0: gira pelos encoders (media das 2 rodas) em vez do tempo
const uint32_t PAUSA_MS        = 800;    // parado (freando) entre as etapas
const uint32_t ESPERA_MS       = 1000;   // do botao ate comecar a andar
const int      RAMPA_POR_MS    = 4;      // aceleracao: 0 -> 400 em 100 ms

// ===================== PINOS: COPIA de ../robocar_esp32/config.h (placa v0.8) =========
// Se mudar a pinagem ou o sentido dos motores la, mude aqui tambem.
const int PIN_ME_IN1 = 33;   // motor esquerdo (IN2+IN4 do U2)
const int PIN_ME_IN2 = 25;   // motor esquerdo (IN1+IN3 do U2)
const int PIN_MD_IN1 = 19;   // motor direito  (IN2+IN4 do U3)
const int PIN_MD_IN2 = 21;   // motor direito  (IN1+IN3 do U3)
const int PIN_SLEEP_E = 32;  // EEP (nSLEEP) do driver esquerdo; HIGH = ligado
const int PIN_SLEEP_D = 18;  // EEP (nSLEEP) do driver direito
const int PIN_ENC_E_A = 26, PIN_ENC_E_B = 27;
const int PIN_ENC_D_A = 17, PIN_ENC_D_B = 16;
const int PIN_VBAT  = 36;    // divisor 220k / 47k
const int PIN_BOTAO = 4;     // botao de largada para o GND
const int PIN_LED   = 2;
const bool INVERTER_E = false;
const bool INVERTER_D = true;
const uint32_t PWM_FREQ = 20000;
const uint8_t  PWM_BITS = 10;
const float DIVISOR_VBAT = (220.0f + 47.0f) / 47.0f;
const int VBAT_CORTE_MV = 9600;          // abaixo disso (com bateria detectada) nao anda
const int VBAT_MINIMA_VALIDA_MV = 5000;  // abaixo disso: fio VBAT solto ou bateria desligada

const int PWM_MAX = (1 << PWM_BITS) - 1;

// ------------------------------------------------------------------ PWM (core 2.x e 3.x)
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
static void pwmIniciar(int pino, int canal) { (void)canal; ledcAttach(pino, PWM_FREQ, PWM_BITS); }
static void pwmEscrever(int pino, int canal, int duty) { (void)canal; ledcWrite(pino, duty); }
#else
static void pwmIniciar(int pino, int canal) { ledcSetup(canal, PWM_FREQ, PWM_BITS); ledcAttachPin(pino, canal); }
static void pwmEscrever(int pino, int canal, int duty) { (void)pino; ledcWrite(canal, duty); }
#endif

// ------------------------------------------------------------------ encoders (quadratura x4)
static const DRAM_ATTR int8_t QDEC[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};
volatile int32_t encE = 0, encD = 0;
volatile uint8_t estE = 0, estD = 0;

static inline int IRAM_ATTR lerPino(int pino) {
  if (pino < 32) return (REG_READ(GPIO_IN_REG) >> pino) & 1;
  return (REG_READ(GPIO_IN1_REG) >> (pino - 32)) & 1;
}
void IRAM_ATTR isrEncE() {
  estE = ((estE << 2) | (lerPino(PIN_ENC_E_A) << 1) | lerPino(PIN_ENC_E_B)) & 0x0F;
  encE += QDEC[estE];
}
void IRAM_ATTR isrEncD() {
  estD = ((estD << 2) | (lerPino(PIN_ENC_D_A) << 1) | lerPino(PIN_ENC_D_B)) & 0x0F;
  encD += QDEC[estD];
}

// ------------------------------------------------------------------ utilidades
static void imprimir(const char* fmt, ...) {
  char buf[160];
  va_list args;
  va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args);
  va_end(args);
  Serial.print(buf);
}

static int lerBateria_mV() {
  return (int)(analogReadMilliVolts(PIN_VBAT) * DIVISOR_VBAT);
}

// Botao com debounce: retorna true uma vez a cada aperto.
static bool botaoApertou() {
  static int estavel = HIGH, ultimoLido = HIGH;
  static uint32_t tMudanca = 0;
  int lido = digitalRead(PIN_BOTAO);
  if (lido != ultimoLido) { ultimoLido = lido; tMudanca = millis(); }
  if (millis() - tMudanca > 40 && lido != estavel) {
    estavel = lido;
    if (estavel == LOW) return true;
  }
  return false;
}

// ------------------------------------------------------------------ motores
// Igual ao firmware do robo: DRV8833 em "slow decay"; valor 0 = freio; -1000..1000.
static void aplicarMotor(int in1, int ch1, int in2, int ch2, int valor, bool inverter) {
  if (inverter) valor = -valor;
  long duty = (long)abs(valor) * PWM_MAX / 1000L;
  if (valor > 0) {
    pwmEscrever(in1, ch1, PWM_MAX); pwmEscrever(in2, ch2, PWM_MAX - duty);
  } else if (valor < 0) {
    pwmEscrever(in1, ch1, PWM_MAX - duty); pwmEscrever(in2, ch2, PWM_MAX);
  } else {
    pwmEscrever(in1, ch1, PWM_MAX); pwmEscrever(in2, ch2, PWM_MAX);
  }
}

int atualE = 0, atualD = 0;   // velocidades aplicadas (depois da rampa)

static void escreverMotores() {
  aplicarMotor(PIN_ME_IN1, 0, PIN_ME_IN2, 1, atualE, INVERTER_E);
  aplicarMotor(PIN_MD_IN1, 2, PIN_MD_IN2, 3, atualD, INVERTER_D);
}

static int rampa(int atual, int alvo, int passo) {
  if (alvo > atual + passo) return atual + passo;
  if (alvo < atual - passo) return atual - passo;
  return alvo;
}

static void ligarDrivers(bool ligar) {
  digitalWrite(PIN_SLEEP_E, ligar ? HIGH : LOW);
  digitalWrite(PIN_SLEEP_D, ligar ? HIGH : LOW);
}

static void desligarTudo() {
  atualE = atualD = 0;
  escreverMotores();     // freio
  ligarDrivers(false);   // driver dorme: roda livre
  pwmEscrever(PIN_ME_IN1, 0, 0); pwmEscrever(PIN_ME_IN2, 1, 0);
  pwmEscrever(PIN_MD_IN1, 2, 0); pwmEscrever(PIN_MD_IN2, 3, 0);
}

// Leva os motores ate (alvoE, alvoD) com rampa e mantem ate acabar o tempo ou,
// se pulsos > 0, ate a media dos encoders andar 'pulsos' (com o tempo como limite de seguranca).
// Retorna false se o botao foi apertado (abortar).
static bool executar(int alvoE, int alvoD, uint32_t duracao_ms, long pulsos) {
  uint32_t t0 = millis(), tick = t0;
  int32_t e0 = encE, d0 = encD;
  while (true) {
    if (botaoApertou()) return false;
    uint32_t agora = millis();
    if (agora != tick) {
      int passo = RAMPA_POR_MS * (int)min(agora - tick, (uint32_t)50);
      tick = agora;
      atualE = rampa(atualE, alvoE, passo);
      atualD = rampa(atualD, alvoD, passo);
      escreverMotores();
    }
    if (pulsos > 0) {
      long feitos = (labs((long)(encE - e0)) + labs((long)(encD - d0))) / 2;
      if (feitos >= pulsos) return true;
    }
    if (agora - t0 >= duracao_ms) return true;
  }
}

// Uma etapa do teste: move e depois freia ate parar, mostrando os pulsos dos encoders.
static bool etapa(const char* nome, int alvoE, int alvoD, uint32_t duracao_ms, long pulsos) {
  int32_t e0 = encE, d0 = encD;
  uint32_t t0 = millis();
  imprimir("%-6s ... ", nome);
  bool ok = executar(alvoE, alvoD, duracao_ms, pulsos);
  uint32_t dt = millis() - t0;
  if (ok) ok = executar(0, 0, PAUSA_MS, 0);   // desacelera e fica freando
  imprimir("%lu ms | pulsos E=%ld D=%ld\n", (unsigned long)dt, (long)(encE - e0), (long)(encD - d0));
  return ok;
}

static void sequencia() {
  int vbat = lerBateria_mV();
  if (vbat >= VBAT_MINIMA_VALIDA_MV && vbat < VBAT_CORTE_MV) {
    imprimir("Bateria baixa (%d mV): carregue antes de testar. Nao vou andar.\n", vbat);
    return;
  }
  if (vbat < VBAT_MINIMA_VALIDA_MV)
    imprimir("AVISO: sem leitura da bateria (fio VBAT solto?). Os motores so andam com a bateria ligada.\n");
  else
    imprimir("Bateria: %.2f V\n", vbat / 1000.0f);

  imprimir("Largada em %lu ms (aperte o botao de novo para cancelar)\n", (unsigned long)ESPERA_MS);
  digitalWrite(PIN_LED, HIGH);
  uint32_t t0 = millis();
  while (millis() - t0 < ESPERA_MS) {
    if (botaoApertou()) { imprimir("Cancelado.\n"); digitalWrite(PIN_LED, LOW); return; }
  }

  encE = encD = 0;
  ligarDrivers(true);
  long pulsosGiro = PULSOS_GIRO_360 > 0 ? PULSOS_GIRO_360 : 0;
  uint32_t tempoGiro = PULSOS_GIRO_360 > 0 ? TEMPO_GIRO_MS * 3 : TEMPO_GIRO_MS;  // x3: so limite
  bool ok = etapa("FRENTE", VEL_RETA, VEL_RETA, TEMPO_FRENTE_MS, 0) &&
            etapa("GIRO", VEL_GIRO, -VEL_GIRO, tempoGiro, pulsosGiro) &&
            etapa("RE", -VEL_RETA, -VEL_RETA, TEMPO_TRAS_MS, 0);
  desligarTudo();
  digitalWrite(PIN_LED, LOW);
  imprimir(ok ? "Fim. Aperte o botao para repetir.\n" : "\nPARADO pelo botao. Aperte de novo para recomecar.\n");
  if (ok && PULSOS_GIRO_360 == 0)
    imprimir("Se o GIRO deu exatamente 1 volta, use PULSOS_GIRO_360 = media dos pulsos E e D do giro.\n");
}

// ------------------------------------------------------------------ setup / loop
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_SLEEP_E, OUTPUT); pinMode(PIN_SLEEP_D, OUTPUT);
  ligarDrivers(false);
  pinMode(PIN_BOTAO, INPUT_PULLUP);

  pwmIniciar(PIN_ME_IN1, 0); pwmIniciar(PIN_ME_IN2, 1);
  pwmIniciar(PIN_MD_IN1, 2); pwmIniciar(PIN_MD_IN2, 3);
  desligarTudo();

  pinMode(PIN_ENC_E_A, INPUT_PULLUP); pinMode(PIN_ENC_E_B, INPUT_PULLUP);
  pinMode(PIN_ENC_D_A, INPUT_PULLUP); pinMode(PIN_ENC_D_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_E_A), isrEncE, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_E_B), isrEncE, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_D_A), isrEncD, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_D_B), isrEncD, CHANGE);

  imprimir("\nRobocar Blitz - teste de movimento. Aperte o botao de largada.\n");
}

void loop() {
  // LED piscando devagar = esperando o botao
  digitalWrite(PIN_LED, (millis() / 500) % 2 ? HIGH : LOW);
  if (botaoApertou()) sequencia();
}
