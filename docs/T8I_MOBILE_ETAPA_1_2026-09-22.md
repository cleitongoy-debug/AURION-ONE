# AURION ONE — etapa 1: oficina Canon T8i no APK móvel

Data: 2026-09-22. Branch de desenvolvimento: `feat/t8i-mobile-editor-20260922`. Este documento registra código preparado, NÃO uma instalação ou um teste concluído no POCO. Não divulgar fotos ou dados privados neste repositório público.

## Base preservada
- Base: `android/` Mobile Fixo v2.0.0; `applicationId` preservado: `one.aurion.mobile.fixed`; código do painel de PC não alterado.
- Novo HTML isolado `android/app/src/main/assets/t8i.html`, nova ponte SAF `android/app/src/main/java/one/aurion/app/T8iBridge.java`.
- `android/prepare_t8i.py` executa em checkout isolado do CI: verifica âncoras, cria backups locais em `android/build/t8i-prepatch/`, conecta botão T8i no painel existente e adiciona ponte Android. Abortará se código-base não corresponder. Não reconstrói/substitui outras abas.
- `versionCode=21`, `versionName=2.1.0`; build `assembleDebug` via GitHub Actions. APK debug não é release assinada de produção. Instalação sobre versão diferente depende de mesmo applicationId e assinatura compatível: não desinstalar antes de exportar backup.

## O que foi programado — ainda sujeito a teste no aparelho
1. Abrir foto JPG/PNG e escolher CR3 via seletor oficial de arquivos Android; provedores como Drive só aparecem se disponíveis no aparelho e autorizados pelo usuário. Não há OAuth Drive embutido.
2. Ao selecionar CR3, tentar extrair somente um JPEG incorporado para prévia. Não existe decodificador RAW CR3 nesta etapa; nem todo CR3 fornecerá JPEG extraível. Um CR3 é fotografia RAW, não um vídeo Canon Log; não aplicar LUT C-Log automaticamente.
3. Editor local da prévia por canvas, não destrutivo: exposição, contraste, realces, sombras, temperatura, matiz, saturação, vibração; comparar antes/depois; ajuste localizado por retângulo, força selecionável. São aproximações visuais no espaço de pixels, não Lightroom completo, fluxo RAW de alta profundidade nem DaVinci Color/ACES.
4. LUTs criativas `.cube` 3D de grade 2–33; JSON de perfil validado e confirmação antes de aplicar; presets e notas locais, receita JSON exportável.
5. Câmera/galeria por seletor Android (`input capture`): compatibilidade deve ser testada no aparelho. Sem API de câmera manual/RAW no POCO nesta etapa.
6. Seleção explícita de pasta por Android SAF e gravação nova de JPEG/PNG/JSON nela, com mensagem de sucesso/falha. Salvar depende de suporte do provedor e permissões; a pasta pode ser local ou um provedor externo que suporte escrita. Nunca sobrescrever originais. O editor não salva os pixels originais em sua memória permanente; manter CR3 no Drive e exportar receita.
7. Nova ponte nativa restringe tipos MIME, nome e tamanho, mantém URI de pasta privada e somente é liberada na página interna `file:///android_asset/t8i.html`. Nunca conceder acesso de arquivos à WebView toda.

## Testes de aceitação obrigatórios (NÃO EXECUTADOS no dispositivo nesta etapa)
- [ ] Workflow compila APK debug e publica hash SHA-256.
- [ ] APK abre e todas as abas antigas continuam acessíveis; T8i abre dentro da mesma WebView e VOLTAR retorna ao painel.
- [ ] Selecionar uma foto JPG da galeria e comprovar prévia, mudança visível, antes/depois e reset.
- [ ] Selecionar CR3 original do Drive: registrar nome, tamanho, se JPEG embutido aparece; sem prévia exigir JPEG pareado. Não chamar isso de revelação RAW.
- [ ] Importar uma LUT `.cube` válida e uma inválida; validar aplicação e mensagem de erro.
- [ ] Salvar perfil, exportar receita JSON, fechar/reabrir e verificar notas/preset.
- [ ] Escolher pasta local autorizada, exportar JPEG e PNG, abrir cada arquivo em galeria externa e comparar qualidade com prévia.
- [ ] Testar pasta Drive via seletor Android e resultado de upload real, sem presumir suporte do provedor.
- [ ] Testar falta de permissão, cancelamento de seleção, espaço esgotado e arquivos grandes: sem falso sucesso.
- [ ] Testar conexão PC/serviços e regressão dos módulos Agente, Band, Modelos sem declarar que foram corrigidos por esta etapa.

## Pendências para etapas seguintes
- Revelação verdadeira de RAW Canon CR3 em 14/16 bits e exportação em resolução plena: backend PC com decodificador oficial/compatível, inventário da ferramenta e amostra ponta a ponta; não instalar atualizações incompatíveis automaticamente.
- Edição generativa de regiões por modelo de IA: exige autenticação e job backend ComfyUI concluído com imagem de saída; o retângulo atual é máscara de ajuste manual.
- Chat/agentes e listagem de modelos no POCO: contrato autenticado privado com PC, teste Ollama de geração; status HTTP não é demonstração.
- Login Google Drive/GitHub e navegação integrada: OAuth oficial e fluxo de retorno validado. Não armazenar senhas/cookies ou interceptar login de terceiros; links externos podem exigir navegador/app por política do provedor.
- Mi Band 9 Pro: diagnóstico BLE/notificação existente não equivale a dados ou controle proprietário. Headset do capacete: verificar perfil de áudio Bluetooth, permissões, reconhecimento e saída de voz com consentimento e teste parado em segurança. Não operar telas ou controles durante condução.

## Fontes e regras de trabalho
`Biblia_da_Inteligencia_Artificial_AURION_ONE.docx`, `docs/DIGITALPEN_BIBLIA_VISUAL_MODULOS_REFERENCIAS_3D_COR_CINEMA_2026-09-20.md`, `LABORATORIO_IA.md`. Preservar backup, validar funcionalidade com arquivo real, registrar execução/data/erro/rollback. Arquivos privados nunca entram no Git público.
