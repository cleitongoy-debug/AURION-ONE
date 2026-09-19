# AURION ONE — velocímetros históricos com evidência

Registro: 19/09/2026 UTC. Fonte de atualização: operador no POCO + GitHub autorizado. Este documento não é telemetria em tempo real do Windows.

## Evidências novas e limites

- Captura enviada pelo operador mostra no **relógio** uma notificação com título `AURION ONE · Teste` e texto de teste da notificação AURION. A captura do APK de teste 0.3.0 mostra o botão nativo **TESTAR BAND**. **Resultado: teste de entrega da notificação AURION à Band 9 Pro confirmado por captura do operador**; não comprova API direta do relógio, leitura de sensores nem disponibilidade contínua.
- Capturas de Mi Fitness e Bluetooth mostram Xiaomi Smart Band 9 Pro pareada/conectada ao POCO e opção de espelhamento de notificações ativada. Captura Bluetooth mostra fone YP10 2x conectado e ativo no instante retratado; não comprova microfone capturando áudio no AURION.
- Captura Tailscale mostra POCO e PC com indicadores verdes no instante da captura; não comprova que o backend AURION no PC aceite conexões autenticadas nem que seu código local esteja atualizado.
- Capturas de painéis Windows mostram modelos locais e indicadores de GPU/ComfyUI. Sem arquivo de inventário atual e chamada API validada, não tratar quantidades da imagem como telemetria atual nem somá-las entre painéis diferentes.

## Definições dos indicadores

| Indicador | Fonte permitida | Unidade e regra | O que NÃO significa |
| --- | --- | --- | --- |
| Histórico GitHub | API pública `GET /repos/cleitongoy-debug/AURION-ONE`, timestamps de criação e commits | Datas ISO do próprio GitHub, commits contados apenas se paginação exaustiva ou `Link`/API GraphQL apropriados; exibir `amostra` quando parcial | Horas de estudo ou horas de IA trabalhando |
| Antiguidade do projeto no Git | `created_at` do repositório | Dias de calendário desde a criação; rotular **tempo decorrido**, não tempo trabalhado | Esforço contínuo |
| Atividade da amostra | Até 100 commits recentes retornados pela API, identificados por SHA único | Número de commits **na amostra** e datas do primeiro/último commit da amostra; apresentar limite 100 explicitamente | Total histórico do repo, tempo gasto ou nº de pessoas/agentes |
| Primeira evidência AURION | Primeiro timestamp verificável de documento ou log, com referência concreta | Data histórica documentada; permitir múltiplas origens | Data de início inquestionável do trabalho com IA |
| Horas de trabalho com IA | Sessões com `started_at`, `ended_at`, operador e fonte comprovada | Somente soma de duração de sessões registradas, deduplicadas, filtrando horários inválidos e sobreposições. Enquanto inexistentes: **sem medição** | Tempo entre dois commits, idade do usuário, uptime ou número inventado |
| Uptime PC | Métrica obtida por endpoint local autenticado com timestamp fresco | Segundos desde boot coletados e atualizados; se offline: dado antigo/desconhecido | Horas de estudo |
| Modelos locais | Inventário do PC via API autenticada com `scanned_at` | Contagem atual dos itens efetivamente detectados; separar modelos Ollama de arquivos ComfyUI e excluir duplicatas por caminho | Modelos carregados, treinados ou funcionando sem teste |
| Drivers | Enumeração local somente leitura de GPU e versões; não transmitir inventário privado ao Git público | Nome e versão verificados no dispositivo e horário de coleta | Driver atualizado ou GPU pronta para gerar automaticamente |
| Testes por dispositivo | Evento estruturado com evidência e data (usuário/captura/API) | Status distintos: capturado, testado por endpoint, expira, desconhecido | Permissão perpétua ou controle remoto |

## Integridade / segurança

- Este GitHub é público: NÃO publicar tempos de sessão privados, inventário detalhado, identificadores de dispositivos, token, nomes de pastas particulares, dados de saúde ou conteúdo privado da Bíblia.
- Primeiro protótipo de velocímetros no HTML pode consultar **somente metadados públicos** do repositório GitHub; não depende de segredo OAuth no APK. Usar timeout, mensagens de erro, data da consulta e separar medição de estimativa. Não preencher valores fictícios.
- Não ativar varredura de todos os discos, atualização de drivers, instalação de modelos, geração de GPU nem conexão Bluetooth remota para mostrar o velocímetro. Scan do PC é operação autenticada, somente leitura e consentida.
- Migração futura: backend guarda sessões e agrega totais de modo privado; frontend só recebe métricas autorizadas. Sem backend atualizado, manter `Horas registradas: sem medição`.

## Reversão

Documentação isolada. O velocímetro HTML fica em `mobile/aurion-one-live.html` e pode ser revertido pelo commit específico; não altera APK nativo, modelo ou serviço do PC.
