#!/bin/sh
# Chamado pelo servico robocar (robocar.service): espera a ESP32 aparecer e roda o modo corrida.
# Uso: sh iniciar.sh [PORTA]   (padrao /dev/ttyUSB0)
PORTA=${1:-/dev/ttyUSB0}
cd "$(dirname "$0")/.." || exit 1

i=0
while [ ! -e "$PORTA" ]; do
  i=$((i + 1))
  if [ "$i" -gt 30 ]; then
    echo "ESP32 nao encontrada em $PORTA (cabo USB?). O servico tenta de novo em 3 s."
    exit 1
  fi
  sleep 1
done

# exec: o python recebe o SIGINT do systemd direto e desliga a ESP32 com seguranca
exec /usr/bin/python3 -u seguir_linha.py --esp32 "$PORTA" --sem-janela --log
