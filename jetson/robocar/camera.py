"""Captura de imagem: camera CSI da Jetson (GStreamer) ou webcam/video para testes.

Decisoes (ver docs/decisoes.md, D-004):
  * appsink drop=true max-buffers=1 sync=false -> sempre o quadro MAIS RECENTE
    (no codigo original a fila era ilimitada e a latencia podia crescer sem limite);
  * reducao para 320x180 e conversao para cinza (GRAY8) no hardware (nvvidconv),
    sem videoconvert nem cvtColor na CPU;
  * fallback automatico: GRAY8 -> BGR, e sem as propriedades de exposicao se o L4T recusar.
"""

import cv2


def gstreamer_pipeline(sensor_id, captura_largura, captura_altura, fps, flip_method,
                       saida_largura, saida_altura, formato="GRAY8", exposicao_ns=None,
                       ganho=None, trava_auto_exposicao=False, trava_balanco_branco=False):
    props = ["sensor-id=%d" % sensor_id]
    if exposicao_ns:
        props.append('exposuretimerange="%d %d"' % (int(exposicao_ns), int(exposicao_ns)))
    if ganho:
        props.append('gainrange="%s %s"' % (ganho, ganho))
    if trava_auto_exposicao:
        props.append("aelock=true")
    if trava_balanco_branco:
        props.append("awblock=true")

    if formato == "GRAY8":
        conversao = "video/x-raw, width=(int)%d, height=(int)%d, format=(string)GRAY8 ! " % (
            saida_largura, saida_altura)
    else:
        conversao = ("video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
                     "videoconvert ! video/x-raw, format=(string)BGR ! ") % (saida_largura, saida_altura)

    return ("nvarguscamerasrc %s ! "
            "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! %s"
            "appsink drop=true max-buffers=1 sync=false"
            % (" ".join(props), captura_largura, captura_altura, fps, flip_method, conversao))


class Camera(object):
    """Fornece quadros em escala de cinza (uint8, altura x largura)."""

    def __init__(self, cfg_camera, fonte=None):
        self.cfg = cfg_camera
        self.fonte = fonte if fonte is not None else cfg_camera["fonte"]
        self.cap = None
        self.descricao = ""
        self.eh_arquivo = False
        self._abrir()

    def _abrir(self):
        fonte = self.fonte
        if isinstance(fonte, str) and fonte.isdigit():
            fonte = int(fonte)
        if fonte == "csi":
            self._abrir_csi()
        else:
            self.cap = cv2.VideoCapture(fonte)
            self.eh_arquivo = not isinstance(fonte, int)
            self.descricao = ("arquivo %s" if self.eh_arquivo else "webcam %s") % fonte
        if self.cap is None or not self.cap.isOpened():
            raise RuntimeError("Nao foi possivel abrir a camera/fonte: %s" % self.fonte)

    def _abrir_csi(self):
        c = self.cfg
        base = dict(sensor_id=c["sensor_id"], captura_largura=c["captura_largura"],
                    captura_altura=c["captura_altura"], fps=c["fps"], flip_method=c["flip_method"],
                    saida_largura=c["saida_largura"], saida_altura=c["saida_altura"])
        extras = dict(exposicao_ns=c["exposicao_ns"], ganho=c["ganho"],
                      trava_auto_exposicao=c["trava_auto_exposicao"],
                      trava_balanco_branco=c["trava_balanco_branco"])
        tem_extras = any(extras.values())
        tentativas = []
        for formato in ("GRAY8", "BGR"):
            if tem_extras:
                tentativas.append((formato, extras))
            tentativas.append((formato, {}))

        for formato, ext in tentativas:
            args = dict(base)
            args.update(ext)
            cap = cv2.VideoCapture(gstreamer_pipeline(formato=formato, **args), cv2.CAP_GSTREAMER)
            if cap.isOpened():
                self.cap = cap
                self.descricao = "CSI %dx%d@%d -> %dx%d %s%s" % (
                    base["captura_largura"], base["captura_altura"], base["fps"],
                    base["saida_largura"], base["saida_altura"], formato,
                    " (exposicao/ganho manuais)" if ext else "")
                if tem_extras and not ext:
                    print("AVISO: exposicao/ganho manuais nao aceitos por este L4T; usando automatico.")
                return
            cap.release()

    def ler(self):
        """Retorna (ok, cinza)."""
        ok, quadro = self.cap.read()
        if not ok or quadro is None:
            return False, None
        if quadro.ndim == 3:
            quadro = cv2.cvtColor(quadro, cv2.COLOR_BGR2GRAY)
        largura = self.cfg["saida_largura"]
        if quadro.shape[1] != largura:  # webcam/arquivo: reduz mantendo a proporcao
            altura = int(round(quadro.shape[0] * largura / float(quadro.shape[1])))
            quadro = cv2.resize(quadro, (largura, altura), interpolation=cv2.INTER_AREA)
        return True, quadro

    def liberar(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
