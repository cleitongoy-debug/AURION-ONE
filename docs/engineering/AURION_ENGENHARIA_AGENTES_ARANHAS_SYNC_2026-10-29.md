# AURION ONE — Engenharia de agentes, ARANHAS e sincronização
**Revisão:** 2026-10-29 · **Objetivo:** corrigir a engenharia existente de CHINA/DeepSeek e do agente noturno; não criar personas.

## 1. Diagnóstico de engenharia
AURION já tem histórico de anos e papéis funcionais. O gargalo a resolver é a integração operacional: coleta, estado persistente, deduplicação, leitura cruzada, execução de ferramentas, verificação e handoff. Um nome ou prompt não cria capacidade de execução. Cada integração deve ter teste de acesso e prova de resultado.

O acervo recuperado em “AURION HISTORIA — RESUMO DOCUMENTAL.txt” identifica MCP como caminho para ferramentas/contexto e A2A para comunicação entre agentes; lista CHINA/DeepSeek como programação/backend, Gemini/ÁGUIA como pesquisa/análise, LOVART como visual e LÚMEN como arquitetura. Isso é evidência histórica do desenho desejado, não prova de que as integrações estejam hoje ativas.

Pasta de referências do Capitão: https://drive.google.com/drive/folders/1y0Zz0iECamt_bm_nlxmT_rOSssKc1cSl

## 2. Pesquisa técnica consultada
- **OpenAI Agents SDK**: agentes com ferramentas, handoffs, guardrails, sessões e tracing. Fontes: https://openai.github.io/openai-agents-python/ · https://openai.github.io/openai-agents-python/sessions/ · https://openai.github.io/openai-agents-python/tracing/
- **MCP, especificação 2026-07-28**: núcleo stateless, multi-round-trip, roteamento, resultados de listagem cacheáveis e endurecimento de autorização. Fonte: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/blog/content/posts/2026-07-28-spec-ga/index.md
- **A2A**: protocolo aberto para comunicação interoperável entre agentes remotos; inclui vídeo introdutório oficial de menos de 8 minutos. Fonte: https://a2a-protocol.org/v1.0.0/
- **DeepSeek tool calls**: a API pode solicitar uma ferramenta, mas o cliente/runtime precisa validar e executar a função e devolver o resultado; tool call não é execução mágica. Fonte: https://api-docs.deepseek.com/guides/tool_calls/
- **DeepSeek context cache**: cache de prefixo é best-effort e não substitui memória persistente. Fonte: https://api-docs.deepseek.com/guides/kv_cache/
- **OpenJarvis**: referência de arquitetura com agentes simples, tool loops, ReAct, agentes agendados, memória persistente, scheduler e traces. Avaliar antes de instalar; não presumir que já esteja instalado. Fontes: https://github.com/open-jarvis/OpenJarvis/blob/main/docs/architecture/overview.md · https://github.com/open-jarvis/OpenJarvis/blob/main/docs/user-guide/agents.md
- **Microsoft Agent Framework Python 1.23.0 (22/10/2026)**: notas citam base de compatibilidade MCP 2.x e forwarding allowlisted em A2A; requer testes de compatibilidade antes de atualizar. Fonte: https://github.com/microsoft/agent-framework/releases
- **OpenAI Agents API**: contexto, ferramentas, subagentes e execução longa com checkpoints/resultados intermediários. Fonte: https://openai.com/pt-BR/index/introducing-the-agents-api/
- **Atualizações OpenAI**: anúncios GPT-6.1 Terra (26/10) e Decisions API (22/10) aparecem no feed oficial; só adotar se resolver um gargalo medido. Fonte: https://openai.com/news/product-releases/ · notas: https://help.openai.com/en/articles/6825453-chatgpt-release-notes

## 3. Arquitetura-alvo
1. **Inventário de capacidades:** para cada agente, registrar modelo/plataforma, ferramentas, contas autorizadas, repositórios, memória, scheduler, limites e horário. Estados de acesso: CONFIRMADO POR TESTE / CONFIGURADO NÃO TESTADO / AUSENTE / EXPIRADO / SEM PERMISSÃO.
2. **Coleta:** ler primeiro índice canônico, diário, issues/PRs e entregas recentes; buscar fontes primárias; preservar URL/ID, data, origem, hash quando possível.
3. **Registro comum:** cada achado tem finding_id, projeto, prioridade, owner, evidência, estado, dependências e próximo passo. Estados: NOVO, EM_ANALISE, REPRODUZIDO, CORRIGIDO, VERIFICADO, BLOQUEADO, DUPLICADO, REJEITADO.
4. **Memória persistente:** diário append-only + índice pesquisável + checkpoint de execução. Não sobrescrever evidência original; deduplicar por ID/hash; reabrir e conferir após gravação.
5. **Planejamento e roteamento:** decompor tarefa, atribuir executor e revisor por capacidade real; agentes compartilham achados, não precisam compartilhar credenciais.
6. **Execução segura:** ferramentas allowlisted, schemas validados, timeout/retries limitados, logs sanitizados e rollback. Separar leitura, escrita reversível e ação de alto impacto.
7. **Verificação independente:** arquivo escrito → readback; código → testes; APK → package/versionCode/assinatura/hash e origem reproduzível; comunicação → ACK real. “Pedido” não é “concluído”.
8. **Handoff:** registrar o que mudou, artefato, teste, status, bloqueio e próxima ação. Rodadas agendadas não podem alegar execução contínua entre ticks.

## 4. Contrato por função
- **ARANHA 1 — Coleta/ponte:** inventário incremental de documentos, vídeos, imagens, código e metadados; atribuir origem; atualizar índice sem duplicatas.
- **ARANHA 2 — Auditoria/reparo:** ler os achados das ARANHAS 1, 3, 4 e 5 antes de trabalhar; reproduzir falhas; criar patch mínimo, teste e rollback; se sem ambiente, registrar bloqueio.
- **ARANHA 3 — Tempo/origem:** distinguir horas humanas, tempo de execução do agente, timestamps e ciclos simulados; deduplicar; nunca inferir horas de contagem de arquivos.
- **ARANHA 4 — Git/CI/APK:** comparar código, workflow, manifest, package, versionCode, assinatura, hash, releases e CI; não instalar/publicar sem cadeia de build verificada.
- **ARANHA 5 — Biblioteca/avisos:** índice canônico, deduplicação, confirmação de gravação/readback; nunca alegar que agente recebeu mensagem sem ACK.
- **CHINA/DeepSeek — backend:** tool calling conectado ao runtime; ler os achados antes de editar; produzir patch/commit/PR e testes quando tiver acesso; caso contrário entregar patch completo e declarar que não foi aplicado.
- **Agente noturno — execução agendada:** no início, restaurar checkpoint e ler os handoffs/PRs/achados dos outros; concluir uma unidade por rodada; salvar logs sanitizados, testes e próxima ação. Sem alegar loops ou trabalho durante intervalos sem execução.

## 5. Regra universal de leitura cruzada
Antes de começar, cada agente deve:
1. Ler este documento e o registro central da tarefa.
2. Ler as últimas entregas das outras ARANHAS e de CHINA/agente noturno.
3. Identificar duplicatas, contradições e achados complementares.
4. Escolher uma lacuna ainda aberta e pesquisar por fontes independentes, priorizando docs oficiais, repositórios upstream, changelogs, issues/PRs e vídeos técnicos do mantenedor.
5. Acrescentar ao finding existente ou abrir novo somente se realmente distinto.
6. Pedir revisão cruzada; preservar divergências com evidência.
7. Fechar somente após teste/readback; caso contrário marcar BLOQUEADO.
8. Não pedir ao Capitão que retransmita conteúdo já disponível no Drive/GitHub.
9. Não declarar sync, notificação, acesso ou execução sem prova.

## 6. Fila de implementação
**P0:** inventariar o código/prompt/runtime real de CHINA e do agente noturno: ferramentas, scheduler, armazenamento de sessão, memória, logs, acesso Drive/GitHub e limites.
**P0:** definir schemas comuns para task, finding, evidence, handoff, capability e run receipt, preservando compatibilidade legada.
**P0:** testar leitura cruzada e idempotência da ponte; repetir coleta sem criar duplicatas.
**P1:** testar sessão expirada, timeout, resultado vazio, falha de escrita, gravação sem readback e permissão ausente.
**P1:** adicionar run_id, agent_id, timestamps, chamadas de ferramenta, status, links de artefatos, testes, custos disponíveis, erros e next_action.
**P1:** usar issue GitHub central como fila atual; habilitar MCP/A2A só após confirmar endpoint e runtime.
**P2:** comparar OpenJarvis, Agents SDK, MCP/A2A e Microsoft Agent Framework com compatibilidade, licença, hardware, custo e regressão. Não instalar todos.

## 7. Testes de aceitação
- T1: nova rodada restaura contexto sem o Capitão repetir informações.
- T2: duas coletas iguais não duplicam achados.
- T3: ARANHA 2 demonstra leitura de achados úteis das ARANHAS 4 e 5 ou justifica não aplicabilidade.
- T4: cada tool call registra entrada sanitizada, saída, status e timestamp; falha nunca vira sucesso.
- T5: arquivo gravado é reaberto e comparado por readback.
- T6: patch vem com teste reproduzível e rollback.
- T7: agente noturno salva checkpoint e a próxima rodada retoma.
- T8: horas, execução contínua, notificações e acessos só são afirmados com evidência.
- T9: segredos e dados pessoais não entram em issues/logs públicos.
- T10: custo e retrabalho são medidos sem inventar números.

## 8. Limites desta pesquisa
Esta revisão consultou documentação e releases externos e recuperou snippets do acervo histórico. Ainda não inspecionou integralmente o banco arqueológico SQLite de 137 MB, todos os vídeos nem os prompts/códigos atuais de CHINA e do agente noturno. Não instalou software, não alterou o PC/APK e não acessou contas fechadas. A etapa seguinte é auditar o repositório e os runtimes reais e implementar os gaps com testes.

**Critério final:** engenharia pronta = artefato versionado + teste + readback + handoff. Texto promissor ou agente “ativo” não basta.
