"""Log CSV que sobrevive a corte de energia, fotos de depuracao sem janela e opcoes da camera."""
import os
import shutil
import tempfile
import unittest

import numpy as np

from robocar import camera, desenho, registro
from robocar.visao import DetectorLinha
from robocar import configuracao
from testes import sintetico


class TestLogCSV(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.caminho = os.path.join(self.pasta, "log.csv")

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def test_linhas_chegam_ao_arquivo_sem_fechar(self):
        log = registro.LogCSV(self.caminho, intervalo_flush_s=0.0, intervalo_fsync_s=0.05)
        log.escrever(t=1.5, estado="SEGUINDO", erro=0.25)
        with open(self.caminho) as f:           # outro leitor (= o que sobra no cartao num corte)
            linhas = f.read().splitlines()
        self.assertEqual(len(linhas), 2)
        self.assertTrue(linhas[1].startswith("1.5000,"))
        log.fechar()

    def test_fechar_grava_tudo(self):
        log = registro.LogCSV(self.caminho)
        for k in range(100):
            log.escrever(t=float(k))
        log.fechar()
        with open(self.caminho) as f:
            self.assertEqual(len(f.read().splitlines()), 101)


class TestFotosDebug(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def test_periodicas_eventos_e_limite(self):
        f = registro.FotosDebug(os.path.join(self.pasta, "sessao"), periodo_s=1.0, max_fotos=4)
        img = lambda: np.zeros((10, 20, 3), np.uint8)
        self.assertIsNotNone(f.talvez_salvar(0.0, img))            # primeira periodica
        self.assertIsNone(f.talvez_salvar(0.5, img))               # cedo demais
        self.assertTrue(f.talvez_salvar(0.6, img, "parado").endswith("_parado.jpg"))   # evento: sempre
        self.assertIsNotNone(f.talvez_salvar(1.0, img))
        self.assertIsNotNone(f.talvez_salvar(1.1, img, "buscando"))
        self.assertIsNone(f.talvez_salvar(5.0, img, "parado"))     # chegou no limite
        self.assertEqual(len(os.listdir(os.path.join(self.pasta, "sessao"))), 4)

    def test_painel_imagem_e_mascara_lado_a_lado(self):
        cfg = configuracao.carregar_config()
        det = DetectorLinha(cfg["visao"], sintetico.CALIBRACAO)
        cinza = sintetico.Cena().linha(sintetico.vertical(160)).imagem()
        painel = desenho.painel_debug(cinza, det.processar(cinza), [("teste", desenho.BRANCO)])
        self.assertEqual(painel.shape, (2 * cinza.shape[0], 4 * cinza.shape[1], 3))


class TestPipelineCamera(unittest.TestCase):

    def test_travas_de_exposicao_e_balanco(self):
        base = dict(sensor_id=0, captura_largura=1280, captura_altura=720, fps=60, flip_method=0,
                    saida_largura=320, saida_altura=180)
        p = camera.gstreamer_pipeline(trava_auto_exposicao=True, trava_balanco_branco=True,
                                      exposicao_ns=2000000, **base)
        self.assertIn("aelock=true", p)
        self.assertIn("awblock=true", p)
        self.assertIn('exposuretimerange="2000000 2000000"', p)
        self.assertNotIn("awblock", camera.gstreamer_pipeline(**base))


if __name__ == "__main__":
    unittest.main()
