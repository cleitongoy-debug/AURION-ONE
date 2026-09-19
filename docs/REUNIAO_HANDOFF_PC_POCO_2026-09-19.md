# Reunião AURION ONE — passagem de turno PC ↔ POCO

Data do registro: 2026-09-19. Estado **documental**, não teste remoto realizado por este registro.

## Evidências fornecidas pelo operador
- Scan Windows concluído em 18/09/2026, 23:33–23:37, percorreu C:, D:, E: e F:. ZIP do inventário recebido na conversa, **não publicado no GitHub** por conter caminhos privados. O scan lista metadados de nomes correspondentes, não conteúdo de arquivos nem horas auditadas.
- Capturas mostram ComfyUI anunciando interface `127.0.0.1:8188`, Ollama carregando `llava:7b`, PC e POCO listados no Tailscale. Capturas não provam disponibilidade atual, acesso remoto autenticado ou geração de imagens pelo app.
- Relato de testes: `/health` 200, `/api/inventory` 200 em algumas chamadas e 401 em outra, `/api/prompt` 422; PID Uvicorn 11400 e ComfyUI 19528 no momento do registro. Não publicar tokens ou payloads com segredos.
- Referências de UI enviadas em imagens: carrossel 3D, cartões animados, painéis translúcidos, profundidade e animação 3D; implementar visual original e responsivo, sem copiar código de terceiros.

## Inspeção de código no GitHub
- `mobile/aurion-one-live.html` ainda contém envio de chat com `{prompt:text}` e sem Authorization na versão inspecionada; há incompatibilidade relatada com contrato PC `{text,device_id,moving}` + Bearer. Confirmar schema atual no servidor ANTES de mudar o cliente.
- `tools/patch_mobile_contract.py` existe, mas **a existência do script não prova que foi aplicado**, nem que HTTPS/CORS/Tailscale, autenticação ou APK foram validados.

## Ordem de execução e critérios de aceite
1. Ler implementação real de `/api/prompt` e testes; confirmar campos, tipos, resposta e política de autenticação; diagnosticar 401 separadamente de 422.
2. Corrigir cliente e servidor apenas onde necessário; evitar persistir token no HTML, logs, Git ou capturas. Testar chamada válida e inválida em ambiente local, registrar status e resposta redigida.
3. Testar HTTPS privado via Tailscale PC↔POCO e origem da WebView; não abrir portas no roteador. Exibir estados separados para Ollama, ComfyUI, ponte PC e autenticação; não marcar online por inferência.
4. Fazer testes de interface em tela POCO, incluindo barra superior, abas, rolagem e formulário. Adicionar efeitos 3D como aprimoramento progressivo com redução de movimento e alternativa simples.
5. Registrar diff, commit, teste, reversão e SHA do build. Só publicar APK depois de confirmar build, assinatura e compatibilidade com instalação existente; atualização HTML via botão do app não é APK novo.
6. Para a história: cruzar Drive e inventário PC por conteúdo e hashes com consentimento; deduplicar cópias e snapshots. Não somar horas de agentes paralelos, ciclos de snapshots ou tempo de calendário como horas trabalhadas.

**Não executado neste registro:** comandos no Windows, conexão remota ao POCO, patch no HTML, build de APK, teste ponta a ponta ou ativação de contas ChatGPT/Gemini/Drive. Preservar `.venv/`, `remote-agent/aurion_remote_agent.egg-info/` e modelos locais.
