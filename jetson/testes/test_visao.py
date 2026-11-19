import unittest

from robocar.visao import DetectorLinha, segmentos_1d
from testes.sintetico import CALIBRACAO, Cena, H, W, config, curva, vertical

import numpy as np


def detector(**ajustes):
    return DetectorLinha(config(**ajustes)["visao"], CALIBRACAO)


def aquecer(det, x, quadros=3):
    """Simula alguns quadros de reta antes do cenario (o detector usa o historico)."""
    for _ in range(quadros):
        det.processar(Cena().linha(vertical(x)).imagem())


class TestSegmentos(unittest.TestCase):

    def test_une_buracos_pequenos_e_descarta_curtos(self):
        perfil = np.array([0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0], bool)
        self.assertEqual(segmentos_1d(perfil, largura_min=2, gap_max=1), [(1, 5)])

    def test_vazio(self):
        self.assertEqual(segmentos_1d(np.zeros(10, bool)), [])


class TestDeteccao(unittest.TestCase):

    def test_reta_centralizada(self):
        r = detector().processar(Cena().linha(vertical(160)).imagem())
        self.assertAlmostEqual(r["erro"], 0.0, delta=0.05)
        self.assertEqual(r["n_validos"], 4)

    def test_reta_a_direita(self):
        r = detector().processar(Cena().linha(vertical(220)).imagem())
        self.assertAlmostEqual(r["erro"], (220 - 160) / 160.0, delta=0.05)

    def test_curva_antecipada(self):
        r = detector().processar(Cena().linha(curva(160, 40)).imagem())
        self.assertLess(r["erro_longe"], r["erro"] - 0.1, "a faixa distante deve ver a curva antes")

    def test_cruzamento_perpendicular(self):
        d = detector()
        aquecer(d, 170)
        r = d.processar(Cena().linha(vertical(170)).linha([(0, 150), (W, 150)]).imagem())
        self.assertTrue(r["cruzamento"])
        self.assertAlmostEqual(r["erro"], (170 - 160) / 160.0, delta=0.05)

    def test_intersecao_em_x_segue_a_mesma_linha(self):
        d = detector()
        aquecer(d, 160)
        r = d.processar(Cena().linha(vertical(160)).linha([(60, H), (260, 0)]).imagem())
        self.assertAlmostEqual(r["erro"], 0.0, delta=0.08)
        self.assertAlmostEqual(r["erro_longe"], 0.0, delta=0.08)

    def test_sem_linha(self):
        r = detector().processar(Cena().imagem())
        self.assertIsNone(r["erro"])
        self.assertEqual(r["n_validos"], 0)

    def test_marca_grande_sinalizada_e_linha_comum_nao(self):
        com_marca = detector().processar(
            Cena().linha(vertical(160)).retangulo((40, 90), (280, H)).imagem())
        so_linha = detector().processar(Cena().linha(vertical(160)).imagem())
        self.assertTrue(com_marca["marca"])
        self.assertFalse(so_linha["marca"])


class TestIluminacao(unittest.TestCase):
    """O limiar adaptativo deve funcionar onde o limiar fixo do codigo original (60,5) falha."""

    def _cenario(self, brilho, cor_linha):
        return Cena(brilho=brilho).linha(vertical(150), cor=cor_linha).imagem()

    def _detecta(self, r):
        return r["erro"] is not None and abs(r["erro"] + 0.0625) < 0.05 and r["n_validos"] >= 3

    def test_pouca_luz(self):
        img = self._cenario(70, 14)
        self.assertTrue(self._detecta(detector().processar(img)))
        self.assertFalse(self._detecta(detector(limiar_modo="fixo", limiar_fixo=60.5).processar(img)))

    def test_exposicao_alta(self):
        img = self._cenario(250, 130)
        self.assertTrue(self._detecta(detector().processar(img)))
        self.assertFalse(self._detecta(detector(limiar_modo="fixo", limiar_fixo=60.5).processar(img)))

    def test_sombra_lateral(self):
        img = Cena(gradiente=(0.45, 1.0)).linha(vertical(80)).imagem()
        r = detector().processar(img)
        self.assertAlmostEqual(r["erro"], -0.5, delta=0.05)


if __name__ == "__main__":
    unittest.main()
