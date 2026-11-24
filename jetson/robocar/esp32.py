"""Porta serial com a ESP32 (E/S). O formato das mensagens fica em protocolo.py.

Requer pyserial:  sudo apt install python3-serial
"""

import time

from . import protocolo


def _abrir(serial, porta, baud):
    ser = serial.Serial()
    ser.port = porta
    ser.baudrate = baud
    ser.timeout = 0
    ser.write_timeout = 0
    ser.dtr = False  # evita reset da placa ao abrir (nem toda placa respeita)
    ser.rts = False
    ser.exclusive = True  # dois programas na mesma porta misturam comandos e telemetria (21/11/2026)
    ser.open()
    return ser


def recebe_linha_valida(ser, tempo_s=1.0, relogio=time.time, dormir=time.sleep):
    """True se chegar alguma linha '$...*HH' com checksum certo em tempo_s (a ESP32 manda $T a cada 20 ms)."""
    fim = relogio() + tempo_s
    buf = ""
    while relogio() < fim:
        n = ser.in_waiting
        if n:
            buf += ser.read(n).decode("ascii", "ignore")
            linhas = buf.split("\n")
            buf = linhas.pop()
            if any(protocolo.validar(l) for l in linhas):
                return True
            buf = buf[-200:]
        dormir(0.02)
    return False


def abrir_porta(porta, baud=115200, esperar_boot_s=1.5, tentativas=4):
    """Abre a porta serial real (pyserial) e confere se a telemetria chega legivel.

    Na Jetson Nano (kernel 4.9, chip CP2102 da ESP32), a primeira abertura depois de ligar o USB as vezes
    recebe os dados embaralhados, como se a velocidade nao tivesse sido programada no chip (21/11/2026).
    Abrir a porta em outra velocidade e voltar resolve: e o que se faz aqui antes de desistir.
    """
    import serial  # importado aqui: o resto do software funciona sem pyserial
    ser = None
    for tentativa in range(1, tentativas + 1):
        if tentativa > 1:
            print("AVISO: nada legivel da ESP32 em %s; reabrindo a porta (%d/%d)..."
                  % (porta, tentativa - 1, tentativas - 1))
            ser.close()
            outra = _abrir(serial, porta, 9600)  # forca o driver a reprogramar a velocidade do chip USB-serial
            time.sleep(0.2)
            outra.close()
            ser = _abrir(serial, porta, baud)
        else:
            ser = _abrir(serial, porta, baud)
        time.sleep(esperar_boot_s)  # abrir a porta pode reiniciar a ESP32 (ela volta em ~1 s)
        ser.reset_input_buffer()
        if recebe_linha_valida(ser):
            if tentativa > 1:
                print("Porta serial OK depois de reabrir.")
            ser.reset_input_buffer()
            return ser
    print("AVISO: a ESP32 nao mandou nada legivel. Confira se o firmware gravado e o robocar_esp32.")
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
