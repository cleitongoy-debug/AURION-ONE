# AURION — QA instalação RK Jamaica · 2026-10-13

## Falha reportada
O operador informou que o APK Cliente 001 V7.4 não instalava no Android. A instalação física não pôde ser reproduzida porque o POCO não está conectado nesta sessão.

## Diagnóstico técnico verificado nos artefatos
- APK V7.4 de 57.335.012 bytes: ZIP íntegro e assinatura v2 (RSA SHA-256) criptograficamente válida.
- `resources.arsc` era um recurso `STORED` com deslocamento de dados **96.742 (mod 4 = 2)**. Estava **desalinhado**, comportamento incompatível com verificações de instalação exigidas em versões modernas do Android.
- Foi encontrada rotação de certificados entre compilações V7.4, que também pode produzir `INSTALL_FAILED_UPDATE_INCOMPATIBLE` quando o package ID é igual.
- O instalador fornecido ao usuário inicialmente usava `one.aurion.mobile.superstudio.preview74`.

## Correção entregue nesta sessão
- Reconstruído APK de instalação independente `one.aurion.mobile.superstudio.preview75`, mantendo o pacote de 46 imagens, o projeto inicial e o storyboard.
- `resources.arsc` passa a **96.748 (mod 4 = 0)**.
- Gerada assinatura APK Scheme v2, com integridade validada por verificação local do conteúdo e certificado.
- Otimizada rotina `arrayBufferB64` da pré-carga para preencher um `Uint8Array` diretamente e evitar a alocação de um array normal com dezenas de milhões de entradas.
- Executados `node --check` nos três scripts de produção, Bootstrap, media e tools: aprovação.
- Arquivo local final: `AURION_RK_JAMAICA_CORRIGIDO_INSTALAR.apk` (57.335.596 bytes).
- SHA-256 do APK: `d3b075c6d992740d6e11c6e1825dbe6cfd2d6950d7a861d3e41e3d3c54a19a74`.

## Estado pendente
- **Ainda não foi executado teste de instalação no POCO**; assinatura e alinhamento válidos não comprovam que o Package Installer aceitará a APK nas condições específicas do dispositivo.
- Este APK tem ID novo e não atualiza em cima da antiga versão. Não apagar arquivos/dados das instalações anteriores antes do backup.
- O pacote incorpora assets do Cliente 001 gerados localmente e não contém upload automático do Drive; NÃO publicar os arquivos de imagens no repositório público.
- Para futuras atualizações in-place, preservar seguramente o keystore da versão selecionada; não expor chave privada em GitHub público. Evitar alteração no APK depois de assiná-lo.
- Se o Android ainda negar, colher a mensagem completa de instalação ou log ADB (`adb install -r <arquivo.apk>`) antes de outra correção.
