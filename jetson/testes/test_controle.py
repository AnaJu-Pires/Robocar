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
        _, _, reta = self.c.atualizar(det(0.0, 0.0), 1.0)     # depois da rampa de largada
        _, _, curva = self.c.atualizar(det(0.0, 0.6), 1.02)
        self.assertLess(curva["v"], reta["v"])

    def test_acelera_aos_poucos_e_freia_na_hora(self):
        a = self.cfg["controle"]["acel_max"]
        self.c.iniciar(0.0)
        _, _, i1 = self.c.atualizar(det(0.0, 0.0), 0.05)
        self.assertAlmostEqual(i1["v"], min(self.cfg["controle"]["v_max"], a * 0.05), places=6)
        _, _, i2 = self.c.atualizar(det(0.0, 0.0), 2.0)
        self.assertAlmostEqual(i2["v"], self.cfg["controle"]["v_max"], places=6)
        _, _, i3 = self.c.atualizar(det(0.0, 0.6), 2.02)          # curva: cai direto para v_min
        self.assertAlmostEqual(i3["v"], self.cfg["controle"]["v_min"], places=6)

    def test_sem_limite_de_aceleracao(self):
        self.cfg["controle"]["acel_max"] = 0.0
        self.c = controle.Controlador(self.cfg["controle"], self.cfg["parada"])
        self.c.iniciar(0.0)
        _, _, i = self.c.atualizar(det(0.0, 0.0), 0.02)
        self.assertAlmostEqual(i["v"], self.cfg["controle"]["v_max"], places=6)

    def _a_lat_g(self, esq, dir_):
        c = self.cfg["controle"]
        ve, vd = esq * c["v_por_comando_m_s"], dir_ * c["v_por_comando_m_s"]
        return abs((ve + vd) / 2 * (ve - vd) / c["bitola_m"]) / 9.81

    def _em_regime(self, d, ajustes=None):
        cfg = configuracao.carregar_config(ajustes=ajustes or {})
        c = controle.Controlador(cfg["controle"], cfg["parada"])
        c.iniciar(0.0)
        out = None
        for k in range(1, 200):                       # 4 s: passa a rampa do acel_max
            out = c.atualizar(d, k * 0.02)
        return out

    def test_curva_fechada_respeita_limite_lateral(self):
        # correcao forte (linha bem a direita): sem o limite daria > 1 g com o v4 (que tomba com ~0,77 g)
        esq, dir_, info = self._em_regime(det(0.5, 0.6), {"controle": {"v_max": 0.6, "v_min": 0.5}})
        self.assertLessEqual(self._a_lat_g(esq, dir_), self.cfg["controle"]["a_lat_max_g"] + 1e-6)
        self.assertAlmostEqual(info["a_lat_g"], self.cfg["controle"]["a_lat_max_g"], places=6)

    def test_limite_mantem_o_raio_da_curva(self):
        a = self._em_regime(det(0.5, 0.6), {"controle": {"v_max": 0.6, "v_min": 0.5}})
        b = self._em_regime(det(0.5, 0.6), {"controle": {"v_max": 0.6, "v_min": 0.5, "a_lat_max_g": 0}})
        self.assertGreater(self._a_lat_g(b[0], b[1]), self.cfg["controle"]["a_lat_max_g"])   # sem limite: passaria
        # mesmas proporcoes entre as rodas (mesmo raio), so mais devagar
        self.assertAlmostEqual(a[0] / a[1], b[0] / b[1], places=6)
        self.assertLess(abs(a[0]), abs(b[0]))

    def test_reta_nao_e_afetada_pelo_limite(self):
        esq, dir_, info = self._em_regime(det(0.0, 0.0))
        self.assertAlmostEqual(esq, self.cfg["controle"]["v_max"], places=6)
        self.assertAlmostEqual(esq, dir_, places=9)
        self.assertAlmostEqual(info["a_lat_g"], 0.0, places=9)

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
