"""Sequencia de manobras por tempo (teste de movimento pela Jetson). Sem E/S.

Cada etapa e (nome, esq, dir, duracao_s), com esq/dir em [-1, 1] como no controle.
Os valores padrao vieram do teste so com a ESP32 (firmware/teste_movimento, 21/11/2026):
giro de 360 graus no lugar = 0,6 por 2,0 s.
"""

VEL_RETA = 0.4
TEMPO_RETA_S = 1.5
VEL_GIRO = 0.6
TEMPO_GIRO_S = 2.0
PAUSA_S = 0.8


def criar_sequencia(vel=VEL_RETA, tempo=TEMPO_RETA_S, vel_giro=VEL_GIRO, tempo_giro=TEMPO_GIRO_S,
                    pausa=PAUSA_S):
    """Frente -> pausa -> giro no lugar para a direita -> pausa -> re -> pausa."""
    return [
        ("FRENTE", vel, vel, tempo),
        ("PAUSA", 0.0, 0.0, pausa),
        ("GIRO", vel_giro, -vel_giro, tempo_giro),
        ("PAUSA", 0.0, 0.0, pausa),
        ("RE", -vel, -vel, tempo),
        ("PAUSA", 0.0, 0.0, pausa),
    ]


def duracao_total(sequencia):
    return sum(etapa[3] for etapa in sequencia)


def comando_em(sequencia, t):
    """Tempo t (s desde a largada) -> (indice, nome, esq, dir), ou None quando a sequencia acabou."""
    if t < 0:
        return None
    inicio = 0.0
    for i, (nome, esq, dir_, duracao) in enumerate(sequencia):
        if t < inicio + duracao:
            return i, nome, esq, dir_
        inicio += duracao
    return None
