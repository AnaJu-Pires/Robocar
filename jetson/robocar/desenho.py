"""Sobreposicoes de depuracao (janelas). Nao afeta o controle."""

import cv2

from . import visao

VERDE, AMARELO, VERMELHO, BRANCO = (0, 255, 0), (0, 255, 255), (0, 0, 255), (255, 255, 255)
_CORES = {visao.OK: VERDE, visao.LARGO: (0, 165, 255), visao.AUSENTE: VERMELHO}


def rotulo_direcao(erro, margem):
    """Mesmo criterio do codigo original (MARGEM_CENTRO)."""
    if erro is None:
        return "LINHA PERDIDA"
    if erro < -margem:
        return "ESQUERDA"
    if erro > margem:
        return "DIREITA"
    return "RETO"


def imagem_debug(cinza, det, textos=(), escala=2):
    """Imagem colorida ampliada: ROI, centro, pontos por faixa e textos [(texto, cor), ...]."""
    img = cv2.cvtColor(cinza, cv2.COLOR_GRAY2BGR)
    if escala != 1:
        img = cv2.resize(img, None, fx=escala, fy=escala, interpolation=cv2.INTER_NEAREST)
    H, W = img.shape[:2]
    y0 = det["y0"] * escala
    cv2.line(img, (0, y0), (W, y0), (255, 255, 0), 1)          # limite da ROI
    cv2.line(img, (W // 2, y0), (W // 2, H), (255, 0, 0), 1)   # centro da camera
    trilha = []
    for (x, y, larg, estado) in det["pontos"]:
        if x is None:
            continue
        p = (int(x * escala), int(y * escala))
        meia = int(larg * escala / 2)
        cv2.line(img, (p[0] - meia, p[1]), (p[0] + meia, p[1]), _CORES[estado], 2)
        cv2.circle(img, p, 5, _CORES[estado], -1)
        if estado == visao.OK:
            trilha.append(p)
    for a, b in zip(trilha[:-1], trilha[1:]):
        cv2.line(img, a, b, AMARELO, 2)
    if trilha:
        cv2.line(img, (W // 2, H - 10), trilha[0], AMARELO, 1)
    for k, (texto, cor) in enumerate(textos):
        cv2.putText(img, texto, (8, 22 + 22 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.55, cor, 2)
    return img


def mascara_ampliada(mascara, escala=2):
    return cv2.resize(mascara, None, fx=escala, fy=escala, interpolation=cv2.INTER_NEAREST)
