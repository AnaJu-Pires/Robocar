# Robocar Blitz - atalhos. Rode a partir da raiz do repositorio:  make <alvo>
# Variaveis: PYTHON (python3), PORTA (/dev/ttyUSB0), VIDEO (arquivo de video),
#            OPCOES (repassadas ao programa, ex.: OPCOES="--sem-janela --log")

PYTHON ?= python3
PORTA  ?= /dev/ttyUSB0
VIDEO  ?=
OPCOES ?=
JETSON := cd jetson &&

.PHONY: metricas chassi chassi-verificar chassi-cortar chassi-negativos sim-esp32 ajuda testes benchmark calibrar visao gravar video carro bancada movimento servico diagnostico calibrar-auto config placa drc limpar

ajuda:  ## lista os alvos
	@echo "Alvos (make <alvo>):"
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | expand -t 18

testes:  ## testes automaticos (sem camera e sem ESP32)
	$(JETSON) $(PYTHON) -m unittest discover -s testes -t . -v

benchmark:  ## tempo do algoritmo atual x original nesta maquina
	$(JETSON) $(PYTHON) -m testes.benchmark

calibrar:  ## calibracao preto/branco -> jetson/config/calibracao.json
	$(JETSON) $(PYTHON) calibrar.py $(OPCOES)

calibrar-auto:  ## calibracao sem janela (via SSH): linha e chao visiveis embaixo; salva e grava uma foto
	$(JETSON) $(PYTHON) calibrar.py --auto $(OPCOES)

visao:  ## camera ao vivo, so visualizacao (nao move motores)
	$(JETSON) $(PYTHON) seguir_linha.py $(OPCOES)

gravar:  ## camera ao vivo gravando quadros em dados/gravacoes/
	$(JETSON) $(PYTHON) seguir_linha.py --gravar $(OPCOES)

video:  ## reprocessa um video: make video VIDEO=dados/gravacoes/arquivo.avi
	@test -n "$(VIDEO)" || (echo "use: make video VIDEO=dados/gravacoes/arquivo.avi" && false)
	F="$$(realpath '$(VIDEO)')" && $(JETSON) $(PYTHON) seguir_linha.py --fonte "$$F" $(OPCOES)

carro:  ## modo corrida: ESP32 + sem janela + log em dados/logs/ (PORTA=/dev/ttyUSB0)
	$(JETSON) $(PYTHON) seguir_linha.py --esp32 $(PORTA) --sem-janela --log $(OPCOES)

sim-esp32:  ## simula o firmware da ESP32 no PC e testa com o codigo da Jetson (g++)
	bash firmware/simulacao/compilar.sh

bancada:  ## teste de motores com janela e log, armando pela Jetson (RODAS SUSPENSAS!)
	$(JETSON) $(PYTHON) seguir_linha.py --esp32 $(PORTA) --log --armar $(OPCOES)

movimento:  ## sem camera: frente, giro 360 e re pela ESP32 (largada no botao; OPCOES="--armar" = rodas no ar)
	$(JETSON) $(PYTHON) teste_movimento.py --esp32 $(PORTA) $(OPCOES)

servico:  ## instala o inicio automatico no boot (modo carro; pede a senha do sudo)
	sudo bash jetson/servico/instalar.sh $(PORTA)

metricas:  ## numeros da ultima corrida (ou LOG=dados/logs/x.csv; PULSOS=pulsos por volta da roda)
	$(JETSON) $(PYTHON) metricas_log.py $(LOG) $(if $(PULSOS),--pulsos-volta $(PULSOS),)

diagnostico:  ## junta logs, configuracao e fotos em ~/diagnostico_<data>.tar.gz
	bash jetson/servico/diagnostico.sh

config:  ## mostra os parametros efetivos (padrao + config.json)
	$(JETSON) $(PYTHON) seguir_linha.py --mostrar-config

placa:  ## regenera as saidas da placa da ESP32 (PDFs 1:1, furacao, STEP, imagens) com o kicad-cli
	bash hardware/placa_esp32/gerar_saidas.sh

drc:  ## placa da ESP32: DRC + so B.Cu + paridade esquema x placa (precisa do Python do KiCad)
	$(PYTHON) hardware/placa_esp32/verificar.py

chassi:  ## chassi v4 (3 andares): verifica e gera DXF, PDF 1:1, STEP, imagens (T=espessura FOLGA=folga do rasgo)
	cd mecanica/chassi_v4/fonte && $(PYTHON) gerar.py

chassi-verificar:  ## chassi v4 (3 andares): so as verificacoes (massa, CG, tombamento, interferencia, cabos...)
	cd mecanica/chassi_v4/fonte && $(PYTHON) gerar.py --so-verificar

chassi-cortar:  ## chassi v4 (3 andares): como chassi-verificar, mas medida estimada que muda o corte vira ERRO
	cd mecanica/chassi_v4/fonte && $(PYTHON) gerar.py --so-verificar --para-cortar

chassi-negativos:  ## chassi v4 (3 andares): prova que cada verificacao pega um defeito plantado (~2 min)
	cd mecanica/chassi_v4/fonte && $(PYTHON) testes_negativos.py

limpar:  ## remove caches do Python
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
