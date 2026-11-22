import unittest

import teste_movimento
from robocar import manobra, protocolo
from robocar.esp32 import LinkESP32


class ESP32Falsa(object):
    """Imita o firmware na porta serial: SEM_JETSON -> PRONTO com $M, ARMADO com $A, PRONTO com $S.
    Responde uma telemetria a cada leitura e conta encoders proporcionais ao comando."""

    def __init__(self, responde=True, desarmar_no_ms=None):
        self.estado = protocolo.SEM_JETSON
        self.responde = responde
        self.desarmar_no_ms = desarmar_no_ms
        self.ms = 0
        self.enc_e = self.enc_d = 0
        self.ultimo = (0, 0)
        self.recebidos = []     # (estado, esq, dir) de cada $M
        self.comandos = []      # letras recebidas, em ordem
        self.pendente = b""

    # --- lado da Jetson (API do pyserial usada pelo LinkESP32)
    def write(self, dados):
        for linha in dados.decode("ascii").splitlines():
            corpo = protocolo.validar(linha)
            if not corpo:
                continue
            self.comandos.append(corpo[0])
            if corpo[0] == "M":
                _, _, e, d = corpo.split(",")
                self.ultimo = (int(e), int(d))
                self.recebidos.append((self.estado, int(e), int(d)))
                if self.estado == protocolo.SEM_JETSON:
                    self.estado = protocolo.PRONTO
            elif corpo[0] == "A" and self.estado == protocolo.PRONTO:
                self.estado = protocolo.ARMADO
            elif corpo[0] == "S" and self.estado == protocolo.ARMADO:
                self.estado = protocolo.PRONTO

    @property
    def in_waiting(self):
        if not self.pendente and self.responde:
            self.ms += 20
            if self.desarmar_no_ms is not None and self.ms >= self.desarmar_no_ms:
                self.estado = protocolo.PRONTO   # "botao apertado"
            if self.estado == protocolo.ARMADO:
                self.enc_e += self.ultimo[0] // 50
                self.enc_d += self.ultimo[1] // 50
            self.pendente = protocolo.montar("T,%d,%d,%d,11800,%d,0" % (
                self.ms, self.enc_e, self.enc_d, self.estado)).encode("ascii")
        return len(self.pendente)

    def read(self, n):
        dados, self.pendente = self.pendente[:n], self.pendente[n:]
        return dados

    def close(self):
        pass


class Relogio(object):
    def __init__(self):
        self.t = 1000.0

    def agora(self):
        return self.t

    def dormir(self, s):
        self.t += s


def executar(esp, armar=True, sequencia=None):
    rel = Relogio()
    saida = []
    codigo = teste_movimento.rodar(LinkESP32(esp), sequencia or manobra.criar_sequencia(), armar=armar,
                                   relogio=rel.agora, dormir=rel.dormir, imprimir=saida.append)
    return codigo, saida


class TestSequencia(unittest.TestCase):

    def test_etapas_e_limites(self):
        seq = manobra.criar_sequencia(vel=0.4, tempo=1.5, vel_giro=0.6, tempo_giro=2.0, pausa=0.8)
        self.assertAlmostEqual(manobra.duracao_total(seq), 1.5 + 2.0 + 1.5 + 3 * 0.8)
        self.assertEqual(manobra.comando_em(seq, 0.0), (0, "FRENTE", 0.4, 0.4))
        self.assertEqual(manobra.comando_em(seq, 1.5)[1], "PAUSA")
        self.assertEqual(manobra.comando_em(seq, 2.3), (2, "GIRO", 0.6, -0.6))
        self.assertEqual(manobra.comando_em(seq, 5.1), (4, "RE", -0.4, -0.4))
        self.assertIsNone(manobra.comando_em(seq, manobra.duracao_total(seq)))
        self.assertIsNone(manobra.comando_em(seq, -0.1))


class TestTesteMovimento(unittest.TestCase):

    def test_sequencia_completa_armando_pela_jetson(self):
        esp = ESP32Falsa()
        codigo, saida = executar(esp)
        self.assertEqual(codigo, 0)
        armados = [(e, d) for estado, e, d in esp.recebidos if estado == protocolo.ARMADO]
        self.assertIn((400, 400), armados)
        self.assertIn((600, -600), armados)
        self.assertIn((-400, -400), armados)
        # ordem: frente antes do giro, giro antes da re
        self.assertLess(armados.index((400, 400)), armados.index((600, -600)))
        self.assertLess(armados.index((600, -600)), armados.index((-400, -400)))
        # nada se move antes de armar; no fim desarma com $S
        self.assertTrue(all(e == 0 and d == 0 for estado, e, d in esp.recebidos if estado != protocolo.ARMADO))
        self.assertEqual(esp.comandos[-1], "S")
        self.assertEqual(esp.estado, protocolo.PRONTO)
        self.assertTrue(any(s.startswith("GIRO") for s in saida))

    def test_sem_armar_espera_o_botao(self):
        esp = ESP32Falsa()
        rel = Relogio()
        saida = []
        link = LinkESP32(esp)

        def dormir(s):
            rel.dormir(s)
            if rel.t > 1001.0 and esp.estado == protocolo.PRONTO and "S" not in esp.comandos:
                esp.estado = protocolo.ARMADO   # alguem apertou o botao depois de 1 s

        codigo = teste_movimento.rodar(link, manobra.criar_sequencia(), armar=False, relogio=rel.agora,
                                       dormir=dormir, imprimir=saida.append)
        self.assertEqual(codigo, 0)
        self.assertNotIn("A", esp.comandos)
        self.assertIn("Aperte o botao de largada.", saida)

    def test_botao_no_meio_para_na_hora(self):
        esp = ESP32Falsa(desarmar_no_ms=2000)
        codigo, saida = executar(esp)
        self.assertEqual(codigo, 1)
        self.assertEqual(esp.ultimo, (0, 0))
        self.assertTrue(any(s.startswith("PARADO") for s in saida))

    def test_sem_telemetria_desiste(self):
        codigo, saida = executar(ESP32Falsa(responde=False))
        self.assertEqual(codigo, 2)
        self.assertTrue(saida[-1].startswith("ERRO"))


if __name__ == "__main__":
    unittest.main()
