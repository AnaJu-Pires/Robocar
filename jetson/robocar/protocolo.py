"""Protocolo serial Jetson <-> ESP32 (logica pura). Especificacao: docs/05_protocolo_serial.md.

Qualquer mudanca aqui exige mudar JUNTO: firmware/robocar_esp32 (config.h + .ino),
docs/05_protocolo_serial.md e testes/test_protocolo.py, e incrementar VERSAO.
"""

VERSAO = 2   # v2 (24/11/2026): flag DESLIGAR na telemetria

# Estados informados pela ESP32 na telemetria
SEM_JETSON = 0      # sem comandos validos recentes: motores desligados, nao arma
PRONTO = 1          # recebendo comandos, desarmado: aguarda o botao de largada
ARMADO = 2          # motores obedecem a Jetson
FALHA_BATERIA = 3   # bateria abaixo do corte: desarmado ate reiniciar
NOMES_ESTADO = {SEM_JETSON: "SEM_JETSON", PRONTO: "PRONTO", ARMADO: "ARMADO",
                FALHA_BATERIA: "FALHA_BATERIA"}

# Bits do campo 'flags' da telemetria
FLAG_WATCHDOG = 1   # armado, mas sem comando ha > 250 ms: freando
FLAG_BATERIA_BAIXA = 2
FLAG_DESLIGAR = 4   # botao segurado com o robo parado: a Jetson deve fazer shutdown


def checksum(corpo):
    c = 0
    for ch in corpo:
        c ^= ord(ch)
    return c


def montar(corpo):
    return "$%s*%02X\n" % (corpo, checksum(corpo))


def validar(linha):
    """Retorna o corpo de uma linha '$...*HH' valida ou None."""
    linha = linha.strip()
    if not linha.startswith("$") or "*" not in linha:
        return None
    corpo, _, chk = linha[1:].rpartition("*")
    try:
        if int(chk, 16) != checksum(corpo):
            return None
    except ValueError:
        return None
    return corpo


def _faixa(x):
    return int(round(max(-1.0, min(1.0, x)) * 1000))


def cmd_motores(seq, esq, dir_):
    """esq/dir em [-1, 1] -> '$M,seq,esq,dir*HH' com inteiros -1000..1000."""
    return montar("M,%d,%d,%d" % (seq % 10000, _faixa(esq), _faixa(dir_)))


def cmd_parar():
    return montar("S")


def cmd_armar():
    return montar("A")


def cmd_versao():
    """Pede a ESP32 que responda '$I,robocar_esp32,v<N>'."""
    return montar("V")


def interpretar(corpo):
    """Corpo validado -> dict {'tipo': 'T'|'I', ...} ou None se o formato for invalido."""
    partes = corpo.split(",")
    if partes[0] == "T" and len(partes) == 7:
        try:
            ms, enc_e, enc_d, vbat_mv, estado, flags = [int(p) for p in partes[1:]]
        except ValueError:
            return None
        return {"tipo": "T", "ms": ms, "enc_e": enc_e, "enc_d": enc_d, "vbat": vbat_mv / 1000.0,
                "estado": estado, "armado": estado == ARMADO, "flags": flags,
                "desligar": bool(flags & FLAG_DESLIGAR)}
    if partes[0] == "I":
        texto = ",".join(partes[1:])
        info = {"tipo": "I", "texto": texto, "versao": None}
        if len(partes) >= 3 and partes[1] == "robocar_esp32" and partes[2].startswith("v"):
            try:
                info["versao"] = int(partes[2][1:])
            except ValueError:
                pass
        return info
    return None
