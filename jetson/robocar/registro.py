"""Registro de testes em dados/: log CSV por quadro, gravacao dos quadros crus e fotos de depuracao."""

import os
import threading
import time

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
    """CSV por quadro que sobrevive a um corte de energia.

    Antes, o log so ia para o cartao quando o sistema resolvia (dezenas de segundos) e um corte da
    chave perdia a corrida inteira (o log 20261121_204647.csv ficou so com o cabecalho). Agora:
    flush a cada 'intervalo_flush_s' (barato, no laco principal) e fsync numa thread separada a cada
    'intervalo_fsync_s' (o fsync no microSD pode demorar dezenas de ms e nao pode travar o controle).
    Num corte, perde-se no maximo ~intervalo_fsync_s + intervalo_flush_s.
    """

    def __init__(self, caminho, intervalo_flush_s=0.5, intervalo_fsync_s=2.0):
        self.caminho = caminho
        self.f = open(caminho, "w")
        self.f.write(",".join(CAMPOS_LOG) + "\n")
        self.intervalo_flush_s = intervalo_flush_s
        self.t_flush = 0.0
        self._lock = threading.Lock()
        self._fim = threading.Event()
        self._thread = None
        if intervalo_fsync_s and intervalo_fsync_s > 0:
            self._thread = threading.Thread(target=self._sincronizar, args=(intervalo_fsync_s,))
            self._thread.daemon = True
            self._thread.start()

    def _sincronizar(self, intervalo):
        while not self._fim.wait(intervalo):
            try:
                with self._lock:
                    fd = self.f.fileno()
                os.fsync(fd)
            except (OSError, ValueError):
                return

    def escrever(self, **valores):
        with self._lock:
            self.f.write(",".join(_fmt(valores.get(c)) for c in CAMPOS_LOG) + "\n")
            agora = time.time()
            if agora - self.t_flush >= self.intervalo_flush_s:
                self.f.flush()
                self.t_flush = agora

    def fechar(self):
        self._fim.set()
        if self._thread:
            self._thread.join(1.0)
        with self._lock:
            self.f.flush()
            try:
                os.fsync(self.f.fileno())
            except OSError:
                pass
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


class FotosDebug(object):
    """Salva a imagem de depuracao (imagem + mascara) sem janela: para trabalhar so por SSH.

    Salva a cada 'periodo_s' e tambem nos eventos (largada, linha sumiu, parou), ate 'max_fotos'.
    Os arquivos ficam em dados/capturas/<sessao>/NNNN_<motivo>.jpg (traga para o PC com scp).
    """

    def __init__(self, pasta, periodo_s, max_fotos=400):
        self.pasta = pasta
        if not os.path.isdir(pasta):
            os.makedirs(pasta)
        self.periodo_s = float(periodo_s)
        self.max_fotos = int(max_fotos)
        self.n = 0
        self.t_ult = None

    def talvez_salvar(self, t, gerar_imagem, motivo=None):
        """gerar_imagem: funcao sem argumentos que devolve a imagem (so e chamada se for salvar)."""
        if self.n >= self.max_fotos:
            return None
        periodica = self.periodo_s > 0 and (self.t_ult is None or t - self.t_ult >= self.periodo_s)
        if not (periodica or motivo):
            return None
        if periodica:
            self.t_ult = t
        self.n += 1
        caminho = os.path.join(self.pasta, "%04d_%s.jpg" % (self.n, motivo or "periodica"))
        cv2.imwrite(caminho, gerar_imagem(), [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        return caminho
