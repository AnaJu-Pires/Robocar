"""Porta serial com a ESP32 (E/S). O formato das mensagens fica em protocolo.py.

Requer pyserial:  sudo apt install python3-serial
"""

import time

from . import protocolo


def abrir_porta(porta, baud=115200, esperar_boot_s=1.5):
    """Abre a porta serial real (pyserial)."""
    import serial  # importado aqui: o resto do software funciona sem pyserial
    ser = serial.Serial()
    ser.port = porta
    ser.baudrate = baud
    ser.timeout = 0
    ser.write_timeout = 0
    ser.dtr = False  # evita reset da placa ao abrir (nem toda placa respeita)
    ser.rts = False
    ser.open()
    time.sleep(esperar_boot_s)  # a placa pode reiniciar ao abrir a porta
    ser.reset_input_buffer()
    return ser


class LinkESP32(object):
    """Recebe um objeto do tipo serial ja aberto (real ou falso, nos testes)."""

    def __init__(self, ser):
        self.ser = ser
        self.seq = 0
        self.buf = ""
        self.telemetria = None
        self.t_telemetria = 0.0
        self.versao_firmware = None
        self.linhas_invalidas = 0

    def _escrever(self, mensagem):
        try:
            self.ser.write(mensagem.encode("ascii"))
        except Exception as e:  # buffer cheio/desconexao: o watchdog da ESP32 freia o robo
            print("AVISO serial:", e)

    def enviar_motores(self, esq, dir_):
        self.seq += 1
        self._escrever(protocolo.cmd_motores(self.seq, esq, dir_))

    def parar(self):
        self._escrever(protocolo.cmd_parar())

    def armar(self):
        self._escrever(protocolo.cmd_armar())

    def pedir_versao(self):
        self._escrever(protocolo.cmd_versao())

    def ler(self):
        """Processa o que chegou (nao bloqueia); atualiza self.telemetria."""
        try:
            n = self.ser.in_waiting
            if n:
                self.buf += self.ser.read(n).decode("ascii", "ignore")
        except Exception as e:
            print("AVISO serial:", e)
            return
        while "\n" in self.buf:
            linha, self.buf = self.buf.split("\n", 1)
            corpo = protocolo.validar(linha)
            msg = protocolo.interpretar(corpo) if corpo else None
            if msg is None:
                if linha.strip():
                    self.linhas_invalidas += 1
                continue
            if msg["tipo"] == "T":
                self.telemetria = msg
                self.t_telemetria = time.time()
            else:
                print("ESP32:", msg["texto"])
                if msg["versao"] is not None:
                    self.versao_firmware = msg["versao"]
                    if msg["versao"] != protocolo.VERSAO:
                        print("ERRO: firmware usa protocolo v%d, Jetson usa v%d - regrave a ESP32."
                              % (msg["versao"], protocolo.VERSAO))
        if len(self.buf) > 512:
            self.buf = ""

    def fechar(self):
        try:
            self.parar()
            time.sleep(0.05)
            self.ser.close()
        except Exception:
            pass
