# dados/

Saídas geradas nos testes. **Não vão para o git** (veja `.gitignore`); só este README é versionado.

| Pasta | Gerado por | Conteúdo |
|---|---|---|
| `gravacoes/` | `make gravar` / `seguir_linha.py --gravar` | Vídeos `.avi` com os quadros crus em cinza. Reprocesse com `make video VIDEO=...` |
| `logs/` | `make carro` / `seguir_linha.py --log` | CSV por quadro: erro, estado, comandos, bateria, encoders (colunas em `jetson/robocar/registro.py`) |
| `capturas/` | tecla `f` na janela do `seguir_linha.py` | Quadros `.png` para análise ou novos testes |

Os nomes são automáticos (`AAAAMMDD_HHMMSS`). Ao registrar um teste em [docs/06_testes.md](../docs/06_testes.md), cite o nome do arquivo correspondente.
