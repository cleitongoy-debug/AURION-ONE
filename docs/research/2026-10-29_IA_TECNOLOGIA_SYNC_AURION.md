# AURION ONE — IA, tecnologia e sincronização entre agentes
**Data:** 29/10/2026 | **Janela:** 22–29/10/2026 | **Status:** pesquisa inicial com fontes oficiais; não representa toda a internet.

## 1. Atualizações da semana e implicações

### GPT-6.1 Terra (OpenAI, 26/10)
Modelo voltado a raciocínio visual e uso do computador em Work/Codex e API. Benchmarks são declarações do fornecedor; testar no ambiente AURION antes de escolher. Implicação: pode ajudar a analisar screenshots, fluxos GUI e desenhos técnicos, mas não presumir disponibilidade nem dar controle irrestrito.
Fonte: https://openai.com/index/introducing-gpt-6-1-terra/

### ServiceNow e Oracle (OpenAI, 27–28/10)
Expansão de integrações com workflows corporativos, contexto e ações controladas por permissões e aprovações. Algumas funções estão planejadas/preview. Implicação: integrar agentes a sistemas por ferramentas autorizadas, RBAC e logs; nunca entregar senhas a prompts.
Fontes: https://openai.com/index/openai-servicenow-partnership-expansion/ | https://openai.com/index/oracle-apps-in-chatgpt/

### Mensageria proativa e contexto
Notas ChatGPT de 27–28/10 mencionam iCloud Mail/Calendar e início limitado de mensagens para dots nos EUA. Disponibilidade depende de rollout/região/plataforma. Implicação: contexto entre interfaces exige identidade persistente, autorização por usuário, estado compartilhado e auditoria.
Fonte: https://help.openai.com/en/articles/6825453-chatgpt-release-notes

### Claude Duet (Anthropic, 21/10)
Prévia de agente proativo para Pro/Max por lista de espera; descreve tarefas em segundo plano e confirmação antes de agir. Não assumir acesso disponível.
Fonte: https://claude.com/resources/articles/claude-duet
Implicação: separar observação, sugestão, ação de baixo risco e ação que exige aprovação.

### Skills reutilizáveis e voz
Há relatos recentes de padronização/compartilhamento de Agent Skills e atualizações de voz. Confirmar cada item na fonte primária, licença e requisitos antes de adotar.
Fontes de descoberta: https://promptsjourney.com/news/ | https://support.claude.com/pt/articles/12138966-notas-de-lancamento | https://gemini.google/br/release-notes/?hl=pt-BR

## 2. Estado AURION referido nos registros (não é telemetria ao vivo)
- Base 177: painel AURION 5058, Hub 5059, ComfyUI 8188, Ollama 11434 e Tailscale.
- Acervo: registros diferentes relatam 3.221/16.313 documentos extraídos e, em outro instantâneo, 30.652 arquivos/4.760 pastas. Não somar nem tratar como estado atual.
- Gargalo: extração de arquivos grandes, cache/retomada e passagem de contexto ARANHA → CHINA → agente noturno.
- APK: registros conflitam entre package one.aurion.poco.v6 e one.aurion.mobile.superstudio. Não publicar/atualizar até provar artefato, hash, certificado e build reproduzível.
- Créditos limitados e erro 429 foram relatados; estimar custo antes de tarefas caras.

## 3. Arquitetura proposta

### Registro canônico
Cada descoberta deve ter event_id, timestamp UTC, agent_id, task_id, source URI/hash, claim, nível de evidência, status, responsável, dependências, próxima ação, custo e ACKs. Status: CANDIDATE, VALIDATED, BLOCKED, REJECTED, DONE. DONE exige teste/readback. Agentes referenciam IDs, não duplicam documentos.

### Responsabilidades ARANHA
1. Origem/proveniência e histórico.
2. Passagens entre agentes e cobertura.
3. Horas/ciclos sem dupla contagem.
4. Git/build/APK/assinatura.
5. Biblioteca, avisos e readback.
Antes de pesquisar, cada uma lê o quadro central e os resultados das demais. Ao terminar, publica síntese, links e provas. Não declarar agente avisado sem ACK.

### Ponte CHINA ↔ agente noturno ↔ ARANHAS
1. Ingestão por polling/webhook autenticado dos repositórios autorizados.
2. Validar schema, tamanho, MIME, hash e origem; redigir segredos.
3. Usar banco local transacional já disponível (SQLite é suficiente para o primeiro teste), com migrações e backup.
4. Indexar texto por chunks retomáveis; BM25 e embeddings opcionais com URI, autoria e data.
5. Fila persistente pending/running/blocked/done, idempotência, timeout, retries com backoff e limite de custo.
6. CHINA e agente noturno recebem os mesmos IDs e evidências, mas fazem análises independentes.
7. Depois cada agente lê pelo menos dois pareceres de outros, registra concordância/discordância e atualiza a síntese sem apagar a origem.
8. Logs redigidos, tempo real, custo e resultado de teste.

### Agente noturno
É trabalhador com fila persistente, checkpoints, limites de custo e entrega de manhã, não só mais um chat. Se PC desligado, tarefas ficam pendentes; não alegar execução 24/7. Usar Task Scheduler/serviço existente, heartbeat, logs rotativos e watchdog; validar primeiro em modo somente leitura.

### Escritório funcional no APK
- Usuários/tenants reais, cadastro consentido, sessões revogáveis e trilha de auditoria.
- Salas públicas/privadas, convite, mensagens, anexos/referências, presença, chamada privada 1:1.
- Compartilhamento de tela por sessão com aceite explícito, indicador visível e botão de parar; não gravar por padrão.
- Papéis RBAC: dono/admin, gerente, funcionário, secretário/operador, cliente, visitante. Patentes visuais não substituem autorização no servidor.
- Cada secretário carrega missão/contexto só do operador e clientes autorizados; isolamento por cliente testado no servidor.
- Drive/GitHub por OAuth/escopo mínimo. 4shared só por API/método oficial permitido; não raspar nem guardar senha. Localização e microfone com permissões claras.

## 4. Ordem de engenharia
P0: provar package/versionCode/hash/certificado do APK; congelar release conflitante.
P0: ponte de contexto read-only; mesmo event_id visível para ARANHA, CHINA e agente noturno.
P1: ingestão de arquivos grandes com chunks, checkpoint, retomada e deduplicação.
P1: teste E2E: ARANHA publica → ponte ingere → CHINA e noturno leem → pareceres independentes → leitura cruzada → ACK.
P1: modelo de dados e RBAC antes de polir UI.
P2: salas/chat/anexos/presença; depois chamadas e compartilhamento de tela.
P2: conectores autorizados Drive/GitHub; avaliar 4shared separadamente.
P3: distribuição gradual, backup/rollback, testes de segurança e telemetria consentida.

## 5. Critérios de aceite
- Mesmo event_id e versão/hash registrados pela ponte, CHINA e agente noturno.
- Leitura registrada com timestamp; parecer individual e síntese cruzada.
- Falhas retomam sem duplicar ações; arquivos grandes são retomáveis.
- Testes provam isolamento entre clientes e permissões de salas.
- Compartilhamento de tela exige aceite e pode ser encerrado.
- APK publicado/instalado coincide com build reproduzível e assinatura validada.
- DONE só com evidência; sem ACK = PENDENTE.

## 6. Missão para todos os agentes
1. Ler este documento completo e a pasta NOVO#ARANHA#SKILL.
2. Ler issue central e relatórios ARANHA 1–5.
3. Pesquisar sua especialidade em fontes primárias, incluindo a janela de 7 dias.
4. Ler dois relatórios de outros agentes e apontar evidência nova, discordância, risco omitido e ação complementar.
5. Registrar seu próprio relatório com links, data, certeza, custo/requisitos e teste AURION.
6. Não afirmar leitura, aviso, sincronização ou conclusão sem ACK/readback.
7. Estimar créditos antes de builds e começar pelo teste barato que possa refutar a hipótese.

## 7. Fontes verificadas
- OpenAI GPT-6.1 Terra, 26/10: https://openai.com/index/introducing-gpt-6-1-terra/
- OpenAI + ServiceNow, 28/10: https://openai.com/index/openai-servicenow-partnership-expansion/
- OpenAI + Oracle, 27/10: https://openai.com/index/oracle-apps-in-chatgpt/
- ChatGPT release notes, 27–28/10: https://help.openai.com/en/articles/6825453-chatgpt-release-notes
- Claude Duet, 21/10: https://claude.com/resources/articles/claude-duet
- Anthropic release notes: https://support.claude.com/pt/articles/12138966-notas-de-lancamento
- Google Gemini release notes: https://gemini.google/br/release-notes/?hl=pt-BR
- Tracker secundário para localizar anúncios primários: https://promptsjourney.com/news/

## 8. Limites
Pesquisa pública feita em 29/10/2026; não cobre literalmente toda a internet nem assiste integralmente a todos os vídeos. PC, APK instalado, contas fechadas, 4shared e dispositivos não foram inspecionados ao vivo. Nenhuma alteração foi aplicada ao PC/APK. Atualizar este documento por versão/adendo, sem duplicar nem apagar evidências antigas.
