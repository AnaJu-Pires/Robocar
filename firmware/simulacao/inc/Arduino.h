// Arduino falso para rodar o firmware no PC (simulacao). Serial = stdin/stdout; eventos em stderr.
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <algorithm>
#include <chrono>
#include <unistd.h>
#include <fcntl.h>
#ifndef ESP_ARDUINO_VERSION_MAJOR
#define ESP_ARDUINO_VERSION_MAJOR 3
#endif
#define IRAM_ATTR
#define DRAM_ATTR
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define CHANGE 3
using std::min; using std::max;
template<class T, class L, class H> T constrain(T x, L lo, H hi) { return x < lo ? lo : (x > hi ? hi : x); }
uint32_t millis();
void pinMode(int p, int m);
void digitalWrite(int p, int v);
int digitalRead(int p);
uint32_t analogReadMilliVolts(int p);
int digitalPinToInterrupt(int p);
void attachInterrupt(int i, void (*f)(), int m);
bool ledcAttach(int pin, uint32_t f, uint8_t bits);
bool ledcWrite(int pin, uint32_t duty);
uint32_t sim_gpio_in(int bank);
#define REG_READ(r) sim_gpio_in(r)
struct SerialFalso {
  void begin(long) { fcntl(0, F_SETFL, fcntl(0, F_GETFL) | O_NONBLOCK); }
  int pend = -1;
  int available() { if (pend >= 0) return 1; unsigned char c; if (::read(0, &c, 1) == 1) { pend = c; return 1; } return 0; }
  int read() { int c = pend; pend = -1; return c; }
  void print(const char* s) { fputs(s, stdout); fflush(stdout); }
};
extern SerialFalso Serial;
