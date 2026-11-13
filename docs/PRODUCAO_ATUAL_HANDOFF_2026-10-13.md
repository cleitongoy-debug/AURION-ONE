# AURION ONE — PRODUÇÃO ATUAL — 2026-10-13

## Objetivo
Centralizar produção REAL de personagens para clientes: referências fotográficas -> model sheet com T-pose em 8 vistas -> arte para modelagem 3D -> quadro de storyboard -> pré-cena/clipe -> revisão -> entrega. Preservar autoria, identidade, original, proveniência e histórico de erros.

## Base verificada
- Repositório: `cleitongoy-debug/AURION-ONE`, área `android/`.
- Binário histórico (não alterado): `android/updates/AURION_EU3_MAESTRO_7_1_0.apk`. Manifesto existente `android/updates/latest.json`: `versionCode=73`, `versionName=7.1.0`, pacote `one.aurion.poco.v6`.
- Código-fonte `android/app/build.gradle` anterior: pacote `one.aurion.mobile.superstudio`, versão 7.0.0. **Pacotes diferentes: NÃO publicar o APK da branch como atualização in-place sobre o pacote do histórico.** Não substituir `android/updates/latest.json` sem conferir assinatura, SHA256, package, versionCode e instalação no POCO.
- Build do piloto: `7.2.0-production-preview`, `versionCode 74`, pacote distinto preservado. Instala como aplicativo de teste independente, sujeito a assinatura/debug e verificação.
- GitHub Actions na PR produz artefato de teste, não uma release oficial.

## Implementado na branch deste piloto
- Entrada "Produção" no painel Android.
- Página `android/app/src/main/assets/production.html` com operação local/offline, sem tokens em texto:
  - Projeto, cliente, identidade imutável, estilo, briefing, pasta Drive configurável;
  - 5 slots de imagens-fonte, arquivos preservados em IndexedDB; metadados separados;
  - 8 slots de vistas em T-pose: 0/45/90/135/180/225/270/315 graus;
  - prompt pronto para cada vista, prompt conjunto e contact sheet; NÃO renderiza malha nem gera imagem autonomamente;
  - storyboard com cenas editáveis, ação, ambiente, lente, câmera, duração, prompt de still e prompt de vídeo;
  - imagens de evidência por cena; histórico por agente/plataforma/status/link;
  - CSV de shotlist, JSON com prompts, histórico e referências, resumo para cliente e checklist de revisão;
  - exportação para Downloads/SAF; ponte Android nova `saveProductionManifest` para gravar JSON na pasta do Android concedida por seletor de diretórios; sucesso informado só após gravação confirmada.
- Os **arquivos de mídia não são incluídos no JSON**. O app mantém Blobs em armazenamento local e o usuário precisa também enviar imagens e clipes finais à pasta de mídia.

## Estrutura Drive criada — CANÔNICA
Sob `AURION_C4D/PRODUÇÃO/#PRODUCAO#ATUAL`, 11 pastas:
`00_INDICE_MESTRE_E_CONTROLE`,
`01_CLIENTES_BRIEFINGS`,
`02_REFERENCIAS_ORIGINAIS`,
`03_PERSONAGEM_TPOSE_360`,
`04_PROMPTS_FLUXOS_E_PRESETS`,
`05_CENAS_E_STORYBOARD`,
`06_CLIP_ANIMATIC_AUDIO`,
`07_MODELAGEM_3D_RIG_TEXTURAS`,
`08_ARANHA_E_REGISTROS_AGENTES`,
`09_REVISOES_APROVACOES`,
`10_ENTREGAS_CLIENTE`.
A pasta de agentes contém `00_CAIXA_DE_ENTRADA_ARANHA`, `FALCAO`, `RATO`, `KANG`, `CHINA`, `OUTROS_AGENTES`, `CONFLITOS_E_HANDOFFS`.
IDs/links privados devem ser inseridos pelo operador nos campos de configuração locais do APK, **não** publicados no repositório público.

## Protocolo ARANHA por produção
Unidade: uma evidência por execução de agente, sem sobrescrever originais. Identificador de job; ID de personagem; data/hora ISO; responsável; plataforma/modelo; entrada e links; prompt e configurações; saída e link; resultado (`EM ANDAMENTO|PRODUZIDO|VALIDADO|REJEITADO|ERRO`); comentário de continuidade; autor da aprovação. O campo `VALIDADO` só após evidência inspecionada. Sem fabricar porcentagem de pesquisa ou tarefas autônomas executadas.

**Fluxo do operador**:
1. Preencher personagem com ID estável e até 5 fotos do modelo (não editar original).
2. Copiar prompts de cada ângulo e gerar em plataformas/agentes escolhidos.
3. Importar cada saída REAL na vista correspondente; checar rosto, roupas, proporções e acessórios. Se inconsistentes, registrar rejeição e repetir.
4. Quando o model sheet estiver aprovado, produzir modelagem no C4D/Blender, conservar links FBX/OBJ, texturas, versão e licença.
5. Criar cenas e clipes curtos com continuidade; anexar frames reais a cada cena.
6. Registrar atividade e evidências dos agentes. Exportar manifesto JSON em pasta do Android autorizada por `AUTORIZAR PASTA` + `GRAVAR NA PASTA` ou salvar localmente e enviar ao Drive.
7. Conferir nomes, direitos, aprovação e somente então preparar entrega ao cliente.

## Próximas integrações — NÃO ENTREGUES NESTA PR
- Geração real de 8 imagens e multiview por ComfyUI via API ou motor conectado; atual são PROMPTS e SLOTS que recebem resultados.
- Sync automático bidirecional com Google Drive: requer OAuth/SAF confiável, fila de upload, retry, hashes, evitar duplicatas, conflitos e confirmação por arquivo.
- ARANHA ativa fazendo polling de agentes, filas e transporte automático entre plataformas; atualmente a aba é registro e exportação acionada pelo operador.
- Geração de clipes, transformação multiview->malha 3D, visualizador 3D 360° real.
- APK final assinado e update in-place para `one.aurion.poco.v6`: requer fonte e assinatura compatíveis.

## Critérios de aceite reais no POCO
1. Instalar a versão de teste em paralelo à versão do usuário; **não desinstalar a atual**.
2. Abrir Produção e importar cinco imagens de tamanho moderado, reiniciar app, verificar persistência.
3. Trocar nome/ID do personagem, verificar se referências continuam vinculadas ao mesmo job.
4. Copiar oito prompts; conferir exatamente oito ângulos, consistência de identidade e pose.
5. Criar duas cenas; copiar prompt de still/clip; anexar evidências e reiniciar.
6. Registrar dois agentes e checar persistência e exportação JSON/CSV.
7. Abrir seletor Android de pasta e escolher destino controlado; gravar JSON e verificar arquivo diretamente no destino; se Drive não oferecer pasta via SAF, exportar local e subir manualmente.
8. Testar falhas de permissão, grande imagem, app fechado e exportação sem destino; nenhuma operação deve mostrar ON falso.
9. Compilar debug no GitHub Actions; registrar status e links de artefato. Não publicar atualização oficial antes de testes e assinatura compatível.

## Regras
Não mexer na versão 7.1.0 original, não apagar versões, não expor credenciais ou links privados no Git público, não dizer que IA gerou mídia sem saída real comprovada, não confundir prompt com imagem, não criar percentuais inventados. Cliente tem prioridade sobre experimentação.
