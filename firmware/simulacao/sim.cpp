#include "Arduino.h"
SerialFalso Serial;
static auto T0 = std::chrono::steady_clock::now();
uint32_t millis() { return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - T0).count(); }
static int nivel[40], modo[40];
static int pwm[40];
static void (*isr[40])() = {0};
static const char* arq(const char* n) { static char b[256]; snprintf(b, 256, "%s/%s", getenv("SIMDIR"), n); return b; }
static int lerArq(const char* n, int def) { FILE* f = fopen(arq(n), "r"); if (!f) return def; int v = def; if (fscanf(f, "%d", &v) != 1) v = def; fclose(f); return v; }
void pinMode(int p, int m) { modo[p] = m; if (m == INPUT_PULLUP) nivel[p] = 1; }
void digitalWrite(int p, int v) { if (nivel[p] != v || modo[p] != 99) fprintf(stderr, "%u DW %d %d\n", millis(), p, v); nivel[p] = v; modo[p] = 99; }
int digitalRead(int p) { if (p == 4) return lerArq("botao", 1); return nivel[p]; }
uint32_t analogReadMilliVolts(int) { return (uint32_t)lerArq("pino36_mv", 0); }
int digitalPinToInterrupt(int p) { return p; }
void attachInterrupt(int i, void (*f)(), int) { isr[i] = f; }
bool ledcAttach(int pin, uint32_t f, uint8_t bits) { fprintf(stderr, "0 LEDC %d %u %u\n", pin, f, bits); return true; }
bool ledcWrite(int pin, uint32_t d) { if (pwm[pin] != (int)d) fprintf(stderr, "%u PWM %d %u\n", millis(), pin, d); pwm[pin] = d; return true; }
uint32_t sim_gpio_in(int bank) { uint32_t r = 0; for (int i = 0; i < 32; i++) { int p = bank * 32 + i; if (p < 40 && nivel[p]) r |= 1u << i; } return r; }
// encoder: gira N passos de quadratura no encoder esquerdo (26/27) e direito (17/16)
static void passo(int a, int b, int dir, int& fase) {
  static const int seq[4][2] = {{0,0},{1,0},{1,1},{0,1}};
  fase = (fase + dir + 4) % 4; int na = seq[fase][0], nb = seq[fase][1];
  if (nivel[a] != na) { nivel[a] = na; isr[a](); }
  if (nivel[b] != nb) { nivel[b] = nb; isr[b](); }
}
void setup(); void loop();
int main() {
  setup();
  int fe = 0, fd = 0;
  for (;;) {
    loop();
    int ne = lerArq("enc_e", 0), nd = lerArq("enc_d", 0);
    if (ne || nd) { unlink(arq("enc_e")); unlink(arq("enc_d"));
      for (int i = 0; i < abs(ne); i++) passo(26, 27, ne > 0 ? 1 : -1, fe);
      for (int i = 0; i < abs(nd); i++) passo(17, 16, nd > 0 ? 1 : -1, fd); }
    usleep(200);
  }
}
