/*
 * Robocar Blitz - firmware da ESP32 (controladora escrava)
 * --------------------------------------------------------
 * A Jetson decide a direcao (camera); a ESP32 aplica o PWM com rampa, conta os encoders,
 * mede a bateria, cuida da largada e da seguranca. Pinos e constantes: config.h.
 * Protocolo: docs/05_protocolo_serial.md (comandos M, S, A, V; respostas T e I).
 *
 * ESTADO: validado em simulacao no PC (firmware/simulacao: 20 verificacoes com o codigo real da Jetson);
 * ainda nao gravado numa ESP32 real. Teste por etapas (docs/06_testes.md).
 * Placa: "ESP32 Dev Module" (Arduino-ESP32 core 2.x ou 3.x). Serial USB a 115200 baud.
 *
 * Maquina de estados:
 *   SEM_JETSON --(comando $M valido)--> PRONTO --(botao: apertar e soltar, ou $A)--> ARMADO
 *   ARMADO --(botao: ao apertar, ou $S)--> PRONTO
 *   PRONTO/SEM_JETSON --(botao segurado BOTAO_DESLIGAR_MS)--> flag DESLIGAR (a Jetson faz shutdown)
 *     -> a Jetson some (SEM_JETSON) -> ESPERA_DESLIGAR_MS -> LED 2 piscadas/s = "pode desligar a chave"
 *     (a Jetson voltou a mandar comandos, ou nao parou em DESLIGAR_SEM_RESPOSTA_MS: cancela)
 *   ARMADO --(sem comando > 250 ms)--> freia (flag WATCHDOG) --(> 1000 ms)--> SEM_JETSON
 *   qualquer --(bateria < corte por 2 s)--> FALHA_BATERIA (trava ate reiniciar a placa)
 * Motores so recebem PWM em ARMADO; nos demais estados o driver dorme (nSLEEP baixo).
 */

#include <Arduino.h>
#include "soc/soc.h"        // REG_READ (leitura direta dos GPIOs na interrupcao)
#include "soc/gpio_reg.h"
#include "config.h"

enum Estado { SEM_JETSON = 0, PRONTO = 1, ARMADO = 2, FALHA_BATERIA = 3 };
const int FLAG_WATCHDOG = 1;
const int FLAG_BATERIA_BAIXA = 2;
const int FLAG_DESLIGAR = 4;
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

// ------------------------------------------------------------------ estado global
Estado estado = SEM_JETSON;
int flags = 0;
int alvoE = 0, alvoD = 0;     // -1000..1000 vindos da Jetson
int atualE = 0, atualD = 0;   // apos a rampa
uint32_t ultimoComando = 0, ultimaTelemetria = 0, ultimoTick = 0, inicioVbatBaixa = 0;
uint32_t pedidoDesligar = 0;  // millis() do pedido de desligar (0 = nenhum)
uint32_t jetsonSumiu = 0;     // millis() em que a Jetson parou de mandar comandos depois do pedido (0 = ainda nao)
bool recebeuComando = false;
int vbat_mV = 0;

// ------------------------------------------------------------------ motores
// DRV8833 em "slow decay": frente = IN1 alto e IN2 com PWM invertido (alto = freio).
static void aplicarMotor(int in1, int ch1, int in2, int ch2, int valor, bool inverter) {
  if (inverter) valor = -valor;
  long duty = (long)abs(valor) * PWM_MAX / 1000L * DUTY_MAX_PCT / 100L;
  if (estado != ARMADO) {               // roda livre
    pwmEscrever(in1, ch1, 0); pwmEscrever(in2, ch2, 0);
  } else if (valor > 0) {
    pwmEscrever(in1, ch1, PWM_MAX); pwmEscrever(in2, ch2, PWM_MAX - duty);
  } else if (valor < 0) {
    pwmEscrever(in1, ch1, PWM_MAX - duty); pwmEscrever(in2, ch2, PWM_MAX);
  } else {                              // armado e zero: freio
    pwmEscrever(in1, ch1, PWM_MAX); pwmEscrever(in2, ch2, PWM_MAX);
  }
}

static int rampa(int atual, int alvo, int passo) {
  if (alvo > atual + passo) return atual + passo;
  if (alvo < atual - passo) return atual - passo;
  return alvo;
}

static void escreverSleep(int nivel) {   // EEP (nSLEEP) dos dois DRV8833
  digitalWrite(PIN_SLEEP_E, nivel);
  digitalWrite(PIN_SLEEP_D, nivel);
}

static void mudarEstado(Estado novo) {
  if (novo == estado) return;
  estado = novo;
  alvoE = alvoD = atualE = atualD = 0;
  escreverSleep(novo == ARMADO ? HIGH : LOW);
}

static bool linkRecente(uint32_t limite_ms) {
  return recebeuComando && (millis() - ultimoComando) < limite_ms;
}

static void pedirArmar() {          // so arma com a Jetson enviando comandos
  if (estado == PRONTO && linkRecente(WATCHDOG_FREIO_MS)) mudarEstado(ARMADO);
}

static void pedirDesarmar() {
  if (estado == ARMADO) mudarEstado(PRONTO);
}

// ------------------------------------------------------------------ protocolo
static uint8_t checksum(const char* ini, const char* fim) {
  uint8_t c = 0;
  for (const char* p = ini; p < fim; p++) c ^= (uint8_t)*p;
  return c;
}

static void enviar(const char* corpo) {
  char saida[96];
  snprintf(saida, sizeof(saida), "$%s*%02X\n", corpo, checksum(corpo, corpo + strlen(corpo)));
  Serial.print(saida);
}

static void enviarVersao() {
  char msg[40];
  snprintf(msg, sizeof(msg), "I,robocar_esp32,v%d", PROTOCOLO_VERSAO);
  enviar(msg);
}

static void tratarLinha(char* linha) {          // linha comeca com '$'
  char* asterisco = strrchr(linha, '*');
  if (!asterisco || asterisco - linha < 2) return;
  unsigned int chk = 0;
  if (sscanf(asterisco + 1, "%2x", &chk) != 1) return;
  if (chk != checksum(linha + 1, asterisco)) return;
  *asterisco = '\0';
  char* corpo = linha + 1;

  if (corpo[0] == 'M') {
    long seq; int e, d;
    if (sscanf(corpo, "M,%ld,%d,%d", &seq, &e, &d) == 3) {
      alvoE = constrain(e, -1000, 1000);
      alvoD = constrain(d, -1000, 1000);
      ultimoComando = millis();
      recebeuComando = true;
      if (estado == SEM_JETSON) mudarEstado(PRONTO);
    }
  } else if (corpo[0] == 'S') {
    pedirDesarmar();
  } else if (corpo[0] == 'A') {
    pedirArmar();
  } else if (corpo[0] == 'V') {
    enviarVersao();
  }
}

static void lerSerial() {
  static char buf[64];
  static uint8_t len = 0;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '$') { len = 0; buf[len++] = c; continue; }
    if (len == 0) continue;
    if (c == '\n' || c == '\r') { buf[len] = '\0'; tratarLinha(buf); len = 0; continue; }
    if (len < sizeof(buf) - 1) buf[len++] = c; else len = 0;
  }
}

// ------------------------------------------------------------------ botao de largada
// Armado: apertar PARA na hora. Parado: apertar e soltar (< BOTAO_DESLIGAR_MS) ARMA; segurar
// BOTAO_DESLIGAR_MS pede a Jetson para desligar (flag DESLIGAR) e nao arma ao soltar.
static void lerBotao() {
  static int estavel = HIGH, ultimoLido = HIGH;
  static uint32_t tMudanca = 0, tApertou = 0;
  static bool usado = true;             // este aperto ja teve efeito (parou ou pediu desligar)
  uint32_t agora = millis();
  int lido = digitalRead(PIN_BOTAO);
  if (lido != ultimoLido) { ultimoLido = lido; tMudanca = agora; }
  if (agora - tMudanca > 40 && lido != estavel) {
    estavel = lido;
    if (estavel == LOW) {               // apertou
      tApertou = agora;
      usado = false;
      if (estado == ARMADO) { pedirDesarmar(); usado = true; }   // parar nao espera soltar
    } else if (!usado) {                // soltou um aperto curto: largada
      usado = true;
      pedirArmar();
    }
  }
  if (estavel == LOW && !usado && agora - tApertou >= BOTAO_DESLIGAR_MS) {
    usado = true;
    pedidoDesligar = agora ? agora : 1;
  }
}

// ------------------------------------------------------------------ bateria
static void lerBateria() {
  static float filtro = 0;
  float mv = analogReadMilliVolts(PIN_VBAT) * DIVISOR_VBAT;
  filtro = (filtro == 0) ? mv : 0.95f * filtro + 0.05f * mv;
  vbat_mV = (int)filtro;
  bool valida = vbat_mV >= VBAT_MINIMA_VALIDA_MV;
  if (valida && vbat_mV < VBAT_AVISO_MV) flags |= FLAG_BATERIA_BAIXA; else flags &= ~FLAG_BATERIA_BAIXA;
  if (valida && vbat_mV < VBAT_CORTE_MV) {
    if (inicioVbatBaixa == 0) inicioVbatBaixa = millis();
    if (millis() - inicioVbatBaixa > 2000) mudarEstado(FALHA_BATERIA);
  } else {
    inicioVbatBaixa = 0;
  }
}

// ------------------------------------------------------------------ seguranca do link
static void verificarWatchdog() {
  if (estado == FALHA_BATERIA) return;
  if (estado == ARMADO && !linkRecente(WATCHDOG_FREIO_MS)) {
    alvoE = alvoD = 0;                  // freia, mas continua armado por mais um tempo
    flags |= FLAG_WATCHDOG;
  } else {
    flags &= ~FLAG_WATCHDOG;
  }
  if (estado != SEM_JETSON && !linkRecente(WATCHDOG_DESARME_MS)) mudarEstado(SEM_JETSON);
}

// ------------------------------------------------------------------ desligar a Jetson (D-039)
// Devolve true quando ja pode desligar a chave: a Jetson pediu/aceitou desligar, sumiu (sem comandos) e
// passou ESPERA_DESLIGAR_MS. Cancela se a Jetson voltar a mandar comandos ou se nunca parar de mandar.
static bool acompanharDesligamento(uint32_t agora) {
  if (!pedidoDesligar) return false;
  if (!jetsonSumiu) {
    if (estado == SEM_JETSON) {
      jetsonSumiu = agora ? agora : 1;
    } else if (agora - pedidoDesligar > DESLIGAR_AVISO_MS + DESLIGAR_SEM_RESPOSTA_MS) {
      pedidoDesligar = 0;               // a Jetson nao desligou (programa antigo, sem a regra do sudo...)
      return false;
    }
    return false;
  }
  if (estado != SEM_JETSON) {           // a Jetson voltou (ex.: o servico reiniciou o programa): cancela
    pedidoDesligar = jetsonSumiu = 0;
    return false;
  }
  return agora - jetsonSumiu >= ESPERA_DESLIGAR_MS;
}

// ------------------------------------------------------------------ setup / loop
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  if (PIN_BUZZER >= 0) pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_SLEEP_E, OUTPUT); pinMode(PIN_SLEEP_D, OUTPUT);
  escreverSleep(LOW);
  pinMode(PIN_BOTAO, INPUT_PULLUP);

  pwmIniciar(PIN_ME_IN1, 0); pwmIniciar(PIN_ME_IN2, 1);
  pwmIniciar(PIN_MD_IN1, 2); pwmIniciar(PIN_MD_IN2, 3);
  aplicarMotor(PIN_ME_IN1, 0, PIN_ME_IN2, 1, 0, INVERTER_E);
  aplicarMotor(PIN_MD_IN1, 2, PIN_MD_IN2, 3, 0, INVERTER_D);

  pinMode(PIN_ENC_E_A, INPUT_PULLUP); pinMode(PIN_ENC_E_B, INPUT_PULLUP);
  pinMode(PIN_ENC_D_A, INPUT_PULLUP); pinMode(PIN_ENC_D_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_E_A), isrEncE, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_E_B), isrEncE, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_D_A), isrEncD, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_D_B), isrEncD, CHANGE);

  enviarVersao();
}

void loop() {
  uint32_t agora = millis();
  lerSerial();
  lerBotao();
  verificarWatchdog();

  if (agora != ultimoTick) {            // tick de 1 ms: rampa + PWM
    uint32_t passos = agora - ultimoTick;
    ultimoTick = agora;
    int passo = RAMPA_POR_MS * (int)min(passos, (uint32_t)50);
    atualE = rampa(atualE, alvoE, passo);
    atualD = rampa(atualD, alvoD, passo);
    aplicarMotor(PIN_ME_IN1, 0, PIN_ME_IN2, 1, atualE, INVERTER_E);
    aplicarMotor(PIN_MD_IN1, 2, PIN_MD_IN2, 3, atualD, INVERTER_D);
  }

  if (agora - ultimaTelemetria >= TELEMETRIA_MS) {
    ultimaTelemetria = agora;
    lerBateria();
    bool desligando = pedidoDesligar && agora - pedidoDesligar < DESLIGAR_AVISO_MS;
    if (desligando) flags |= FLAG_DESLIGAR; else flags &= ~FLAG_DESLIGAR;
    bool podeDesligar = acompanharDesligamento(agora);
    char corpo[72];
    snprintf(corpo, sizeof(corpo), "T,%lu,%ld,%ld,%d,%d,%d", (unsigned long)agora,
             (long)encE, (long)encD, vbat_mV, (int)estado, flags);
    enviar(corpo);
    if (PIN_BUZZER >= 0)
      digitalWrite(PIN_BUZZER, ((flags & FLAG_BATERIA_BAIXA) && (agora / 250) % 2) ? HIGH : LOW);
    // LED: aceso = armado | piscando lento = pronto | piscando rapido = falha | apagado = sem Jetson
    // desligando: pisca muito rapido do pedido ate poder desligar; pode desligar: 2 piscadas por segundo
    uint32_t fase = agora % 1000;
    bool led = podeDesligar ? (fase < 100 || (fase >= 200 && fase < 300)) :
               pedidoDesligar ? (agora / 50) % 2 :
               estado == ARMADO || (estado == PRONTO && (agora / 500) % 2) ||
               (estado == FALHA_BATERIA && (agora / 100) % 2);
    digitalWrite(PIN_LED, led ? HIGH : LOW);
  }
}
