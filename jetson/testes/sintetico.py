"""Gerador de imagens sinteticas de pista (320x180, linha escura sobre fundo claro).

Imagens sinteticas pegam erros de logica; NAO substituem testes com a camera real na pista.
"""

import cv2
import numpy as np

from robocar import configuracao

W, H = 320, 180
CALIBRACAO = {"branco": 200.0, "preto": 40.0, "limiar": 120.0, "razao": 0.6}


class Cena(object):
    """Cena em float32; use .imagem() para obter o quadro uint8."""

    def __init__(self, brilho=200, ruido=6, gradiente=None, semente=0):
        rng = np.random.RandomState(semente)
        self.img = np.full((H, W), float(brilho), np.float32)
        if gradiente is not None:  # sombra: multiplica da esquerda (g0) para a direita (g1)
            self.img *= np.linspace(gradiente[0], gradiente[1], W, dtype=np.float32)[None, :]
        self.img += rng.normal(0, ruido, (H, W)).astype(np.float32)

    def linha(self, pontos, cor=40, espessura=12):
        pts = np.array(pontos, np.int32).reshape(-1, 1, 2)
        cv2.polylines(self.img, [pts], False, float(cor), espessura)
        return self

    def retangulo(self, p1, p2, cor=30):
        cv2.rectangle(self.img, p1, p2, float(cor), -1)
        return self

    def imagem(self):
        return np.clip(self.img, 0, 255).astype(np.uint8)


def vertical(x):
    return [(x, H), (x, 0)]


def curva(x0, x1, n=40):
    """Curva parabolica da base (x0, H) ate o topo (x1, 0)."""
    ys = np.linspace(H, 0, n)
    s = (H - ys) / H
    return list(zip(x0 + (x1 - x0) * s * s, ys))


def config(**ajustes_visao):
    return configuracao.carregar_config(ajustes={"visao": ajustes_visao} if ajustes_visao else None)
