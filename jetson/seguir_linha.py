"""Seguidor de linha: programa principal da Jetson Nano.

Evolucao do seguir_linha.py original (preservado em legado/). Mantem a ROI inferior, o erro
normalizado (-1 esquerda .. +1 direita), o rotulo ESQUERDA/RETO/DIREITA, "PROCURAR <lado>"
e as janelas de imagem e mascara.

Exemplos (ou use o Makefile na raiz do repositorio):
  python3 seguir_linha.py                          # camera CSI, so visualizacao
  python3 seguir_linha.py --fonte video.avi        # reprocessa um video (PC ou Jetson)
  python3 seguir_linha.py --gravar                 # grava quadros em dados/gravacoes/
  python3 seguir_linha.py --esp32 /dev/ttyUSB0 --sem-janela --log   # no carro
  python3 seguir_linha.py --mostrar-config         # parametros efetivos
  python3 seguir_linha.py --sem-janela --fotos 1   # pelo SSH: salva imagem+mascara a cada 1 s e nos eventos

Teclas (com janela): q sair | i iniciar/reiniciar | p parar | f salvar quadro em dados/capturas/
"""

import argparse
import json
import os
import sys
import time

import cv2

from robocar import configuracao, controle, desenho, protocolo
from robocar.camera import Camera
from robocar.leds import FALHAS_APAGA_LUZ, LedsRobo
from robocar.registro import FotosDebug, GravadorVideo, LogCSV
from robocar.visao import DetectorLinha

AUTO = "auto"


def argumentos():
    ap = argparse.ArgumentParser(description="Seguidor de linha - Robocar Blitz (Jetson Nano)")
    ap.add_argument("--config", help="arquivo de configuracao (padrao: config/config.json)")
    ap.add_argument("--fonte", help="csi | indice da webcam | arquivo de video")
    ap.add_argument("--esp32", help="porta serial da ESP32, ex.: /dev/ttyUSB0")
    ap.add_argument("--sem-leds", action="store_true", help="nao mexe na luz da camera nem no LED codigo-rodando")
    ap.add_argument("--sem-janela", action="store_true", help="nao abre janelas (uso no carro)")
    ap.add_argument("--limiar-fixo", type=float, help="ignora a calibracao e usa este limiar (0-255)")
    ap.add_argument("--gravar", nargs="?", const=AUTO, help="grava os quadros (.avi); padrao em dados/gravacoes/")
    ap.add_argument("--log", nargs="?", const=AUTO, help="log CSV por quadro; padrao em dados/logs/")
    ap.add_argument("--fotos", nargs="?", type=float, const=2.0, metavar="SEG",
                    help="sem janela (SSH): salva imagem+mascara a cada SEG s (padrao 2) e nos eventos "
                         "(largada, linha sumiu, parou) em dados/capturas/<data>/")
    ap.add_argument("--armar", action="store_true",
                    help="arma a ESP32 sem o botao (SOMENTE bancada, com as rodas suspensas)")
    ap.add_argument("--mostrar-config", action="store_true", help="mostra os parametros efetivos e sai")
    return ap.parse_args()


def carregar(args):
    ajustes = {}
    if args.limiar_fixo is not None:
        ajustes["visao"] = {"limiar_modo": "fixo", "limiar_fixo": args.limiar_fixo}
    if args.esp32:
        ajustes["esp32"] = {"porta": args.esp32}
    if args.sem_janela:
        ajustes["exibicao"] = {"janela": False}
    cfg = configuracao.carregar_config(args.config, ajustes)
    calib = None if args.limiar_fixo is not None else configuracao.carregar_calibracao()
    return cfg, calib


def fmt(x):
    return "--" if x is None else "%.3f" % x


def desligar_jetson():
    """Shutdown pedido pelo botao da ESP32 (segurado 3 s). Precisa da regra do sudo do 'make servico'."""
    import subprocess
    try:
        r = subprocess.call(["sudo", "-n", "/sbin/shutdown", "-h", "now"])
    except OSError as e:
        r = e
    if r != 0:
        print("ERRO: nao consegui desligar (%s). Rode 'make servico' (libera o shutdown sem senha) "
              "ou desligue com: sudo shutdown -h now" % r)
        return 1
    return 0


def textos_debug(direcao, erro, det, ctrl, info, esq, dir_, fps, proc_ms):
    return [
        ("Direcao: %s" % direcao, desenho.VERMELHO if erro is None else desenho.VERDE),
        ("Erro: %s  longe: %s" % (fmt(erro), fmt(det["erro_longe"])), desenho.AMARELO),
        ("%s  v=%.2f  E=%+.2f D=%+.2f" % (ctrl.estado, info["v"], esq, dir_), desenho.BRANCO),
        ("%.0f fps  proc %.1f ms  limiar %.0f%s" % (
            fps, proc_ms, det["limiar"], "  CRUZAMENTO" if det["cruzamento"] else ""), desenho.AMARELO),
    ]


def pode_desligar_sem_senha():
    """A regra do sudo do 'make preparar-jetson' esta instalada? (sudo -n -l nao pede senha)"""
    import subprocess
    try:
        with open(os.devnull, "w") as nada:
            return subprocess.call(["sudo", "-n", "-l", "/sbin/shutdown", "-h", "now"],
                                   stdout=nada, stderr=nada) == 0
    except OSError:
        return False


def salvar_quadro(cinza, n):
    caminho = configuracao.arquivo_de_dados("capturas", "png", time.strftime("%Y%m%d_%H%M%S_") + str(n))
    cv2.imwrite(caminho, cinza)
    print("Quadro salvo:", caminho)


def main():
    args = argumentos()
    try:
        cfg, calib = carregar(args)
    except configuracao.ErroConfiguracao as e:
        print("ERRO de configuracao:", e)
        return 2
    if args.mostrar_config:
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        return 0
    if calib:
        print("Calibracao: branco=%.1f preto=%.1f limiar=%.1f (%s)" % (
            calib["branco"], calib["preto"], calib["limiar"], calib.get("data", "")))
    elif cfg["visao"]["limiar_modo"] == "adaptativo":
        print("AVISO: sem config/calibracao.json - rode calibrar.py. Usando razao padrao.")

    leds = LedsRobo(ativo=not args.sem_leds)
    leds.luz(True)          # antes de abrir a camera: a exposicao automatica ja converge com a luz acesa
    try:
        cam = Camera(cfg["camera"], args.fonte)
    except Exception:
        leds.apagar()
        raise
    print("Fonte:", cam.descricao)
    detector = DetectorLinha(cfg["visao"], calib)
    if detector.razao != detector.razao_calibrada:
        print("AVISO: calibracao com contraste baixo (razao %.2f); usando %.2f. Melhore a pista/luz e recalibre."
              % (detector.razao_calibrada, detector.razao))
    ctrl = controle.Controlador(cfg["controle"], cfg["parada"])
    freio = controle.FreioFinal(cfg["parada"]["freio_s"])
    margem = cfg["controle"]["margem_centro"]
    janela = cfg["exibicao"]["janela"]
    a_cada = max(1, int(cfg["exibicao"]["a_cada_n_frames"]))
    periodo_print = 1.0 / max(0.1, cfg["exibicao"]["imprimir_hz"])

    link = None
    if cfg["esp32"]["porta"]:
        from robocar.esp32 import LinkESP32, abrir_porta
        link = LinkESP32(abrir_porta(cfg["esp32"]["porta"], cfg["esp32"]["baud"]))
        link.pedir_versao()
        print("ESP32 em %s - aperte o botao de largada para armar." % cfg["esp32"]["porta"])
        if not pode_desligar_sem_senha():
            print("AVISO: segurar a largada 3 s NAO vai desligar a Jetson (falta a regra do sudo). "
                  "Rode uma vez: make preparar-jetson")
    else:
        print("Sem ESP32: modo somente visao (comandos calculados, nao enviados).")
        ctrl.iniciar(time.time())

    gravador = None
    if args.gravar:
        destino = configuracao.arquivo_de_dados("gravacoes", "avi") if args.gravar == AUTO else args.gravar
        gravador = GravadorVideo(destino, cfg["camera"]["fps"])
        print("Gravando em", destino)
    log = None
    if args.log:
        destino = configuracao.arquivo_de_dados("logs", "csv") if args.log == AUTO else args.log
        log = LogCSV(destino)
        print("Log em", destino)

    fotos = None
    if args.fotos is not None:
        pasta = os.path.splitext(configuracao.arquivo_de_dados("capturas", "d"))[0]  # dados/capturas/<data_hora>
        fotos = FotosDebug(pasta, args.fotos)
        print("Fotos de depuracao em", pasta)

    armado_ant = False
    armar_pendente = bool(link and args.armar)  # a ESP32 so arma depois de estar PRONTO
    estado_ant = estado_foto_ant = ctrl.estado
    n, fps, proc_ms, falhas = 0, 0.0, 0.0, 0
    t_ant = t_print = time.time()
    desligar = False

    try:
        while True:
            ok, cinza = cam.ler()
            t = time.time()
            if not ok:
                if cam.eh_arquivo:
                    print("Fim do video.")
                    break
                falhas += 1
                leds.vivo(t, False)
                if falhas >= FALHAS_APAGA_LUZ:
                    leds.luz(False)     # luz apagada = camera sem quadros
                if falhas > 30:
                    print("ERRO: a camera parou de enviar quadros.")
                    break
                continue
            falhas = 0
            leds.luz(True)
            if gravador:
                gravador.escrever(cinza)

            t0 = time.time()
            det = detector.processar(cinza)

            tel = None
            if link:
                link.ler()
                tel = link.telemetria
                if tel and tel.get("desligar"):
                    print(">>> DESLIGAR: botao segurado com o robo parado. Desligando a Jetson...")
                    desligar = True
                    break
                if armar_pendente and tel and tel["estado"] == protocolo.PRONTO:
                    link.armar()
                    armar_pendente = False
                armado = bool(tel and tel["armado"])
                if armado and not armado_ant:
                    freio.cancelar()
                    detector.resetar()
                    ctrl.iniciar(t)
                    print(">>> LARGADA")
                elif armado_ant and not armado:
                    ctrl.aguardar()
                    print(">>> DESARMADO (%s)" % protocolo.NOMES_ESTADO.get(tel["estado"] if tel else -1, "?"))
                armado_ant = armado

            esq, dir_, info = ctrl.atualizar(det, t)
            if link:
                link.enviar_motores(esq, dir_)  # enviado sempre: mantem o link "vivo" na ESP32
            if ctrl.estado == controle.PARADO and estado_ant != controle.PARADO:
                print(">>> PARADO:", ctrl.motivo)
                freio.parou(t)          # zero armado = freio; desarma (roda solta) so depois de freio_s
            if link and freio.hora_de_desarmar(t):
                link.parar()
            estado_ant = ctrl.estado
            leds.vivo(t, ctrl.estado in (controle.SEGUINDO, controle.AVANCANDO, controle.BUSCANDO))
            proc_ms = 0.9 * proc_ms + 0.1 * (time.time() - t0) * 1000.0

            dt, t_ant = t - t_ant, t
            if dt > 0:
                fps = 0.9 * fps + 0.1 / dt if fps else 1.0 / dt
            n += 1

            erro = det["erro"]
            direcao = desenho.rotulo_direcao(erro, margem)
            if erro is None and ctrl.estado == controle.AVANCANDO:
                direcao = "SEM LINHA: RETO"
            elif erro is None:
                direcao = "PROCURAR %s" % ("DIREITA" if ctrl.ultimo_lado > 0 else "ESQUERDA")

            if fotos:
                motivo = ctrl.estado.lower() if ctrl.estado != estado_foto_ant else None
                estado_foto_ant = ctrl.estado
                salvo = fotos.talvez_salvar(t, lambda: desenho.painel_debug(cinza, det, textos_debug(
                    direcao, erro, det, ctrl, info, esq, dir_, fps, proc_ms)), motivo)
                if salvo and motivo:
                    print("Foto (%s): %s" % (motivo, salvo))

            if t - t_print >= periodo_print:
                t_print = t
                print("%-17s erro=%6s longe=%6s faixas=%d %s| %s v=%.2f E=%+.2f D=%+.2f | "
                      "%.0f fps proc=%.1f ms limiar=%.0f%s" % (
                          direcao, fmt(erro), fmt(det["erro_longe"]), det["n_validos"],
                          "CRUZ " if det["cruzamento"] else "", ctrl.estado, info["v"], esq, dir_,
                          fps, proc_ms, det["limiar"], " vbat=%.2fV" % tel["vbat"] if tel else ""))

            if log:
                log.escrever(t=t, proc_ms=proc_ms, erro=erro, erro_longe=det["erro_longe"],
                             inclinacao=det["inclinacao"], n_validos=det["n_validos"],
                             cruzamento=det["cruzamento"], marca=det["marca"], limiar=det["limiar"],
                             estado=ctrl.estado, v=info["v"], u=info["u"], esq=esq, dir=dir_,
                             vbat=tel["vbat"] if tel else None, enc_e=tel["enc_e"] if tel else None,
                             enc_d=tel["enc_d"] if tel else None,
                             estado_esp32=tel["estado"] if tel else None)

            if janela and n % a_cada == 0:
                textos = textos_debug(direcao, erro, det, ctrl, info, esq, dir_, fps, proc_ms)
                cv2.imshow("Seguidor de Linha", desenho.imagem_debug(cinza, det, textos))
                cv2.imshow("Mascara - Linha Preta", desenho.mascara_ampliada(det["mascara"]))
                tecla = cv2.waitKey(1) & 0xFF
                if tecla == ord("q"):
                    break
                elif tecla == ord("i"):
                    detector.resetar()
                    ctrl.iniciar(time.time())
                elif tecla == ord("p"):
                    ctrl.parar("tecla p")
                elif tecla == ord("f"):
                    salvar_quadro(cinza, n)
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario.")
    finally:
        leds.apagar()
        if link:
            link.fechar()
        cam.liberar()
        if gravador:
            gravador.fechar()
        if log:
            log.fechar()
        if janela:
            cv2.destroyAllWindows()
    if desligar:
        return desligar_jetson()
    return 0


if __name__ == "__main__":
    sys.exit(main())
