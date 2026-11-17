import json
import os
import shutil
import tempfile
import unittest

from robocar import configuracao


class TestConfiguracao(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def _arquivo(self, conteudo):
        caminho = os.path.join(self.pasta, "config.json")
        with open(caminho, "w") as f:
            json.dump(conteudo, f)
        return caminho

    def test_config_da_equipe_e_valida(self):
        cfg = configuracao.carregar_config()  # config/config.json do repositorio
        self.assertEqual(set(cfg), set(configuracao.PADRAO))

    def test_sobrescreve_e_ignora_comentarios(self):
        cfg = configuracao.carregar_config(self._arquivo({"_nota": "x", "controle": {"kp": 1.5}}))
        self.assertEqual(cfg["controle"]["kp"], 1.5)
        self.assertEqual(cfg["controle"]["kd"], configuracao.PADRAO["controle"]["kd"])

    def test_chave_desconhecida_gera_erro(self):
        with self.assertRaises(configuracao.ErroConfiguracao):
            configuracao.carregar_config(self._arquivo({"controle": {"kpp": 1.0}}))

    def test_ajustes_tem_prioridade(self):
        cfg = configuracao.carregar_config(self._arquivo({"controle": {"kp": 1.5}}),
                                           ajustes={"controle": {"kp": 2.0}})
        self.assertEqual(cfg["controle"]["kp"], 2.0)

    def test_calibracao_ida_e_volta(self):
        caminho = os.path.join(self.pasta, "calibracao.json")
        configuracao.salvar_calibracao(200.0, 40.0, caminho=caminho)
        c = configuracao.carregar_calibracao(caminho)
        self.assertEqual(c["limiar"], 120.0)
        self.assertAlmostEqual(c["razao"], 0.6)

    def test_calibracao_invertida_rejeitada(self):
        with self.assertRaises(ValueError):
            configuracao.salvar_calibracao(40.0, 200.0, caminho=os.path.join(self.pasta, "c.json"))


if __name__ == "__main__":
    unittest.main()
