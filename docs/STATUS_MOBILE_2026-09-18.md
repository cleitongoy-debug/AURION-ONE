# AURION ONE — status móvel (18/09/2026)

## Confirmado
- Repositório `cleitongoy-debug/AURION-ONE` acessível no POCO; conexão GitHub do assistente conseguiu gravar `mobile/aurion-launcher.html` (commit `294fedace91378f86f7c091152338b2e42193ca1`).
- Usuário usa POCO X7, Termux e Mi Fitness com Mi Band 9 Pro.
- URL GitHub Pages `https://cleitongoy-debug.github.io/AURION-ONE/mobile/aurion-launcher.html` retorna 404 no celular; não afirmar que o painel foi publicado.
- Capturas mostram GitHub `/settings` da conta pessoal e 404 em tentativa de acessar configurações do repositório; o repositório em si abre. Não confundir as duas páginas.
- `remote-agent/aurion_remote/app.py` possui FastAPI, `/health`, `/api/status`, `/api/device`, `/api/prompt`, token e painel HTML local; não há confirmação de execução do PC nem conectividade remota.

## Próximos passos verificáveis
1. Conferir URL e nome exatos do proprietário do repositório no navegador autenticado; verificar configurações do repositório em vez de configurações da conta.
2. Habilitar GitHub Pages pela interface administrativa, se disponível, usando branch `main`, pasta `/ (root)`; aguardar deploy e verificar URL HTTP 200. Criar arquivos no GitHub não habilita Pages.
3. Usar `mobile/aurion-launcher.html` como central de links; ela não autentica nem conecta automaticamente serviços de terceiros.
4. Quando PC ligar, executar diagnóstico do `remote-agent` e disponibilizar painel apenas por HTTPS em rede privada com autenticação; nunca publicar token, IP privado sensível ou portas de administração no GitHub público.
5. Mi Fitness é o app do relógio; notificações e permissões dependem do Android/Mi Fitness. Não prometer API de controle da Mi Band.
6. Termux pode servir para testes e desenvolvimento local; não instalar pacotes nem expor servidor sem consentimento e verificação.

## Segurança e entregas
Não colocar senhas, tokens, cookies ou dados de contas pessoais/redes sociais neste repositório público. Vincular serviços apenas via login oficial/OAuth quando houver integração compatível. Não operar a tela durante deslocamentos; comandos remotos bloqueados em movimento conforme configuração do agente.
