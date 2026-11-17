# Robocar Blitz - atalhos. Rode a partir da raiz do repositorio:  make <alvo>
# Variaveis: PYTHON (python3), PORTA (/dev/ttyUSB0), VIDEO (arquivo de video),
#            OPCOES (repassadas ao programa, ex.: OPCOES="--sem-janela --log")

PYTHON ?= python3
PORTA  ?= /dev/ttyUSB0
VIDEO  ?=
OPCOES ?=
JETSON := cd jetson &&

.PHONY: ajuda testes benchmark calibrar visao gravar video carro bancada config limpar

ajuda:  ## lista os alvos
	@echo "Alvos (make <alvo>):"
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | expand -t 14

testes:  ## testes automaticos (sem camera e sem ESP32)
	$(JETSON) $(PYTHON) -m unittest discover -s testes -t . -v

benchmark:  ## tempo do algoritmo atual x original nesta maquina
	$(JETSON) $(PYTHON) -m testes.benchmark

calibrar:  ## calibracao preto/branco -> jetson/config/calibracao.json
	$(JETSON) $(PYTHON) calibrar.py $(OPCOES)

visao:  ## camera ao vivo, so visualizacao (nao move motores)
	$(JETSON) $(PYTHON) seguir_linha.py $(OPCOES)

gravar:  ## camera ao vivo gravando quadros em dados/gravacoes/
	$(JETSON) $(PYTHON) seguir_linha.py --gravar $(OPCOES)

video:  ## reprocessa um video: make video VIDEO=dados/gravacoes/arquivo.avi
	@test -n "$(VIDEO)" || (echo "use: make video VIDEO=dados/gravacoes/arquivo.avi" && false)
	F="$$(realpath '$(VIDEO)')" && $(JETSON) $(PYTHON) seguir_linha.py --fonte "$$F" $(OPCOES)

carro:  ## modo corrida: ESP32 + sem janela + log em dados/logs/ (PORTA=/dev/ttyUSB0)
	$(JETSON) $(PYTHON) seguir_linha.py --esp32 $(PORTA) --sem-janela --log $(OPCOES)

bancada:  ## teste de motores com janela e log, armando pela Jetson (RODAS SUSPENSAS!)
	$(JETSON) $(PYTHON) seguir_linha.py --esp32 $(PORTA) --log --armar $(OPCOES)

config:  ## mostra os parametros efetivos (padrao + config.json)
	$(JETSON) $(PYTHON) seguir_linha.py --mostrar-config

limpar:  ## remove caches do Python
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
