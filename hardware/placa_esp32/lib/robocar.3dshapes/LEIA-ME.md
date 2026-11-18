# Modelos 3D próprios do projeto

Regra: **não desenhar modelo 3D**. Usamos o modelo nativo do KiCad (`${KICAD10_3DMODEL_DIR}`) ou um modelo baixado do
fabricante/distribuidor. Se não houver nenhum, a pegada fica só com conectores genéricos nativos.

| Arquivo | Peça | Origem | Como está na pegada |
|---|---|---|---|
| `DEVKIT_V1_ESP32-WROOM-32.step` | ESP32 DevKit V1, **30 pinos** (15 por lado, fileiras a 25,4 mm, USB e botões EN/BOOT numa ponta, antena na outra) | baixado pela equipe (SnapEDA, peça "DEVKIT V1 ESP32-WROOM-32", exportado do SolidWorks 2021) | `ESP32_DevKit_V1_30p_SoldaManual`: offset (12,7; −20,05; 8,5) mm, rotação (270; 0; 180). A placa assenta em cima das barras fêmea nativas de 8,5 mm |

Do mesmo pacote baixado vieram também um símbolo e uma pegada (`MODULE_DEVKIT_V1_ESP32-WROOM-32`). **Não foram usados:**
a pegada tem **38 furos (19 por lado)**, é da DevKit de 38 pinos, e não bate com a nossa placa nem com o próprio STEP
(que tem 30 pinos). Continuamos com a pegada `_SoldaManual` de 30 pinos (ilhas grandes para corrosão caseira).

Sem modelo baixado:
* **Módulo DRV8833** (Smart Kits, 2 fileiras de 6 pinos a 15,24 mm): só as 2 barras fêmea nativas
  `PinSocket_1x06_P2.54mm_Vertical`. O módulo em si não aparece no 3D: ele é mais baixo que a ESP32, então a altura
  máxima da placa montada continua sendo a da ESP32 (≈ 16,8 mm acima da face de baixo do fenolite).
* **Jumpers JP1/JP2** (fio rígido deitado): sem modelo.

Os antigos `ESP32_DevKit_V1_30p.wrl` e `DRV8833_Modulo.wrl` (caixas desenhadas à mão) foram apagados.
