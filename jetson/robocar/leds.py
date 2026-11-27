"""Luz da camera e LED "codigo rodando" na placa de interface (D-033), barra J41 da Jetson Nano.

  J41 pino 15 (gpio194) -> 1k -> porta do IRLZ44N -> luz branca 5 V   ACESA = camera entregando quadros
  J41 pino 19 (gpio16)  -> 10k -> base do BC337  -> LED amarelo       PISCA = seguir_linha.py rodando o laco
                                                                     (1 Hz esperando a largada, 4 Hz andando)
O LED vermelho (J41 pino 16, "Jetson ligada / pode desligar a chave") e do servico botao-desligar, nao daqui.

Os dois pinos sao exportados como saida em 0 e liberados para o usuario pelo servico botao-desligar (root):
o programa do robo roda sem sudo. Sem os pinos (PC, servico parado) tudo vira no-op com UM aviso; o robo
anda do mesmo jeito. Python 3.6, sem dependencias.
"""
import os

from robocar.botao_desligar import GpioSysfs

GPIO_LUZ = 194       # J41 pino 15
GPIO_VIVO = 16       # J41 pino 19
PISCA_ESPERANDO_HZ = 1.0
PISCA_ANDANDO_HZ = 4.0
FALHAS_APAGA_LUZ = 5  # quadros seguidos sem imagem: apaga a luz (avisa que a camera parou)


def padrao_vivo(t, andando):
    """1 = aceso. Meio periodo aceso, meio apagado."""
    f = PISCA_ANDANDO_HZ if andando else PISCA_ESPERANDO_HZ
    return 1 if int(t * f * 2.0) % 2 == 0 else 0


class LedsRobo(object):
    def __init__(self, base='/sys/class/gpio', avisar=print, ativo=True):
        self.pinos = {}
        self.valor = {}
        faltando = []
        for nome, numero in ((('luz', GPIO_LUZ), ('vivo', GPIO_VIVO)) if ativo else ()):
            g = GpioSysfs(numero, base)
            if os.access(os.path.join(g.dir, 'value'), os.W_OK):
                self.pinos[nome] = g
            else:
                faltando.append('gpio%d' % numero)
        if faltando and avisar:
            avisar('LEDs do J41: desligados (sem %s). Normal: o painel do J41 nao e usado (D-039).' % ', '.join(faltando))

    def _por(self, nome, v):
        g = self.pinos.get(nome)
        if g is None or self.valor.get(nome) == v:
            return
        try:
            g.escrever(v)
            self.valor[nome] = v
        except (IOError, OSError):
            del self.pinos[nome]          # pino sumiu: para de tentar, o robo segue

    def luz(self, ligada):
        self._por('luz', 1 if ligada else 0)

    def vivo(self, t, andando):
        self._por('vivo', padrao_vivo(t, andando))

    def apagar(self):
        self._por('luz', 0)
        self._por('vivo', 0)
