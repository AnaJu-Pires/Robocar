"""Metricas de corrida a partir do log CSV (robocar/metricas.py)."""
import unittest

from robocar import metricas


def linha(t, estado="SEGUINDO", erro="0.1", cruz="0", v="0.35", vbat="12.0", ee=0, ed=0, proc="4.0"):
    return {"t": str(t), "estado": estado, "erro": erro, "cruzamento": cruz, "v": v, "vbat": vbat,
            "enc_e": str(ee), "enc_d": str(ed), "proc_ms": proc}


class TestMetricas(unittest.TestCase):
    def test_volta_simples(self):
        ls = [linha(0.0, "AGUARDANDO", erro="")]
        ls += [linha(1.0 + k / 60.0, ee=k * 10, ed=k * 10) for k in range(120)]       # 2 s a 60 fps
        ls += [linha(3.0, "PARADO", erro="")]
        m = metricas.calcular(ls, pulsos_por_volta=560, diametro_roda_m=0.042)
        self.assertAlmostEqual(m["duracao_s"], 119 / 60.0, places=3)
        self.assertAlmostEqual(m["fps_real"], 60.0, places=1)
        self.assertEqual(m["perdeu_linha_vezes"], 0)
        self.assertAlmostEqual(m["linha_vista_pct"], 100.0)
        self.assertAlmostEqual(m["distancia_m"], 1190 / 560.0 * 3.14159265 * 0.042, places=4)
        self.assertEqual(m["estado_final"], "PARADO")

    def test_conta_perdas_e_cruzamentos(self):
        ls = [linha(0.0), linha(0.1, cruz="1"), linha(0.2, cruz="1"), linha(0.3),
              linha(0.4, "BUSCANDO", erro=""), linha(0.5, "BUSCANDO", erro=""), linha(0.6),
              linha(0.7, "BUSCANDO", erro=""), linha(0.8, cruz="1")]
        m = metricas.calcular(ls)
        self.assertEqual(m["perdeu_linha_vezes"], 2)
        self.assertEqual(m["cruzamentos_detectados"], 2)
        self.assertAlmostEqual(m["linha_vista_pct"], 100.0 * 6 / 9)
        self.assertNotIn("distancia_m", m)           # sem pulsos por volta: so os pulsos

    def test_conta_avancos_sem_linha(self):
        ls = [linha(0.0), linha(0.1, "AVANCANDO", erro=""), linha(0.2, "AVANCANDO", erro=""), linha(0.3),
              linha(0.4, "AVANCANDO", erro=""), linha(0.5, "PARADO", erro="")]
        m = metricas.calcular(ls)
        self.assertEqual(m["seguiu_reto_sem_linha_vezes"], 2)
        self.assertEqual(m["perdeu_linha_vezes"], 0)
        self.assertEqual(m["quadros_andando"], 5)

    def test_queda_da_bateria(self):
        ls = [linha(0.0, vbat="12.4"), linha(0.1, vbat="11.6"), linha(0.2, vbat="")]
        m = metricas.calcular(ls)
        self.assertAlmostEqual(m["vbat_queda"], 0.8, places=6)

    def test_log_sem_movimento(self):
        m = metricas.calcular([linha(0.0, "AGUARDANDO")])
        self.assertIn("aviso", m)
        self.assertIn("AVISO", metricas.texto(m))


if __name__ == "__main__":
    unittest.main()
