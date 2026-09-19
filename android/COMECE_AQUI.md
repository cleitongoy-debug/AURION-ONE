# AURION ONE Android — COMECE AQUI

> **Estado verificado em 18/09/2026:** existe um APK **debug 0.2.0 compilado**, mas não uma versão final com todas as integrações comprovadas. O arquivo foi extraído e conferido nesta conversa; **instalação/abertura no POCO e sincronização com PC permanecem sem teste confirmado**. Atualize as afirmações deste documento com novas evidências, não volte a dizer que não existe APK.

## APK debug já encontrado

- [Compilação GitHub Actions nº 8](https://github.com/cleitongoy-debug/AURION-ONE/actions/runs/35387872277), commit `f26729c18fb4e02616dc97dea2a503ee95af01aa`, resultado `success`.
- Artefato: `AURION-ONE-ANDROID-DEBUG-APK`, ID `10564403178`, arquivo `app-debug.apk` (13.900 bytes). Artefatos podem expirar; o link não é garantia de disponibilidade permanente.
- SHA-256 do APK: `4c39edbc743afb66081e5bfbadced3bc8c3e28161f20cc88f684af1d293d9d62`, conferido com `SHA256SUMS.txt` do workflow.
- APK debug foi disponibilizado diretamente na conversa do operador. Não há release pública assinada com chave de produção confirmada e a instalação no aparelho não foi verificada.
- `android/app/build.gradle`: `applicationId one.aurion.app`, `versionCode 2`, `versionName 0.2.0`. O botão **Atualizar** da Activity baixa apenas HTML do painel; não substitui o binário Android, autenticação OAuth ou permissões nativas.

## Links de continuidade

- [Reunião oficial de IAs](https://github.com/cleitongoy-debug/AURION-ONE/issues/2) — passagem de contexto assíncrona e registros datados.
- [Laboratório e correção da localização do APK](https://github.com/cleitongoy-debug/AURION-ONE/issues/3).
- [Critérios Android + PC](https://github.com/cleitongoy-debug/AURION-ONE/blob/main/docs/ENTREGA_ANDROID_PC_CRITERIOS.md).
- [Código-fonte Android](https://github.com/cleitongoy-debug/AURION-ONE/tree/main/android).

## O que existe e o que ainda falta

O APK 0.2.0 abre um WebView cujo HTML pode ser atualizado por `mobile/aurion-one-live.html`. A versão incluída como fallback é básica. O backend PC em `remote-agent/aurion_remote/app.py` recebeu o endpoint autenticado `POST /api/scan` e botão de scanner no painel do **PC** (commit `af38bf577ec35a7844bc38f7000b60e34ca6a7d4`); isso **não significa que o serviço Windows já aplicou/reiniciou com esse código**, nem que o botão existe na tela Android.

A conexão móvel ainda exige corrigir o contrato entre `mobile/aurion-one-live.html` e `/api/prompt`, autorização segura na rede privada e teste real. `/api/image` não existe nesse backend. Login Google/Drive, acesso às sessões de ChatGPT/Gemini/Adapta, Mi Fitness/Mi Band, microfone Bluetooth, mídia e autoatualização do APK não estão comprovados; não exibir ON fictício.

## Instalação e segurança

Instale apenas APK cuja origem e checksum você consiga conferir. Uma atualização instalada sobre aplicativo existente precisa ter **mesmo applicationId, assinatura compatível e versionCode adequado**; caso contrário o Android pode impedir a atualização. Não peça desinstalação como solução padrão, pois dados locais podem ser perdidos. Permissões são concedidas no aparelho pelo operador. Não publicar senhas, tokens, cookies, URLs com credenciais, dados do relógio ou arquivos privados neste GitHub público. Não operar a tela enquanto dirige.

## Próximo teste mínimo

Quando o operador estiver parado em segurança, registrar se o APK abre no POCO, quais abas aparecem, e se a URL privada do PC responde com sessão autenticada. Não repetir testes de login GitHub, Tailscale, modelos Ollama ou detecção de processos já documentados sem nova hipótese. A execução do scan do PC só deve ser declarada concluída depois de resposta real de `/api/scan` com `scanned_at` atualizado.
