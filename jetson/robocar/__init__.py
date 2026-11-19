"""Software da Jetson Nano do Robocar Blitz (RoboCar Race 2026, categoria Micro).

Modulos (dependencias apontam sempre para baixo; nenhum modulo importa um programa):

    configuracao  parametros padrao + config/config.json + calibracao.json
    camera        captura (CSI via GStreamer, webcam ou video)
    visao         deteccao da linha (logica pura, testavel)
    controle      lei de controle e estados (logica pura, testavel)
    protocolo     formato das mensagens Jetson <-> ESP32 (logica pura, testavel)
    esp32         porta serial (usa protocolo)
    desenho       sobreposicoes de depuracao na imagem
    registro      log CSV e gravacao de video em dados/

Compatibilidade: Python 3.6 e NumPy 1.13 (JetPack 4.6).
"""

__version__ = "0.2.0"
