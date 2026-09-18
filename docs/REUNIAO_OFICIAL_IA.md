# AURION ONE — REUNIÃO OFICIAL DE RESOLUÇÃO

Aberta em 18/09/2026. Ponto de encontro de agentes e IAs que **tenham acesso autorizado** ao repositório. Este documento é uma ata assíncrona, não uma sala de chat em tempo real nem autorização para executar comandos no PC.

## Entrada de cada participante
1. Ler `LABORATORIO_IA.md`, `docs/REGISTRO_PC_REAL_2026-09-18.md`, `docs/STATUS_MOBILE_2026-09-18.md`, a issue #2 e os commits posteriores. Documentos antigos podem conter estados superados; conferir horários.
2. Registrar presença **na issue #2, em comentário**, com: `IA/agente | horário UTC | capacidades/skills efetivamente disponíveis | etapa assumida | evidência consultada | ação proposta ou concluída | bloqueio | próximo responsável`. Não alegar presença de outra IA sem comentário dela.
3. Antes de agir, ler comentários novos da issue e verificar commits recentes. Evitar trabalho duplicado. Cada IA relata a etapa recebida, confere evidências e entrega a próxima etapa com caminho/commit/teste.
4. Para código, criar alteração pequena e revisável; relatar arquivo, commit ou PR, testes executados e resultado, riscos e reversão. Não executar instalações, autorreparo destrutivo ou ações em contas sem aprovação específica do operador.
5. Nunca publicar tokens, cookies, senhas, IPs privados, inventário pessoal completo, arquivos privados da Bíblia, áudio do capacete ou dados do relógio no GitHub público. Não compartilhar sessões de serviços pagos nem prometer acesso API sem integração oficial.

## Estado inicial conhecido — NÃO confundir com teste atual
- Operador confirmou em CMD: `LIGAR_AURION_PC.cmd` inicia portal `http://127.0.0.1:8765`; bridge escreveu snapshots em ciclos; Ollama respondeu. Inventário apresentado pelo operador às 21:19:02 UTC listou quatro modelos: `qwen3-4b-thinking-2507.Q4_K_M:latest`, `qwen3.5:4b`, `llava:7b`, `deepseek-r1:7b`.
- Captura posterior mostra ComfyUI iniciado manualmente com interface anunciada em `127.0.0.1:8188`; snapshot anterior dizia offline, portanto é necessário atualizar o status, não reiniciar o programa. A captura não valida geração de imagens.
- Falha observada no portal `Comando local → Executar`: HTTP 422 por ausência de `body.text` (entrada exibida continha `device_id=portal-pc` e `moving=false`). Corrigir frontend para enviar texto válido e testar resultado; não tratar como erro de instalação.
- Painel móvel existente envia `{prompt}` sem Bearer, mas backend exige `{text, device_id, moving}` e autenticação. `/api/image` não está implementado no backend inspecionado. POCO com aplicativo aberto não comprova sincronização PC↔POCO.
- Mi Band 9 Pro usa Mi Fitness no POCO, mas notificações recebidas no relógio não foram comprovadas. Microfone Bluetooth do capacete e captura autorizada de áudio não foram comprovados.
- Drive `configured=false/connected=false` no bridge. GitHub `reachable=true` significa consulta pública de commit, não canal de mensagens bidirecional nem acesso automático de outras IAs.

## Etapas de resolução e critérios de aceite
| Etapa | Trabalho | Critério de aceite | Situação inicial |
| --- | --- | --- | --- |
| 1 | Corrigir contrato do formulário local `/api/prompt` | Requisição autenticada com `text`, `device_id`, `moving`; teste com resposta real ou erro explícito | PENDENTE |
| 2 | Atualizar indicadores PC/Ollama/ComfyUI | Luz verde só após teste recente do endpoint; estado desatualizado identificado por horário | PENDENTE |
| 3 | Sincronizar POCO ↔ PC | Pareamento consentido, HTTPS privado, autenticação, teste bidirecional; sem abrir porta no roteador | PENDENTE |
| 4 | Mi Band 9 Pro / Mi Fitness | Notificação de teste recebida e confirmada no relógio, com permissões concedidas pelo usuário | PENDENTE |
| 5 | Microfone do capacete | Dispositivo pareado no POCO, permissão explícita, teste de entrada de áudio com veículo parado | PENDENTE |
| 6 | Agentes e edição | Identidade, capacidades reais, pedido de alteração, aprovação, commit/PR, testes e reversão auditáveis | PENDENTE |
| 7 | Drive / apps oficiais | Login/OAuth oficial ou pasta sincronizada explicitamente autorizada; teste específico por serviço | PENDENTE |
| 8 | APK | Build concluído, artefato e assinatura verificados antes de recomendar atualização no POCO | PENDENTE |

## Comunicação e coordenação
- **Ata estável:** este arquivo. **Conversa entre participantes:** https://github.com/cleitongoy-debug/AURION-ONE/issues/2 (comentários, não edição simultânea da ata).
- Cada IA só vê mensagens que efetivamente consultar; não existe obrigação técnica automática de presença, polling ou execução. O operador pode compartilhar o link com as IAs abertas. Não inventar participantes.
- Quem chegar: ler a última etapa e os comentários mais recentes, registrar presença, assumir uma tarefa sem duplicar, publicar evidência e indicar a próxima etapa. Se houver conflito, parar e pedir decisão ao operador.
- Segurança: sem acesso remoto irrestrito, sem instalação silenciosa, sem copiar credenciais, sem mexer na tela do operador ou de outros usuários. Testes de POCO/relógio/capacete somente com o veículo parado.

## Registro de abertura
- Participante: ChatGPT nesta conversa; capacidade confirmada: leitura e gravação de arquivos/issue no GitHub por conector autorizado; **não** acesso ao CMD, sessão de outras IAs, POCO, relógio ou microfone.
- Entrega: criação desta ata. Próxima ação: cada IA convidada registrar sua própria presença na issue #2 e escolher etapa com evidências.
