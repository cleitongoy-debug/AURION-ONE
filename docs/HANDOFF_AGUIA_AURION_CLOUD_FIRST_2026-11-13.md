# ORDEM DE EXECUÇÃO — ÁGUIA / AURION CLOUD-FIRST
Data: 2026-11-13
Origem: FALCÃO (ChatGPT)
Destino: ÁGUIA (Gemini), com registro pelo SKIP
Repositório: cleitongoy-debug/AURION-ONE
Branch de trabalho observada: falcao/titan-telegram-bridge-20261113

## MISSÃO
Concluir a ativação do AURION fora do PC do operador. Usar os serviços, credenciais e hospedagens aos quais a ÁGUIA já tem acesso. Não pedir ao operador para instalar outro servidor, não depender de Ollama/local PC e não expor segredos no GitHub, Notion, Drive público, logs ou conversa.

## O QUE O FALCÃO JÁ VERIFICOU NO REPOSITÓRIO
1. Existe `remote-agent/scripts/telegram_titan_bridge.py`.
2. O script atual é explicitamente um bridge executado no PC do usuário. Ele usa `getUpdates` (long polling), lê `TELEGRAM_BOT_TOKEN` do ambiente ou .env e restringe o chat por `ALLOWED_CHAT_ID`.
3. Para responder, tenta `AURION_TITAN_CHAT_URL` + `AURION_API_KEY`; em contingência pode recorrer a Ollama em `127.0.0.1:11434` ou cache local. Portanto, na forma atual, NÃO é independente do PC.
4. O workflow `.github/workflows/aurion-memory-tests.yml` executa testes; não é um worker permanente nem prova de bot ativo.
5. A execução GitHub Actions #43362291988 falhou em um teste offline: `test_fallback_uses_cached_records_and_discloses_offline_state`, com assertion sobre a frase “não é uma nova pesquisa”. Verificar novamente a branch e reproduzir antes de alterar; não presumir que a falha continua.
6. Não foi encontrada confirmação de deployment, webhook Telegram registrado, mensagem enviada ou worker em execução.

## AÇÃO 1 — INVENTÁRIO DOS ACESSOS JÁ DISPONÍVEIS À ÁGUIA
Sem solicitar novas credenciais ao operador:
- Identificar os dois drives pagos e o arquivo online canônico já usados pelo AURION.
- Identificar a hospedagem/cloud/runtime já disponível, domínio, funções, banco, scheduler e armazenamento.
- Identificar credenciais já guardadas em secret manager/variáveis privadas: Telegram bot token, chat ID autorizado, endpoint TITAN, chave de API, acesso ao arquivo/memória e serviços de ingestão.
- Verificar permissões reais e validade sem imprimir valores. Nunca copiar tokens para código, commits, issues, logs ou mensagens.
- Registrar somente nomes dos serviços, status, escopos, data/hora da verificação e evidência não sensível.

## AÇÃO 2 — MIGRAR TELEGRAM PARA NUVEM
Objetivo: o bot deve funcionar mesmo com o PC do operador desligado.
- Reutilizar o bot/token existente, se válido; não criar outro bot sem necessidade.
- Preferir webhook HTTPS no runtime já existente. Se a hospedagem disponível não aceitar webhook, usar worker persistente com long polling. Não usar GitHub Actions como processo contínuo.
- Configurar token e segredo do webhook apenas no secret manager/variáveis privadas do provedor.
- Validar identidade do bot via getMe; validar webhook via getWebhookInfo (ou estado do poller); impedir dois consumidores concorrentes de getUpdates.
- Validar chat privado autorizado. Se Telegram exigir que o usuário inicie a conversa, enviar instrução curta para /start; não alegar que o bot pode iniciar conversa privada antes disso.
- Implementar comandos mínimos: /start, /help, /status, /ping. /status deve mostrar runtime, memória, conectividade e horário da última sincronização, sem expor segredos.
- Implementar envio proativo de mensagem com fila/retry, deduplicação/idempotência, rate-limit, timeout e registro de entrega. Nunca enviar mensagens em massa.
- Teste de aceitação obrigatório: enviar ao chat autorizado uma mensagem identificável, por exemplo “AURION CLOUD ONLINE — teste de ativação — <timestamp UTC>”. Confirmar resposta Telegram API ok=true e guardar message_id/status (não o token). Se não houver autorização/chat iniciado, reportar o bloqueio exato.

## AÇÃO 3 — CÉREBRO E MEMÓRIA ONLINE
- Conectar o endpoint de conversa TITAN já disponível; eliminar dependência obrigatória de Ollama e 127.0.0.1.
- Usar arquivo/drive canônico online como memória de longo prazo. Não substituir nem reorganizar pastas canônicas.
- Conectar os dois drives e as fontes de dados já autorizadas por meio dos conectores/SDKs existentes. Ingestão incremental, não duplicar arquivos.
- Cada registro ingerido deve guardar: source_id, caminho/URL, timestamp de origem, timestamp de ingestão, hash, agente responsável, status de validação e referência ao original.
- Manter estados separados: VALIDADO, CANDIDATO, EXPERIMENTAL, REJEITADO. Não transformar inferências em fatos.
- Preservar originais; sem exclusões ou movimentações destrutivas.

## AÇÃO 4 — AGENTES E CICLO DE TRABALHO
- Inventariar agentes/aranhas cadastrados, seus gatilhos, credenciais, heartbeat e destino de saída.
- Reativar apenas agentes que tenham configuração válida e escopo autorizado.
- Definir heartbeat e watchdog no runtime cloud; registrar último sinal, erro e próxima tentativa.
- Criar um canal de handoff entre ÁGUIA, FALCÃO e SKIP usando o repositório/arquivo canônico já existente. Não depender de uma API externa nova se o sistema atual já tiver canal.
- Cada agente deve gravar resultado estruturado e evidência; evitar que um agente declare outro ativo sem heartbeat ou teste real.

## AÇÃO 5 — TESTES E CORREÇÕES
- Reproduzir a falha do workflow #43362291988 na branch atual.
- Corrigir teste ou implementação conforme o contrato real; não enfraquecer o teste só para ficar verde.
- Adicionar testes para: webhook/polling, autorização de chat, segredo ausente, retry, deduplicação, indisponibilidade do cérebro, memória online indisponível e fallback sem PC.
- Testar a aplicação sem Ollama instalado/rodando e com o PC desligado.
- Adicionar health endpoint protegido ou status interno sem expor dados sensíveis.
- Confirmar deploy, health check e mensagem real no Telegram.

## CRITÉRIOS DE CONCLUSÃO — NÃO MARCAR COMO CONCLUÍDO SEM TODOS
[ ] runtime cloud identificado e deployment confirmado
[ ] nenhum caminho crítico depende do PC ou Ollama
[ ] Telegram bot autenticado e webhook/poller ativo na nuvem
[ ] chat privado autorizado e /start concluído, se exigido
[ ] mensagem proativa de teste entregue; message_id registrado
[ ] cérebro TITAN acessível na nuvem
[ ] memória online conectada e sincronização incremental comprovada
[ ] drives e fontes existentes inventariados/conectados
[ ] agentes com heartbeat comprovado
[ ] testes corrigidos e workflow verde
[ ] SKIP atualizou arquivo canônico com evidências

## FORMATO DA DEVOLUTIVA DA ÁGUIA
Responder no arquivo canônico e neste handoff:
- SERVIÇO | STATUS | EVIDÊNCIA | ÚLTIMA VERIFICAÇÃO | BLOQUEIO
- deployment URL/ID (não incluir credenciais)
- Telegram: bot username, webhook/poller status, chat autorizado (mascarado), message_id do teste
- lista de agentes e heartbeat
- commit SHA, workflow run URL e resultado dos testes
- pendências que dependem exclusivamente do operador, se houver

## REGRAS DE SEGURANÇA E AUTORIDADE
- O operador autorizou usar os acessos existentes da ÁGUIA para esta missão; isso não autoriza publicar segredos nem ampliar permissões.
- Não solicitar que o operador cole tokens/chaves no chat.
- Não apagar, mover ou sobrescrever a memória canônica.
- Não fazer compras, contratar planos ou criar custos.
- Não afirmar “ligado”, “online” ou “mensagem enviada” sem evidência técnica correspondente.
- Se um acesso estiver indisponível, reportar exatamente qual serviço/permissão falta e qual ação mínima o operador precisa executar. Não devolver uma lista genérica de infraestrutura.

## PRIORIDADE IMEDIATA
1) descobrir runtime cloud e secrets já disponíveis à ÁGUIA;
2) implantar o Telegram no runtime existente;
3) enviar e comprovar a mensagem de teste;
4) conectar memória online e TITAN;
5) reativar agentes com heartbeat;
6) corrigir testes e registrar tudo.


---

## ATUALIZAÇÃO FALCÃO — 2026-11-14: LEITOR DO DRIVE E CONTINUIDADE

O operador forneceu o endereço do serviço já existente **Leitor do Google Drive**:
`https://leitor-do-google-drive-bc578.shrd01.internal.goskip.dev`
e mostrou o painel com catálogo informado de 6.091 itens. O operador autorizou a continuidade da integração com os serviços e credenciais já existentes. Nenhum valor de chave foi copiado para este documento ou para o GitHub.

### Revisão estática do código de sincronização apresentado pelo operador
- O serviço consulta a conta do Drive via conector de proprietário (`GOOGLEDRIVE_GET_ABOUT`) e enumera itens via `GOOGLEDRIVE_FIND_FILE`.
- A rota de sincronização usa páginas de 100 itens e limita o loop a 50 páginas por execução: teto de 5.000 itens por execução.
- O código apresentado encerra o loop também quando ocorre erro do conector e, mesmo assim, grava estado `completed` e retorna `success: true`. Portanto, o estado atual pode mascarar sincronização parcial.
- O painel informa 6.091 itens. Esse número pode representar catálogo acumulado ou múltiplas execuções; não prova que uma única execução percorreu integralmente o Drive.
- A leitura da origem Drive é não destrutiva; o serviço mantém catálogo/cache próprios e pode invalidar cache local quando metadados mudam.
- A tela descrita também apresenta divergência entre “0 arquivos e 0 pastas” e “6.091 itens”. A causa ainda não foi localizada no código frontend/API completo.

### Integração ainda não verificada em runtime
O endpoint acima e a documentação `pocketbase/AURION_API_DOCS.md` foram mencionados, mas o conteúdo completo da documentação e as rotas de busca/leitura não estão presentes na branch `main) acessível nesta sessão. A sessão atual não dispõe de uma ferramenta de chamada HTTP genérica nem de conexão ao painel privado do Skip; portanto, não foi possível autenticar, testar rotas, consultar o secret manager, iniciar o runtime ou enviar mensagem Telegram. Não declarar essas ações como realizadas.

### Próxima execução técnica obrigatória
1. ÁGUIA/operador deve abrir o projeto Skip já existente e permitir que o agente com acesso ao workspace faça o inventário do runtime e dos secrets já configurados, sem revelar valores.
2. Confirmar a especificação real de busca, leitura de conteúdo, autenticação e paginação no `AURION_API_DOCS.md`.
3. Corrigir a sincronização para só marcar `completed` quando não houver `nextPageToken` e nenhuma falha; registrar estado parcial/erro e permitir continuação por cursor.
4. Criar a integração TITAN → Leitor usando os endpoints reais, com limite, proveniência, cache e tratamento de formatos; não presumir que todos os 6.091 itens tenham texto extraído.
5. Conectar os outros projetos Skip existentes pelo mecanismo de integração já configurado no workspace, sem criar serviços pagos ou duplicar memória.
6. Só depois executar o teste de ponta a ponta e registrar evidência: pesquisa no acervo, leitura de documento, resposta do TITAN, estado do runtime e recibo Telegram.

**Estado desta atualização:** inventário GitHub e revisão estática realizados; integração Skip, deploy cloud, Telegram e heartbeat permanecem NÃO VERIFICADOS. Esta atualização não altera nem revoga credenciais.
