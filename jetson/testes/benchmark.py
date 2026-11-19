"""Tempo de processamento por quadro: algoritmo atual x algoritmo original (legado/).

Uso (a partir de jetson/):  python3 -m testes.benchmark      (ou: make benchmark)
Mede so o algoritmo na maquina onde roda. Na Jetson, rode la para ter o numero real.
"""

import time

import cv2
import numpy as np

from robocar.visao import DetectorLinha
from testes.sintetico import CALIBRACAO, Cena, config, curva


def algoritmo_original(cinza, limiar=60.5, inicio_roi=0.55):
    """Reproducao de legado/seguir_linha.py (maior contorno + centroide) para comparacao."""
    altura, largura = cinza.shape[:2]
    y_inicio = int(altura * inicio_roi)
    gray = cv2.GaussianBlur(cinza[y_inicio:altura], (5, 5), 0)
    _, mascara = cv2.threshold(gray, limiar, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((5, 5), np.uint8)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)
    res = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos = res[0] if len(res) == 2 else res[1]  # OpenCV 3.x devolve 3 valores
    validos = [c for c in contornos if cv2.contourArea(c) >= 300 * (largura / 960.0) ** 2]
    if not validos:
        return None
    m = cv2.moments(max(validos, key=cv2.contourArea))
    if m["m00"] == 0:
        return None
    return (m["m10"] / m["m00"] - largura // 2) / (largura / 2.0)


def medir(funcao, n=300):
    t0 = time.time()
    for _ in range(n):
        funcao()
    return (time.time() - t0) / n * 1000.0


def main():
    pequena = Cena().linha(curva(160, 60)).imagem()
    grande_bgr = cv2.resize(cv2.cvtColor(pequena, cv2.COLOR_GRAY2BGR), (960, 540))
    detector = DetectorLinha(config()["visao"], CALIBRACAO)
    t_novo = medir(lambda: detector.processar(pequena))
    t_orig = medir(lambda: algoritmo_original(cv2.cvtColor(grande_bgr, cv2.COLOR_BGR2GRAY)))
    print("Tempo por quadro NESTA maquina (so o algoritmo):")
    print("  original (960x540 BGR): %.2f ms" % t_orig)
    print("  atual    (320x180 cinza): %.2f ms" % t_novo)

    x = Cena().linha([(160, 180), (160, 0)]).linha([(60, 180), (260, 0)]).imagem()
    print("Intersecao em X (ideal = 0): original %.3f | atual (sem historico) %.3f" % (
        algoritmo_original(x, limiar=120), DetectorLinha(config()["visao"], CALIBRACAO).processar(x)["erro"]))


if __name__ == "__main__":
    main()
