"""Botao de desligar a Jetson e LED "pode desligar a chave" (D-028), na barra J41 da Jetson Nano.

Ligacao (placa extra hardware/placa_desligar):
  J41 pino 18 (gpio15)  <- botao para o GND, pull-up de 10k para o 3V3 (pino 17) e 1k em serie
  J41 pino 16 (gpio232) -> 10k -> base do BC337 -> LED verde (100 ohm, do 3V3) acende
LED aceso = Linux rodando. Ao desligar, o LED continua aceso ate o modulo cortar a propria energia;
APAGOU (com a chave ainda ligada) = pode desligar a chave. Nunca apagamos o LED por software.

Este modulo nao depende do programa do robo nem da ESP32: roda num servico proprio (botao-desligar.service).
Python 3.6, sem dependencias (GPIO pelo sysfs do L4T R32).
"""
import os
import time

GPIO_BOTAO = 15      # J41 pino 18 (SPI2_CS0) - o mesmo pino do exemplo de botao da NVIDIA (jetson-gpio)
GPIO_LED = 232       # J41 pino 16 (SPI2_CS1)
SEGURAR_S = 2.0      # tempo segurando o botao para desligar
SOLTO_PARA_ARMAR_S = 0.5   # so arma depois de ver o botao SOLTO por esse tempo (fio em curto nao desliga no boot)
PISCAR_S = 1.5       # LED pisca rapido por esse tempo quando o pedido e aceito; depois fica aceso


class GpioSysfs(object):
    """Um pino pelo /sys/class/gpio (base trocavel para testes)."""

    def __init__(self, numero, base='/sys/class/gpio'):
        self.numero = int(numero)
        self.base = base
        self.dir = os.path.join(base, 'gpio%d' % self.numero)

    def _escrever(self, arquivo, texto):
        with open(arquivo, 'w') as f:
            f.write(texto)

    def exportar(self, espera_s=2.0):
        if not os.path.isdir(self.dir):
            self._escrever(os.path.join(self.base, 'export'), str(self.numero))
        t0 = time.time()
        while not os.path.exists(os.path.join(self.dir, 'direction')):
            if time.time() - t0 > espera_s:
                raise IOError('gpio%d nao apareceu em %s' % (self.numero, self.base))
            time.sleep(0.05)

    def como_entrada(self):
        self._escrever(os.path.join(self.dir, 'direction'), 'in')

    def como_saida(self, valor):
        # 'high'/'low' troca a direcao e o valor de uma vez (sem pulso no pino)
        self._escrever(os.path.join(self.dir, 'direction'), 'high' if valor else 'low')

    def ler(self):
        with open(os.path.join(self.dir, 'value')) as f:
            return int(f.read().strip() or '0')

    def escrever(self, valor):
        self._escrever(os.path.join(self.dir, 'value'), '1' if valor else '0')


class MaquinaBotao(object):
    """Decide quando desligar, a partir de leituras (t, apertado). Sem E/S: testavel.

    ESPERA_SOLTO -> (solto por SOLTO_PARA_ARMAR_S) -> PRONTO -> (apertado) -> APERTADO
    APERTADO -> (soltou antes de SEGURAR_S) -> PRONTO
    APERTADO -> (segurou SEGURAR_S) -> DESLIGANDO (passo() devolve 'desligar' uma unica vez)
    """
    ESPERA_SOLTO, PRONTO, APERTADO, DESLIGANDO = 'espera_solto', 'pronto', 'apertado', 'desligando'

    def __init__(self, segurar_s=SEGURAR_S, solto_para_armar_s=SOLTO_PARA_ARMAR_S, piscar_s=PISCAR_S):
        self.segurar_s = segurar_s
        self.solto_para_armar_s = solto_para_armar_s
        self.piscar_s = piscar_s
        self.estado = self.ESPERA_SOLTO
        self.t_mudou = None
        self.t_desligou = None

    def passo(self, t, apertado):
        if self.t_mudou is None:
            self.t_mudou = t
        if self.estado == self.ESPERA_SOLTO:
            if apertado:
                self.t_mudou = t
            elif t - self.t_mudou >= self.solto_para_armar_s:
                self.estado = self.PRONTO
        elif self.estado == self.PRONTO:
            if apertado:
                self.estado, self.t_mudou = self.APERTADO, t
        elif self.estado == self.APERTADO:
            if not apertado:
                self.estado, self.t_mudou = self.PRONTO, t
            elif t - self.t_mudou >= self.segurar_s:
                self.estado, self.t_desligou = self.DESLIGANDO, t
                return 'desligar'
        return None

    def led(self, t):
        """1 = aceso. Pisca 5 Hz logo depois do pedido; fora isso, sempre aceso."""
        if self.estado == self.DESLIGANDO and t - self.t_desligou < self.piscar_s:
            return int((t - self.t_desligou) * 10) % 2 == 0
        return 1
