#!/bin/bash
# Instala (ou atualiza) o inicio automatico do robo no boot da Jetson.
# Uso:  sudo bash jetson/servico/instalar.sh [PORTA]      (padrao /dev/ttyUSB0)
# Desfazer: sudo systemctl disable --now robocar
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Rode com sudo:  sudo bash $0 ${1:-}"
  exit 1
fi
USUARIO=${SUDO_USER:-}
if [ -z "$USUARIO" ] || [ "$USUARIO" = "root" ]; then
  echo "Rode com sudo a partir do seu usuario (ex.: blitz), nao como root."
  exit 1
fi
REPO=$(cd "$(dirname "$0")/../.." && pwd)
PORTA=${1:-/dev/ttyUSB0}

case "$REPO" in
  *" "*) echo "O caminho do repositorio nao pode ter espacos: $REPO"; exit 1 ;;
esac
id -nG "$USUARIO" | grep -qw dialout || {
  echo "AVISO: $USUARIO nao esta no grupo dialout (acesso a ESP32). Rodando: usermod -aG dialout $USUARIO"
  usermod -aG dialout "$USUARIO"
}

# shutdown sem senha (so este comando): o botao da ESP32 segurado 3 s desliga a Jetson com seguranca
REGRA=$(mktemp)
echo "$USUARIO ALL=(root) NOPASSWD: /sbin/shutdown -h now" > "$REGRA"
if visudo -cf "$REGRA" >/dev/null; then
  install -m 0440 "$REGRA" /etc/sudoers.d/robocar-desligar
else
  echo "AVISO: regra do sudo invalida; o desligamento pelo botao nao vai funcionar."
fi
rm -f "$REGRA"

sed -e "s|@USUARIO@|$USUARIO|g" -e "s|@REPO@|$REPO|g" -e "s|@PORTA@|$PORTA|g" \
  "$REPO/jetson/servico/robocar.service" > /etc/systemd/system/robocar.service
# botao de desligar no J41 (pino 18) + LED "pode desligar a chave" (pino 16): servico proprio, como root (D-028)
sed -e "s|@REPO@|$REPO|g" "$REPO/jetson/servico/botao-desligar.service" > /etc/systemd/system/botao-desligar.service
systemctl daemon-reload
systemctl enable robocar.service
systemctl enable --now botao-desligar.service

echo
echo "Servico instalado: liga sozinho no proximo boot (usuario $USUARIO, porta $PORTA)."
echo "  Iniciar agora:        sudo systemctl start robocar"
echo "  Ver o que ele mostra: journalctl -u robocar -f"
echo "  Parar (para usar make visao/calibrar/bancada): sudo systemctl stop robocar"
echo "  Desligar o inicio automatico: sudo systemctl disable --now robocar"
echo "  Desligar a Jetson sem SSH: segure o botao de DESLIGAR (tampo, lado direito) por 2 s;"
echo "    o LED verde pisca, fica aceso e APAGA quando a Jetson terminou: so entao desligue a chave."
echo "    Reserva: com o robo parado, segure o botao de largada por 3 s (LED da ESP32 pisca rapido)."
echo "  Testar o botao sem desligar: sudo systemctl stop botao-desligar && sudo python3 jetson/servico/botao_desligar.py --teste"
