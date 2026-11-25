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


class TestCalibracaoRuim(unittest.TestCase):
    """Caso real de 22/11/2026: calibracao 106/66 (razao 0,81) e fita brilhante. Com um reflexo claro
    na imagem, o limiar (81 % do "branco") ficava acima do chao: o chao virava "escuro" e a linha sumia."""

    CAL_RUIM = {"branco": 106.0, "preto": 66.0, "limiar": 86.0, "razao": 0.81}

    def _cena(self):
        # chao 150, reflexo 200 na lateral direita (eleva o "branco"), fita acinzentada (90) em x = 120
        return Cena(brilho=150).retangulo((260, 0), (319, H), cor=200).linha(vertical(120), cor=90).imagem()

    def test_razao_da_calibracao_e_limitada(self):
        det = DetectorLinha(config()["visao"], self.CAL_RUIM)
        self.assertAlmostEqual(det.razao_calibrada, 0.81)
        self.assertAlmostEqual(det.razao, 0.70)

    def test_linha_encontrada_com_a_razao_limitada(self):
        r = DetectorLinha(config()["visao"], self.CAL_RUIM).processar(self._cena())
        self.assertIsNotNone(r["erro"])
        self.assertAlmostEqual(r["erro"], -0.25, delta=0.05)
        self.assertFalse(r["cruzamento"])

    def test_sem_limite_o_chao_vira_linha(self):
        det = DetectorLinha(config(razao_max=1.0)["visao"], self.CAL_RUIM)
        r = det.processar(self._cena())
        self.assertTrue(r["erro"] is None or r["cruzamento"] or abs(r["erro"] + 0.25) > 0.05)


class TestSuavizacaoDoLimiar(unittest.TestCase):

    def test_limiar_muda_aos_poucos(self):
        det = detector()
        claro = det.processar(Cena(brilho=200).linha(vertical(160)).imagem())["limiar"]
        escuro = det.processar(Cena(brilho=120).linha(vertical(160)).imagem())["limiar"]
        cru = detector().processar(Cena(brilho=120).linha(vertical(160)).imagem())["limiar"]
        self.assertGreater(escuro, cru)       # nao pulou direto para o valor novo
        self.assertLess(escuro, claro)        # mas ja andou na direcao certa

    def test_sem_suavizacao(self):
        det = detector(suavizar_limiar=1.0)
        det.processar(Cena(brilho=200).linha(vertical(160)).imagem())
        escuro = det.processar(Cena(brilho=120).linha(vertical(160)).imagem())["limiar"]
        cru = detector().processar(Cena(brilho=120).linha(vertical(160)).imagem())["limiar"]
        self.assertAlmostEqual(escuro, cru)


if __name__ == "__main__":
    unittest.main()
