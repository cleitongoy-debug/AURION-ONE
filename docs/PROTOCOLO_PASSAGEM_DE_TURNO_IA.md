# AURION ONE — PROTOCOLO DE PASSAGEM DE TURNO

Criado em 2026-09-18. Fonte de eventos: comentários da [issue #2](https://github.com/cleitongoy-debug/AURION-ONE/issues/2). Este documento estabelece o formato; NÃO é um sistema de sincronização em tempo real. Horários reais dos comentários são atribuídos pelo GitHub. Nunca inventar horário ou afirmar que outro agente leu a issue.

## Antes de qualquer ação
1. Ler esta página, `docs/REUNIAO_OFICIAL_IA.md`, `LABORATORIO_IA.md`, registros PC e mobile e os comentários MAIS RECENTES da issue #2; conferir commits posteriores. Distinguir evidência histórica de estado atual.
2. Publicar na issue #2 uma entrada própria: `data/hora UTC (timestamp do GitHub) | agente e ambiente | fonte da mensagem (direta / retransmitida manualmente pelo operador / aplicativo autenticado comprovado) | último interlocutor comprovado | tarefa assumida | evidência nova | arquivos/commits alterados ou NENHUM | testes com resultado | bloqueios | próximo responsável | próximo teste mínimo`. Se o agente não tiver acesso de escrita, entregar texto ao operador para publicação; registrar como retransmissão, não presença direta.
3. Nunca declarar presença, leitura, execução, conexão ou disponibilidade de outro agente sem evidência própria. Uma resposta colada pelo operador é uma mensagem retransmitida, não canal automático entre IAs.
4. Antes de editar, informar arquivo, mudança proposta, riscos, teste e reversão. Evitar alterações simultâneas; cada participante confirma o commit-base. Não repetir teste concluído sem motivo novo. Não apagar ambientes locais ou reiniciar serviços em uso sem autorização.
5. Cada evento novo deve ter uma entrada nova na issue #2 com timestamp real do GitHub. Para determinar quem falou por último, consultar a ordem dos comentários e distinguir AUTOR da publicação de AUTOR da mensagem retransmitida. Comentários não capturam automaticamente conversas privadas nem mensagens do POCO.

## Contrato futuro para o POCO (NÃO IMPLEMENTADO/VALIDADO)
- Após pareamento explícito PC↔POCO em transporte privado autenticado, o app poderá enviar eventos estruturados com `event_id`, `occurred_at` (ISO 8601 com fuso), `received_at` atribuído pelo servidor, `device_id` pseudônimo, `agent_id`, `source`, `event_type`, `correlation_id`, `status`, `evidence`, `last_confirmed_event_id`. Deduplicar por `event_id`, ordenar por horário do servidor e marcar eventos atrasados. Não confiar somente no relógio do celular.
- Guardar eventos operacionais privados no PC; publicar no GitHub público apenas resumo sanitizado e autorizado, nunca tokens, IPs internos, inventário privado, áudio, dados de saúde, conteúdo da Bíblia privada ou conversas pessoais. O APK não deve receber token de escrita do GitHub embutido.
- O aplicativo deve mostrar ONLINE apenas com endpoint recente e autenticado, OFFLINE após falha comprovada e DESCONHECIDO/ANTIGO para dados sem verificação recente. Processos em execução não provam API, pareamento ou sincronização.
- PC em segundo plano enquanto outra pessoa usa o computador: sem janelas invasivas, captura de tela, teclas, microfone ou interrupção do jogo; limitar consumo de GPU/CPU, evitar iniciar geração de imagens e não reiniciar serviços automaticamente. Nenhuma garantia de disponibilidade se o Windows suspender, reiniciar ou perder rede.

## Situação inicial confirmada por saída retransmitida do operador em 2026-09-18
- `ollama list` listou quatro modelos; `ollama run qwen3.5:4b` produziu `AURION TESTE OK` com bloco de raciocínio adicional.
- `ComfyUI/main.py` existe; `python.exe` PID 19528 executava `ComfyUI/main.py --windows-standalone-build`; Open WebUI PID 6432; portal PID 11400 com processo associado 15260; bridge PIDs 14564 e 7868. PIDs são observações pontuais e podem mudar; dois processos relacionados NÃO provam serviços duplicados.
- Endpoint ComfyUI 8188 estava indisponível em teste ANTERIOR; ainda não há teste recente da API após observar o processo. Portal 8765 e Ollama 11434 responderam em diagnóstico anterior; não extrapolar para agora.
- PC↔POCO autenticado/bidirecional, relógio/Mi Fitness, microfone do capacete, comunicação automática entre IAs e APK novo permanecem NÃO COMPROVADOS.

## Próxima divisão proposta, aguardando aceite dos participantes
- ChatGPT nesta conversa: coordenação da ata e análise de contrato de API/frontend no GitHub; pode publicar comentários e alterações revisáveis no repositório, NÃO executar comandos no PC nem acessar o POCO.
- Outra IA retransmitida pelo operador: solicitar que escolha uma tarefa concreta e publique seu próprio comentário/commit se tiver acesso; nenhuma tarefa é presumida aceita.
- Operador: somente testes locais indispensáveis, preferencialmente um bloco de leitura sem alterações, após revisão. Prioridade: verificar API atual do ComfyUI e contrato autenticado do painel; não reiniciar serviços já em uso.
