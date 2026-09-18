# AURION ONE — critérios de entrega Android + PC

Data: 2026-09-18. Estado: especificação, NÃO é APK compilado nem conexão testada.

## Evidências inspecionadas
- `android/app/src/main/java/one/aurion/app/MainActivity.java`: WebView com Atualizar/Socorro nativos, painel remoto em `mobile/aurion-one-live.html`; não implementa Credential Manager nem notificações nativas.
- `remote-agent/README.md`: servidor Windows em loopback `127.0.0.1:8765`, token em rotas privadas, prompts desligados por padrão; rede privada POCO-PC ainda planejada.
- `LABORATORIO_IA.md`: não repetir testes sem hipótese nova; não divulgar credenciais neste repositório público.

## Bloqueios reais antes de chamar o novo APK de funcional
1. Login Google: registrar cliente OAuth Android com package name e SHA-1 da assinatura usada no APK, e cliente Web; implementar Credential Manager e validar token no backend. Sem IDs válidos e backend verificador, mostrar 'Configuração pendente', jamais 'Conectado'. Login Google não dá acesso automático a ChatGPT/Gemini/Adapta; Google Drive requer autorização separada.
2. PC: verificar execução local do agente, autenticação das rotas, contrato `/health`, `/api/status` e `/api/prompt`; manter shell remoto desabilitado. Só então conectar POCO e PC por HTTPS privado/VPN autenticada; nunca abrir porta do roteador.
3. Android: manter Atualizar/Socorro fora das barras de sistema, conservar fallback offline, registrar erros legíveis, pedir notificações/microfone pelo fluxo nativo somente quando necessários.
4. Modelos/softwares: inventário real e opt-in no PC, sem inventar modelos instalados; só exibir ON depois de chamada autenticada bem-sucedida.
5. Mi Band: testar notificação Android e encaminhamento pelo Mi Fitness; não confundir notificação comum com acesso direto ao relógio.
6. Compilação: confirmar GitHub Actions `assembleDebug`, SHA-256 do APK e versão/commit; instalação e login no POCO permanecem NÃO TESTADOS até evidência do dispositivo.

## Regra para próximas IAs
Não reenviar APK antigo com nome novo. Não prometer 'vou fazer em segundo plano' sem tarefa agendada. Não pedir senha, token ou cookie no chat ou em campo de URL. Registrar commit e resultado de cada teste em `LABORATORIO_IA.md`. Antes de mexer no PC, perguntar apenas se já foi ligado, pois último estado registrado era desligado.

## Próxima implementação concreta
Inspecionar `android/app/build.gradle`, manifest, `remote-agent` e workflow; adicionar UI nativa de login com configuração OAuth não secreta por build, sem simular autenticação; preparar teste local do agente e contrato autenticado; compilar e disponibilizar APK somente após verificação. Se faltar configuração Google Cloud, indicar o bloqueio exato sem marcar login como concluído.
