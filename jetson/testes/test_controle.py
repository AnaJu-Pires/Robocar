import unittest

from robocar import configuracao, controle


def det(erro, erro_longe=None, marca=False):
    return {"erro": erro, "erro_longe": erro if erro_longe is None else erro_longe, "marca": marca}


class TestControlador(unittest.TestCase):

    def setUp(self):
        cfg = configuracao.carregar_config(ajustes={"parada": {
            "usar_marca": True, "tempo_minimo_s": 1.0, "frames_confirmacao": 2, "atraso_s": 0.0}})
        self.cfg = cfg
        self.c = controle.Controlador(cfg["controle"], cfg["parada"])

    def test_parado_ate_iniciar(self):
        self.assertEqual(self.c.atualizar(det(0.3), 0.0)[:2], (0.0, 0.0))

    def test_linha_a_direita_acelera_roda_esquerda(self):
        self.c.iniciar(0.0)
        esq, dir_, _ = self.c.atualizar(det(0.3, 0.4), 0.02)
        self.assertGreater(esq, dir_)

    def test_comandos_limitados(self):
        self.c.iniciar(0.0)
        esq, dir_, _ = self.c.atualizar(det(1.0, 1.0), 0.02)
        self.assertLessEqual(max(abs(esq), abs(dir_)), 1.0)

    def test_reduz_velocidade_em_curva(self):
        self.c.iniciar(0.0)
        _, _, reta = self.c.atualizar(det(0.0, 0.0), 0.02)
        _, _, curva = self.c.atualizar(det(0.0, 0.6), 0.04)
        self.assertLess(curva["v"], reta["v"])

    def test_linha_perdida_busca_e_depois_para(self):
        self.c.iniciar(0.0)
        self.c.atualizar(det(0.3), 0.02)
        esq, dir_, _ = self.c.atualizar(det(None), 0.05)
        self.assertEqual(self.c.estado, controle.BUSCANDO)
        self.assertTrue(esq > 0 > dir_, "deve girar para o ultimo lado visto (direita)")
        self.c.atualizar(det(None), 0.05 + self.cfg["controle"]["tempo_busca_s"] + 0.01)
        self.assertEqual(self.c.estado, controle.PARADO)

    def test_marca_ignorada_antes_do_tempo_minimo(self):
        self.c.iniciar(0.0)
        self.c.atualizar(det(0.0, marca=True), 0.5)
        self.c.atualizar(det(0.0, marca=True), 0.6)
        self.assertEqual(self.c.estado, controle.SEGUINDO)

    def test_marca_confirmada_para_no_box(self):
        self.c.iniciar(0.0)
        self.c.atualizar(det(0.0, marca=True), 1.1)
        self.c.atualizar(det(0.0, marca=True), 1.2)
        self.assertEqual(self.c.estado, controle.PARADO)


if __name__ == "__main__":
    unittest.main()
