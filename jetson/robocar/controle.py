"""Lei de controle do seguidor de linha (roda na Jetson, na taxa da camera).

Saida: comandos normalizados das rodas esquerda/direita em [-1, 1] (a ESP32 aplica o PWM).

Estados:
  AGUARDANDO -> espera a largada (botao da ESP32) ou inicio manual
  SEGUINDO   -> PD no erro lateral + termo de antecipacao (erro da faixa mais distante)
  BUSCANDO   -> linha perdida: gira para o ultimo lado visto por ate 'tempo_busca_s'
  PARADO     -> fim (linha perdida por muito tempo, marca do box ou comando)
"""

AGUARDANDO = "AGUARDANDO"
SEGUINDO = "SEGUINDO"
BUSCANDO = "BUSCANDO"
PARADO = "PARADO"


def _limitar(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


class Controlador(object):

    def __init__(self, cfg_controle, cfg_parada):
        self.c = cfg_controle
        self.p = cfg_parada
        self.estado = AGUARDANDO
        self.motivo = ""
        self._zerar()

    def _zerar(self):
        self.t_inicio = None
        self.e_ant = None
        self.t_ant = None
        self.de = 0.0
        self.ultimo_lado = 1.0
        self.t_perdeu = None
        self.cont_marca = 0
        self.t_marca = None

    def iniciar(self, t):
        self._zerar()
        self.t_inicio = t
        self.estado = SEGUINDO
        self.motivo = ""

    def aguardar(self):
        self.estado = AGUARDANDO
        self.motivo = ""

    def parar(self, motivo=""):
        self.estado = PARADO
        self.motivo = motivo

    def atualizar(self, det, t):
        """Recebe o resultado da visao; retorna (esquerda, direita, info)."""
        info = {"v": 0.0, "u": 0.0}
        if self.estado in (AGUARDANDO, PARADO):
            return 0.0, 0.0, info

        if self._chegou(det, t):
            self.parar("chegada (marca)")
            return 0.0, 0.0, info

        erro = det["erro"]
        if erro is None:
            return self._buscar(t, info)

        self.estado = SEGUINDO
        erro_longe = det["erro_longe"] if det["erro_longe"] is not None else erro
        if self.e_ant is not None and t > self.t_ant:
            derivada = (erro - self.e_ant) / (t - self.t_ant)
            self.de = 0.7 * self.de + 0.3 * derivada  # filtro passa-baixa simples
        self.e_ant, self.t_ant = erro, t

        c = self.c
        u = _limitar(c["kp"] * erro + c["kd"] * self.de + c["k_frente"] * erro_longe, -1.0, 1.0)
        # reduz a velocidade quando a linha esta deslocada perto OU longe (curva a frente)
        severidade = max(abs(erro), abs(erro_longe))
        v = c["v_max"] - (c["v_max"] - c["v_min"]) * min(1.0, severidade / c["severidade_max"])

        lado = erro if abs(erro) > 0.02 else erro_longe
        if abs(lado) > 0.02:
            self.ultimo_lado = 1.0 if lado > 0 else -1.0

        esq, dir_ = v + u, v - u   # erro > 0: linha a direita -> roda esquerda mais rapida
        m = max(abs(esq), abs(dir_))
        if m > 1.0:
            esq, dir_ = esq / m, dir_ / m
        info["v"], info["u"] = v, u
        return esq, dir_, info

    def _chegou(self, det, t):
        p = self.p
        if not p["usar_marca"] or t - self.t_inicio < p["tempo_minimo_s"]:
            return False
        self.cont_marca = self.cont_marca + 1 if det["marca"] else 0
        if self.t_marca is None and self.cont_marca >= p["frames_confirmacao"]:
            self.t_marca = t
        return self.t_marca is not None and t - self.t_marca >= p["atraso_s"]

    def _buscar(self, t, info):
        if self.estado != BUSCANDO:
            self.estado = BUSCANDO
            self.t_perdeu = t
        if t - self.t_perdeu > self.c["tempo_busca_s"]:
            self.parar("linha perdida")
            return 0.0, 0.0, info
        self.e_ant = None
        vb = self.c["v_busca"]
        return (vb, -vb, info) if self.ultimo_lado > 0 else (-vb, vb, info)
