"""Teste de movimento pela Jetson, sem camera: frente, giro de 360 graus no lugar e re.

A ESP32 precisa estar com o firmware do robo (firmware/robocar_esp32), nao com o teste_movimento.ino.

Exemplos (ou use o Makefile na raiz: make movimento PORTA=/dev/ttyUSB0):
  python3 teste_movimento.py --esp32 /dev/ttyUSB0             # largada pelo botao da ESP32
  python3 teste_movimento.py --esp32 /dev/ttyUSB0 --armar     # arma sem botao (RODAS SUSPENSAS!)
  python3 teste_movimento.py --esp32 /dev/ttyUSB0 --giro 2.2  # ajusta o tempo do giro (s)

Apertar o botao da ESP32 durante o movimento (ou Ctrl+C) para na hora.
"""

import argparse
import sys
import time

from robocar import configuracao, manobra, protocolo

PERIODO_S = 0.02            # 50 Hz, como o seguidor de linha
CICLOS_SEM_TELEMETRIA = 25  # ~0,5 s sem telemetria nova durante o movimento: aborta


def argumentos(argv=None):
    ap = argparse.ArgumentParser(description="Teste de movimento pela Jetson - Robocar Blitz")
    ap.add_argument("--esp32", help="porta serial da ESP32 (padrao: config.json ou /dev/ttyUSB0)")
    ap.add_argument("--armar", action="store_true",
                    help="arma a ESP32 sem o botao (SOMENTE com as rodas suspensas)")
    ap.add_argument("--vel", type=float, default=manobra.VEL_RETA, help="velocidade na frente e na re (0-1)")
    ap.add_argument("--tempo", type=float, default=manobra.TEMPO_RETA_S, help="segundos para frente e para tras")
    ap.add_argument("--vel-giro", type=float, default=manobra.VEL_GIRO, help="velocidade das rodas no giro (0-1)")
    ap.add_argument("--giro", type=float, default=manobra.TEMPO_GIRO_S, help="segundos de giro (360 graus)")
    ap.add_argument("--pausa", type=float, default=manobra.PAUSA_S, help="segundos parado entre as etapas")
    return ap.parse_args(argv)


def _esperar_largada(link, armar, relogio, dormir, imprimir, espera_max_s):
    """Manda zero ate a ESP32 armar (botao ou --armar). Retorna a telemetria armada ou um codigo de saida."""
    t_ini = relogio()
    avisou = pediu_armar = False
    while True:
        link.enviar_motores(0.0, 0.0)   # mantem o link vivo: a ESP32 so arma com comandos chegando
        link.ler()
        tel = link.telemetria
        if tel is None:
            if relogio() - t_ini > espera_max_s:
                imprimir("ERRO: nenhuma telemetria valida da ESP32 em %.0f s. Confira o cabo e a porta, se o "
                         "firmware gravado e o robocar_esp32 (e nao o teste_movimento.ino) e rode de novo."
                         % espera_max_s)
                return 2
        elif tel["estado"] == protocolo.FALHA_BATERIA:
            imprimir("ERRO: ESP32 em FALHA_BATERIA (%.2f V). Carregue a bateria e reinicie a ESP32." % tel["vbat"])
            return 1
        elif tel["armado"]:
            return tel
        elif tel["estado"] == protocolo.PRONTO:
            if armar and not pediu_armar:
                link.armar()
                pediu_armar = True
            if not avisou:
                imprimir("ESP32 pronta. Bateria: %.2f V" % tel["vbat"])
                imprimir("Armando pela Jetson (--armar)..." if armar else "Aperte o botao de largada.")
                avisou = True
        dormir(PERIODO_S)


def rodar(link, sequencia, armar=False, relogio=time.time, dormir=time.sleep, imprimir=print,
          espera_max_s=5.0):
    """Executa a sequencia. Retorna 0 se completou, 1 se parou antes (botao, bateria, link) e 2 sem ESP32."""
    tel = _esperar_largada(link, armar, relogio, dormir, imprimir, espera_max_s)
    if not isinstance(tel, dict):
        return tel

    imprimir(">>> LARGADA (%.1f s de manobras)" % manobra.duracao_total(sequencia))
    t0 = relogio()
    etapa_atual, inicio_etapa = None, (t0, tel["enc_e"], tel["enc_d"])
    ultimo_ms, sem_telemetria = tel["ms"], 0

    def fechar_etapa(agora, tel):
        nome = sequencia[etapa_atual][0]
        if nome != "PAUSA":
            imprimir("%-6s %5.0f ms | pulsos E=%d D=%d" % (
                nome, (agora - inicio_etapa[0]) * 1000.0, tel["enc_e"] - inicio_etapa[1],
                tel["enc_d"] - inicio_etapa[2]))

    while True:
        agora = relogio()
        cmd = manobra.comando_em(sequencia, agora - t0)
        link.ler()
        tel = link.telemetria
        if etapa_atual is not None and (cmd is None or cmd[0] != etapa_atual):
            fechar_etapa(agora, tel)
        if cmd is None:
            link.enviar_motores(0.0, 0.0)
            link.parar()
            imprimir("Fim. Para repetir, rode de novo.")
            return 0
        if cmd[0] != etapa_atual:
            etapa_atual, inicio_etapa = cmd[0], (agora, tel["enc_e"], tel["enc_d"])

        if not tel["armado"]:
            link.enviar_motores(0.0, 0.0)
            if tel["estado"] == protocolo.FALHA_BATERIA:
                imprimir("PARADO: bateria baixa (%.2f V). Carregue e reinicie a ESP32." % tel["vbat"])
            else:
                imprimir("PARADO: a ESP32 desarmou (%s). Botao apertado?"
                         % protocolo.NOMES_ESTADO.get(tel["estado"], "?"))
            return 1
        if tel["ms"] == ultimo_ms:
            sem_telemetria += 1
            if sem_telemetria > CICLOS_SEM_TELEMETRIA:
                link.parar()
                imprimir("PARADO: a ESP32 parou de mandar telemetria.")
                return 1
        else:
            ultimo_ms, sem_telemetria = tel["ms"], 0

        link.enviar_motores(cmd[2], cmd[3])
        dormir(PERIODO_S)


def main(argv=None):
    args = argumentos(argv)
    try:
        cfg = configuracao.carregar_config()
    except configuracao.ErroConfiguracao as e:
        print("ERRO de configuracao:", e)
        return 2
    porta = args.esp32 or cfg["esp32"]["porta"] or "/dev/ttyUSB0"
    sequencia = manobra.criar_sequencia(args.vel, args.tempo, args.vel_giro, args.giro, args.pausa)

    from robocar.esp32 import LinkESP32, abrir_porta
    link = LinkESP32(abrir_porta(porta, cfg["esp32"]["baud"]))
    link.pedir_versao()
    print("ESP32 em %s. Frente %.1f s a %.0f%%, giro %.1f s a %.0f%%, re %.1f s." % (
        porta, args.tempo, args.vel * 100, args.giro, args.vel_giro * 100, args.tempo))
    try:
        return rodar(link, sequencia, armar=args.armar)
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario.")
        return 1
    finally:
        link.fechar()   # manda $S: a ESP32 desarma


if __name__ == "__main__":
    sys.exit(main())
