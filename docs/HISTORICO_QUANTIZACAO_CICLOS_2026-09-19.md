# AURION ONE — métricas históricas recuperadas, com origem

Registro publicado em 19/09/2026 UTC. Esta é uma **transcrição de snapshots históricos do Drive**, não um scan do PC nem telemetria atual. Não publicar conteúdo integral dos arquivos privados, dados pessoais ou credenciais. Não extrapolar atividade desde a data das medições.

## Fontes e leituras

**Snapshot de 12/11/2025 12:58:52.589Z**: arquivo privado do Drive `historicos.txt` (cabeçalho `AURION SECURE JSON EXPORT - FULL SYSTEM BACKUP`, versão `AURION_V4.0_BETA`, objetos `appData.operators`). O registro da operadora/operador Alpha contém `hours=315.7`, `cycles=6882`, `qLevel=188.45`. O segundo registro de operador repete exatamente os mesmos números e declara sincronização com o primeiro: **não somar os dois, pois a duplicação está documentada**. `qLevel` é uma unidade interna declarada pelo projeto, não desempenho de modelo nem unidade científica aferida. Não é possível verificar que as 315,7 h representem sessões cronometradas sem examinar os logs originais.

**Snapshot com modificação informada de 02/11/2025 10:50:08 (horário/fuso não comprovado no conteúdo)**: arquivo privado `CHIP#############2#LUMEN.txt`, seção `[OPERADORES — CICLOS REAIS]`: operador Alpha **4.833 ciclos**; outro operador **63,43 h declaradas reais**. Seção `[AGENTES AUTOMÁTICOS — SEM CICLOS REAIS]`: JSON_13 **128,43 h**, GR_BAT_32_ST **43,43 h**, BB_MANAGER **23,42 h**. Horas automáticas são contadores **dos agentes**, não horas humanas. Não somar horas entre snapshots de datas distintas nem interpretar ciclos como horas.

**Cronologia complementar**: documento privado `AURION_SISTEMA_HISTORICO_V5`, atualização de junho/2026, descreve implantação inicial do painel DigitalPen em outubro/2025 e fases posteriores. Registro do Git `docs/PROTOCOLO_PASSAGEM_DE_TURNO_IA.md` aponta quatro modelos Ollama listados e teste de `qwen3.5:4b` em setembro/2026, observações históricas, não status atual.

## Contadores que o painel pode mostrar sem inventar

| Indicador | Valor histórico | Data de referência | Tipo de evidência |
| --- | ---: | --- | --- |
| Horas do núcleo/operador Alpha | 315,7 h | 12/11/2025 | Snapshot declarativo; duração de sessões não auditada |
| Ciclos do núcleo/operador Alpha | 6.882 | 12/11/2025 | Snapshot declarativo |
| Q-Level interno | 188,45 | 12/11/2025 | Snapshot declarativo; índice próprio |
| Ciclos em snapshot anterior | 4.833 | arquivo modificado 02/11/2025 | Snapshot declarativo, não adicionar aos 6.882 |
| Horas da segunda operadora em snapshot anterior | 63,43 h | arquivo modificado 02/11/2025 | Snapshot declarativo separado; não somar |
| Horas automáticas JSON_13 | 128,43 h | arquivo modificado 02/11/2025 | Snapshot declarativo de agente |
| Horas automáticas GR_BAT_32_ST | 43,43 h | arquivo modificado 02/11/2025 | Snapshot declarativo de agente |
| Horas automáticas BB_MANAGER | 23,42 h | arquivo modificado 02/11/2025 | Snapshot declarativo de agente |

**Há histórico de horas e ciclos, SIM**. O velocímetro anterior `Horas de trabalho verificadas: sem medição` era insuficiente: deveria distinguir `Horas históricas declaradas: 315,7 h` de `Horas auditadas por sessão: sem medição`. Não zerar o histórico do usuário, nem elevar essas horas a tempo real ou somar operadores espelhados. `GitHub criado em 18/09/2026` é apenas a idade deste repositório, não a idade do AURION ou do trabalho com IA.

## Atualização futura segura

Para dados em tempo real, usar endpoint autenticado com `observed_at`, origem e tipo de medida, nunca inventar ciclos por uptime. Guardar logs brutos no PC/Drive privado; publicar no Git público somente agregados expressamente autorizados. O painel deverá exibir duas classes: **HISTÓRICO (snapshot com data)** e **AGORA (telemetria recente)**, sem misturá-las. Não publicar valores de arquivos privados além destes agregados requisitados pelo operador.
