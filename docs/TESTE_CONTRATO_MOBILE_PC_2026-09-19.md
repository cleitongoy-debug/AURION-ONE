# Validação do contrato móvel ↔ PC

Estado: **pendente de teste real**. Não executar reset, reinstalar dependências nem publicar credenciais.

1. No servidor, localizar a definição atual de `/api/prompt` e o modelo Pydantic/validação efetiva. Documentar nomes, tipos e campos obrigatórios, sem copiar segredos.
2. No cliente `mobile/aurion-one-live.html`, conferir `sendChat()` e a URL base. Versão inspecionada envia `{prompt:text}` sem Authorization; o relato do PC exige `{text,device_id,moving}` com Bearer. O script `tools/patch_mobile_contract.py` é apenas uma proposta local, não evidência de correção aplicada.
3. Em testes locais controlados, diferenciar `422` (corpo inválido) de `401` (autenticação ausente ou recusada). Nunca imprimir Bearer em console, captura, issue ou logs.
4. Testar pelo endereço HTTPS privado do PC na rede Tailscale e pela WebView no POCO; localhost no POCO aponta para o próprio telefone. Validar certificado, origem/CORS quando aplicável e mensagens de erro claras.
5. Verificar os estados independentemente: portal, API autenticada, Ollama, ComfyUI e geração de imagem. Porta aberta não prova que a função de geração opera.
6. Só após testes, registrar commit/diff, rollback, workflow de build, SHA e assinatura do APK. Atualização de HTML pelo botão ATUALIZAR não reinstala o APK.

Resultados até este documento: **nenhum teste executado aqui**. Evidência externa: capturas do operador e relato de status, que não garantem estado atual.
