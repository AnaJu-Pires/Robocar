"""Jetson (robocar/esp32.py, protocolo.py e controle.py reais) conversando com o firmware da ESP32 simulado no PC.

    make sim-esp32        (na raiz do repositorio; precisa de g++ e Python 3, Linux ou macOS)

O firmware (firmware/robocar_esp32) e compilado com um Arduino falso (inc/Arduino.h + sim.cpp): a serial vira
stdin/stdout, os pinos viram um registro de eventos e o botao, a bateria e os encoders sao arquivos em estado/.
Nao substitui o teste na placa (docs/06_testes.md), mas pega erro de logica, de protocolo e de pinagem.
"""
import os, sys, time, subprocess, fcntl
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)
sys.path.insert(0, os.path.join(AQUI, '..', '..', 'jetson'))
from robocar import protocolo
from robocar.esp32 import LinkESP32
from robocar.controle import Controlador
from robocar import configuracao

SIM = os.path.abspath('estado'); os.makedirs(SIM, exist_ok=True)
for f in os.listdir(SIM): os.remove(os.path.join(SIM, f))
def setf(n, v):
    tmp = os.path.join(SIM, n + '.tmp'); open(tmp, 'w').write(str(v)); os.replace(tmp, os.path.join(SIM, n))
setf('botao', 1); setf('pino36_mv', 0)
log = open('eventos.log', 'w')
p = subprocess.Popen(['build/esp_sim'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, env=dict(os.environ, SIMDIR=SIM))
fcntl.fcntl(p.stdout, fcntl.F_SETFL, os.O_NONBLOCK)

class Ser:
    buf = b''
    @property
    def in_waiting(self):
        try:
            d = os.read(p.stdout.fileno(), 65536)
            if d: self.buf += d
        except BlockingIOError: pass
        return len(self.buf)
    def read(self, n): d, self.buf = self.buf[:n], self.buf[n:]; return d
    def write(self, d): p.stdin.write(d); p.stdin.flush()
    def close(self): pass

link = LinkESP32(Ser()); link.pedir_versao()
ok = []
def check(nome, cond, extra=''):
    ok.append(cond); print(('OK   ' if cond else 'FALHA'), nome, extra)
def rodar(seg, cmd=None, extra=None):
    t1 = time.time() + seg
    while time.time() < t1:
        if cmd: link.enviar_motores(*cmd)
        if extra: extra()
        link.ler(); time.sleep(0.02)
    return link.telemetria
def eventos():
    log.flush(); return [l.split() for l in open('eventos.log')]
def ultimo_pwm():
    v = {}
    for e in eventos():
        if e[1] == 'PWM': v[int(e[2])] = int(e[3])
    return v
def subidas(pino, desde_ms):
    """Quantas vezes o pino foi para 1 a partir de 'desde_ms' (tempo do firmware)."""
    return sum(1 for e in eventos() if e[1] == 'DW' and int(e[2]) == pino and int(e[3]) == 1 and int(e[0]) >= desde_ms)
def nivel(pino):
    v = None
    for e in eventos():
        if e[1] == 'DW' and int(e[2]) == pino: v = int(e[3])
    return v

t = rodar(0.4)
check('responde a versao do protocolo', link.versao_firmware == protocolo.VERSAO, link.versao_firmware)
check('liga em SEM_JETSON, drivers dormindo', t['estado'] == protocolo.SEM_JETSON and nivel(32) == 0 and nivel(18) == 0)
check('PWM a 20 kHz, 10 bits, nos 4 pinos 33/25/19/21', sorted(int(e[2]) for e in eventos() if e[1] == 'LEDC') == [19, 21, 25, 33])
t = rodar(0.3, (0, 0))
check('com comandos da Jetson -> PRONTO', t['estado'] == protocolo.PRONTO)
check('PRONTO nao liga o driver', nivel(32) == 0 and nivel(18) == 0)
# largada pelo J14 (jumper/botao para o GND)
setf('botao', 0); t = rodar(0.1, (0, 0)); setf('botao', 1); t = rodar(0.2, (0, 0))
check('botao de largada (J14) -> ARMADO', t['estado'] == protocolo.ARMADO)
check('ARMADO acorda os dois drivers (GPIO32 e GPIO18 em 1)', nivel(32) == 1 and nivel(18) == 1)
# lado da Jetson: controlador inicia na borda de armado
cfg = configuracao.carregar_config(None, {})
ctrl = Controlador(cfg['controle'], cfg['parada']); ctrl.iniciar(time.time())
det = {'erro': 0.0, 'erro_longe': 0.0, 'marca': False}
e, d, info = ctrl.atualizar(det, time.time() + 1.0)   # depois da rampa de largada (controle.acel_max)
check('controle com a linha no centro -> as duas rodas para frente iguais', e > 0 and abs(e - d) < 1e-9, '(%.2f, %.2f)' % (e, d))
t = rodar(0.4, (e, d))
pw = ultimo_pwm(); duty = int(round(e * 1000)) * 1023 // 1000
check('motor esquerdo (INVERTER_E): GPIO25=1023 e GPIO33 com PWM (frente)', pw[25] == 1023 and pw[33] == 1023 - duty, pw)
check('motor direito: GPIO19=1023 e GPIO21 com PWM', pw[19] == 1023 and pw[21] == 1023 - duty, pw)
e, d, _ = ctrl.atualizar({'erro': 0.5, 'erro_longe': 0.5, 'marca': False}, time.time() + 1.05)
check('linha a direita -> roda esquerda mais rapida', e > d, '(%.2f, %.2f)' % (e, d))
# encoders
setf('enc_e', 140); setf('enc_d', -140); t = rodar(0.2, (e, d))
check('encoders contados (x4) e chegam na telemetria', abs(t['enc_e']) == 140 and abs(t['enc_d']) == 140, (t['enc_e'], t['enc_d']))
# bateria: 12,6 V -> 2,22 V no pino
setf('pino36_mv', round(12600 * 47 / 267)); t = rodar(1.5, (e, d))
check('bateria 12,6 V medida pelo divisor 220k/47k', abs(t['vbat'] - 12.6) < 0.05, t['vbat'])
# watchdog
t = rodar(0.4)
check('Jetson parou de mandar: freia (flag watchdog), ainda armado', t['estado'] == protocolo.ARMADO and t['flags'] & 1 and ultimo_pwm()[33] == 1023 and ultimo_pwm()[25] == 1023)
t = rodar(1.0)
check('sem Jetson por 1 s: desarma e drivers dormem', t['estado'] == protocolo.SEM_JETSON and nivel(32) == 0 and nivel(18) == 0)
# armar pela Jetson ($A, modo bancada) e parar ($S)
t = rodar(0.3, (0, 0)); link.armar(); t = rodar(0.2, (0, 0))
check('$A (bancada) arma', t['estado'] == protocolo.ARMADO)
link.parar(); t = rodar(0.2, (0, 0))
check('$S desarma (fim de prova)', t['estado'] == protocolo.PRONTO)
# botao: armado, apertar para na hora (sem esperar soltar) e soltar nao arma de novo
link.armar(); t = rodar(0.2, (0.3, 0.3))
setf('botao', 0); t = rodar(0.15, (0.3, 0.3))
check('botao apertado com o robo armado -> para na hora', t['estado'] == protocolo.PRONTO and nivel(32) == 0)
setf('botao', 1); t = rodar(0.2, (0, 0))
check('soltar depois de parar nao arma de novo', t['estado'] == protocolo.PRONTO)
# botao segurado 3 s com o robo parado -> flag DESLIGAR, sem armar
setf('botao', 0); t = rodar(1.0, (0, 0))
check('segurando o botao: ainda nao arma nem pede desligar', t['estado'] == protocolo.PRONTO and not t['desligar'])
t = rodar(2.3, (0, 0))
check('segurado 3 s -> flag DESLIGAR na telemetria (protocolo v2)', t['desligar'] and t['estado'] == protocolo.PRONTO, t['flags'])
setf('botao', 1); t = rodar(0.3, (0, 0))
check('soltar depois do pedido de desligar nao arma', t['estado'] == protocolo.PRONTO)
t = rodar(3.2, (0, 0))
check('flag DESLIGAR some depois de 3 s', not t['desligar'], t['flags'])
# sequencia completa de desligar (D-039): LED da ESP32 (GPIO2) diz quando pode cortar a chave
t = rodar(5.0, (0, 0))       # a Jetson continuou mandando (8 s apos o pedido): nao desligou -> cancela
m0 = t['ms']; t = rodar(2.0, (0, 0))
check('Jetson nao obedeceu ao desligar: LED volta ao normal (PRONTO, 1 piscada/s)', subidas(2, m0) <= 3, subidas(2, m0))
setf('botao', 0); t = rodar(3.3, (0, 0)); setf('botao', 1)
check('novo pedido de desligar', t['desligar'], t['flags'])
rodar(1.3)                   # a Jetson fechou o programa: sem comandos
m0 = link.telemetria['ms']; t = rodar(0.5)
check('Jetson sumiu: SEM_JETSON e LED pisca muito rapido (ainda NAO desligar)', t['estado'] == protocolo.SEM_JETSON and subidas(2, m0) >= 4, subidas(2, m0))
rodar(1.6)                   # ESPERA_DESLIGAR_MS = 2 s na simulacao (25 s na placa)
m0 = link.telemetria['ms']; t = rodar(2.0)
n = subidas(2, m0)
check('depois da espera: 2 piscadas por segundo = pode desligar a chave', 3 <= n <= 5, n)
t = rodar(0.3, (0, 0)); m0 = t['ms']; t = rodar(2.0, (0, 0))
check('Jetson voltou a mandar comandos: cancela e volta a PRONTO (1 piscada/s)', t['estado'] == protocolo.PRONTO and subidas(2, m0) <= 3, subidas(2, m0))
# bateria baixa
link.armar(); rodar(0.2, (0.3, 0.3))
setf('pino36_mv', round(9300 * 47 / 267)); t = rodar(4.5, (0.3, 0.3))
check('bateria < 9,6 V por 2 s -> FALHA_BATERIA e motores desligados', t['estado'] == protocolo.FALHA_BATERIA and nivel(32) == 0, (t['vbat'], t['estado']))
link.armar(); t = rodar(0.3, (0.3, 0.3))
check('em FALHA_BATERIA nao arma de novo', t['estado'] == protocolo.FALHA_BATERIA)
check('nenhuma linha invalida recebida', link.linhas_invalidas == 0, link.linhas_invalidas)
p.kill()
print('\n%d/%d OK' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
