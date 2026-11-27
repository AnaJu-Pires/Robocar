#!/bin/bash
# Junta num arquivo so o que precisa para diagnosticar um problema no carro.
# Uso (na Jetson):  make diagnostico      -> ~/diagnostico_<data>.tar.gz
# Depois, no PC:    scp blitz@192.168.55.1:~/diagnostico_*.tar.gz .
set -u
REPO=$(cd "$(dirname "$0")/../.." && pwd)
NOME=diagnostico_$(date +%Y%m%d_%H%M%S)
TMP=$(mktemp -d)
D="$TMP/$NOME"
mkdir -p "$D"

git -C "$REPO" log --oneline -3 > "$D/versao_codigo.txt" 2>&1
{ uptime; echo; df -h /; echo; free -h; } > "$D/sistema.txt" 2>&1
last -x 2>/dev/null | head -40 > "$D/reinicios.txt"
journalctl -u robocar --no-pager -n 3000 > "$D/servico_robocar.txt" 2>&1
dmesg 2>/dev/null | grep -i -E "voltage|current|OC ALARM|soctherm|throttl|mmc|ext4|i/o error|cp210x|ttyUSB|imx219|error -71" \
  | tail -300 > "$D/kernel.txt"
# boot anterior (precisa do journal persistente: make preparar-jetson): como ele terminou?
{ journalctl --list-boots --no-pager | tail -15; echo; echo "== fim do boot anterior"; \
  journalctl -b -1 -n 60 --no-pager; } > "$D/boot_anterior.txt" 2>&1
{ nvpmodel -q 2>&1 | head -2; echo; systemctl is-enabled gpsd.socket ModemManager.service 2>&1; \
  echo; fuser -v /dev/ttyUSB0 2>&1; } > "$D/jetson.txt"
cp "$REPO"/jetson/config/*.json "$D/" 2>/dev/null
cp ~/carro.log ~/movimento.log "$D/" 2>/dev/null
ls -t "$REPO"/dados/logs/*.csv 2>/dev/null | head -3 | while read -r f; do cp "$f" "$D/"; done
ls -t "$REPO"/dados/capturas/*.png 2>/dev/null | head -4 | while read -r f; do cp "$f" "$D/"; done
# fotos de depuracao (--fotos / make fotos): a pasta mais recente, ate 60 fotos
FOTOS=$(ls -td "$REPO"/dados/capturas/*/ 2>/dev/null | head -1)
if [ -n "$FOTOS" ]; then
  mkdir -p "$D/fotos"
  ls "$FOTOS"*.jpg 2>/dev/null | head -60 | while read -r f; do cp "$f" "$D/fotos/"; done
fi

tar czf "$HOME/$NOME.tar.gz" -C "$TMP" "$NOME"
rm -rf "$TMP"
echo "Pronto: $HOME/$NOME.tar.gz ($(du -h "$HOME/$NOME.tar.gz" | cut -f1))"
echo "No PC:  scp blitz@192.168.55.1:~/$NOME.tar.gz ."
