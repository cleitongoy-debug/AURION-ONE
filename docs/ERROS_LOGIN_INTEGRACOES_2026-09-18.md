# AURION ONE — erros de login e integração (18/09/2026)

Documento complementar a `LABORATORIO_IA.md`. Registro de falhas e expectativas relatadas pelo usuário; **não é evidência de implementação nem teste de funcionamento**.

## Problema recorrente
O usuário quer tocar em **Entrar com Google**, escolher a conta já existente no POCO e conceder autorizações oficiais para usar o AURION como central de PC, ChatGPT, Gemini, Adapta, Drive, GitHub e notificações da Mi Band. Repetidamente foram entregues atalhos externos, seletores de provedor e textos prometendo integração; esses controles **não equivalem a login integrado, autorização OAuth nem uso de APIs**. O usuário relata que as abas/ações não abrem ou não fazem o que espera. Não afirmar que tocar em Atualizar resolve autenticação ou integrações nativas.

## Erros a não repetir
- Não pedir e-mail, senha, cookies ou tokens em chat, HTML público ou repositório.
- Não confundir assinatura paga do aplicativo com autorização de API ou acesso à sessão de outro app.
- Não marcar serviços como ON apenas por `navigator.onLine`, por abrir um link, por HTTP `/health` ou por usuário estar logado em outro aplicativo.
- Não publicar botão fictício 'Entrar com Google': requer Credential Manager no Android, OAuth configurado para o pacote e assinatura corretos, cliente web e validação do token no backend. Google Drive requer autorização de escopo separada.
- Não prometer que painel HTML atualizado modifica permissões nativas, instala APK, controla outros apps ou liga o PC.
- Não declarar que Bíblia/Drive foram lidos integralmente sem leitura comprovada.
- Não exigir desinstalação repetida; preservar dados e testar assinatura/atualização.
- Não confundir acesso remoto à área de trabalho com integração de API de cada serviço.

## Evidência nesta rodada
- Código do painel consultado via GitHub: `mobile/aurion-one-live.html`, commit anterior informado `796f0ef5`; contém abas e links oficiais, endpoint PC configurável e seletores de modelos, mas não implementa autenticação Google nativa nem integrações de terceiros.
- Documentação oficial Android: https://developer.android.com/identity/sign-in/credential-manager-siwg e https://developer.android.com/identity/sign-in/credential-manager-siwg-implementation . O fluxo depende de Google Auth Platform/OAuth client IDs, Credential Manager e validação segura do ID token; Drive exige autorização própria.
- Nenhuma credencial OAuth, backend de autenticação, instalação no POCO, conexão PC ou Mi Band foi verificada nesta rodada.

## Próximas entregas verificáveis
1. Inspecionar `android/` (manifest, activity, Gradle, identificador de pacote, assinatura), workflow e backend antes de editar. Identificar requisitos OAuth ainda ausentes sem inventar client ID.
2. Implementar botão nativo real e estados 'não configurado', 'autorização solicitada', 'autenticado e validado' e 'falha'. Não expor ID token em logs.
3. Configurar OAuth por fluxo oficial com consentimento do usuário; verificar login em aparelho real. Autorização Drive separada.
4. Testar PC em rede privada somente quando ligado, autenticação por sessão segura e comandos permitidos, sem exposição pública.
5. Confirmar compatibilidade de notificações Android/Mi Fitness com teste no relógio, sem alegar acesso direto não documentado.
6. Para cada função: código/commit, workflow, APK ou painel publicado, teste real, falhas e reversão.

**Estado deste registro:** documentação criada; implementação de login, conexão e permissões permanece pendente. Nunca apresentar este documento como prova de que o app foi consertado.
