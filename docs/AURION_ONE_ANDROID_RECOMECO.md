# AURION ONE — recomeço Android (18/09/2026)

## Regra zero
Não alterar `index.html`, `mobile/aurion-launcher.html`, V2 local nem configuração Pages sem backup, teste e aprovação. Novo app em `android/`, independente do site 404. Não anunciar APK até compilação e instalação verificadas.

## Objetivo
Um APK Android instalado uma vez no POCO; atualizações posteriores por mecanismo explícito de atualização do app, sem baixar HTMLs separados. Interface única: Início, Chat, Gerações, Arquivos, Agentes, Configurações e Laboratório.

## Arquitetura
- Android nativo Kotlin/Jetpack Compose; credenciais via OAuth oficial com PKCE e Android Keystore, quando cada provedor oferecer integração apropriada. Não capturar cookies, senhas ou sessões de outros aplicativos.
- Orquestrador de tarefas com registro de provedores e capacidades verificadas (`chat`, `image`, `video`, `drive`, `github`, `sheets`). Seleção automática somente entre conectores autenticados e habilitados pelo operador; exibir provedor escolhido, custo/limite quando disponível e resultado.
- Operações de escrita, envio, publicação, exclusão ou cobrança exigem confirmação contextual do usuário; leitura de arquivos restrita ao escopo autorizado. Não enviar Bíblia ou documentos privados a modelos externos sem consentimento.
- Conector PC via rede privada autenticada, TLS e autorização; nunca abrir porta pública ou executar shell arbitrário. PC desligado = offline. Mi Band 9 Pro depende de integração Android oficialmente permitida e permissões.
- Chat independente no app: histórico local e mensagens por API; sites de terceiros não podem ser incorporados com login compartilhado por simples WebView.
- Geração: tarefa real, estado da fila, miniatura, arquivo final e erro; não mostrar preview local como geração concluída.

## Estados de conexão
`não configurado`, `autorização pendente`, `verificando`, `online autenticado`, `offline`, `erro`. `navigator.onLine` não valida PC ou provedor. Não declarar integração ON sem resposta autenticada.

## Ordem de entrega e critérios
1. Projeto Android compilável e APK assinado para teste; abrir no POCO e manter navegação/configurações após reinício.
2. Chat real com um provedor autorizado, diagnóstico e tratamento de erros.
3. Conector PC e geração ComfyUI com resultado real.
4. GitHub/Drive/Docs/Sheets com OAuth e permissões granulares.
5. Outros provedores e vídeo conforme APIs e planos disponíveis.
6. Atualizações seguras e testes de regressão antes de distribuir nova versão.

## Estado comprovado nesta data
Repositório GitHub acessível; painel web novo está em `mobile/aurion-one-live.html`; `index.html` foi restaurado para launcher antigo. Usuário informa 404 no Pages. PC informado desligado. Nenhum APK foi compilado ou instalado, nenhuma autenticação de provedor foi verificada, nenhum chat ou geração remota foi testado. Ambiente de execução desta conversa possui Java, mas não possui Gradle nem Android SDK detectados; portanto não afirmar APK pronto.

## Laboratório / evitar repetição
Antes de agir ler `LABORATORIO_IA.md` e `docs/STATUS_MOBILE_2026-09-18.md`; registrar hipótese, mudança isolada, resultado observado e rollback. Nunca trocar entrada funcional por protótipo nem pedir repetição de teste já documentado sem hipótese nova.
