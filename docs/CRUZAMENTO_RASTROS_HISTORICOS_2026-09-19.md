# AURION ONE — cruzamento de rastros históricos, versão 2

Escopo: leitura seletiva de fontes de trabalho AURION/DigitalPen no Google Drive autorizado, código e documentação do GitHub e capturas fornecidas pelo operador. **Não é varredura completa do Drive ou de todas as unidades do PC.** O GitHub é público: NÃO copiar conteúdo integral de documentos privados, inventários pessoais, nomes de clientes, credenciais ou caminhos privados.

## Evidências identificadas (fontes independentes / snapshots deduplicados)

| Fonte | Marco observável | Como contar |
| --- | --- | --- |
| Drive `LOG#ESTUDOS_DigitalPen_v1.6_Q05.txt` | Registro de pacote DigitalPen Q-05, timestamp do conteúdo `2025-10-19T11:34:52.541117Z`, influência quântica interna 2,27 | 1 marco de estudo/pacote, NÃO 2,27 horas ou execução verificada do agente |
| Drive `CHIP#############2#LUMEN.txt` | Snapshot anterior modificado em 02/11/2025: núcleo 4.833 ciclos; DS20 63,43 h; agentes JSON_13 128,43 h, GR_BAT_32_ST 43,43 h, BB_MANAGER 23,42 h | 1 snapshot. Cópias com mesmo conteúdo/data não são novos ciclos ou horas |
| Drive `AURION_Q9_LOG.txt` | RUN_STARTED 2025-11-04T22:17:07.564683; SYNC_DONE 41/41 e EXPORT_DONE 41; RUN_FINISHED 2025-11-04T22:17:09.370982 | 1 execução com 41 itens; exportação dos mesmos itens NÃO duplica a contagem. Duração do *processo* registrada ~1,81 s, NÃO tempo de trabalho humano |
| Drive `historicos.txt` | Snapshot `2025-11-12T12:58:52.589Z`: núcleo/operador Alpha 315,7 h, 6.882 ciclos e Q-Level 188,45; outro operador repete valores e declara sincronização | Horas declaradas do núcleo, sem prova de sessões; horas espelhadas não se somam |
| Drive `AURION_SISTEMA_HISTORICO_V5` | Dossiê de junho/2026 descreve implantação inicial DigitalPen em outubro/2025 e fases de reativação e wearable | Cronologia documentada, não tempo cronometrado, integração live nem atestado de funcionalidade |
| GitHub `AURION-ONE` | Datas de criação e commits consultados pela API pública, e registros de entrega no issue #2 | Atividade somente deste repositório; criação em setembro/2026 NÃO é nascimento do AURION |

## Cálculos que NÃO dobram fontes

- Diferença **declarada** entre snapshots do mesmo núcleo: `6.882 − 4.833 = 2.049 ciclos`. Não é contador de ciclos reexecutados, nem somar 4.833 + 6.882.
- Horas nominais declaradas de **três agentes distintos no mesmo snapshot anterior**: `128,43 + 43,43 + 23,42 = 195,28 h-agente`. É uma soma de contadores por agente, NÃO 195,28 horas humanas ou horas de calendário. Agentes podem operar em paralelo e o documento não traz o método de medição.
- Núcleo 315,7 h (snapshot posterior) não deve ser somado a 63,43 h (outro operador em snapshot anterior) ou às horas dos agentes. Ausência de sessões individuais com início, fim, operador e proveniência impede auditoria do total efetivamente trabalhado.
- Q-Level 188,45 e influência Q-05 2,27 são **índices internos declarados, de escalas diferentes**; não calcular média, ganho percentual ou 'quantização real' entre eles.
- `SYNC_DONE 41/41` e `EXPORT_DONE 41` se referem à mesma execução, portanto 41 itens observados, não 82 itens distintos. O tempo do processo não representa trabalho pessoal.

## O que falta para 'PC inteiro' e história empresarial

O scanner já disponível em `remote-agent/scripts/scan_system.py` produz inventário de hardware/modelos/locais conhecidos e `scanned_at`; **não percorre todos os discos, não mede horas humanas e não lê todo conteúdo histórico**. `POST /api/scan` exige token e só executa esse script fixo. Não anunciar que todo o PC foi examinado. Uma varredura local abrangente precisa ser separada e opt-in, com inventário **agregado local**, exclusões para arquivos sensíveis, limites de duração, identificação de cópias/versões e registros explícitos de sessão. Não enviar esse inventário para o Git público. Contratos, estatutos, propostas, PIX e arquivos empresariais podem comprovar marcos datados quando examinados, mas NÃO devem ser convertidos automaticamente em tempo dedicado a IA nem publicados no Git público.

## UI e retomada

A aba `História` do painel móvel mantém indicadores dinâmicos do Git público, mostra snapshots históricos (datas e fonte) e separa horas auditadas de horas declaradas e horas de agentes. Patch idempotente: `tools/patch_historia_ampliada.py`; workflow `.github/workflows/aplicar-historico.yml`. O APK **não muda** e pode receber o HTML com botão superior `ATUALIZAR`, sujeito a rede e cache. Status live do PC, Ollama, ComfyUI e relógio continuam dependendo de verificação real.
