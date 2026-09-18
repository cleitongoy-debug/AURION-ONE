# Passagem de turno — APK POCO — 2026-09-18

Origem: pedido explícito do operador nesta conversa, compartilhada manualmente com outros dois agentes. Horário exato da mensagem do operador não disponível; data de referência 2026-09-18. Autor desta anotação: ChatGPT via conector GitHub. Não há comunicação direta entre as IAs.

## Pedido atual
Entregar um NOVO APK instalável para POCO o quanto antes; operador mantém CMD aberto e deseja preservar PC para jogo em segundo plano. Solicita texto pronto para compartilhar com outro agente e registro auditável das mudanças.

## Evidências, não repetir
Saída CMD do operador: Ollama lista quatro modelos e qwen3.5:4b respondeu `AURION TESTE OK`; ComfyUI main.py existe; Python PID 19528 executa ComfyUI; PID 6432 executa Open WebUI; PIDs 11400/15260 são Python run.py do portal; PIDs 14564/7868 são Python bridge_worker.py (não presumir duplicidade). Não há novo teste HTTP de ComfyUI ou PC↔POCO nesta mensagem.

## Revisão do código no GitHub
`android-app/app/build.gradle` em main define applicationId `one.aurion.app`, versionCode 1, versionName 0.1.0, minSdk 26, targetSdk 35. `android-app/settings.gradle` inclui :app. Ainda NÃO há APK novo gerado, assinado, instalado ou testado por esta IA. O painel móvel `mobile/aurion-one-live.html` usa POST `{prompt}` sem bearer enquanto backend `remote-agent/aurion_remote/app.py` exige `{text,device_id,moving}` e bearer; `/api/image` não foi encontrado nesse backend. Não publicar token ou IP privado no repositório público.

## Entrega e divisão de trabalho solicitada ao outro agente
1. Informar arquivo/commit exato em que está trabalhando e se já tem build Android em andamento; evitar sobrescrever mudanças paralelas.
2. Corrigir contrato mobile-PC com pareamento autenticado e transporte HTTPS privado sem abrir porta do roteador; nunca embutir token em APK ou Git.
3. Gerar APK debug para teste controlado ou release com assinatura do operador; registrar caminho REAL do artefato, SHA-256, applicationId, versionCode, assinatura e teste de instalação. Conferir compatibilidade de assinatura com APK já instalado antes de recomendar atualização; nunca pedir desinstalação sem alertar risco de perda de dados.
4. Validar PC↔POCO nos dois sentidos com consentimento; distinguir UI carregada de API autenticada. Não declarar Mi Band, capacete, vídeo ou imagem integrados sem teste específico.
5. Publicar resultado, hora UTC real, arquivos alterados, commit, testes, riscos e rollback na issue #2. Se build não estiver disponível, dizer exatamente qual bloqueio ocorreu, sem inventar link APK.

## Segurança operacional
Não reiniciar nem encerrar serviços do PC, não instalar dependências em massa e não iniciar geração GPU automaticamente enquanto outro usuário joga GTA. A existência de processos não garante disponibilidade atual dos endpoints; saúde deve expirar por timestamp. Registro GitHub é assíncrono, não sincronização automática com POCO.
