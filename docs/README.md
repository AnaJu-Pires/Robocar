# Documentação — índice

Leia na ordem numérica na primeira vez. Depois, use a tabela para ir direto ao assunto.

| Arquivo | Responde |
|---|---|
| [01_regulamento.md](01_regulamento.md) | O que a regra da categoria Micro exige de nós? Onde as fontes divergem? O que perguntar à organização? |
| [02_arquitetura.md](02_arquitetura.md) | Como o sistema funciona de ponta a ponta? Papel da Jetson e da ESP32, estados, tempos, pontos fracos |
| [03_hardware.md](03_hardware.md) | Componentes, massa, elétrica, cálculos, **pinagem** e regras de ligação |
| [04_software.md](04_software.md) | Módulos Python, algoritmo de visão, controle, parâmetros, o que mudou em relação ao código original |
| [05_protocolo_serial.md](05_protocolo_serial.md) | Especificação das mensagens Jetson ↔ ESP32 |
| [06_testes.md](06_testes.md) | Como testar (automático, bancada, pista), critérios de aprovação e registro de resultados |
| [07_plano.md](07_plano.md) | Cronograma até 05/12, próximos passos, pendências e riscos |
| [09_roteiro_testes.md](09_roteiro_testes.md) | **Testar no hardware passo a passo, tudo pelo SSH:** câmera → calibração → detecção → serial → motores → pista; comandos e o que mandar de volta |
| [decisoes.md](decisoes.md) | Registro das decisões técnicas: o que decidimos, por quê e o que descartamos |
| [referencias/](referencias/) | Regulamento oficial (PDF) |

Compras e orçamento: [../compras/README.md](../compras/README.md).
Convenções do repositório: [../CONTRIBUTING.md](../CONTRIBUTING.md).

**Marcação usada:** **[V]** verificado (regulamento, página da loja, medição ou teste executado) · **[E]** estimativa ou cálculo · **[T]** falta testar no hardware.
