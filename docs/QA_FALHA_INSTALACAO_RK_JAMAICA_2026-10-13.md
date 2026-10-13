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

## Atualização operacional: SEGUNDA FALHA REPORTADA PELO OPERADOR

O operador voltou a relatar: "Cara tá dando erro pra instalar confere tudo", inclusive APÓS o APK `AURION_RK_JAMAICA_CORRIGIDO_INSTALAR.apk` com correção do alinhamento.

**Não considerar a hipótese de desalinhamento como causa confirmada da falha atual.** Auditoria neste ambiente:
- Arquivo atual: 57.335.596 bytes, SHA-256 `d3b075c6d992740d6e11c6e1825dbe6cfd2d6950d7a861d3e41e3d3c54a19a74`.
- Teste ZIP CRC: íntegro; 66 entradas; manifest binário AXML declara package `one.aurion.mobile.superstudio.preview75`, versionCode 75, minSdk 26, targetSdk 35, atividade principal `one.aurion.app.MainActivity` com exported=true.
- `resources.arsc` não comprimido alinhado em 4 bytes no offset 96748.
- Assinatura APK Scheme v2: assinatura criptográfica e digest consistentes na implementação de auditoria local, porém **ainda não verificados por apksigner oficial**.
- Contém `classes.dex`, `classes2.dex`, `classes3.dex`, `assets/production.html`, `assets/production_tools.js`, `assets/client001_bootstrap.js`, `assets/client001_media.js` e 47 entradas no diretório client001.
- Não há acesso ao smartphone, ao Package Installer nem ao adb neste runtime. Nenhuma instalação física foi realizada. Não distribuir outro arquivo sem diagnóstico específico.
- Solicitar a mensagem exata/screenshot do Android, ou pelo PC: `adb install -r AURION_RK_JAMAICA_CORRIGIDO_INSTALAR.apk` e capturar `INSTALL_FAILED_*`. Se `adb` não instalado, instalar platform-tools oficiais no PC.
- Diferenciar `INSTALL_FAILED_UPDATE_INCOMPATIBLE` (assinatura/pacote), `INSTALL_FAILED_INVALID_APK` (pacote), `INSTALL_FAILED_NO_MATCHING_ABIS` (ABI), `INSTALL_FAILED_INSUFFICIENT_STORAGE` (espaço), bloqueio de fonte desconhecida e falha de download incompleto.
- NÃO recomendar desinstalar os APKs anteriores, limpar dados ou alterar permissões de segurança sem identificar a causa.

O relatório anterior apontou "alinhamento" como causa provável; agora isso é apenas um defeito histórico corrigido, não explicação da falha atual.
