# AURION ONE / PRODUÇÃO ATUAL — Protocolo <¥> — 2026-10-13

**Referência oficial:** versão 7.3.0-production-actions-preview, versionCode 75, aplicativo de TESTE **one.aurion.mobile.superstudio**. Branch `feature/producao-atual-personagem-storyboard-20261013`, PR #47 (não mesclada).

## Evidência verificável

- Código Android: `android/app/src/main/assets/production.html`, `production_tools.js`, `android/app/build.gradle`.
- Build GitHub Actions #38442063947: SUCCESS, SHA do commit `8c7b31dab707798503f71c4565a8c74407d4cb47`.
- Artifact id 11835682688 — `AURION-PRODUCAO-PREVIEW-7.3.0`. APK SHA-256 `47f0621c8111ed04856d531620f911e47cd1754724aaf8b35bbf5f059cf236ad`.
- ZIP armazenado na pasta de CONTROLE do Drive do usuário; validar acesso antes de afirmar sincronização de mídias.

## Ações efetivamente programadas
1. Registro de projeto local por `projectKey`, catálogo de sessões e restauração, com imagens em IndexedDB e metadados em localStorage.
2. Importação de manifesto JSON com validação e reset consciente de mídias ausentes; arquivamento local de múltiplos arquivos originais via seletor Android.
3. Exportação de originais de slots (fotos e vistas) e mídias arquivadas (limite de 20 MB na exportação para limitar memória do aparelho).
4. Conversão de imagem importada para PNG/JPEG/WebP via Canvas, sujeita ao decodificador do Android. Não mantém metadados EXIF, ICC, RAW, profundidade de cor ou camadas; não modifica os arquivos originais.
5. Montagem real de folha 360 em PNG 2400x1360, usando **apenas vistas importadas**, em ordem de 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°.
6. Gerador COMFYUI real: só mediante URL privada, ComfyUI acessível na rede, workflow exportado no formato API com nós `class_type` e `inputs`; envia `POST /prompt` pela ponte Java já existente (`queueComfy`), e preserva `prompt_id`. Resposta HTTP que aceita prompt NÃO comprova render concluído. Consulta `/history/{prompt_id}` e importação manual de resultado.
7. Atalhos TRI: (1) manifesto local/Android, (2) conexão PC ComfyUI, (3) abertura de pasta Google Drive para upload manual; além do compartilhamento via folha de compartilhamento Android. Logs locais auditáveis da ARANHA.
8. Fix de chave estável de mídia para novas cenas, evitando associações indevidas após exclusão/reordenação.

## Formatos e estado

| Formatos | O que funciona |
| --- | --- |
| PNG / JPEG / WebP | Importar, pré-visualizar, exportar, converter por Canvas |
| Outros formatos de imagem suportados pelo decodificador WebView | Importação como arquivos, prévia somente conforme suporte do Android |
| CR3 / CR2 / DNG / EXR / HDR / PSD / PSB / TIFF / HEIC | Somente arquivamento local de originais; sem revelação/conversão garantida neste módulo |
| MP4 / MOV / WEBM / WAV / MP3 | Somente arquivamento/importação local; produção de vídeo não integrada à tela |
| OBJ / MTL / GLB / GLTF / FBX / BLEND / C4D | Somente arquivamento local; sem visualizador ou conversor/modelagem 3D |
| ZIP | Arquivamento local, não descompacta automaticamente |
| JSON / CSV | Manifesto e shotlist; JSON aceita importação validada |

## Limitações e segurança

- **Nenhum render Octane nativo no Android**. Octane instalado/licenciado num PC com Cinema 4D só pode ser acionado depois da implementação e verificação de um serviço de render autenticado específico; botão inexistente neste pacote.
- **Nenhuma geração autônoma sem PC/modelos**. O módulo ComfyUI existente é fila real, mas os resultados requerem leitura/validação e importação manual no APK.
- **Nenhum upload automático de imagens para Drive**: URL no APK é atalho/identificador, não OAuth. Seletor SAF Android salva manifesto no dispositivo. `chooseWorkspace` exige escolha do usuário.
- **Sem instalação testada no POCO X7 nesta sessão**. CI valida sintaxe e APK compilável, mas não substitui teste funcional físico.
- **Não substitui 7.1.0 `one.aurion.poco.v6`**; package `one.aurion.mobile.superstudio` e assinatura debug. Não atualizar updater da antiga sem mesma package/signing key.
- O repositório pode ter visibilidade pública. Não publicar fotos de clientes, URLs de Drive privadas, tokens ou dados pessoais no GitHub. Clientes e mídias ficam em pastas privadas.
- Direitos e aprovação das referências do cliente permanecem pendentes até evidência.

## Continuidade para agentes
FALCÃO verifica origem/versão e roteia aprovações; ARANHA recolhe evidência e arquivos; RATO verifica integridade/manifests; KANG testa funções Android; CHINA avalia prompts e fluxos. Cada agente escreve o que executou com data/hora, id do arquivo e status `VALIDADO`/`CANDIDATO`/`ERRO`; não inventar progresso. Não duplicar registros; consultar Índice Mestre antes de salvar. Se houver erro de CI, registrar log integral e corrigir na branch, preservando anteriores.
