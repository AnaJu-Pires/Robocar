import unittest

from robocar import configuracao, controle


def det(erro, erro_longe=None, marca=False, cruzamento=False):
    return {"erro": erro, "erro_longe": erro if erro_longe is None else erro_longe, "marca": marca,
            "cruzamento": cruzamento}


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

    def test_linha_perdida_busca_e_depois_para(self):
        self.c.iniciar(0.0)
        self.c.atualizar(det(0.3), 0.02)
        esq, dir_, _ = self.c.atualizar(det(None), 0.05)
        self.assertEqual(self.c.estado, controle.BUSCANDO)
        self.assertTrue(esq > 0 > dir_, "deve girar para o ultimo lado visto (direita)")
        self.c.atualizar(det(None), 0.05 + self.cfg["controle"]["tempo_busca_s"] + 0.01)
        self.assertEqual(self.c.estado, controle.PARADO)

    def test_fim_da_linha_indo_reto_segue_reto_e_para(self):
        # box: a camera perde o fim da linha antes de as rodas chegarem nele -> segue reto e para
        avanco = self.cfg["controle"]["avanco_s"]
        self.c.iniciar(0.0)
        self.c.atualizar(det(0.05, 0.1), 1.0)
        esq, dir_, info = self.c.atualizar(det(None), 1.02)
        self.assertEqual(self.c.estado, controle.AVANCANDO)
        self.assertEqual(esq, dir_, "sem linha indo reto: as duas rodas iguais (reto, sem girar)")
        self.assertGreater(esq, 0.0)
        self.assertLessEqual(esq, self.cfg["controle"]["v_avanco"])
        self.c.atualizar(det(None), 1.02 + avanco - 0.01)
        self.assertEqual(self.c.estado, controle.AVANCANDO)
        self.assertEqual(self.c.atualizar(det(None), 1.02 + avanco + 0.01)[:2], (0.0, 0.0))
        self.assertEqual(self.c.estado, controle.PARADO)
        self.assertEqual(self.c.motivo, "fim da linha")

    def test_linha_volta_depois_do_buraco_continua_seguindo(self):
        # cruzamento/falha curta na linha reta: segue reto e retoma quando a linha reaparece
        self.c.iniciar(0.0)
        self.c.atualizar(det(0.0), 1.0)
        self.c.atualizar(det(None), 1.02)
        self.c.atualizar(det(None), 1.10)
        self.assertEqual(self.c.estado, controle.AVANCANDO)
        self.c.atualizar(det(0.02), 1.12)
        self.assertEqual(self.c.estado, controle.SEGUINDO)

    def test_cruzamento_sem_faixa_valida_segue_reto_mesmo_com_erro(self):
        self.c.iniciar(0.0)
        self.c.atualizar(det(0.4), 1.0)                     # vinha corrigindo para a direita
        esq, dir_, _ = self.c.atualizar(det(None, cruzamento=True), 1.02)
        self.assertEqual(self.c.estado, controle.AVANCANDO)
        self.assertEqual(esq, dir_)

    def test_avanco_desligado_volta_a_girar(self):
        self.cfg["controle"]["avanco_s"] = 0.0
        self.c = controle.Controlador(self.cfg["controle"], self.cfg["parada"])
        self.c.iniciar(0.0)
        self.c.atualizar(det(0.0), 1.0)
        self.c.atualizar(det(None), 1.02)
        self.assertEqual(self.c.estado, controle.BUSCANDO)

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


class TestFreioFinal(unittest.TestCase):

    def test_desarma_uma_vez_depois_do_freio(self):
        f = controle.FreioFinal(0.5)
        self.assertFalse(f.hora_de_desarmar(10.0))
        f.parou(10.0)
        self.assertFalse(f.hora_de_desarmar(10.4))
        self.assertTrue(f.hora_de_desarmar(10.5))
        self.assertFalse(f.hora_de_desarmar(11.0))

    def test_sem_freio_desarma_na_hora(self):
        f = controle.FreioFinal(0.0)
        f.parou(3.0)
        self.assertTrue(f.hora_de_desarmar(3.0))

    def test_nova_largada_cancela(self):
        f = controle.FreioFinal(0.5)
        f.parou(1.0)
        f.cancelar()
        self.assertFalse(f.hora_de_desarmar(2.0))


if __name__ == "__main__":
    unittest.main()
