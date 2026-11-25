"""Botao de desligar a Jetson e LED pode-desligar (robocar/botao_desligar.py e servico/botao_desligar.py)."""
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from robocar.botao_desligar import GpioSysfs, MaquinaBotao, GPIO_BOTAO, GPIO_LED

AQUI = os.path.dirname(os.path.abspath(__file__))
PROGRAMA = os.path.join(AQUI, '..', 'servico', 'botao_desligar.py')


def gravar(caminho, texto):
    with open(caminho, 'w') as f:
        f.write(texto)


def sysfs_falso(base, valor_botao='1'):
    gravar(os.path.join(base, 'export'), '')
    for n, val in ((GPIO_BOTAO, valor_botao), (GPIO_LED, '0')):
        d = os.path.join(base, 'gpio%d' % n)
        os.makedirs(d)
        gravar(os.path.join(d, 'direction'), 'in')
        gravar(os.path.join(d, 'value'), val)


def ler(base, n, arq):
    with open(os.path.join(base, 'gpio%d' % n, arq)) as f:
        return f.read().strip()


class TestMaquina(unittest.TestCase):
    def rodar(self, seq, maq=None):
        maq = maq or MaquinaBotao(segurar_s=2.0, solto_para_armar_s=0.5)
        acoes = []
        for t, ap in seq:
            if maq.passo(t, ap) == 'desligar':
                acoes.append(t)
        return maq, acoes

    def test_segurar_2s_desliga_uma_vez(self):
        seq = [(t / 20.0, False) for t in range(0, 20)] + [(1 + t / 20.0, True) for t in range(0, 80)]
        maq, acoes = self.rodar(seq)
        self.assertEqual(len(acoes), 1)
        self.assertAlmostEqual(acoes[0], 3.0, delta=0.06)
        self.assertEqual(maq.estado, maq.DESLIGANDO)

    def test_aperto_curto_nao_desliga(self):
        seq = [(t / 20.0, False) for t in range(0, 20)] + [(1 + t / 20.0, True) for t in range(0, 30)] + \
              [(2.5 + t / 20.0, False) for t in range(0, 40)]
        _, acoes = self.rodar(seq)
        self.assertEqual(acoes, [])

    def test_botao_em_curto_no_boot_nao_desliga(self):
        # fio em curto (ou botao apertado ao ligar): nunca chegou a ver o botao solto -> nao desliga
        seq = [(t / 20.0, True) for t in range(0, 200)]
        maq, acoes = self.rodar(seq)
        self.assertEqual(acoes, [])
        self.assertEqual(maq.estado, maq.ESPERA_SOLTO)

    def test_led_pisca_e_fica_aceso(self):
        seq = [(t / 20.0, False) for t in range(0, 20)] + [(1 + t / 20.0, True) for t in range(0, 41)]
        maq, acoes = self.rodar(seq)
        t0 = acoes[0]
        estados = [maq.led(t0 + k / 100.0) for k in range(0, 150)]
        self.assertIn(0, estados)                 # pisca
        self.assertEqual(maq.led(t0 + 5.0), 1)    # depois fica aceso ate a energia cair
        self.assertEqual(MaquinaBotao().led(0.0), 1)


class TestGpioSysfs(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        sysfs_falso(self.base)

    def tearDown(self):
        shutil.rmtree(self.base)

    def test_direcao_e_valor(self):
        led = GpioSysfs(GPIO_LED, self.base)
        led.exportar()
        led.como_saida(1)
        self.assertEqual(ler(self.base, GPIO_LED, 'direction'), 'high')
        b = GpioSysfs(GPIO_BOTAO, self.base)
        b.exportar(); b.como_entrada()
        self.assertEqual(b.ler(), 1)

    def test_exportar_sem_pasta_da_erro(self):
        g = GpioSysfs(77, self.base)
        with self.assertRaises(IOError):
            g.exportar(espera_s=0.1)


class TestPrograma(unittest.TestCase):
    """Roda o programa de verdade contra um sysfs falso e um comando de desligar falso."""

    def setUp(self):
        self.base = tempfile.mkdtemp()
        sysfs_falso(self.base)
        self.marca = os.path.join(self.base, 'desligou')

    def tearDown(self):
        shutil.rmtree(self.base)

    def apertar_depois(self, atraso, duracao):
        def f():
            time.sleep(atraso)
            gravar(os.path.join(self.base, 'gpio%d' % GPIO_BOTAO, 'value'), '0')
            time.sleep(duracao)
            gravar(os.path.join(self.base, 'gpio%d' % GPIO_BOTAO, 'value'), '1')
        th = threading.Thread(target=f); th.start()
        return th

    def test_desliga_e_deixa_led_aceso(self):
        th = self.apertar_depois(0.8, 1.2)
        r = subprocess.run([sys.executable, PROGRAMA, '--sysfs', self.base, '--segurar', '0.6', '--uma-vez',
                            '--comando', 'touch %s' % self.marca], stdout=subprocess.PIPE, timeout=15)
        th.join()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(os.path.exists(self.marca), 'nao chamou o comando de desligar')
        self.assertEqual(ler(self.base, GPIO_LED, 'value'), '1')
        self.assertIn(b'desligando', r.stdout)

    def test_sigterm_deixa_led_aceso(self):
        p = subprocess.Popen([sys.executable, PROGRAMA, '--sysfs', self.base, '--comando', 'true'],
                             stdout=subprocess.PIPE)
        time.sleep(0.6)
        gravar(os.path.join(self.base, 'gpio%d' % GPIO_LED, 'value'), '0')   # alguem apagou
        p.terminate(); p.wait(timeout=5); p.stdout.close()
        self.assertEqual(p.returncode, 0)
        self.assertEqual(ler(self.base, GPIO_LED, 'value'), '1')


if __name__ == '__main__':
    unittest.main()
