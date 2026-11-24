# jetson/

Software da Jetson Nano: visão, controle e comunicação com a ESP32. A arquitetura e os algoritmos estão em [docs/04_software.md](../docs/04_software.md).

## Instalação na Jetson Nano 4 GB (JetPack 4.6.x)

```bash
sudo apt install python3-numpy python3-serial
sudo usermod -aG dialout $USER                  # acesso à serial da ESP32 (sair e entrar de novo)
python3 -c "import cv2; print(cv2.getBuildInformation())" | grep -i gstreamer   # deve mostrar YES
sudo nvpmodel -m 0 && sudo jetson_clocks        # modo 10 W: exige 5 V / >= 4 A no J25 com J48 fechado
```
Se a fonte de bancada não fornecer 4 A, use `sudo nvpmodel -m 1` (5 W).
**Não instale `opencv-python` por pip na Jetson:** ele vem sem GStreamer e a câmera CSI não abre.

## Uso

Os comandos rodam na raiz do repositório (ver `make ajuda`):

| Comando | O que faz |
|---|---|
| `make testes` | testes automáticos |
| `make calibrar` | calibração preto/branco → `config/calibracao.json` |
| `make visao` | câmera ao vivo com janelas (não move motores) |
| `make gravar` | idem, gravando vídeo em `dados/gravacoes/` |
| `make video VIDEO=dados/gravacoes/x.avi` | reprocessa um vídeo |
| `make bancada PORTA=/dev/ttyUSB0` | com a ESP32, arma pela Jetson: **rodas suspensas** |
| `make movimento PORTA=/dev/ttyUSB0` | sem câmera: frente, giro de 360° e ré; largada pelo botão da ESP32 (`OPCOES="--giro 2.2"` ajusta o giro; `--armar` só com as rodas suspensas) |
| `make carro PORTA=/dev/ttyUSB0` | modo corrida: sem janela, com log; a largada é o botão |
| `make config` | parâmetros efetivos |

Diretamente: `cd jetson && python3 seguir_linha.py --help`.
Teclas da janela: `q` sair, `i` iniciar, `p` parar, `f` salvar o quadro.

## Início automático no boot (dia da prova)

Na prova não há SSH: a Jetson liga, o programa abre sozinho no modo corrida e espera o **botão de largada**.

```bash
make servico PORTA=/dev/ttyUSB0      # instala e ativa (uma vez); vale a partir do próximo boot
sudo systemctl start robocar         # iniciar agora, sem reiniciar
journalctl -u robocar -f             # ver as mensagens (LARGADA, PARADO, erros)
sudo systemctl stop robocar          # parar: libera a câmera e a porta para make visao/calibrar/bancada
sudo systemctl disable --now robocar # desligar o início automático
```

* O robô **não anda ao ligar**: só depois do botão. Se a ESP32 não estiver conectada, o serviço tenta de novo a cada ~3 s.
* Enquanto o serviço roda, **nenhum outro programa** abre a câmera ou a ESP32 (`make visao`, `calibrar`, `bancada`, `movimento`): pare o serviço antes.
* Logs CSV de cada corrida em `dados/logs/`, como no `make carro`.
* Arquivos: `jetson/servico/` (`robocar.service`, `iniciar.sh`, `instalar.sh`).

## Desenvolvimento no PC

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r jetson/requirements.txt
make testes
make video VIDEO=dados/gravacoes/arquivo.avi     # vídeos gravados na Jetson
```

## Onde mexer

| Quero… | Arquivo |
|---|---|
| ajustar um parâmetro | `config/config.json` (lista completa: `robocar/configuracao.py`) |
| mudar a detecção da linha | `robocar/visao.py` + `testes/test_visao.py` |
| mudar a lei de controle | `robocar/controle.py` + `testes/test_controle.py` |
| mudar mensagens com a ESP32 | `robocar/protocolo.py` + firmware + `docs/05_protocolo_serial.md` (mesmo commit) |
