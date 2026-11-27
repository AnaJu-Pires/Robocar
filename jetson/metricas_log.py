#!/usr/bin/env python3
"""Numeros de uma corrida a partir do log CSV (make carro / seguir_linha.py --log).

Uso:
  python3 metricas_log.py                         # ultimo log em dados/logs/
  python3 metricas_log.py dados/logs/arquivo.csv --pulsos-volta 560
  python3 metricas_log.py --json                  # saida em JSON (para colar no diario)
--pulsos-volta: pulsos do encoder (ja em x4) por volta da RODA, medidos no T07. Sem ele, so os pulsos.
"""
import argparse
import csv
import glob
import json
import os
import sys

from robocar import metricas

AQUI = os.path.dirname(os.path.abspath(__file__))


def ultimo_log():
    arqs = sorted(glob.glob(os.path.join(AQUI, "..", "dados", "logs", "*.csv")), key=os.path.getmtime)
    return arqs[-1] if arqs else None


def principal(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", nargs="?", help="arquivo CSV (padrao: o mais recente em dados/logs/)")
    ap.add_argument("--pulsos-volta", type=float, default=None)
    ap.add_argument("--roda-mm", type=float, default=42.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    arq = a.log or ultimo_log()
    if not arq or not os.path.exists(arq):
        print("Nenhum log encontrado. Rode 'make carro' (grava em dados/logs/) ou passe o arquivo.")
        return 1
    with open(arq) as f:
        linhas = list(csv.DictReader(f))
    m = metricas.calcular(linhas, a.pulsos_volta, a.roda_mm / 1000.0)
    if a.json:
        print(json.dumps(m, indent=1, sort_keys=True))
    else:
        print("Log: %s" % arq)
        print(metricas.texto(m))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
