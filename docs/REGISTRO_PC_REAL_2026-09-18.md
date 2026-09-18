# AURION ONE — registro verificável do PC (18/09/2026)

Leia junto com `LABORATORIO_IA.md`. Este registro corrige a informação antiga de que o PC estava desligado. Fonte: saída de CMD e inventário colados pelo operador nesta conversa; NÃO representa teste remoto executado pela IA.

## Evidência confirmada pelo operador
- Windows build `10.0.26100.9457`; pasta `C:\AURION-ONE`.
- `git pull --ff-only`: fast-forward `79ea2d0..02cbb69` concluído. `git status --short` anterior mostrou `.venv/` e `remote-agent/aurion_remote_agent.egg-info/` não rastreados; não apagar.
- `C:\AURION-ONE\START_AURION.cmd`: instalou/sincronizou dependências, tentou iniciar Ollama, copiou token local para área de transferência, gerou `remote-agent/data/inventory.json`, abriu portal.
- Uvicorn: `http://127.0.0.1:8765`, startup complete; GET `/` e `/api/inventory` HTTP 200. `favicon.ico` HTTP 404 não impede funcionamento do portal.
- Inventário `2026-09-18T21:01:24Z`: Windows 11; Python 3.12.9; RTX 2060 6144 MiB; discos C/D/E/F; Ollama encontrado em AppData, porém `models=[]` e porta 11434 não respondeu; ComfyUI detectado em `C:\COMFYUI`, mas porta 8188 não respondeu; projetos `E:\AURION-QB-QUANTUN` e `E:\LUMEN#QUANTUM#AURION#Q6`; FFmpeg não encontrado no PATH. Isso NÃO comprova ausência de modelos, FFmpeg ou programas em outras pastas.
- Operador relata POCO ligado e contas pagas; conexão POCO↔PC, autenticação Google, sessões de apps terceiros e Mi Band NÃO verificadas.

## Falhas da assistência — não repetir
1. Repetiu pedidos de CMD e testes já concluídos em vez de registrar a evidência e agir no GitHub.
2. Confundiu descoberta de pasta/executável com serviço ativo e prometeu integração antes de implementar/testar.
3. Não leu integralmente a Bíblia DOCX; não alegar que leu.
4. Botão Atualizar do APK altera HTML remoto, não corrige código Android nativo nem OAuth.
5. Painel móvel envia `/api/prompt` com JSON `{prompt:...}` e sem Bearer; agente PC exige Bearer e campo `text` (`PromptRequest`). `/api/image` não existe no agente atual. Corrigir contrato antes de afirmar que chat ou imagem funcionam.
6. Bootstrap atual abre navegador e mantém console em primeiro plano; NÃO está instalado como serviço de fundo nem configurado para iniciar automaticamente após ligar PC.

## Alteração efetiva nesta rodada
- Script `remote-agent/scripts/diagnostico_pc_20260918.ps1`: diagnóstico somente leitura de listeners locais, HTTP /health, Ollama e ComfyUI, processos e inventário. Não mostra token, não altera `.env`, não inicia programas e não abre portas. **Não executado no PC do operador.**

## Próximos critérios de aceite
- Confirmar diagnósticos reais e corrigir Ollama sem sobrescrever instalações existentes.
- Implementar autenticação e contrato JSON consistentes no painel/PC; usar conexão privada HTTPS e autorização explícita; não expor 8765 no roteador.
- Preparar inicialização em segundo plano sem mexer na sessão gráfica dos outros usuários, com instalação/reversão consentidas.
- Confirmar cada integração e permissão individualmente. Assinaturas de ChatGPT/Gemini/Adapta não equivalem a acesso de API ou compartilhamento automático de sessão.
- Preservar histórico, Bíblia, arquivos de modelos e configurações. Nunca registrar segredos no Git público.
