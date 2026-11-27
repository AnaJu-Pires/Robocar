#!/bin/bash
# Prepara o sistema da Jetson para o robo (uma vez; pode rodar de novo sem problema).
# Uso:  sudo bash jetson/servico/preparar_jetson.sh            (ou: make preparar-jetson)
#       sudo bash jetson/servico/preparar_jetson.sh --desfazer (volta gpsd/ModemManager e o journal ao padrao)
#
# Por que (logs do cartao de 21-22/11, ver docs/06_testes.md):
#  1. Toda vez que a ESP32 conectava, o gpsd (servico de GPS do Ubuntu) pegava a /dev/ttyUSB0
#     ("gpsd_control(action=add, arg=/dev/ttyUSB0)") e o ModemManager testava a porta. O gpsd abre a
#     porta, troca a velocidade para procurar um GPS e le os bytes da telemetria: e a causa provavel da
#     "telemetria embaralhada" ao abrir a porta. Nenhum dos dois serve para o robo: ficam mascarados.
#  2. Desligar pelo botao de largada (segurar 3 s com o robo parado, D-039): o seguir_linha.py chama
#     "sudo -n /sbin/shutdown -h now", que precisa de uma regra do sudo sem senha (so esse comando).
#  3. O journal so existia na memoria: cada corte de energia apagava o historico. Fica persistente, e
#     gravando a cada 15 s (o padrao e 5 min: um corte perderia justamente os ultimos minutos).
set -euo pipefail

RAIZ=${RAIZ:-}                      # so para os testes (instala dentro de outra pasta)
SERVICOS="gpsd.socket gpsd.service ModemManager.service"

if [ "$(id -u)" -ne 0 ]; then
  echo "Rode com sudo:  sudo bash $0 ${1:-}"
  exit 1
fi

existe() { systemctl list-unit-files "$1" 2>/dev/null | grep -q "^$1"; }

if [ "${1:-}" = "--desfazer" ]; then
  for s in $SERVICOS; do existe "$s" && systemctl unmask "$s" && systemctl enable "$s" 2>/dev/null || true; done
  rm -f "$RAIZ/etc/systemd/journald.conf.d/robocar.conf" "$RAIZ/etc/sudoers.d/robocar-desligar"
  systemctl restart systemd-journald || true
  echo "Desfeito: gpsd/ModemManager liberados; journal volta ao padrao; regra do shutdown removida."
  exit 0
fi

echo "== 1/4 Tirando o gpsd e o ModemManager da porta da ESP32"
for s in $SERVICOS; do
  if existe "$s"; then
    systemctl disable --now "$s" >/dev/null 2>&1 || true
    systemctl mask "$s" >/dev/null
    echo "   $s: parado e mascarado"
  else
    echo "   $s: nao instalado (ok)"
  fi
done

echo "== 2/4 Desligar pelo botao de largada (segurar 3 s): shutdown sem senha, so este comando"
USUARIO=${SUDO_USER:-}
if [ -n "$USUARIO" ] && [ "$USUARIO" != "root" ]; then
  REGRA=$(mktemp)
  echo "$USUARIO ALL=(root) NOPASSWD: /sbin/shutdown -h now" > "$REGRA"
  if visudo -cf "$REGRA" >/dev/null; then
    mkdir -p "$RAIZ/etc/sudoers.d"
    install -m 0440 "$REGRA" "$RAIZ/etc/sudoers.d/robocar-desligar"
    echo "   ok: $USUARIO pode rodar 'sudo shutdown -h now' sem senha"
  else
    echo "   AVISO: regra do sudo invalida; o desligamento pelo botao nao vai funcionar"
  fi
  rm -f "$REGRA"
else
  echo "   AVISO: rode com sudo a partir do seu usuario (ex.: blitz) para instalar a regra"
fi

echo "== 3/4 Journal persistente (sobrevive ao desligar), gravando a cada 15 s"
mkdir -p "$RAIZ/var/log/journal" "$RAIZ/etc/systemd/journald.conf.d"
cat > "$RAIZ/etc/systemd/journald.conf.d/robocar.conf" <<'EOF'
# Robocar (jetson/servico/preparar_jetson.sh): historico entre boots, sem perder os ultimos minutos num corte
[Journal]
Storage=persistent
SyncIntervalSec=15s
SystemMaxUse=200M
EOF
if [ -z "$RAIZ" ]; then
  systemd-tmpfiles --create --prefix /var/log/journal || true
  systemctl restart systemd-journald
  journalctl --flush || true
fi
echo "   ok: /var/log/journal (ver boots anteriores: journalctl --list-boots)"

echo "== 4/4 Conferencias"
if [ -n "$USUARIO" ] && ! id -nG "$USUARIO" | grep -qw dialout; then
  usermod -aG dialout "$USUARIO"
  echo "   $USUARIO entrou no grupo dialout (acesso a ESP32): saia e entre de novo no SSH"
else
  echo "   grupo dialout: ok"
fi
if [ -z "$RAIZ" ]; then
  echo "   modo de energia: $(nvpmodel -q 2>/dev/null | grep -i 'power mode' | head -1 || echo '?')"
  # /dev/video0 so existe se o sensor foi reconhecido no boot; o dmesg pode ja ter perdido as linhas do boot
  if ls /dev/video* >/dev/null 2>&1; then
    echo "   camera: detectada ($(ls /dev/video* | tr '\n' ' '))"
  else
    echo "   CAMERA NAO DETECTADA (sem /dev/video*): desligue tudo, confira o cabo flat nas duas pontas e ligue de novo"
  fi
  if [ -e /dev/ttyUSB0 ]; then
    if fuser /dev/ttyUSB0 >/dev/null 2>&1; then
      echo "   /dev/ttyUSB0 em uso por:"; fuser -v /dev/ttyUSB0 2>&1 | sed 's/^/     /'
      echo "   (se for o robocar.service, tudo bem)"
    else
      echo "   /dev/ttyUSB0: livre"
    fi
  else
    echo "   /dev/ttyUSB0 nao existe agora (ESP32 desconectada?)"
  fi
fi
echo
echo "Pronto. Nada disso precisa ser repetido a cada boot."
