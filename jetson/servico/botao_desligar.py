#!/usr/bin/env python3
"""Robocar Blitz - botao de desligar a Jetson (J41 pino 18) e LED "pode desligar a chave" (J41 pino 16).

Roda como root no servico botao-desligar.service (instalado por 'make servico'), separado do programa do robo:
funciona mesmo com o robocar.service parado, com a ESP32 desconectada ou com o programa travado.

  segurar o botao 2 s  -> LED pisca rapido 1,5 s -> shutdown -> LED aceso ate a Jetson cortar a energia
  LED APAGOU (chave ainda ligada) -> pode desligar a chave geral

Uso:
  sudo python3 botao_desligar.py            # servico (desliga de verdade)
  sudo python3 botao_desligar.py --teste    # mostra o botao e pisca o LED ao apertar; NAO desliga
Opcoes de teste: --sysfs DIR (GPIO falso), --comando "echo desligar" (troca o shutdown), --uma-vez.
"""
import argparse
import os
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from robocar.botao_desligar import GpioSysfs, MaquinaBotao, GPIO_BOTAO, GPIO_LED  # noqa: E402
from robocar.leds import GPIO_LUZ, GPIO_VIVO  # noqa: E402

PERIODO_S = 0.05


def liberar_leds_do_robo(sysfs):
    """Luz da camera (gpio194) e LED codigo-rodando (gpio16), D-033: saida em 0 e escrita liberada para o
    programa do robo (que roda sem sudo). Falha aqui so avisa: o botao de desligar continua funcionando."""
    for n in (GPIO_LUZ, GPIO_VIVO):
        g = GpioSysfs(n, sysfs)
        try:
            g.exportar()
            g.como_saida(0)
            os.chmod(os.path.join(g.dir, 'value'), 0o666)
        except (IOError, OSError) as e:
            print('AVISO: gpio%d (LEDs do robo) indisponivel: %s' % (n, e))


def principal(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--teste', action='store_true', help='nao desliga; mostra o botao e pisca o LED')
    ap.add_argument('--sysfs', default='/sys/class/gpio', help='diretorio do GPIO (testes)')
    ap.add_argument('--comando', default='/bin/systemctl poweroff', help='comando de desligar')
    ap.add_argument('--segurar', type=float, default=2.0, help='segundos segurando o botao (padrao 2)')
    ap.add_argument('--uma-vez', action='store_true', help='sai depois de pedir o desligamento (testes)')
    args = ap.parse_args(argv)

    botao = GpioSysfs(GPIO_BOTAO, args.sysfs)
    led = GpioSysfs(GPIO_LED, args.sysfs)
    try:
        botao.exportar(); botao.como_entrada()
        led.exportar(); led.como_saida(1)          # LED aceso = Linux rodando
    except (IOError, OSError) as e:
        print('ERRO no GPIO (%s). Rode como root; confira se o SPI do J41 nao foi ligado no jetson-io.' % e)
        return 1
    liberar_leds_do_robo(args.sysfs)

    def sair(sig, frame):
        try:
            led.escrever(1)       # nunca apagar: so o corte de energia do modulo apaga o LED
        except (IOError, OSError):
            pass
        sys.exit(0)
    signal.signal(signal.SIGTERM, sair)
    signal.signal(signal.SIGINT, sair)

    maq = MaquinaBotao(segurar_s=args.segurar)
    print('botao_desligar: pronto (gpio%d = botao, gpio%d = LED)%s' % (GPIO_BOTAO, GPIO_LED, ' [TESTE]' if args.teste else ''))
    ultimo, ultimo_led = None, None
    while True:
        t = time.time()
        try:
            apertado = botao.ler() == 0
        except (IOError, OSError):
            apertado = False
        if args.teste and apertado != ultimo:
            print('%.2f botao %s' % (t, 'APERTADO' if apertado else 'solto'))
        ultimo = apertado
        acao = maq.passo(t, apertado)
        if acao == 'desligar':
            print('botao_desligar: botao segurado %.1f s -> desligando%s' % (args.segurar, ' (TESTE: nao desliga)' if args.teste else ''))
            sys.stdout.flush()
            if not args.teste:
                subprocess.call(args.comando, shell=True)
            elif not args.uma_vez:
                maq = MaquinaBotao(segurar_s=args.segurar)   # no teste, volta a esperar
                maq.estado, maq.t_desligou = maq.DESLIGANDO, t
        estado_led = maq.led(t)
        if estado_led != ultimo_led:
            try:
                led.escrever(estado_led)
            except (IOError, OSError):
                pass
            ultimo_led = estado_led
        if args.uma_vez and maq.estado == maq.DESLIGANDO and t - maq.t_desligou > maq.piscar_s:
            led.escrever(1)
            return 0
        if args.teste and maq.estado == maq.DESLIGANDO and t - maq.t_desligou > maq.piscar_s:
            maq = MaquinaBotao(segurar_s=args.segurar)
            maq.estado = maq.PRONTO
        time.sleep(PERIODO_S)


if __name__ == '__main__':
    sys.exit(principal())
