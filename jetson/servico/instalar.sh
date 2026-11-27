#!/bin/bash
# Instala (ou atualiza) o inicio automatico do robo no boot da Jetson.
# Uso:  sudo bash jetson/servico/instalar.sh [PORTA] [--botao-j41]   (porta padrao /dev/ttyUSB0)
#       --botao-j41: tambem o servico do botao de desligar no J41 (opcao "a", D-028). A equipe escolheu a
#       opcao "b" (segurar a largada 3 s, D-039): sem a placa ligada no J41, o pino 18 fica solto e o
#       servico poderia ler um "aperto" falso. Por isso ele so e instalado com esta opcao.
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
PORTA=/dev/ttyUSB0
BOTAO_J41=0
for a in "$@"; do
  case "$a" in
    --botao-j41) BOTAO_J41=1 ;;
    *) PORTA=$a ;;
  esac
done

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
if [ "$BOTAO_J41" = 1 ]; then
  # botao de desligar no J41 (pino 18) + LED "pode desligar a chave" (pino 16): servico proprio, como root (D-028)
  sed -e "s|@REPO@|$REPO|g" "$REPO/jetson/servico/botao-desligar.service" > /etc/systemd/system/botao-desligar.service
  systemctl daemon-reload
  systemctl enable --now botao-desligar.service
elif [ -e /etc/systemd/system/botao-desligar.service ]; then
  systemctl disable --now botao-desligar.service || true   # instalado antes: sem a placa do J41, desliga
fi
systemctl daemon-reload
systemctl enable robocar.service

echo
echo "Servico instalado: liga sozinho no proximo boot (usuario $USUARIO, porta $PORTA)."
echo "  Iniciar agora:        sudo systemctl start robocar"
echo "  Ver o que ele mostra: journalctl -u robocar -f"
echo "  Parar (para usar make visao/calibrar/bancada): sudo systemctl stop robocar"
echo "  Desligar o inicio automatico: sudo systemctl disable --now robocar"
echo "  Desligar a Jetson sem SSH: com o robo parado, SEGURE o botao de largada por 3 s."
echo "    LED da ESP32: pisca muito rapido = desligando (NAO corte a chave);"
echo "    2 piscadas por segundo (ou apagado) = pode desligar a chave."
if [ "$BOTAO_J41" = 1 ]; then
  echo "  Botao do J41: segure 2 s; o LED dele APAGA quando a Jetson terminou."
  echo "  Testar sem desligar: sudo systemctl stop botao-desligar && sudo python3 jetson/servico/botao_desligar.py --teste"
fi
