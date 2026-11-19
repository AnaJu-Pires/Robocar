"""Parametros do sistema: valores padrao (fonte unica), arquivo da equipe e calibracao.

Ordem de prioridade:  PADRAO (este arquivo)  <  config/config.json  <  opcoes de linha de comando.
Chaves desconhecidas no config.json geram erro (pega erro de digitacao antes de ir para a pista).
Chaves iniciadas por "_" sao comentarios e sao ignoradas.
"""

import copy
import json
import os
import time

PASTA_JETSON = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_REPO = os.path.dirname(PASTA_JETSON)
PASTA_CONFIG = os.path.join(PASTA_JETSON, "config")
PASTA_DADOS = os.path.join(PASTA_REPO, "dados")
ARQ_CONFIG = os.path.join(PASTA_CONFIG, "config.json")
ARQ_CALIBRACAO = os.path.join(PASTA_CONFIG, "calibracao.json")

PADRAO = {
    "camera": {
        "fonte": "csi",               # "csi", indice de webcam ("0") ou caminho de video
        "sensor_id": 0,
        "captura_largura": 1280,      # modo do sensor IMX219; 1920x1080@30 era o do codigo original
        "captura_altura": 720,
        "fps": 60,
        "flip_method": 0,             # 0-7 (nvvidconv); 2 = girar 180 graus
        "saida_largura": 320,         # resolucao processada (reducao feita no hardware)
        "saida_altura": 180,
        "exposicao_ns": None,         # ex.: 2000000 = 2 ms (fixa); None = automatica
        "ganho": None,                # ex.: 4; None = automatico
        "trava_auto_exposicao": False,
    },
    "visao": {
        "inicio_roi": 0.45,           # fracao da altura onde comeca a regiao analisada
        "n_faixas": 4,                # faixas horizontais (de baixo/perto para cima/longe)
        "limiar_modo": "adaptativo",  # "adaptativo" | "fixo" | "otsu"
        "limiar_fixo": 60.5,          # usado no modo "fixo" (valor do codigo original)
        "razao_limiar_padrao": 0.55,  # limiar/branco quando nao ha calibracao.json
        "percentil_branco": 90,       # percentil da ROI que mede o "branco" atual
        "limiar_min": 15,
        "limiar_max": 220,
        "abertura": True,             # filtro morfologico 3x3 contra ruido
        "frac_coluna": 0.4,           # fracao de pixels escuros para a coluna contar como linha
        "largura_min_px": 2,
        "gap_max_px": 2,              # une trechos separados por reflexo
        "fator_largo": 2.5,           # largura > fator x largura tipica = faixa "larga" (cruzamento)
        "largura_larga_frac": 0.3,    # ou largura > fracao da imagem
        "salto_max_frac": 0.35,       # deslocamento maximo aceito em relacao a posicao prevista
        "preferencia_bifurcacao": "reto",  # "reto" | "esquerda" | "direita"
        "marca_frac_escura": 0.45,    # fracao escura da ROI que conta como "marca" (box)
    },
    "controle": {
        "kp": 0.6,
        "kd": 0.05,
        "k_frente": 0.3,              # peso do erro da faixa mais distante (antecipacao)
        "v_max": 0.35,                # fracao do PWM maximo (conservador para os primeiros testes)
        "v_min": 0.2,
        "severidade_max": 0.6,        # erro a partir do qual a velocidade cai para v_min
        "v_busca": 0.25,
        "tempo_busca_s": 0.6,         # linha perdida por mais tempo -> PARADO
        "margem_centro": 0.12,        # so para o rotulo ESQUERDA/RETO/DIREITA
    },
    "parada": {
        "usar_marca": False,          # ligar quando soubermos como o box e marcado
        "tempo_minimo_s": 5.0,        # ignora marcas logo apos a largada
        "frames_confirmacao": 3,
        "atraso_s": 0.0,              # tempo entre ver a marca e parar
    },
    "esp32": {
        "porta": None,                # ex.: "/dev/ttyUSB0"
        "baud": 115200,
    },
    "exibicao": {
        "janela": True,
        "a_cada_n_frames": 2,
        "imprimir_hz": 2.0,
    },
}


class ErroConfiguracao(ValueError):
    pass


def _mesclar(base, novo, caminho=""):
    for chave, valor in novo.items():
        if chave.startswith("_"):
            continue
        if chave not in base:
            raise ErroConfiguracao("parametro desconhecido: %s%s" % (caminho, chave))
        if isinstance(base[chave], dict):
            if not isinstance(valor, dict):
                raise ErroConfiguracao("%s%s deve ser uma secao {...}" % (caminho, chave))
            _mesclar(base[chave], valor, caminho + chave + ".")
        else:
            base[chave] = valor
    return base


def carregar_config(caminho=None, ajustes=None):
    """PADRAO + config.json (se existir) + ajustes (dict aninhado)."""
    cfg = copy.deepcopy(PADRAO)
    caminho = caminho or ARQ_CONFIG
    if os.path.exists(caminho):
        with open(caminho, "r") as f:
            try:
                _mesclar(cfg, json.load(f))
            except ErroConfiguracao as e:
                raise ErroConfiguracao("%s: %s" % (caminho, e))
    if ajustes:
        _mesclar(cfg, ajustes)
    return cfg


def carregar_calibracao(caminho=None):
    """Dicionario da calibracao ou None se ainda nao foi feita."""
    caminho = caminho or ARQ_CALIBRACAO
    if not os.path.exists(caminho):
        return None
    with open(caminho, "r") as f:
        return json.load(f)


def salvar_calibracao(branco, preto, extras=None, caminho=None):
    if branco <= preto:
        raise ValueError("branco (%.1f) deve ser maior que preto (%.1f)" % (branco, preto))
    limiar = (branco + preto) / 2.0
    dados = {
        "branco": round(float(branco), 1),
        "preto": round(float(preto), 1),
        "limiar": round(float(limiar), 1),
        "razao": round(float(limiar / branco), 4),  # usada pelo limiar adaptativo
        "data": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if extras:
        dados.update(extras)
    caminho = caminho or ARQ_CALIBRACAO
    with open(caminho, "w") as f:
        json.dump(dados, f, indent=2)
    return dados


def arquivo_de_dados(subpasta, extensao, nome=None):
    """Caminho em dados/<subpasta>/ com nome automatico por data/hora."""
    pasta = os.path.join(PASTA_DADOS, subpasta)
    if not os.path.isdir(pasta):
        os.makedirs(pasta)
    nome = nome or time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(pasta, "%s.%s" % (nome, extensao))
