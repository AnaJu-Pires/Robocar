import unittest

from robocar import protocolo


class TestProtocolo(unittest.TestCase):

    def test_comando_motores(self):
        msg = protocolo.cmd_motores(12, -0.5, 0.8)
        self.assertEqual(protocolo.validar(msg), "M,12,-500,800")

    def test_comando_motores_limita_faixa(self):
        self.assertEqual(protocolo.validar(protocolo.cmd_motores(1, -3.0, 2.0)), "M,1,-1000,1000")

    def test_checksum_errado_rejeitado(self):
        self.assertIsNone(protocolo.validar("$M,12,-500,801*00"))
        self.assertIsNone(protocolo.validar("lixo"))

    def test_telemetria(self):
        corpo = protocolo.validar(protocolo.montar("T,1000,15,-3,11850,2,1"))
        t = protocolo.interpretar(corpo)
        self.assertEqual(t["tipo"], "T")
        self.assertAlmostEqual(t["vbat"], 11.85)
        self.assertTrue(t["armado"])
        self.assertEqual(t["enc_d"], -3)
        self.assertEqual(t["flags"] & protocolo.FLAG_WATCHDOG, protocolo.FLAG_WATCHDOG)

    def test_flag_desligar(self):
        msg = protocolo.interpretar(protocolo.validar(protocolo.montar("T,10,0,0,11800,1,4")))
        self.assertTrue(msg["desligar"])
        msg = protocolo.interpretar(protocolo.validar(protocolo.montar("T,10,0,0,11800,1,3")))
        self.assertFalse(msg["desligar"])

    def test_pedido_de_versao(self):
        self.assertEqual(protocolo.validar(protocolo.cmd_versao()), "V")

    def test_mensagem_de_versao_do_firmware(self):
        info = protocolo.interpretar("I,robocar_esp32,v%d" % protocolo.VERSAO)
        self.assertEqual(info["versao"], protocolo.VERSAO)

    def test_telemetria_malformada(self):
        self.assertIsNone(protocolo.interpretar("T,1,2,3"))
        self.assertIsNone(protocolo.interpretar("T,a,b,c,d,e,f"))


if __name__ == "__main__":
    unittest.main()
