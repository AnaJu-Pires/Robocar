# legado/

Versões **originais** do software, sem nenhuma alteração. Ficam aqui como referência e para comparação. Não são usadas pelo sistema atual.

| Arquivo original | Substituído por | Análise do que mudou |
|---|---|---|
| `peb.py` | [jetson/calibrar.py](../jetson/calibrar.py) | [docs/04_software.md](../docs/04_software.md#7-código-original-e-o-que-mudou) |
| `seguir_linha.py` | [jetson/seguir_linha.py](../jetson/seguir_linha.py) + pacote [jetson/robocar/](../jetson/robocar/) | idem |

O algoritmo original de detecção (maior contorno + centroide) está reproduzido em `jetson/testes/benchmark.py`, para comparação.
