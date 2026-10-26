# AURION ONE — Engenharia China/DeepSeek + Agente Noturno + ARANHA 1
**Data:** 26/10/2026  
**Autor:** FALCÃO / coordenação técnica  
**Estado:** ESPECIFICAÇÃO E HANDOFF CRIADOS; implementação em runtime ainda não verificada.

> Objetivo: corrigir a engenharia operacional, não inventar personas. Este documento não afirma que China ou Agente Noturno já foram alterados.

## Contexto histórico do projeto
A documentação histórica descreve o AURION como consequência da trajetória DigitalPen, automação, IA, 3D e criação. A regra de arquitetura é separar pessoa, codinome, agente IA, computador, conta e pasta. A persistência e a resolução de problemas aparecem desde os registros LÚMEN. Fonte histórica fornecida no acervo: https://drive.google.com/file/d/1wGEQbQ1k0VNnjmWLoXAfbLtfqJARHVmG/view

A pasta de ponte ARANHA 1 indicada pelo Capitão: https://drive.google.com/drive/folders/1y0Zz0iECamt_bm_nlxmT_rOSssKc1cSl

## Princípio de engenharia
Prompt/persona/skill não é um agente operacional por si só. Um agente operacional exige runtime executável, modelo/provedor configurado, ferramentas com permissões, estado persistente, scheduler/worker, logs, retries, checkpoints, limites de custo, segurança e critério de sucesso verificável.

## Arquitetura alvo
1. **Orquestrador** — recebe tarefas e cria task_id; consulta índice antes de iniciar.
2. **Registro persistente** — task_id, event_id, owner, fonte, timestamps UTC e local, estado, tentativas, custos, resultados, links e hash quando disponível.
3. **Runtime especializado** — China/DeepSeek para pesquisa técnica, leitura de documentação, comparação e tarefas de código autorizadas.
4. **Agente Noturno** — worker/scheduler real, executa lotes incrementais, checkpoint, retry com backoff, retoma após reinício e entrega relatório matinal. Não alegar trabalho em background quando só existe prompt.
5. **ARANHA 1** — coleta e indexação de documentação, vídeos e evidências na pasta autorizada; atualiza inventário existente e deduplica.
6. **Ponte entre agentes** — issue/handoff compartilhado inicialmente; MCP para ferramentas; A2A se houver runtime/endpoints compatíveis e autenticados.
7. **Verificador independente** — checa saída de ferramenta, teste, hash/readback; o modelo que declara sucesso não é o único verificador.
8. **Observabilidade** — log de chamada de modelo, tool call, saída, duração, erro, uso/custo, handoff e resultado.

## Estados e regras de conclusão
Estados: QUEUED, RUNNING, WAITING_APPROVAL, BLOCKED, FAILED, SUCCEEDED, VERIFIED. SUCCEEDED não equivale a VERIFIED. VERIFIED exige teste/readback independente.

Nunca:
- alegar que notificou uma conta fechada sem ACK;
- tratar silêncio como prova de execução, descanso ou falha;
- somar ciclos/horas de agentes com horas humanas;
- declarar o Drive/PC/POCO/Mi Band sincronizados sem recibo por destino;
- expor tokens, chaves ou caminhos privados;
- instalar APK ou publicar release sem aprovação do Capitão.

## China / DeepSeek — trilha técnica
- Identificar o modelo/endpoint realmente usado, versão, API, formato de mensagens e tool calls.
- Validar function calling e retorno da ferramenta; manter histórico completo de tool_call_id/result.
- Se usar Search & Fetch, verificar limites, preço e permissões atuais antes de habilitar.
- Tratar timeout, 429, respostas vazias, erros de esquema e conteúdo não confiável.
- Usar schema estrito para tarefas estruturadas; validar a saída por código/teste.
- Medir latência, custo, taxa de conclusão, taxa de ferramenta falha e recuperação.
- Testar fallback para outro provedor sem duplicar ações de escrita.

## Agente Noturno — trilha técnica
- Descobrir se é uma automação agendada, serviço persistente, GitHub Actions, worker local ou apenas prompt.
- Confirmar trigger real, timezone, processo vivo, logs, permissões, persistência e destino dos resultados.
- Implementar lote incremental e checkpoints idempotentes.
- Repetir falhas transitórias com backoff; não repetir ações não idempotentes sem consultar estado.
- Definir teto de tempo/custo e modo pausa/aprovação para escrita, instalação e publicação.
- Produzir relatório com executado, falhou, bloqueado, não testado, custo e links.
- Testar reinício e recuperação para garantir que uma tarefa não se perca nem duplique.

## ARANHA 1 — coleta e ponte
Pasta autorizada: https://drive.google.com/drive/folders/1y0Zz0iECamt_bm_nlxmT_rOSssKc1cSl
- Ler o inventário atual antes de criar outro.
- Coletar URL original, título, canal/autor, data, duração, capítulos/timestamps e transcrição disponível.
- Separar tutorial oficial, documentação, artigo, fórum, vídeo de terceiros e hipótese.
- Para MetaHuman → Unreal → FBX → Marvelous → C4D → Octane/ComfyUI, registrar versão de software, formato, escala, unidade, rig, topologia, materiais, licença e teste de ida/volta.
- Registrar erro de acesso/sessão sem fingir que conteúdo foi lido.
- Não mover nem duplicar originais.

## Aprendizado cruzado obrigatório
- ARANHA 1: coleta, documentação, ponte visual/3D.
- ARANHA 2: auditoria independente e reprodução de falhas.
- ARANHA 3: cronologia, horas/ciclos, origem e deduplicação.
- ARANHA 4: Git, build, Android/APK, versões e handoffs.
- ARANHA 5: biblioteca, índice, avisos e persistência.
- China/DeepSeek: pesquisa independente, APIs e proposta de implementação.
- Agente Noturno: scheduler, worker, checkpoints, retries e relatórios.
- FALCÃO: reconciliação de achados, conflitos e critérios de aceite.

Cada agente deve ler os últimos relatórios dos demais, citar autoria, registrar apenas diferenças úteis e devolver correções/contraevidências. Se não puder acessar uma plataforma, publicar handoff com a limitação; não alegar sync.

## Critérios de aceite
1. Inventário real de runtime/código/config dos agentes China e Noturno, com CONFIRMADO/CANDIDATO/AUSENTE/BLOQUEADO.
2. Diagrama de arquitetura atual e alvo.
3. Teste ponta a ponta de pesquisa → ferramenta → resultado → persistência → readback.
4. Testes de timeout, 429, saída inválida, reinício, retry, idempotência e deduplicação.
5. Evidência de um ciclo noturno real com timestamps, logs e relatório matinal.
6. Relatório de custo/latência/falhas e plano de rollback.
7. Registro atualizado na pasta autorizada e handoff lido de volta.

## Fontes oficiais pesquisadas em 26/10/2026
- DeepSeek Search & Fetch: https://api-docs.deepseek.com/guides/search/
- DeepSeek tool calls: https://api-docs.deepseek.com/guides/tool_calls/
- DeepSeek changelog (Search API anunciado em 17/10; verificar modelo/API atual): https://api-docs.deepseek.com/updates/?release=deepseek-coder
- OpenAI Agents API overview: https://developers.openai.com/api/docs/guides/agents-api/overview
- OpenAI Agents tracing: https://developers.openai.com/api/docs/guides/agents-api/tracing
- OpenAI MCP: https://developers.openai.com/api/docs/guides/agents-api/tools/mcp
- OpenAI integrations and observability: https://developers.openai.com/api/docs/guides/agents/integrations-observability
- Agent2Agent (A2A) protocol: https://a2a-protocol.org/v1.0.0/
- Google Gemini CLI skills: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md
- Google Workspace Skills rollout notice: https://workspaceupdates.googleblog.com/2026/10/an-update-on-launch-of-skills-in-gemini-app-and-workspace.html
- Vídeo Google Cloud Tech — Introduction to A2A Protocol (06/02/2026): https://www.youtube.com/watch?v=Fbr_Solax1w
- Vídeo Google for Developers — MCP, ADK, A2A end-to-end (02/12/2025), capítulos 0:38 arquitetura, 5:04 MCP server, 8:42 agente, 10:21 A2A, 12:28 teste: https://www.youtube.com/watch?v=6mQwHqK1I5w

## Delta da última semana
- OpenAI publicou itens no período 19–26/10, incluindo segurança de ambiente de treino (23/10), work activities (26/10), Decisions API (22/10) e notas sobre Agents/uso de ferramentas. Ver https://openai.com/news/?display=list
- DeepSeek documentou abertura da Search API e atualização DeepSeek-V4.1-Flash-1017 no changelog de 17/10. Isso é relevante para o papel de pesquisa do China, mas a ativação só deve ocorrer após conferir credenciais, custos e formato real.
- MCP e A2A são complementares: MCP conecta um agente a ferramentas/recursos; A2A conecta agentes/runtimes. Nenhum deles cria sozinho persistência, scheduler, autorização ou verificação.
- O Google Gemini Skills rollout foi descrito como gradual; não presumir disponibilidade idêntica em todas as contas/ambientes.
- A pesquisa é uma amostra primária direcionada, não uma alegação de leitura de toda a internet ou de todos os vídeos. Próximas rodadas devem registrar cada URL lida, data, timestamps/transcrição e delta.

## Estado atual
- Issue de coordenação técnica criada: https://github.com/cleitongoy-debug/AURION-ONE/issues/58
- Implementação do runtime China: NÃO INSPECIONADA nesta rodada.
- Implementação do Agente Noturno: NÃO INSPECIONADA nesta rodada.
- Teste ponta a ponta: NÃO EXECUTADO.
- Documento gravado no repositório como especificação; ainda precisa ser copiado/readback na pasta Drive dedicada quando a ferramenta Drive estiver disponível.
