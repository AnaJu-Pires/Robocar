#!/usr/bin/env bash
# Compila o firmware da ESP32 para o PC (Arduino falso) e roda o roteiro com o codigo da Jetson.
set -euo pipefail
cd "$(dirname "$0")"
FW=../robocar_esp32
mkdir -p build estado
{ echo '#include "Arduino.h"'; cat "$FW/robocar_esp32.ino"; } > build/fw.cpp
g++ -std=c++17 -O1 -Wall -Wextra -Wno-unused-parameter -DESPERA_DESLIGAR_MS_SIM=2000 -Iinc -I"$FW" -o build/esp_sim sim.cpp build/fw.cpp
python3 roteiro.py
