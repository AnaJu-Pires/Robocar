"""Deteccao da linha preta por faixas horizontais (logica pura; sem camera e sem janelas).

Algoritmo (detalhes e motivacao em docs/04_software.md e docs/decisoes.md, D-003):
  1. ROI = parte inferior da imagem; limiar (adaptativo, fixo ou Otsu) -> mascara de escuro.
  2. A ROI e dividida em N faixas, de baixo (perto) para cima (longe).
  3. Em cada faixa: perfil de colunas escuras -> segmentos continuos.
  4. Escolhe o segmento mais proximo da posicao PREVISTA (extrapolada das faixas de baixo
     ou do quadro anterior). Segmento largo demais (cruzamento/marca) ou longe demais da
     previsao (outra linha) nao e usado.
  5. Saida: erro perto, erro longe, inclinacao, flags de cruzamento e de marca.
"""

import cv2
import numpy as np

OK = "ok"
LARGO = "largo"
AUSENTE = "ausente"


def segmentos_1d(perfil, largura_min=2, gap_max=2):
    """Trechos continuos True de um vetor booleano -> lista de (inicio, fim) inclusivos.

    Trechos separados por ate 'gap_max' colunas sao unidos (reflexo/ruido na linha).
    """
    p = np.concatenate(([0], perfil.astype(np.int8), [0]))
    d = np.diff(p)
    inicios = np.flatnonzero(d == 1)
    fins = np.flatnonzero(d == -1) - 1
    segs = []
    for a, b in zip(inicios, fins):
        if segs and a - segs[-1][1] - 1 <= gap_max:
            segs[-1][1] = int(b)
        else:
            segs.append([int(a), int(b)])
    return [(a, b) for a, b in segs if b - a + 1 >= largura_min]


def _centro(seg):
    return 0.5 * (seg[0] + seg[1])


class DetectorLinha(object):

    def __init__(self, cfg_visao, calibracao=None):
        self.cfg = cfg_visao
        self.n = int(cfg_visao["n_faixas"])
        self.razao = float(cfg_visao["razao_limiar_padrao"])
        self.limiar_fixo = float(cfg_visao["limiar_fixo"])
        if calibracao:
            self.razao = float(calibracao.get("razao") or self.razao)
            self.limiar_fixo = float(calibracao.get("limiar") or self.limiar_fixo)
        self.kernel = np.ones((3, 3), np.uint8)
        self.resetar()

    def resetar(self):
        self.x_ant = [None] * self.n
        self.largura_ref = [None] * self.n
        self.frames_sem_linha = 0

    # ------------------------------------------------------------------ limiar
    def calcular_limiar(self, roi):
        modo = self.cfg["limiar_modo"]
        if modo == "fixo":
            return self.limiar_fixo
        amostra = roi[::4, ::4]
        if modo == "otsu":
            t, _ = cv2.threshold(amostra, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return float(t)
        # adaptativo: a ROI e majoritariamente fundo claro; o percentil alto mede o "branco"
        # atual e o limiar acompanha mudancas de iluminacao e da exposicao automatica.
        branco = float(np.percentile(amostra, self.cfg["percentil_branco"]))
        return float(min(max(branco * self.razao, self.cfg["limiar_min"]), self.cfg["limiar_max"]))

    # ---------------------------------------------------------------- previsao
    def _prever(self, i, validos, largura):
        if len(validos) >= 2:
            (i0, x0), (i1, x1) = validos[-2], validos[-1]
            return x1 + (x1 - x0) * float(i - i1) / float(i1 - i0)
        if len(validos) == 1:
            return validos[0][1]
        if self.x_ant[i] is not None:
            return self.x_ant[i]
        return largura / 2.0

    def _escolher(self, segs, previsto, salto_max):
        melhor = min(segs, key=lambda s: abs(_centro(s) - previsto))
        pref = self.cfg["preferencia_bifurcacao"]
        if pref in ("esquerda", "direita") and len(segs) > 1:
            proximos = [s for s in segs if abs(_centro(s) - previsto) <= salto_max]
            if len(proximos) > 1:
                melhor = (min if pref == "esquerda" else max)(proximos, key=_centro)
        return melhor

    # -------------------------------------------------------------- principal
    def processar(self, cinza):
        cfg = self.cfg
        H, W = cinza.shape[:2]
        y0 = int(H * cfg["inicio_roi"])
        roi = cinza[y0:H]

        limiar = self.calcular_limiar(roi)
        _, mascara = cv2.threshold(roi, limiar, 255, cv2.THRESH_BINARY_INV)
        if cfg["abertura"]:
            mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, self.kernel)

        h_roi = H - y0
        hf = max(1, h_roi // self.n)
        min_pix = max(1, int(round(cfg["frac_coluna"] * hf)))
        largura_larga = cfg["largura_larga_frac"] * W
        salto_max = cfg["salto_max_frac"] * W

        pontos = []
        validos = []  # (indice_faixa, x)
        varias_linhas = False
        for i in range(self.n):
            yb = h_roi - i * hf
            ya = max(0, yb - hf)
            perfil = np.count_nonzero(mascara[ya:yb], axis=0) >= min_pix
            segs = segmentos_1d(perfil, cfg["largura_min_px"], cfg["gap_max_px"])
            varias_linhas = varias_linhas or len(segs) > 1
            previsto = self._prever(i, validos, W)
            tem_referencia = bool(validos) or self.x_ant[i] is not None
            estado, x, larg = AUSENTE, None, 0

            if segs:
                melhor = self._escolher(segs, previsto, salto_max)
                x = _centro(melhor)
                larg = melhor[1] - melhor[0] + 1
                ref_l = self.largura_ref[i]
                if tem_referencia and abs(x - previsto) > salto_max:
                    estado = AUSENTE        # salto grande: outra linha ou ruido
                elif larg > largura_larga or (ref_l is not None and larg > cfg["fator_largo"] * ref_l):
                    estado = LARGO          # linha perpendicular ou marca grande
                else:
                    estado = OK
                    self.largura_ref[i] = larg if ref_l is None else 0.8 * ref_l + 0.2 * larg

            if estado == OK:
                validos.append((i, x))
                self.x_ant[i] = x
            pontos.append((x, y0 + (ya + yb) // 2, larg, estado))

        cx = W / 2.0
        if validos:
            erro = (validos[0][1] - cx) / cx
            erro_longe = (validos[-1][1] - cx) / cx
            inclinacao = 0.0
            if len(validos) >= 2:
                ii = np.array([v[0] for v in validos], dtype=np.float64)
                xx = np.array([v[1] for v in validos], dtype=np.float64)
                di = ii - ii.mean()
                inclinacao = float((di * (xx - xx.mean())).sum() / (di * di).sum()) / cx
            self.frames_sem_linha = 0
        else:
            erro = erro_longe = None
            inclinacao = 0.0
            self.frames_sem_linha += 1
            if self.frames_sem_linha > 3:
                self.x_ant = [None] * self.n  # permite readquirir a linha em qualquer posicao

        frac_escura = float(np.count_nonzero(mascara)) / mascara.size
        return {
            "erro": erro,                  # -1 (esquerda) .. +1 (direita), faixa mais proxima
            "erro_longe": erro_longe,      # mesma escala, faixa valida mais distante
            "inclinacao": inclinacao,      # variacao de x por faixa (normalizada)
            "n_validos": len(validos),
            "cruzamento": any(p[3] == LARGO for p in pontos),
            "varias_linhas": varias_linhas,
            "marca": frac_escura >= cfg["marca_frac_escura"],
            "frac_escura": frac_escura,
            "limiar": limiar,
            "pontos": pontos,
            "y0": y0,
            "mascara": mascara,
        }
