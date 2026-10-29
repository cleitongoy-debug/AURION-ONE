# AURION — Engenharia operacional de agentes e pesquisa cruzada
**Atualizado:** 29/10/2026  
**Escopo:** China/DeepSeek, Agente Noturno, ARANHA 1 (ponte Drive + redes) e sincronização das cinco ARANHAS.  
**Status:** estudo técnico e plano de validação; não afirmar implementação até existirem logs e readback.

## Decisão de engenharia
O objetivo não é criar personas. É transformar os agentes existentes em workers verificáveis, com ferramentas reais, tarefas persistentes, retomada após falha, pesquisa independente e leitura cruzada. A skill instrui; o runtime executa. Prompt, mensagem de ativação ou automação marcada como ativa não provam trabalho concluído.

## Mudanças relevantes localizadas nesta semana (22–29/10/2026)
### 1. AAIF anunciou quatro projetos abertos em 22/10
A Agentic AI Foundation anunciou a incorporação de Agent Skills, Open Responses, OpenEnv e OpenSandbox. Isso reforça quatro camadas úteis para AURION: competências portáveis, interface multi-provedor, ambientes de avaliação e execução isolada. Não significa que qualquer uma esteja instalada ou conectada no AURION.
Fonte primária: https://www.linuxfoundation.org/press/agentic-ai-foundation-announces-four-new-projects-agent-skills-open-responses-openenv-and-opensandbox

### 2. OpenAI Agents SDK: loop, handoff, estado e tracing
A documentação atual descreve loop de agente que executa chamadas de ferramenta, incorpora resultados e continua até um ponto real de parada; oferece handoffs e tracing com etapas e resultados. A lição para o runtime AURION: salvar estado de tarefa e saída de ferramentas, não apenas o texto final.
Fontes: https://developers.openai.com/api/docs/guides/agents/sdk
https://developers.openai.com/api/docs/guides/agents/running-agents
https://developers.openai.com/api/docs/guides/agents/orchestration
https://developers.openai.com/api/docs/guides/agents/integrations-observability

### 3. DeepSeek Tool Calls
A documentação oficial explica que o modelo emite uma chamada, mas o cliente precisa executar a função, anexar a resposta da ferramenta com o identificador correto e chamar o modelo novamente. O modelo não executa a ferramenta sozinho. Argumentos JSON devem ser validados; há diferenças entre endpoints e modos, então a compatibilidade deve ser testada com o endpoint e o model ID realmente usados.
Fontes: https://api-docs.deepseek.com/guides/tool_calls/
https://api-docs.deepseek.com/api/create-chat-completion/
https://api-docs.deepseek.com/api/create-response/

### 4. Segurança e interoperabilidade
OpenSandbox é apresentado como infraestrutura de sandbox com APIs e runtimes para execução de código/GUI e avaliação; A2A e MCP resolvem problemas de interoperabilidade distintos. Não adicionar um protocolo por moda: primeiro mapear runtime, identidade, endpoints, permissões, transportes e evidências existentes.
Fonte: https://www.linuxfoundation.org/press/agentic-ai-foundation-announces-four-new-projects-agent-skills-open-responses-openenv-and-opensandbox

## Arquitetura alvo (mínimo operacional)
1. **Dispatcher/fila:** task_id estável, prioridade, owner, dependências, deadline/custo máximo e idempotency_key.
2. **Worker/runtime:** provedor e model ID explícitos, ferramentas allowlisted, timeout, retry com backoff e cancelamento.
3. **Persistência:** SQLite/Postgres ou store existente; eventos append-only. Registrar status, timestamps UTC + horário humano, tentativa, input/output sanitizados, referências/IDs, hashes, erro e custo.
4. **Ciclo de ferramentas:** validar schema/argumentos → executar ferramenta → guardar resultado → devolver ao modelo no formato exigido pelo endpoint → continuar loop.
5. **Recuperação:** ao reiniciar, recuperar QUEUED/RUNNING expirado; nunca repetir efeito não idempotente sem chave e readback.
6. **Estados:** QUEUED, RUNNING, WAITING_APPROVAL, BLOCKED, FAILED, SUCCEEDED, VERIFIED. SUCCEEDED não é VERIFIED; VERIFIED exige confirmação independente.
7. **Observabilidade:** task_id/event_id correlacionando modelo, ferramenta, worker, escrita externa e readback. Logs sanitizados; sem chaves, tokens ou conteúdo pessoal desnecessário.
8. **Aprovações:** leitura pode ser automática dentro do escopo autorizado; gravação, instalação, publicação ou alterações irreversíveis exigem permissão explícita e registro.
9. **Pesquisa cruzada:** cada agente lê os relatórios publicados pelos outros, identifica convergências, contradições e lacunas, faz pesquisa própria com seu acesso, atribui a fonte e publica apenas delta + correções. Nunca copiar sem verificar nem assumir acesso a conta fechada.
10. **Noturno:** lote limitado por tempo/custo; checkpoint por tarefa; quiet hours; resumo matinal; falhas ficam BLOCKED/FAILED com motivo. Não alegar execução em background sem worker vivo e logs.

## Plano de teste de contrato — China/DeepSeek
- T1: chamada de função simples com JSON válido; confirmar que o backend executou e o retorno foi associado ao tool_call_id correto.
- T2: JSON inválido/argumento extra; deve rejeitar sem executar.
- T3: timeout/429; backoff limitado, estado persistido e erro visível.
- T4: resposta de ferramenta após reinício; retomar sem duplicar a ação.
- T5: endpoint/modelo incompatível com ferramenta; falhar explicitamente e não inventar resultado.
- T6: teste de segredo-canário; garantir que não apareça no prompt, logs públicos ou documento.
- T7: duas tarefas concorrentes; estado separado, sem sobrescrita cruzada.
- T8: readback independente do artefato criado antes de VERIFIED.

## Plano do Agente Noturno
1. Confirmar qual é a implementação real: scheduler, workflow, serviço residente ou apenas prompt.
2. Localizar entrypoint, ambiente, configuração, logs, armazenamento e trigger existentes; não inventar caminhos.
3. Executar heartbeat, tarefa de leitura e tarefa sintética de escrita em sandbox.
4. Simular falha e reinício; provar recuperação sem duplicação.
5. Emitir relatório matinal com sucessos VERIFICADOS, falhas, itens bloqueados, custo/tempo medido e próximos passos.
6. Se runtime indisponível, registrar NO_RUNTIME/BLOCKED; não fingir atividade.

## ARANHA 1 — ponte de coleta
Pasta indicada pelo Capitão: https://drive.google.com/drive/folders/1y0Zz0iECamt_bm_nlxmT_rOSssKc1cSl
- Fazer inventário incremental de todos os itens acessíveis; manter ID/link original, título, tipo, autor, data, fonte/rede, hash quando possível, status de leitura e resumo.
- Para YouTube/vídeos: URL canônica, título/canal, data, duração, capítulos/timestamps, transcrição identificada como automática ou verificada, trechos relevantes e conclusão técnica. Não dizer que assistiu vídeo se só leu título/legenda.
- Pipeline de interesse: MetaHuman → Unreal → FBX → Marvelous Designer → C4D 2023 → Octane/ComfyUI; verificar escalas, topologia, rig, materiais/SSS, bit depth, textura/PBR e versões.
- Atualizar índice existente em vez de criar cópias. Não mover nem reescrever originais.
- “Três redes sincronizadas” só após comprovação independente de escrita e readback em cada destino autorizado.

## Matriz de pesquisa e aprendizagem cruzada
- **ARANHA 1:** ponte, inventário, vídeos/documentação e pipeline 3D; entrega links, timestamps e artefatos.
- **ARANHA 2:** auditoria independente dos achados da 1; tenta reproduzir; marca conflito e confiança.
- **ARANHA 3:** cronologia, contagem, deduplicação por ID/hash/conteúdo; horas humanas apenas com registros apropriados.
- **ARANHA 4 / CHINA:** engenharia de runtime, tool calling, API, build/release e testes reproduzíveis.
- **ARANHA 5 / Agente Noturno:** scheduler, persistência, retry, relatório e sincronização dos resultados.
- **FALCÃO/coordenação:** consolidar deltas, garantir proveniência, cobrar readback, não marcar pendência resolvida sem prova.

## Contrato de relatório para todos os agentes
Cada execução deve registrar: task_id, agent_id, versão/runtime, início/fim, fontes consultadas, ferramenta realmente chamada, saída, teste, erro, custo medido quando disponível, status, artefato/link, hash/ID e readback. Agente deve primeiro consultar os relatórios recentes dos outros, pesquisar independentemente e publicar diferenças/correções com atribuição. Sem ACK verificável, estado é PENDENTE; sem prova de escrita, não existe sincronização confirmada.

## Limites e próximos passos
Este documento é uma especificação baseada em documentação pública e nos achados registrados no issue #58. Ainda não comprova que o código de China ou do Agente Noturno foi modificado. A implementação deve começar pelo inventário do runtime real e testes T1–T8; depois, corrigir o que os testes demonstrarem. A pasta Drive foi indicada como destino, mas a gravação nela deve ser confirmada por leitura de volta antes de declarar sincronização.

## Fontes primárias consultadas
- Linux Foundation / AAIF, 22/10/2026: https://www.linuxfoundation.org/press/agentic-ai-foundation-announces-four-new-projects-agent-skills-open-responses-openenv-and-opensandbox
- OpenAI Agents SDK: https://developers.openai.com/api/docs/guides/agents/sdk
- OpenAI running agents: https://developers.openai.com/api/docs/guides/agents/running-agents
- OpenAI orchestration and handoffs: https://developers.openai.com/api/docs/guides/agents/orchestration
- OpenAI integrations and observability: https://developers.openai.com/api/docs/guides/agents/integrations-observability
- DeepSeek Tool Calls: https://api-docs.deepseek.com/guides/tool_calls/
- DeepSeek Chat Completion: https://api-docs.deepseek.com/api/create-chat-completion/
- DeepSeek Responses: https://api-docs.deepseek.com/api/create-response/
- Agent Skills specification: https://github.com/agentskills/agentskills
- AAIF conference schedule and videos as they are released: https://events.linuxfoundation.org/agntcon-mcpcon-north-america/


## Atualização complementar da semana — 29/10/2026
Pesquisa oficial adicional no newsroom da OpenAI identificou, no período, GPT-6.1 Terra (26/10; foco em computer use), expansão de integração com Oracle (27/10), parceria ServiceNow para workflows empresariais (28/10), além de materiais de segurança e engenharia publicados em 23–26/10. São sinais de evolução de agentes com uso de computador, workflows entre sistemas, segurança e infraestrutura; não provam que o AURION tenha essas funções implementadas.
Fontes: https://openai.com/news/ (lista oficial)
https://openai.com/news/company-announcements/
https://openai.com/news/product-releases/

## Vídeos e mídia
A página oficial da AGNTCon + MCPCon diz que as gravações das sessões estão sendo publicadas progressivamente. A ARANHA 1 deve registrar cada URL de vídeo, título, apresentador, duração, timestamps e fonte da transcrição; o relatório só pode marcar VÍDEO_ASSISTIDO se houve leitura real do vídeo/transcrição, não apenas da página do evento.
Fonte: https://events.linuxfoundation.org/agntcon-mcpcon-north-america/
