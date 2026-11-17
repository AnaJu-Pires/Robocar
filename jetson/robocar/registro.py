"""Registro de testes em dados/: log CSV por quadro e gravacao dos quadros crus."""

import cv2

CAMPOS_LOG = ["t", "proc_ms", "erro", "erro_longe", "inclinacao", "n_validos", "cruzamento",
              "marca", "limiar", "estado", "v", "u", "esq", "dir", "vbat", "enc_e", "enc_d",
              "estado_esp32"]


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return "%.4f" % v
    return str(v)


class LogCSV(object):

    def __init__(self, caminho):
        self.caminho = caminho
        self.f = open(caminho, "w")
        self.f.write(",".join(CAMPOS_LOG) + "\n")

    def escrever(self, **valores):
        self.f.write(",".join(_fmt(valores.get(c)) for c in CAMPOS_LOG) + "\n")

    def fechar(self):
        self.f.close()


class GravadorVideo(object):
    """Grava quadros em cinza (MJPG) para reprocessar depois com --fonte."""

    def __init__(self, caminho, fps):
        self.caminho = caminho
        self.fps = float(fps)
        self.vw = None

    def escrever(self, cinza):
        if self.vw is None:
            self.vw = cv2.VideoWriter(self.caminho, cv2.VideoWriter_fourcc(*"MJPG"), self.fps,
                                      (cinza.shape[1], cinza.shape[0]))
        self.vw.write(cv2.cvtColor(cinza, cv2.COLOR_GRAY2BGR))

    def fechar(self):
        if self.vw is not None:
            self.vw.release()
