# AURION — Regra de Engenharia Operacional Compartilhada

**Data de registro:** 2026-11-17  
**Origem:** ordem do Capitão + especificação ARANHA/CHINA/Agente Noturno fornecida nesta conversa.  
**Natureza:** regra de engenharia e contrato de operação; não é prova de implantação nos runtimes externos.

## Regra central

ARANHA 1–5 não são cinco chats isolados nem cinco personagens. São frentes especializadas de uma engenharia operacional compartilhada. CHINA (DeepSeek) e o Agente Noturno participam do mesmo ciclo de conhecimento, cada um usando somente as capacidades realmente disponíveis em sua sessão/runtime.

Nenhum agente deve pedir ao Capitão para transportar manualmente descobertas que possam ser entregues pelo canal autorizado. Quando não houver canal ou permissão, criar handoff persistente com estado explícito e responsável; nunca fingir envio.

## Técnica extraída: ciclo de aprendizagem cruzada

1. **Ler antes de agir:** consultar especificação canônica, índice, tarefa ativa e relatórios recentes das outras frentes.
2. **Reservar trabalho:** obter task_id e event_id; declarar agente, modelo/provedor, runtime, ferramentas e escopos disponíveis.
3. **Pesquisar independentemente:** produzir achados próprios, com fontes, datas, versões e evidência; não copiar resultado alheio como execução própria.
4. **Cruzar conhecimento:** registrar reused_findings, new_delta, conflicts, counterevidence e open_questions.
5. **Executar com segurança:** usar permissões mínimas, branch/arquivo reservado, fila durável, checkpoints, retries limitados, timeout, idempotência e aprovação humana para ações destrutivas.
6. **Persistir uma vez:** Drive guarda artefatos/evidências; GitHub guarda código, issues, PRs e testes; Notion mantém índice, decisões e estado. Adaptadores são independentes.
7. **Ler de volta:** cada destino exige readback próprio. Escrita aceita não equivale a leitura confirmada.
8. **Revisão independente:** o autor não valida sozinho a própria correção. Outra frente reproduz ou audita antes de VERIFIED.
9. **Boletim único:** FALCÃO/orquestração consolida entregas, divergências e bloqueios sem relatórios repetidos.
10. **Retomar sem perder estado:** Agente Noturno só pode ser chamado de ativo quando trigger, worker, heartbeat, checkpoint, log e retomada forem demonstrados.

## Papéis operacionais

- **ARANHA 1 — Coleta e ponte:** fontes, documentos, vídeos, inventário, metadados e proveniência na pasta autorizada.
- **ARANHA 2 — Reprodução e auditoria:** reproduzir achados, testar hipóteses e buscar contraevidências.
- **ARANHA 3 — Cronologia e integridade:** timestamps, deduplicação, hashes, métricas e consistência.
- **ARANHA 4 — Engenharia e QA:** código, branches, testes, build, Android/APK e rollback; sem publicar sem autorização.
- **ARANHA 5 — Biblioteca e despacho:** índice canônico, links, handoffs, readback e distribuição autorizada.
- **CHINA / DeepSeek — Pesquisa independente:** pesquisa/revisão e testes de ferramentas apenas quando o runtime/API real oferecer tais capacidades; registrar model ID, endpoint, tool calls, erros e custos.
- **Agente Noturno — Orquestração persistente:** scheduler/worker, fila, checkpoints, locks, retries, heartbeat, retomada e relatório matinal.
- **FALCÃO — Coordenação e auditoria:** reconciliar achados, abrir correções, exigir evidência independente e publicar o boletim único.

## Contrato de evento

Campos mínimos: event_id, task_id, agent_id, created_at_utc, visibility, source_ref, destination, status, evidence_refs, content_hash (quando aplicável), retry_count, supersedes e readback_status.

Estados: QUEUED, RUNNING, WAITING_APPROVAL, BLOCKED, FAILED, SUCCEEDED, VERIFIED.

- SUCCEEDED = ação terminou e produziu saída.
- VERIFIED = critério de aceite confirmado por teste independente e/ou readback.
- BLOCKED_NO_ACCESS = falta de conector, credencial ou permissão.
- SEND_PENDING / ACK_PENDING = handoff enviado ou preparado sem confirmação de leitura.
- Silêncio, heartbeat isolado, prompt, skill, issue ou cron configurado não provam execução útil.

## Regra de evidência e linguagem

Toda afirmação operacional deve ser rotulada como CONFIRMADO, CANDIDATO, REPORTED, INFERENCE, BLOCKED ou NOT_TESTED. Relatar comando, saída, timestamp, arquivo/URL, hash/commit e responsável quando existirem. Não declarar sincronização total sem confirmação separada em cada rede. Não converter ciclos em horas humanas. Não declarar PC/POCO testado a partir de teste sintético.

## Segurança

Segredos e dados pessoais ficam fora de prompts e issues públicas. Usar scopes mínimos, allowlist, sandbox, logs sanitizados e aprovação humana para instalação, exclusão, publicação ou mensagens externas. Preservar originais e evitar duplicação.

## Critério de aceite da engenharia compartilhada

A regra só estará implantada quando houver: inventário dos runtimes reais; leitura cruzada registrada por cada agente; pelo menos um fluxo ponta a ponta; evento persistido; readback em cada destino autorizado; teste de falha/retomada/idempotência; auditoria independente; e ACKs dos agentes externos. Até lá, a regra está **REGISTRADA**, enquanto implantação e propagação permanecem **PENDENTES DE PROVA**.

## Registro de origem

Esta regra consolida a arquitetura proposta para ARANHA 1–5, CHINA/DeepSeek e Agente Noturno, incluindo a ponte Drive/GitHub/Notion e o ciclo de colaboração. Ela não altera por si só prompts, contas fechadas, automações agendadas, PC ou POCO.
