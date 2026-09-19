# AURION ONE — atualização Android com teste nativo de notificação

Data de referência: 2026-09-19 UTC. Origem: pedido do operador e capturas do POCO fornecidas na conversa; capturas privadas NÃO publicadas.

## Evidências distintas
- Operador mostrou Xiaomi Smart Band 9 Pro **conectada ao POCO** no Mi Fitness e no Bluetooth. Isso NÃO equivale à integração com o AURION.
- Mi Fitness mostra `Notificações de apps` habilitada e `Espelhar notificações do telefone` selecionado. Não há ainda evidência de notificação do AURION recebida no relógio.
- O APK 0.2.0 abriu no POCO (captura), mas não comprovou APIs ChatGPT/Gemini/Adapta/Drive, chat remoto nem geração.

## Alteração executável nova
- `android/app/src/main/java/one/aurion/app/BandNotificationTest.java`: cria canal de notificação e publica teste Android quando o operador toca em **Testar Band**; permissão POST_NOTIFICATIONS solicitada no contexto para Android 13+. O resultado comprova emissão via Android apenas; **recebimento no relógio requer confirmação do operador**.
- `android/app/src/main/java/one/aurion/app/MainActivity.java`: terceiro botão nativo `Testar Band`, preservando Atualizar, Socorro, WebView e cache do painel.
- `android/app/src/main/AndroidManifest.xml`: permissão contextual de notificações.
- `android/app/build.gradle`: versionCode 3, versionName 0.3.0; mesmo applicationId.
- Workflow `.github/workflows/aurion-android-apk.yml` faz build de APK debug em push de `android/**`; só considerar instalador disponível após `success`, artefato baixado e SHA-256 verificado. Build e dispositivo são testes distintos.

## Autenticação de contas — o que falta DE VERDADE
- A conexão GitHub deste ChatGPT permite leitura/gravação autorizada no repositório NESTA conversa; isso não transmite sessão ao APK.
- O login Google/GitHub/ChatGPT/Gemini/Adapta no app requer integração oficialmente suportada para CADA fornecedor, client IDs/redirect URIs configurados, autorização consentida, armazenamento seguro e validação pelo backend. Não existe OAuth universal ou herança automática dos apps já logados. Login externo por link é apenas abertura de serviço.
- O painel móvel e a API do PC ainda dependem de pareamento autenticado em HTTPS privado; a atualização do HTML não ativa controle remoto, ComfyUI nem `/api/image` ausente no backend auditado.
- Nunca incluir cookies, senhas, tokens de escrita ou dados privados do Drive no Git público ou em APK.

## Atenção: atualização sobre APK 0.2.0
O workflow usa assinatura **debug** gerada no ambiente GitHub Actions. Uma execução em outro runner pode gerar certificado diferente, mesmo com applicationId igual e versionCode maior; o Android então recusa atualização no lugar. NÃO pedir desinstalação automática; risco de perda de configuração. Para atualização estável, configurar assinatura de release com keystore privado gerenciado pelo operador (não no Git público), ou preservar a chave debug original por processo seguro. Ainda não comprovado qual assinatura está no aparelho.

## Teste mínimo do operador, parado em segurança
1. Atualizar/instalar somente se o Android oferecer atualização compatível; se houver erro de assinatura, parar e registrar o erro sem desinstalar.
2. Abrir AURION e tocar em `Testar Band`; conceder permissão do Android se solicitada.
3. Confirmar notificação no telefone e verificar se chegou na Mi Band; reportar separadamente os dois resultados.
4. O painel deve marcar Mi Band como `relatada conectada ao POCO`, e AURION→Band como `confirmada pelo operador` somente depois do teste.

**Não realizado por esta IA:** acesso ao POCO/PC, verificação direta Bluetooth, prova de chegada ao relógio, OAuth de terceiros e instalação Android. Nenhum serviço do PC foi reiniciado.
