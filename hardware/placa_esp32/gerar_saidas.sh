#!/usr/bin/env bash
# Robocar Blitz - gera as saidas da placa da ESP32 a partir do .kicad_pcb / .kicad_sch.
# Uso (na raiz do repositorio):  make placa      ou   bash hardware/placa_esp32/gerar_saidas.sh
# Precisa: kicad-cli (KiCad 7 ou mais novo) e, para as imagens PNG, pdftoppm (poppler) e ImageMagick.
set -euo pipefail
cd "$(dirname "$0")"
P=placa_esp32
F=fabricacao
mkdir -p "$F" imagens

# Os modelos 3D usam ${KICAD10_3DMODEL_DIR}. Fora do KiCad 10, aponta para a pasta de modelos instalada.
if [ -z "${KICAD10_3DMODEL_DIR:-}" ]; then
  for d in /usr/share/kicad/3dmodels /Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels; do
    [ -d "$d" ] && export KICAD10_3DMODEL_DIR="$d" && break
  done
fi

echo "== esquematico (PDF)"
kicad-cli sch export pdf -o "$P.pdf" "$P.kicad_sch" >/dev/null

echo "== arte do cobre 1:1 (so B.Cu: face simples), preto = cobre, marca de broca no centro das ilhas"
kicad-cli pcb export pdf --layers B.Cu,Edge.Cuts --black-and-white --drill-shape-opt 1 \
  -o "$F/1_cobre_transferencia_1x1.pdf" "$P.kicad_pcb" >/dev/null

echo "== folha de montagem (lado dos componentes, jumpers JP1/JP2 em serigrafia)"
kicad-cli pcb export pdf --layers F.Cu,F.SilkS,F.Fab,Edge.Cuts \
  -o "$F/2_montagem_e_jumpers.pdf" "$P.kicad_pcb" >/dev/null

echo "== furacao (Excellon) e mapa de brocas"
kicad-cli pcb export drill --format excellon --drill-origin plot --excellon-separate-th --generate-map --map-format pdf \
  -o "$F/" "$P.kicad_pcb" >/dev/null

echo "== STEP (placa + ESP32 do fabricante + barras femea/pecas nativas do KiCad)"
kicad-cli pcb export step --subst-models --force -o "$P.step" "$P.kicad_pcb" >/dev/null

if command -v pdftoppm >/dev/null && command -v convert >/dev/null; then
  echo "== imagens"
  T=$(mktemp -d)
  png() {  # png <saida.png> <layers> [--mirror]
    kicad-cli pcb export pdf --layers "$2" ${3:-} -o "$T/x.pdf" "$P.kicad_pcb" >/dev/null
    pdftoppm -r 600 -png -singlefile "$T/x.pdf" "$T/x"
    convert "$T/x.png" -trim +repage -bordercolor white -border 20 "$1"
  }
  png imagens/cobre_vista_de_cima.png B.Cu,F.SilkS,Edge.Cuts
  png imagens/montagem_e_jumpers.png  F.Cu,F.SilkS,F.Fab,Edge.Cuts
  png imagens/lado_do_cobre.png       B.Cu,Edge.Cuts --mirror
  rm -rf "$T"
fi
echo "ok"
