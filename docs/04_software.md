# 04 — Software

## 1. Organização do código da Jetson

```
jetson/
├── seguir_linha.py      programa principal (visão + controle + ESP32 + log)
├── calibrar.py          calibração preto/branco → config/calibracao.json
├── config/              config.json (ajustes da equipe), calibracao.json (gerado; fora do git)
├── robocar/             biblioteca: toda a lógica, sem dependência dos programas
│   ├── configuracao.py  PADRAO (fonte única dos parâmetros) + leitura/validação
│   ├── camera.py        captura CSI (GStreamer) / webcam / vídeo
│   ├── visao.py         detecção da linha (lógica pura)
│   ├── controle.py      lei de controle e estados (lógica pura)
│   ├── protocolo.py     mensagens Jetson ↔ ESP32 (lógica pura)
│   ├── esp32.py         porta serial (usa protocolo)
│   ├── desenho.py       sobreposições de depuração
│   └── registro.py      log CSV e gravação de vídeo em dados/
└── testes/              unittest + gerador de imagens sintéticas + benchmark
```

**Regras de dependência:**
* programas → `robocar`;
* `esp32` → `protocolo`;
* `desenho` → `visao`;
* nada em `robocar` importa um programa;
* `visao`, `controle` e `protocolo` não fazem E/S, por isso são testáveis sem hardware.

**Compatibilidade:** Python 3.6 e NumPy 1.13 (JetPack 4.6). Não usar `dataclasses`, `np.quantile` nem sintaxe 3.8+. A conferência foi feita com `vermin`.

## 2. Captura (camera.py)

* Modo padrão 1280 × 720 @ 60 fps, reduzido **no hardware** (nvvidconv) para 320 × 180 em **GRAY8**. Não há conversão de cor na CPU.
* `appsink drop=true max-buffers=1 sync=false`: sempre o quadro mais recente. No original a fila era ilimitada, o que fazia a latência crescer ([decisoes.md](decisoes.md) D-004).
* Fallbacks automáticos: GRAY8 → BGR; exposição manual → automática, se o L4T recusar.
* `--fonte` aceita índice de webcam ou arquivo de vídeo, para desenvolver no PC.
* IMX219-160: o campo de visão largo traz distorção nas bordas. Por ora o erro é medido em pixels, sem corrigir a lente. Se o erro perto das bordas atrapalhar o controle, corrigir com a calibração da câmera [T].

## 3. Visão (visao.py)

1. ROI = parte inferior da imagem (`inicio_roi`). Limiar → máscara de pixels escuros. Abertura 3 × 3 remove ruído.
2. **Limiar adaptativo:** `limiar = razao × percentil90(ROI)`. A `razao` vem da calibração (limiar/branco). Acompanha a iluminação do local e a exposição automática ([decisoes.md](decisoes.md) D-003).
3. A ROI é dividida em `n_faixas` faixas, de baixo para cima. Em cada faixa: perfil de colunas escuras → segmentos contínuos.
4. O segmento escolhido é o **mais próximo da posição prevista**, extrapolada das faixas de baixo ou do quadro anterior. Assim:
   * em cruzamentos e interseções em X o robô continua na linha que seguia;
   * segmento **largo demais** (linha perpendicular ou marca) não é usado → `cruzamento`;
   * segmento **longe demais** da previsão (outra linha, ruído) não é usado.
5. Saídas:
   * `erro` (faixa mais próxima, −1 = esquerda … +1 = direita);
   * `erro_longe` (faixa válida mais distante);
   * `inclinacao`;
   * `cruzamento`, `varias_linhas`;
   * `marca` (fração escura ≥ `marca_frac_escura`).

## 4. Controle (controle.py)

* `u = kp·erro + kd·d(erro)/dt + k_frente·erro_longe`, limitado a [−1, 1]. A derivada passa por um filtro passa-baixa.
* Velocidade: `v = v_max − (v_max − v_min) · min(1, max(|erro|, |erro_longe|) / severidade_max)`. O robô freia **antes** da curva.
* Rodas: `esquerda = v + u`, `direita = v − u`, normalizadas para que nenhuma passe de 1.
* Subida de `v` limitada a `acel_max` (fração do PWM por segundo, padrão 2,0 ≈ 0,4 g): o chassi v3 levanta a esfera acima de ~0,47 g ([D-030](decisoes.md)). Só a subida: frear e virar continuam imediatos. Na largada, 0 → 0,35 leva 0,18 s.
* Linha sumiu **indo reto** (último `|erro|` e `|erro_longe|` ≤ `reto_max_erro`) ou num **cruzamento**: estado AVANCANDO, segue reto a no máximo `v_avanco` por até `avanco_s`. Se a linha volta, segue normalmente (cruzamento, falha na fita); se não volta, PARADO "fim da linha" — é assim que o robô entra no box e para ([D-038](decisoes.md)).
* Linha sumiu **numa curva**: BUSCANDO, gira para o último lado visto por até `tempo_busca_s`; depois PARADO.
* Ao parar (PARADO), a Jetson ainda manda motores em zero por `parada.freio_s` (a ESP32 armada com zero = freio) e só então desarma; desarmada, a roda fica solta.
* Marca do box (opcional): parada após `tempo_minimo_s` e `frames_confirmacao` quadros seguidos.
* Os ganhos atuais (`kp` 0,6, `kd` 0,05, `k_frente` 0,3, `v_max` 0,35) são **iniciais e conservadores**. O ajuste é feito na pista com os logs.

## 5. Parâmetros

* **Valores padrão e explicação de cada parâmetro:** `PADRAO` em [configuracao.py](../jetson/robocar/configuracao.py). É a fonte única.
* **Ajustes da equipe:** [config/config.json](../jetson/config/config.json). Só o que difere ou o que se ajusta com frequência.
* **Validação:** chave desconhecida = erro (pega erro de digitação). Chaves iniciadas por `_` são comentários.
* **Ver os valores efetivos:** `make config`.

| Para ajustar… | Parâmetros |
|---|---|
| Orientação, modo e exposição da câmera | `camera.flip_method`, `captura_*`, `fps`, `exposicao_ns`, `ganho` |
| Região analisada e robustez | `visao.inicio_roi`, `n_faixas`, `limiar_modo`, `salto_max_frac`, `fator_largo` |
| Limiar com calibração ruim ou luz variando | `visao.razao_min`, `razao_max`, `suavizar_limiar` |
| Bifurcação e box | `visao.preferencia_bifurcacao`, `visao.marca_frac_escura`, `parada.*` |
| Comportamento na pista | `controle.kp`, `kd`, `k_frente`, `v_max`, `v_min`, `severidade_max`, `acel_max` |
| Perda de linha, fim da linha e box | `controle.reto_max_erro`, `avanco_s`, `v_avanco`, `tempo_busca_s`, `v_busca`, `parada.freio_s` |

## 6. Dados de teste

* `--gravar` salva os quadros crus. `--fonte <vídeo>` reprocessa com outros parâmetros, permitindo ajustar a visão **sem a pista**.
* `--log` salva um CSV por quadro (colunas em [registro.py](../jetson/robocar/registro.py)).
* A tecla `f` salva o quadro atual.
* Tudo vai para [dados/](../dados/), que fica fora do git.

## 7. Código original e o que mudou

Os originais estão intactos em [legado/](../legado/).

**`peb.py` → `calibrar.py`:**
* a lógica (mediana de uma região, limiar = média) estava correta e foi mantida;
* o limiar não era salvo: era preciso copiar `LIMIAR = 60.5` à mão. Agora é salvo em JSON;
* calibrava no centro da imagem, e não na região usada pelo seguidor. Agora a região inferior é o padrão;
* faltava conferir contraste e branco > preto. Foram adicionados a calibração automática (Otsu) e a pré-visualização da máscara.

**`seguir_linha.py`:**

| Problema no original | Efeito | Correção |
|---|---|---|
| Fila do appsink ilimitada | Latência crescente | Fila de 1 quadro |
| 1920 × 1080 → BGRx → videoconvert (CPU) → BGR → cinza; blur, abertura, fechamento e contornos em 960 × 243; `imshow` e `print` a cada quadro | CPU gasta à toa | 320 × 180 GRAY8 no hardware; janela a cada N quadros; `print` a 2 Hz; modo sem janela |
| Limiar fixo 60,5 | Falha com pouca luz e com exposição alta (testes) | Limiar adaptativo calibrado |
| Maior contorno + centroide | Erro de −0,203 numa interseção em X (ideal 0) | Faixas com previsão: erro 0,000 |
| Só erro lateral | Reage tarde nas curvas | Erro longe + redução de velocidade |
| Sem comunicação, sem parada, área mínima fixa em pixels | Não atende "parar no box" | Controle, protocolo, parada |

**Resultados:** os testes automáticos passam no PC. Algoritmo: 0,5–0,75 ms contra 0,8–1,8 ms do original, **no PC** [V]. O ganho maior na Jetson deve vir do pipeline de captura, ainda **não medido** [T].
