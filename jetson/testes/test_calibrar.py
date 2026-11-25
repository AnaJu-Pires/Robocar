import unittest

import calibrar
from testes.sintetico import Cena, vertical


class TestCalibracaoAutomatica(unittest.TestCase):

    def test_linha_e_chao_visiveis(self):
        rois = [Cena(brilho=200, semente=i).linha(vertical(160), cor=40).imagem()[100:] for i in range(10)]
        branco, preto, n = calibrar.calibrar_quadros(rois)
        self.assertEqual(n, 10)
        self.assertAlmostEqual(branco, 200, delta=6)
        self.assertAlmostEqual(preto, 40, delta=6)

    def test_so_chao_falha(self):
        rois = [Cena(brilho=200, semente=i).imagem()[100:] for i in range(10)]
        self.assertIsNone(calibrar.calibrar_quadros(rois))

    def test_sem_quadros(self):
        self.assertIsNone(calibrar.calibrar_quadros([]))


if __name__ == "__main__":
    unittest.main()
