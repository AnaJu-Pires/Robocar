"""Luz da camera e LED codigo-rodando (robocar/leds.py, D-033) contra um sysfs falso."""
import os
import shutil
import tempfile
import unittest

from robocar import leds
from robocar.leds import GPIO_LUZ, GPIO_VIVO, LedsRobo


def gravar(caminho, texto):
    with open(caminho, 'w') as f:
        f.write(texto)


class TestLeds(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        for n in (GPIO_LUZ, GPIO_VIVO):
            os.makedirs(os.path.join(self.base, 'gpio%d' % n))
            gravar(self.valor(n), '0')
        self.avisos = []

    def tearDown(self):
        shutil.rmtree(self.base)

    def valor(self, n):
        return os.path.join(self.base, 'gpio%d' % n, 'value')

    def ler(self, n):
        with open(self.valor(n)) as f:
            return f.read().strip()

    def test_luz_liga_e_apaga(self):
        l = LedsRobo(self.base, avisar=self.avisos.append)
        self.assertEqual(self.avisos, [])
        l.luz(True)
        self.assertEqual(self.ler(GPIO_LUZ), '1')
        l.luz(False)
        self.assertEqual(self.ler(GPIO_LUZ), '0')

    def test_pisca_mais_rapido_andando(self):
        def trocas(andando):
            vs = [leds.padrao_vivo(k / 100.0, andando) for k in range(200)]     # 2 s
            return sum(1 for a, b in zip(vs, vs[1:]) if a != b)
        self.assertEqual(trocas(False), 3)     # 1 Hz: aceso 0,5 s / apagado 0,5 s
        self.assertEqual(trocas(True), 15)     # 4 Hz
        l = LedsRobo(self.base, avisar=None)
        l.vivo(0.0, True)
        self.assertEqual(self.ler(GPIO_VIVO), '1')
        l.vivo(0.13, True)
        self.assertEqual(self.ler(GPIO_VIVO), '0')

    def test_apagar_deixa_tudo_em_zero(self):
        l = LedsRobo(self.base, avisar=None)
        l.luz(True); l.vivo(0.0, False)
        l.apagar()
        self.assertEqual((self.ler(GPIO_LUZ), self.ler(GPIO_VIVO)), ('0', '0'))

    def test_sem_gpio_nao_quebra_e_avisa_uma_vez(self):
        vazio = tempfile.mkdtemp()
        try:
            l = LedsRobo(vazio, avisar=self.avisos.append)
            l.luz(True); l.vivo(1.0, True); l.apagar()
        finally:
            shutil.rmtree(vazio)
        self.assertEqual(len(self.avisos), 1)
        self.assertIn('gpio%d' % GPIO_LUZ, self.avisos[0])

    def test_pino_some_no_meio_nao_quebra(self):
        l = LedsRobo(self.base, avisar=None)
        shutil.rmtree(os.path.join(self.base, 'gpio%d' % GPIO_LUZ))
        l.luz(True)                      # IOError engolido
        l.luz(False)
        self.assertNotIn('luz', l.pinos)

    def test_desativado_nao_mexe(self):
        l = LedsRobo(self.base, avisar=self.avisos.append, ativo=False)
        l.luz(True)
        self.assertEqual(self.ler(GPIO_LUZ), '0')
        self.assertEqual(self.avisos, [])


if __name__ == '__main__':
    unittest.main()
