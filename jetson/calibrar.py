"""Calibracao de preto e branco (antigo peb.py; original preservado em legado/peb.py).

Mantido do original: mediana da intensidade de uma regiao; teclas B (branco), P (preto),
R (recalibrar), Q (sair); limiar = media entre branco e preto; indicacao BRANCO/PRETO.

Acrescentado:
  S  salva em config/calibracao.json (lido automaticamente pelo seguir_linha.py)
  A  calibracao automatica (Otsu) com linha e fundo visiveis no retangulo
  C  alterna a regiao: "inferior" (a mesma do seguidor - recomendado) ou "central" (original)
  janela de mascara com o limiar atual e aviso de contraste baixo

Uso: python3 calibrar.py [--fonte csi|0|video.avi]
"""

import argparse
import sys

import cv2
import numpy as np

from robocar import configuracao
from robocar.camera import Camera

CONTRASTE_MIN = 40.0
ESCALA = 2


def regiao(cinza, modo, inicio_roi):
    H, W = cinza.shape[:2]
    if modo == "central":
        lado = int(min(H, W) * 0.45)  # equivale ao quadrado 250x250 do original em 960x540
        x1, y1 = W // 2 - lado // 2, H // 2 - lado // 2
        return x1, y1, x1 + lado, y1 + lado
    return 0, int(H * inicio_roi), W, H


def calibrar_otsu(pixels):
    """Separa fundo e linha automaticamente. Retorna (branco, preto) ou None."""
    t, _ = cv2.threshold(pixels, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    claros, escuros = pixels[pixels > t], pixels[pixels <= t]
    if claros.size < 0.05 * pixels.size or escuros.size < 0.01 * pixels.size:
        return None  # nao ha linha E fundo suficientes na regiao
    return float(np.median(claros)), float(np.median(escuros))


def desenhar(cinza, ret, intensidade, branco, preto, modo):
    frame = cv2.resize(cv2.cvtColor(cinza, cv2.COLOR_GRAY2BGR), None, fx=ESCALA, fy=ESCALA,
                       interpolation=cv2.INTER_NEAREST)
    altura, largura = frame.shape[:2]
    x1, y1, x2, y2 = [v * ESCALA for v in ret]
    cv2.rectangle(frame, (x1, y1), (x2 - 1, y2 - 1), (0, 255, 0), 2)

    def texto(t, y, cor, tam=0.6):
        cv2.putText(frame, t, (12, y), cv2.FONT_HERSHEY_SIMPLEX, tam, cor, 2)

    texto("Intensidade (mediana): %.1f   regiao: %s" % (intensidade, modo), 25, (0, 255, 255))
    if branco is not None:
        texto("Branco calibrado: %.1f" % branco, 50, (255, 255, 255))
    if preto is not None:
        texto("Preto calibrado: %.1f" % preto, 75, (200, 200, 200))
    if branco is not None and preto is not None:
        limiar, contraste = (branco + preto) / 2.0, branco - preto
        baixo = contraste < CONTRASTE_MIN
        texto("Limiar: %.1f  contraste: %.0f%s" % (limiar, contraste, "  (BAIXO!)" if baixo else ""),
              100, (0, 0, 255) if baixo else (0, 255, 255))
        resultado = "BRANCO" if intensidade >= limiar else "PRETO"
        cv2.putText(frame, resultado, (largura // 2 - 70, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    (255, 255, 255) if resultado == "BRANCO" else (0, 0, 255), 3)
    else:
        texto("Calibre: B = branco | P = preto | A = automatico", altura - 45, (0, 255, 255))
    texto("Q sair | R recalibrar | S salvar | C regiao", altura - 15, (0, 255, 0), 0.55)
    return frame


def main():
    ap = argparse.ArgumentParser(description="Calibracao preto/branco - Robocar Blitz")
    ap.add_argument("--fonte")
    args = ap.parse_args()

    cfg = configuracao.carregar_config()
    cam = Camera(cfg["camera"], args.fonte)
    print("Fonte:", cam.descricao)
    anterior = configuracao.carregar_calibracao()
    branco = anterior["branco"] if anterior else None
    preto = anterior["preto"] if anterior else None
    if anterior:
        print("Calibracao anterior: branco=%.1f preto=%.1f" % (branco, preto))
    modo = "inferior"

    while True:
        ok, cinza = cam.ler()
        if not ok:
            print("ERRO: Nao foi possivel receber o frame.")
            break
        ret = regiao(cinza, modo, cfg["visao"]["inicio_roi"])
        roi = cinza[ret[1]:ret[3], ret[0]:ret[2]]
        intensidade = float(np.median(roi))

        cv2.imshow("Deteccao Preto e Branco", desenhar(cinza, ret, intensidade, branco, preto, modo))
        if branco is not None and preto is not None:
            _, mascara = cv2.threshold(cinza, (branco + preto) / 2.0, 255, cv2.THRESH_BINARY_INV)
            cv2.imshow("Mascara (linha = branco)", cv2.resize(mascara, None, fx=ESCALA, fy=ESCALA,
                                                              interpolation=cv2.INTER_NEAREST))
        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("b"):
            branco = intensidade
            print("BRANCO calibrado: %.1f" % branco)
        elif tecla == ord("p"):
            preto = intensidade
            print("PRETO calibrado: %.1f" % preto)
        elif tecla == ord("a"):
            r = calibrar_otsu(roi)
            if r is None:
                print("Automatico falhou: deixe a LINHA e o FUNDO visiveis dentro do retangulo.")
            else:
                branco, preto = r
                print("AUTOMATICO: branco=%.1f preto=%.1f" % (branco, preto))
        elif tecla == ord("r"):
            branco = preto = None
            print("Calibracao apagada.")
        elif tecla == ord("c"):
            modo = "central" if modo == "inferior" else "inferior"
        elif tecla == ord("q"):
            break

        if tecla in (ord("b"), ord("p"), ord("a"), ord("s")) and branco is not None and preto is not None:
            try:
                dados = configuracao.salvar_calibracao(branco, preto,
                                                       extras={"regiao": modo, "camera": cam.descricao})
                print("Salvo em %s: %s" % (configuracao.ARQ_CALIBRACAO, dados))
                if branco - preto < CONTRASTE_MIN:
                    print("AVISO: contraste baixo; melhore a iluminacao ou a exposicao da camera.")
            except ValueError as e:
                print("ERRO:", e, "- recalibre (tecla R).")

    cam.liberar()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
