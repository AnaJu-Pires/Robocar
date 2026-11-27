# 09 — Roteiro de testes no hardware (tudo pelo SSH)

Do mais simples ao robô na pista. **Não pule etapa**: cada uma depende da anterior. Tudo roda pelo SSH, sem
monitor na Jetson. Os critérios e o registro continuam em [06_testes.md](06_testes.md).

Em cada etapa: rode os comandos, confira o **critério**, e me mande o que está em **"Mandar"**.

## Como trabalhar pelo SSH

* **Pela rede (recomendado):** cabo de rede da Jetson no roteador, o mesmo do PC. A Jetson ganha internet (para o
  `git`) e o PC a acha pelo nome. No **PowerShell do Windows**:
  ```bash
  ssh blitz@blitz-desktop.local
  ```
  Se o nome não responder, pegue o IP da Jetson na lista de aparelhos do roteador (ex.: http://192.168.15.1) e use
  `ssh blitz@IP`. Nos comandos abaixo, troque `blitz-desktop.local` pelo IP se for o caso.
  Depois de ligar ou reiniciar, espere **2–3 min**: o `ping` pode responder antes de o SSH estar pronto
  ("Connection refused"). O endereço IPv6 muda a cada boot: use sempre o nome `.local`.
* **Pelo cabo micro-USB** (`ssh blitz@192.168.55.1`): **não use no PC com Windows 11 da equipe.** Em 27/11 o
  Windows reconheceu a Jetson como "UsbNcm Host Device", não recebeu endereço, e desativar o adaptador ou tirar o cabo
  **travou e reiniciou o PC** várias vezes (falha do driver do Windows, não da Jetson).
* Trazer arquivos da Jetson para o PC (rode **no PC**, não dentro do SSH). Exemplo para uma pasta de fotos:
  ```bash
  scp -r blitz@blitz-desktop.local:Robocar/dados/capturas/PASTA .
  ```
  O `make diagnostico` junta logs, configuração e fotos num arquivo só e mostra o `scp` para trazê-lo.
* **Não** use `ssh -X` nem os comandos com janela (`make visao`, `make calibrar`, `make bancada`): pelo SSH use
  `make fotos`, `make calibrar-auto` e `make carro`. O `ssh -X` derrubava a câmera.
* Antes de qualquer teste com a câmera ou a ESP32: `sudo systemctl stop robocar` (se o serviço estiver instalado).
* Mude **um parâmetro por vez** no `jetson/config/config.json` (`nano jetson/config/config.json`).

## Com monitor na Jetson (etapas 1 a 3 sem precisar de outra pessoa)

Para câmera, calibração e detecção dá para trabalhar **direto na Jetson**, ao lado do robô: monitor HDMI, teclado e
mouse, abrir o Terminal (**Ctrl+Alt+T**) e rodar os comandos com janela. Nenhum deles abre a porta da ESP32: o robô
**não anda**.

1. `cd ~/Robocar && git pull`
2. **Câmera e distância cega:** `make visao`. A janela mostra a imagem ao vivo com a região analisada (linha
   azul-clara). Ponha a tira de fita atravessada à frente do robô e vá puxando até ela sumir pela borda de baixo;
   meça da tira até o eixo das rodas. `q` fecha.
3. **Calibração com escolha da exposição:** robô sobre a linha (linha e chão dentro do retângulo verde), depois
   `make calibrar`:
   * olhe "**Ao vivo: ... contraste**" no rodapé (verde = bom, ≥ 60; vermelho = baixo);
   * aperte **E** para trocar a exposição (auto, 1, 2, 3, 4, 6, 8 ms; a imagem some ~2 s) e **G** para o ganho;
     fique com a combinação de **maior contraste** em que o chão não fica estourado (branco abaixo de ~230);
   * aperte **A**: calibra e **salva** (branco, preto e a exposição/ganho escolhidos). `q` fecha.
   * O `seguir_linha.py` passa a usar a mesma exposição sozinho (aparece "Camera: exposicao ... (da calibracao)").
4. **Detecção empurrando o robô:** `make visao OPCOES="--log"` e empurre sobre reta, curva, cruzamento, X e fim de
   linha, olhando a janela; depois `make metricas`.

## Etapa 0 — Preparar (uma vez)

1. Atualizar o código na Jetson. Precisa de internet (Wi-Fi):
   ```bash
   cd ~/Robocar && git fetch origin && git checkout -B claude/seguir-linha-pista origin/claude/seguir-linha-pista
   ```
2. Testes automáticos e preparação do sistema:
   ```bash
   make testes
   ```
   ```bash
   make preparar-jetson
   ```
   O `preparar-jetson` tira o gpsd e o ModemManager da porta da ESP32 e deixa o journal persistente. Depois:
   `sudo reboot`, espere ~1 min e entre de novo no SSH.
3. **Gravar o firmware da ESP32** desta branch (protocolo **v2**; motores com `INVERTER_E = true`), pela Arduino IDE no
   PC ([firmware/README.md](../firmware/README.md)). A Jetson e a ESP32 precisam da mesma versão.

**Critério:** `make testes` sem falhas; `preparar-jetson` mostra "camera: detectada" (se não, desligue tudo e
confira o cabo flat). **Mandar:** a saída do `make preparar-jetson`.

## Etapa 1 — Câmera: o que ela vê

Robô parado sobre a linha reta (pode ser fita isolante preta de 19–20 mm sobre EVA/cartolina clara):
```bash
make fotos SEG=1
```
Deixe ~5 s e aperte Ctrl+C. Ele mostra a pasta das fotos; traga 2 ou 3 para o PC.

**Distância cega** (define quanto o robô anda depois de a linha sumir): com o `make fotos SEG=0.5` rodando,
ponha uma tira de fita preta **atravessada** no chão, à frente do robô, e vá puxando-a em direção ao robô até ela
**sumir pela borda de baixo** da imagem. Meça com régua a distância da tira ao **eixo das rodas**.

**Critério:** a linha aparece embaixo, perto do centro, nítida; a linha azul-clara (início da região analisada)
fica acima da linha preta na metade de baixo. **Mandar:** 2 fotos (uma com a linha, uma com a tira atravessada) e
a distância cega em cm.

## Etapa 2 — Calibração e exposição

Com a linha e o chão claro visíveis na parte de baixo:
```bash
make calibrar-auto
```
Ele mostra branco, preto e **contraste** e salva uma foto em `dados/capturas/`.

* **Contraste ≥ 60:** ótimo, siga.
* **Contraste < 60** (em 22/11 deu 40): trave a exposição. No `config.json`, dentro de `"camera"`:
  ```json
  "exposicao_ns": 3000000, "ganho": 4, "trava_balanco_branco": true
  ```
  Rode `make calibrar-auto` de novo. Teste 2, 3 e 6 ms (`2000000`, `3000000`, `6000000`): fica o que der mais
  contraste **sem estourar o branco** (branco abaixo de ~230). Mais que 6 ms borra a imagem com o robô andando.
* Repita com a luz da sala acesa e apagada (e depois com a fita de LED, quando chegar).

**Mandar:** as linhas de resultado do `calibrar-auto` de cada tentativa e a foto da melhor.

## Etapa 3 — Detecção, empurrando o robô com a mão (sem motores)

ESP32 desconectada ou sem bateria. Sem ESP32, o programa já começa "seguindo" e só calcula os comandos:
```bash
make fotos SEG=0.5 OPCOES="--log"
```
Empurre o robô devagar sobre: reta, curva, **cruzamento de 90°**, **interseção em X** e **fim de linha**. Depois:
```bash
make metricas
```
Grave também um vídeo curto do mesmo trajeto, para eu ajustar a visão no PC:
```bash
make gravar OPCOES="--sem-janela"
```

**Critério:** nas fotos, os pontos verdes ficam sobre a linha; no cruzamento aparece **CRUZAMENTO** e os pontos
continuam na linha que o robô seguia; no fim da linha, "SEM LINHA: RETO" (estado AVANCANDO). "Quadros com a
linha" ≥ 95 % fora do fim. **Mandar:** `make diagnostico` (traz log e fotos) e o vídeo de `dados/gravacoes/`.

## Etapa 4 — Serial Jetson ↔ ESP32 (rodas no ar)

ESP32 no USB, bateria ligada, **rodas suspensas**:
```bash
make carro
```
Deve aparecer `ESP32: robocar_esp32,v2` e nenhum `ERRO`. Aperte e solte a largada: `>>> LARGADA`. Aperte de novo:
para. Ctrl+C fecha o programa e desarma na hora.

**Watchdog (T08):** arme de novo e, **noutra janela de SSH**, mate o programa sem aviso:
```bash
pkill -9 -f seguir_linha.py
```
As rodas têm de frear em 250 ms e o LED da ESP32 apagar em ~1 s (desarmou sozinho, sem a Jetson).

**Critério:** versão v2, sem `AVISO serial`; LED aceso armado; com o `pkill -9`, freia e o LED apaga. **Mandar:** a
saída do terminal (copiar e colar).

## Etapa 5 — Motores e encoders na bancada (rodas no ar)

```bash
make movimento OPCOES="--armar"
```
Frente, giro e ré, com os pulsos dos encoders de cada etapa.

* As duas rodas giram para a frente na "FRENTE"? Se uma girar ao contrário: `INVERTER_E/INVERTER_D` no
  `config.h` (gravar de novo).
* **Encoder esquerdo:** nos logs de 22/11 ele ficou em **0 em todas as corridas**. Se continuar 0: desligue, confira o
  cabo no J12 (A, B, −, +) e meça com o multímetro, girando a roda à mão, se A e B alternam entre ~0 e ~3,3 V (T06).

**Critério:** sentido certo nas duas rodas; os dois encoders contando e com o sinal coerente. **Mandar:** a saída do
terminal.

## Etapa 6 — Pista, devagar

Comece com `"v_max": 0.25` no `config.json`. Robô no início da linha:
```bash
make carro OPCOES="--fotos 1"
```
Largada pelo botão. Ao terminar, Ctrl+C e `make metricas`. Faça um trecho por vez: reta → curva → cruzamento →
X → **fim da linha dentro de um box** (desenhe um retângulo de fita em volta do fim da linha, do tamanho do box da
pista, se souberem).

**Parar dentro do box:** o robô segue reto `controle.avanco_s` (0,35 s) depois de a linha sumir, freia e para.
* Parou **antes** do box: aumente `avanco_s` (cada +0,1 s ≈ +4 cm a `v_avanco` 0,25; estimativa, confira).
* Passou do box: diminua.

**Critério:** completa cada trecho sem "linha perdida" e para dentro do box em 5 de 5 tentativas. **Mandar:**
`make diagnostico` de cada sessão (log + fotos dos eventos) e o que vocês viram (ex.: "no X ele virou para a
esquerda").

## Etapa 7 — Mais rápido

Suba `v_max` de 0,05 em 0,05, uma volta completa de cada vez. A partir de 0,40, confira se a roda de dentro levanta
nas curvas fechadas ([D-032](decisoes.md)). Meta: 20 voltas seguidas sem falha (T14). Congelar o código em 02/12.

**Mandar:** `make metricas` de cada velocidade.

## Depois de cada sessão

* Desligue a Jetson **antes** da chave: `sudo shutdown -h now` pelo SSH. Sem SSH (na prova), com o robô parado e
  o programa rodando, **segure a largada 3 s**: o LED da ESP32 pisca muito rápido e, quando fizer **2 piscadas por
  segundo** (ou apagar), pode desligar a chave. Faça o teste T15 uma vez para medir o tempo.
  A conexão SSH cai; espere mais **20 s** e só então desligue a chave. O LED verde da Jetson **não** apaga (ele fica
  no 5 V): não espere por ele.
* Anote em [06_testes.md](06_testes.md) (ou me mande que eu anoto).
