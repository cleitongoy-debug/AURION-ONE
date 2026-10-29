# AURION ONE — Estudo semanal de IA, agentes e engenharia operacional
**Data de corte:** 29/10/2026  
**Janela de atualidade:** 22–29/10/2026, com fontes anteriores citadas quando ainda definem o estado atual  
**Responsável pela síntese:** FALCÃO / coordenação técnica  
**Estado:** pesquisa documental + inspeção estática do repositório; NÃO é certificação de runtime nem prova de execução no PC/POCO.

## 1. Objetivo prático
Corrigir a engenharia de China/DeepSeek, Agente Noturno e ARANHA 1. Não é um exercício de persona. O resultado esperado é um fluxo executável com ferramentas, memória persistente, agendamento real, coleta com proveniência, handoff entre agentes, recuperação de falhas e readback independente.

Pasta de ponte indicada pelo Capitão: https://drive.google.com/drive/folders/1y0Zz0iECamt_bm_nlxmT_rOSssKc1cSl  
Issue central de engenharia: https://github.com/cleitongoy-debug/AURION-ONE/issues/58  
Coordenação das ARANHAS: https://github.com/cleitongoy-debug/AURION-ONE/issues/55

## 2. Achados de engenharia confirmados no código consultado
### 2.1 Bridge atual NÃO é um agente autônomo
Arquivo: https://github.com/cleitongoy-debug/AURION-ONE/blob/3aaa9b2994d2827b88f67971dc47813025999e25/remote-agent/scripts/aurion_bridge_worker.py
- O próprio cabeçalho define o worker como status-only/read-only.
- Faz sondagens locais de portal/Ollama/ComfyUI e lê o commit público do GitHub.
- Drive só verifica presença de uma pasta sincronizada configurada por `AURION_DRIVE_SYNC_DIR`; não lê documentos, não usa OAuth e não coleta arquivos.
- O JSON de status diz explicitamente que não existe conexão ChatGPT/Gemini/Drive OAuth, controle remoto, auto-reparo nem conexão bidirecional ChatGPT.
- O timestamp é gerado antes de terminar as sondagens; não é uma medição monotônica de duração de cada serviço.
- O worker não é por si só a China, não é ARANHA 1 e não é o Agente Noturno.

### 2.2 Launcher não configura inicialização automática
Arquivo: https://github.com/cleitongoy-debug/AURION-ONE/blob/3aaa9b2994d2827b88f67971dc47813025999e25/remote-agent/scripts/start_bridge.ps1
- Inicia um único worker oculto e evita duplicação simples.
- Informa explicitamente que não configura startup automático do Windows.
- Logo, a existência do script não prova que o processo funciona à noite ou após reinicialização.

### 2.3 Benchmark local não valida China/DeepSeek remoto
Arquivo: https://github.com/cleitongoy-debug/AURION-ONE/blob/3aaa9b2994d2827b88f67971dc47813025999e25/tools/aurion_model_benchmark.py
- Testa apenas modelos que já estejam instalados no Ollama local; padrão `qwen3.5:4b` e `deepseek-r1:7b`.
- Executa duas prompts fixas por modelo e salva um relatório local privado.
- Declara expressamente que NÃO testa recuperação da Bíblia, memória longa, ComfyUI, visão ou integrações multiagente.
- Portanto, não serve como prova de que a API DeepSeek Search/Fetch, function calling, memória compartilhada ou handoff entre agentes esteja funcionando.

### 2.4 Especificação existente
Documento de engenharia anterior: https://github.com/cleitongoy-debug/AURION-ONE/blob/3aaa9b2994d2827b88f67971dc47813025999e25/docs/engineering/CHINA_DEEPSEEK_AGENTE_NOTURNO_ARANHA1_2026-10-26.md
Issue #58 já contém o plano P0–P3 e os critérios de aceite. Este estudo atualiza a evidência; não substitui nem duplica a especificação canônica.

## 3. Pesquisa externa recente — fontes primárias
### OpenAI — 22 e 26 de outubro
- **Decisions API (22/10):** atualização listada no changelog da API. Relevância para AURION: decisões estruturadas e cache/contexto podem ser úteis em pipelines; não substituem a fila de tarefas, o estado persistente nem o worker.
- **GPT-6.1 Terra (26/10):** lançado para raciocínio visual, uso preciso de computador e escrita. Isso não implica acesso automático a arquivos/contas nem execução em background.
Fontes:
- https://developers.openai.com/api/docs/changelog?mw_entry=2026-09-29-962e96e45069e83d
- https://help.openai.com/en/articles/9624314-model-release-notes
- https://openai.com/news/product-releases/

### DeepSeek — Search/Fetch e chamadas de ferramentas
- O changelog oficial informa a abertura da Search API e a atualização DeepSeek-V4.1-Flash-1017 em 17/10; é a última atualização específica de pesquisa encontrada na documentação oficial consultada, embora seja anterior à janela de sete dias.
- Search/Fetch são endpoints separados, autenticados com bearer key; retorno e custo precisam ser validados no runtime.
- A documentação indica cobrança por 1.000 chamadas bem-sucedidas de Search e Fetch e limites de QPS por conta/domínio. Antes de ativar coleta em lote, verificar preços e limites atuais na página oficial.
- Tool calling exige que o código da aplicação execute a ferramenta e devolva o resultado com o identificador correto ao modelo. A resposta do modelo não executa sozinha a ação.
Fontes:
- https://api-docs.deepseek.com/updates/
- https://api-docs.deepseek.com/guides/search/
- https://api-docs.deepseek.com/guides/tool_calls/

### Google — Gemini Skills rollout
- O anúncio oficial de 13/10 diz que Skills no Gemini app estão em rollout gradual com conclusão esperada em meados de novembro; a integração com Drive foi anunciada como recurso futuro a ser liberado, não presumido como universalmente disponível.
- Skills no Workspace sofreram atraso sem nova data confirmada naquele anúncio.
- Para a engenharia AURION: uma skill é instrução/empacotamento de capacidade, não um daemon, scheduler, runtime de agente nem prova de permissão a Drive.
Fonte: https://workspaceupdates.googleblog.com/2026/10/an-update-on-launch-of-skills-in-gemini-app-and-workspace.html

### AWS — práticas operacionais de agentes
- A orientação de Agentic AI Lens exige papéis claros, critérios de sucesso, handoffs padronizados, testes de falhas reais, métricas operacionais e runbooks vivos.
- Para AURION, a lição é fazer da passagem entre agentes um objeto persistente e auditável, com owner, contrato de entrada/saída, status e evidência, e não confiar em “todos sabem”.
Fontes:
- https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentops01.html
- https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentic-ai-lens.html

### Protocolos e vídeos técnicos já listados no documento-base
A especificação de 26/10 já lista os vídeos oficiais sobre A2A e MCP/ADK e seus capítulos. Eles devem ser tratados como fontes a assistir/validar, não como vídeos assistidos nesta rodada, até haver registro de leitura/transcrição:
- https://www.youtube.com/watch?v=Fbr_Solax1w
- https://www.youtube.com/watch?v=6mQwHqK1I5w
Protocolo A2A: https://a2a-protocol.org/v1.0.0/

## 4. Arquitetura de destino proposta
1. **Task ledger canônico:** tarefa com task_id/event_id, agente proprietário, criada_em, started_at, heartbeat, ended_at, timezone, status, tentativa, custo/latência, fontes, artefatos e hashes.
2. **Estados explícitos:** QUEUED → RUNNING → (WAITING_APPROVAL | BLOCKED | FAILED | SUCCEEDED) → VERIFIED somente após readback/teste independente. Nunca confundir SUCCEEDED com VERIFIED.
3. **Worker noturno real:** agendador (Task Scheduler/serviço Windows ou runner equivalente) + processo com heartbeat, fila persistente, checkpoint, lease/lock, retry com backoff, limite de tempo/custo e resumo matinal. Confirmar qual runtime existe antes de escolher implementação.
4. **China/DeepSeek adapter:** provider/model id configurável, endpoint versionado, tool calling com histórico correto, Search/Fetch como ferramentas com esquema validado, timeout, retry só para falhas transitórias, rate-limit, redaction e idempotência para ações de escrita.
5. **ARANHA 1 collector:** inventário incremental na pasta designada; URL, título, autor/canal, data, tipo, duração, timestamps/capítulos, status de transcrição, hash, licença, data de coleta e status de readback. Deduplicar por ID e hash; preservar origem.
6. **Sync de três redes:** cada destino precisa de confirmação independente e recibo; falha de sessão/permissão deve virar BLOCKED, não sucesso.
7. **Cross-learning:** antes de publicar, cada agente lê os relatórios mais recentes dos demais, registra o que reaproveitou, divergências, lacunas e nova evidência. Publica delta com links; não replica relatórios inteiros.
8. **Verificador separado:** teste automatizado/readback independente da mesma LLM que propôs a ação.
9. **Segurança:** segredos somente em variável de ambiente/secret store, scopes mínimos, allowlist de ferramentas, aprovação humana para instalação/publicação/escritas irreversíveis, logs sanitizados.

## 5. Plano de execução e critérios
### P0 — inventário real (não concluído)
- Localizar configuração, skill, runtime, modelo e triggers de China/Noturno/ARANHA 1.
- Capturar versões, processos, workflows, permissões, logs e destino dos artefatos.
- Etiquetar cada item CONFIRMADO / CANDIDATO / AUSENTE / BLOQUEADO.

### P1 — testes de contrato (não executados neste estudo)
- leitura simples, chamada de ferramenta, retorno com call_id, 429/timeout, resposta vazia, schema inválido, reinício, dedup, idempotência, readback e não vazamento de segredo.

### P2 — fluxo ponta a ponta (não executado neste estudo)
- pedido → fila persistente → pesquisa independente → coleta → artefato → gravação em destino autorizado → leitura de confirmação → relatório.

### P3 — operação noturna real (não executada neste estudo)
- executar um ciclo controlado com timestamp, heartbeat, checkpoint, logs, custo, resultado e resumo matinal; reiniciar o worker e provar retomada sem duplicação.

### P4 — sync cruzado
- ARANHA 1 coleta/ponte; ARANHA 2 auditoria e testes; ARANHA 3 cronologia/dedup; ARANHA 4 build/Android/Git; ARANHA 5 biblioteca/avisos; China pesquisa independente; Agente Noturno scheduler/recovery; FALCÃO reconcilia.
- Todos leem os resultados dos outros antes de concluir e deixam recibo no issue central.

## 6. Não afirmar como feito
- Não foi executado um job noturno real nesta rodada.
- Não foram testadas credenciais DeepSeek nem chamadas Search/Fetch reais.
- Não foram lidos integralmente todos os vídeos do YouTube; os links ficam como fila de estudo com estado pendente.
- Não foi feita escrita/readback no Drive nesta rodada.
- Não foram alterados nem instalados binários no PC/POCO.
- Não se afirma que todos os agentes receberam uma notificação direta. O issue compartilhado é o handoff disponível; cada agente precisa confirmar leitura/ACK.

## 7. Referências de arquitetura
- OpenAI Agents SDK — handoffs, agentes como ferramentas, estado e tracing: https://developers.openai.com/api/docs/guides/agents/sdk
- OpenAI orchestration/handoffs: https://developers.openai.com/api/docs/guides/agents/orchestration
- OpenAI tracing: https://openai.github.io/openai-agents-python/tracing/
- OpenAI multi-agent: https://developers.openai.com/api/docs/guides/agents-api/multi-agent
- AWS Agentic AI Lens: https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentops01.html

## 8. Próximas ações para os responsáveis
- **China/DeepSeek:** fazer benchmark API real (sem expor chave), validar Search/Fetch + tool call end-to-end, custo/latência/erro, retornar logs sanitizados.
- **Agente Noturno:** identificar scheduler real e executar ciclo controlado com checkpoint/restart/readback.
- **ARANHA 1:** indexar a pasta designada sem duplicar, capturar vídeos/documentação e atualizar o inventário existente.
- **ARANHA 2:** revisar independentemente os testes e buscar falsos positivos.
- **ARANHA 3:** validar timestamps/contadores e deduplicação.
- **ARANHA 4:** auditar runtime/instaladores e não publicar release sem prova.
- **ARANHA 5:** manter índice e handoffs únicos, detectar duplicatas e avisar os responsáveis.
- **FALCÃO:** comparar achados, abrir correções específicas e só declarar VERIFICADO com evidência.
