import unittest

from robocar import protocolo
from robocar.esp32 import LinkESP32


class SerialFalsa(object):
    """Imita a parte da API do pyserial usada pelo LinkESP32."""

    def __init__(self, recebido=""):
        self.entrada = recebido.encode("ascii")
        self.saida = b""

    @property
    def in_waiting(self):
        return len(self.entrada)

    def read(self, n):
        dados, self.entrada = self.entrada[:n], self.entrada[n:]
        return dados

    def write(self, dados):
        self.saida += dados

    def close(self):
        pass


class TestLinkESP32(unittest.TestCase):

    def test_envia_comando_valido(self):
        ser = SerialFalsa()
        link = LinkESP32(ser)
        link.enviar_motores(0.25, -1.0)
        self.assertEqual(protocolo.validar(ser.saida.decode()), "M,1,250,-1000")

    def test_le_telemetria_e_versao_ignorando_lixo(self):
        chegada = (protocolo.montar("I,robocar_esp32,v%d" % protocolo.VERSAO) + "ruido sem formato\n"
                   + protocolo.montar("T,500,10,12,11900,1,0") + "$T,1*00\n")
        link = LinkESP32(SerialFalsa(chegada))
        link.ler()
        self.assertEqual(link.versao_firmware, protocolo.VERSAO)
        self.assertEqual(link.telemetria["estado"], protocolo.PRONTO)
        self.assertFalse(link.telemetria["armado"])
        self.assertEqual(link.linhas_invalidas, 2)

    def test_linha_partida_em_duas_leituras(self):
        msg = protocolo.montar("T,500,10,12,11900,2,0")
        ser = SerialFalsa(msg[:10])
        link = LinkESP32(ser)
        link.ler()
        self.assertIsNone(link.telemetria)
        ser.entrada = msg[10:].encode("ascii")
        link.ler()
        self.assertTrue(link.telemetria["armado"])


if __name__ == "__main__":
    unittest.main()
