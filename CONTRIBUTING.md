# Como trabalhar neste repositório

## 1. Onde cada coisa fica

| Tipo | Lugar | Regra |
|---|---|---|
| Lógica Python (visão, controle, protocolo…) | `jetson/robocar/` | sem E/S nos módulos de lógica; nada aqui importa um programa |
| Programas executáveis | `jetson/*.py` | finos: leem argumentos e chamam a biblioteca |
| Parâmetros | padrão em `jetson/robocar/configuracao.py` (`PADRAO`); ajustes em `jetson/config/config.json` | parâmetro novo: entra no `PADRAO` com comentário e na tabela de `docs/04_software.md` |
| Testes | `jetson/testes/test_*.py` (unittest) | todo comportamento novo ganha teste |
| Firmware | `firmware/robocar_esp32/` | pinos e constantes **só** em `config.h` |
| Documentação | `docs/NN_assunto.md` | cada fato em um lugar só; nos outros, link |
| Decisões técnicas | `docs/decisoes.md` | decisão relevante = nova entrada D-xxx |
| Vídeos, logs, capturas | `dados/` | nunca versionar (já está no `.gitignore`) |
| Compras | `compras/` | a planilha é o documento; o CSV original não se altera |
| Placa eletrônica (KiCad) | `hardware/placa_esp32/` | editar no KiCad; o `.kicad_sch` é a fonte das ligações e a placa é atualizada a partir dele; pinos iguais ao `config.h`; **só cobre em B.Cu** (o `.kicad_dru` barra F.Cu e vias; o que não couber vira jumper JP); 3D só nativo ou baixado; a cada mudança rodar o ERC no KiCad, `make drc` e `make placa` |
| CAD (STL/STEP), quando houver | `hardware/cad/` | criar a pasta quando existir o primeiro arquivo |

## 2. Convenções
* **Idioma:** português, sem acentos em nomes de arquivos e identificadores (o Python 3.6 da Jetson e o Arduino não gostam de acentos).
* **Nomes:** arquivos e pastas em minúsculas com `_` (exceto README, CONTRIBUTING, CHANGELOG e Makefile). Funções e variáveis `snake_case`; classes `CamelCase`; constantes `MAIUSCULAS`.
* **Python 3.6 / NumPy 1.13** (JetPack 4.6): sem `dataclasses`, walrus, `np.quantile` ou anotações de tipos genéricos (`list[int]`). Conferir com `pip install vermin && vermin -t=3.6- jetson`.
* **Unidades:** comandos dos motores normalizados em [−1, 1] na Jetson e em −1000…1000 no protocolo; tensões em V na Jetson e em mV na ESP32.

## 3. Git
Ainda não é um repositório git. Para começar:
```bash
git init && git add . && git commit -m "Estrutura inicial do projeto (v0.2.0)"
```
* `main` sempre funcional (passa em `make testes`). Trabalho novo em ramos (`git switch -c visao-limiar-otsu`).
* Mensagens no imperativo, em português: `Ajusta kp após teste T12 na pista`.
* Mudou o protocolo? Altere `protocolo.py`, o firmware, `docs/05_protocolo_serial.md` e os testes **no mesmo commit** e incremente a versão.
* Atualize o `CHANGELOG.md` a cada entrega relevante.

## 4. Antes de levar código ao carro
1. `make testes` sem falhas.
2. `make config` mostra os parâmetros esperados (chave errada no `config.json` dá erro).
3. Teste com vídeo gravado: `make video VIDEO=dados/gravacoes/...`.
4. Primeiro com as rodas suspensas (`make bancada`), depois na pista.
5. Registre o resultado em `docs/06_testes.md`, citando o arquivo de log em `dados/`.

## 5. Ajustes na pista
Mude **um parâmetro por vez** em `config.json` e grave um log (`make carro` já grava). Anote em `docs/06_testes.md` o que mudou e o efeito observado. Os valores que funcionaram entram no commit com uma mensagem clara.
