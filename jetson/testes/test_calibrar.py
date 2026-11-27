import unittest

import calibrar
from robocar import configuracao
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


class TestExposicaoNaCalibracao(unittest.TestCase):

    def test_teclas_e_g_percorrem_e_voltam(self):
        self.assertEqual(calibrar.proximo(calibrar.EXPOSICOES_NS, None), 1000000)
        self.assertIsNone(calibrar.proximo(calibrar.EXPOSICOES_NS, calibrar.EXPOSICOES_NS[-1]))
        self.assertIsNone(calibrar.proximo(calibrar.GANHOS, 5))          # valor fora da lista: volta ao auto
        self.assertEqual(calibrar.texto_exposicao(3000000, None), "exposicao 3 ms  ganho auto")

    def test_tela_com_linhas_extras(self):
        cinza = Cena().linha(vertical(160)).imagem()
        img = calibrar.desenhar(cinza, (0, 80, 320, 180), 120.0, 200.0, 40.0, "inferior",
                                [("Camera: exposicao 3 ms", (255, 200, 0))])
        self.assertEqual(img.shape, (360, 640, 3))

    def test_seguidor_usa_a_exposicao_da_calibracao(self):
        base = configuracao.carregar_config()["camera"]
        cam, texto = configuracao.camera_com_calibracao(base, {"razao": 0.6, "exposicao_ns": 3000000, "ganho": 4})
        self.assertEqual((cam["exposicao_ns"], cam["ganho"], cam["trava_balanco_branco"]), (3000000, 4, True))
        self.assertIn("3.0 ms", texto)
        self.assertIsNone(base["exposicao_ns"], "nao altera o dicionario original")

    def test_config_json_tem_prioridade_e_auto_nao_muda_nada(self):
        base = dict(configuracao.carregar_config()["camera"], exposicao_ns=2000000)
        cam, texto = configuracao.camera_com_calibracao(base, {"exposicao_ns": 6000000})
        self.assertEqual((cam["exposicao_ns"], texto), (2000000, ""))
        auto = configuracao.carregar_config()["camera"]
        self.assertEqual(configuracao.camera_com_calibracao(auto, {"exposicao_ns": None})[1], "")
        self.assertEqual(configuracao.camera_com_calibracao(auto, None)[1], "")


if __name__ == "__main__":
    unittest.main()
