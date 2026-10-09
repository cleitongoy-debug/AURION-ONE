# Laboratório EU3 — registro de ação
Pesquisa iniciada 2026-10-09T17:36:23Z (14:36:23 BRT). Marco de transição observado 17:46:17Z; correções iniciadas imediatamente depois. Não afirmar precisão de segundos ou leitura integral de cinco anos.

## Causas comprovadas e limites
O documento AURION_LAB_FUSAO_OCTANE declara que registros ficam apenas na aba aberta. O laboratório do APK comparava respostas de duas rotas, sem árvore de pré-requisitos ou prova de leitura. Código antigo usa cortes de contexto de 4000/50000 caracteres. Essas limitações podem excluir conteúdo de uma rodada; não provam qual informação se perdeu em cada sessão anterior. Pesquisa por nomes não substitui leitura do conteúdo, prints e código. Não foi recuperada referência histórica ao EU3 nos trechos examinados; a autoria/experiência no clã Caveira é informação relatada por Cleiton.

## Método implementado
Fila persistida por perfil em localStorage; pré-requisitos só liberam após validação registrada; fonte obrigatória, trecho lido e resultado reproduzível obrigatórios; tempo conta apenas em primeiro plano e não continua após reabrir. Intervalos maiores que 5s são excluídos conservadoramente. Respostas de IA não validam pesquisa automaticamente. Exportação JSON disponível. Validação é declarada pelo operador, não auditoria independente. Ainda não sincroniza esta fila ao Drive.

Referência de pesquisa: https://github.com/mgemard/ikopit commit 936e7d8c52ffe67f4a2ac080867db94879f07d54. Árvore dev/techtree_global_en.gv e calculador war/WEB-INF/research-time.jsp. Componentes, dependências e estimativas de progresso inspiram o método; tempos do jogo não medem aprendizado humano. Nenhuma imagem do jogo copiada.

## Onde estão os estudos localizados
Laboratório Fusion Octane: https://docs.google.com/document/d/1Zh2uT-__vlHAXkz36Ia-_-jXkoRUYcZUsJcF6oc2DSc
Laboratório IA: https://docs.google.com/document/d/1GNiUDjkaBSAttb8DNRotsvpdRlaedMtNb2rcrGBVdGs
Biblioteca conhecimento: https://drive.google.com/drive/folders/1480epyBbO9QGf7y1Nk9Vy1nWIQaPbZy3
Índice: https://docs.google.com/document/d/1-oLBlBtPzsvCExOuLvKDZDkW6pnStOAxU2C44ruWcyM
Diário de ações: https://docs.google.com/document/d/1MKxMxELoYV01qhpHEVvt39D2a1QBtQ1OHBmTvgUtJ70
Pasta de conhecimento histórica: https://drive.google.com/drive/folders/1twLu6zYpN8c8-BGaJn8UBIJhasnxRvDi
A listagem da pasta principal teve paginação parcial. Este mapa identifica o acervo localizado, não certifica que todos os documentos foram lidos.

## APK e instalação
Build local tentou resolver Android Gradle Plugin 8.7.3 e falhou por proxy inacessível. Arquivo APK anterior não contém esta correção. Não disponibilizar APK antigo como novo. Não desinstalar para contornar divergência de assinatura. O comando de instalação deve parar quando build, hash, assinatura ou conexão falham.

## Continuação: compilação concluída e instalador sem Gradle no PC
A falha inicial foi resolvida usando o proxy atual de HTTPS_PROXY em GRADLE_OPTS. assembleDebug e assembleRelease concluíram. A versão 7.0.2-preview (código72) tem rótulo AURION ONE · LAB EU3; a inclusão e os bytes do módulo foram conferidos dentro do APK. APK SHA256: 23138ba5d7e71cdbecd1cf818253662c7e8568b96d5dc867bb70ca528c4fd3b5. Certificado da prévia SHA256: 82504955d5b16244c634731d39c2c8add520e0842c7f4312faf5cb1526f6e3ea. A assinatura difere da prévia anterior. O pacote principal só pode ser atualizado com sua chave original.

O comando APLICAR_LAB_EU3.cmd agora utiliza APK e ADB Windows incluídos, verifica hash, escolhe um aparelho autorizado, instala com -r e abre a prévia. Registra horários e falhas em logs, sem desinstalar. PowerShell validado em parser e testes sintéticos: sucesso, falha de assinatura e hash divergente antes de ADB. Não houve instalação física.

Teste de Chromium real indisponível neste ambiente (socket não permitido; headless shell encerrou). Não declarar aprovação visual ou física. O módulo possui testes de lógica; regressões existentes passaram. A fila ainda não sincroniza ao Drive e não lê documentos automaticamente.

## Auditoria de contraprova, reversão e automação — rodada iniciada 2026-10-09T19:03:03Z
Escopo: leitura dos registros atuais do Drive/Git, código EU3 da PR #42 (head 1da8611b0b9b8efb28225f17ba508bc39d0fd21c), fonte pública ikopit e documentação técnica primária. Somente estudo/QA e documentação nesta rodada; nenhum APK instalado, nenhuma conexão com aparelho comprovada e nenhuma hora humana adicionada aos contadores. A solicitação de 20 minutos é uma meta, não um recibo de duração já cumprida.

### Bate e rebate: resultado reproduzível
Teste sintético Node/VM carregando o research_eu3.js original, armazenamento em memória:
1. Criar A; criar B dependente de A e C dependente de B. B bloqueada antes de provar A: confirmado.
2. Registrar prova aprovada em A, B e C; depois registrar contraprova reprovada em A.
3. Resultado: A=EXPERIMENTAL com duas provas preservadas; B e C têm ready=false, mas continuam com status=VALIDADO. O bloqueio transitivo funciona; o rótulo persistido não expressa a invalidação. A seleção de pré-requisitos também usa o status antigo.
4. Reabrir o motor preserva os itens e deixa active=null: confirmado. Não retoma estudo invisível.
5. Exportação tem version/items. Não existem métodos import/restore nem controle de restauração no módulo. O backup geral do app exporta interface/memory e não inclui a chave aurion_eu3_research_v1. Exportar não demonstra recuperar.
6. Timer com ticks em 1000ms e 100000ms após início em zero registra só 1000ms: confirmado. Intervalo longo é excluído, não contado como dedicação. A gravação de prova encerra a sessão sem receber um timestamp monotônico para contabilizar o último fragmento entre ticks; não prometer precisão de cada segundo humano.

Esses resultados são testes de lógica em ambiente sintético, não QA físico no POCO. Não são horas estudadas por Cleiton nem prova de leitura humana de uma fonte.

### Adaptação EU3 com limites explícitos
O código comunitário ikopit contém árvores de tecnologia em DOT e calculador por faixas percentuais no JSP; não é código oficial do servidor. A servlet Researchtime.java apenas encaminha à página, portanto não contém a fórmula.
O calculador estima tempo total entre elapsed/p_superior e elapsed/p_inferior; a duração restante subtrai elapsed. Limites de porcentagem zero e 100% precisam de tratamento próprio. Exemplo exclusivamente sintético: 20min observados na faixa 47–53% dão total de aproximadamente 37,74–42,55min. Isso é uma estimativa sob o modelo do jogo, não dedução de dedicação humana a partir de progresso de curso.
Na árvore DOT, arestas de layout style=invis e rank=same não devem virar pré-requisitos de pesquisa. Dois pré-requisitos reais de uma técnica exigem os dois critérios aprovados. Publicação oficial gamigo confirma novos itens de pesquisa/balanceamento no Infinity, mas não fornece a fórmula usada pelo calculador comunitário.

### Protocolo proposto para automatizar com provas e reversão
Proposta para implementação futura; não declarar já presente no APK:
- Cada pesquisa registra ID estável, fonte/versionamento (hash ou revisão), pré-requisitos, hipótese, critério, procedimento, orçamento de tempo/tokens e recibos. Uma IA pode propor, executar um teste autorizado e registrar evidência; texto convincente sozinho não prova descoberta.
- Estados separados: CANDIDATO, EM_ESTUDO, EM_TESTE, VALIDADO, EXPERIMENTAL, REVISAO_PENDENTE e BLOQUEADO. Contraprova ou mudança da fonte marca todos os descendentes como REVISAO_PENDENTE, mantendo os recibos antigos e seus horários.
- Executar apenas itens desbloqueados, com limite de tentativas, concorrência e orçamento. Espera/backoff não entra no contador de estudo. Falha de crédito/autenticação não deve repetir sem limite; rotas alternativas precisam comprovar capacidade e acesso.
- Idempotência: uma tentativa tem attemptId; uma operação lógica tem operationId estável. Repetir uma requisição não deve duplicar estudo, entrega ou lançamento financeiro. Deduplicar texto não pode apagar duas sessões reais distintas.
- Antes de publicar resultados, gravar recibo completo por etapa: fonte detectada, conteúdo obtido, intervalo efetivamente lido, teste executado, saída/erro e validação. Metadados de arquivo não equivalem a leitura.
- Backup/restauração deve incluir fila EU3, dedicação e memória documental; conferir versão, perfil, integridade e contagens; importar atomicamente; mostrar relatório de conflitos. Arquivo externo referenciado por URI requer cópia dos bytes ou indicação explícita de ausência.
- Reversão não apaga histórico: criar snapshot antes da alteração, preservar provas, registrar evento de reversão e reexecutar a validação em ordem de dependências. Troca de assinatura Android não deve ser contornada por desinstalação.

### Auditoria do agendador existente
Leitura estática de AurionHourlyWorker.java/AurionStartupWorker.java: o worker existente observa manifest/Git, metadados Drive, perfil/modelos HF e snapshot PC. Não executa pesquisas EU3 automaticamente e não comprova leitura de documentos. contentRead=false nos registros Drive é correto.
O indicador agregado ok torna-se true se qualquer uma das consultas tem sucesso; portanto “ciclo concluído” não comprova todas as conexões. Além disso, o sync_event é gravado antes da execução de AurionPcMemorySync.run e antes de r receber pcMemorySync; esse evento não contém o resultado final dessa etapa. Proposta: persistir resultado por serviço e um recibo final depois de todas as etapas, distinguindo CONCLUIDO/PARCIAL/BLOQUEADO. Observação de código, sem execução de rede do aparelho.
WorkManager serve para tarefas persistentes sujeitas às restrições do sistema; periodicidade não é cronômetro de dedicação e não promete execução exata em segundo específico.

### Referências primárias e critérios para a próxima implementação
- Código comunitário de autoria: https://github.com/mgemard/ikopit/tree/936e7d8c52ffe67f4a2ac080867db94879f07d54 ; dev/techtree_en.gv, dev/techtree_global_en.gv, war/WEB-INF/research-time.jsp.
- Publicação do servidor: https://corporate.gamigo.com/en/presse/empire-universe-3-world-server-launched-with-new-features/
- Android WorkManager: https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work
- Dependências e invalidação por mudança de entradas (DVC): https://doc.dvc.org/user-guide/pipelines/defining-pipelines
- Repetição/idempotência de operações (Temporal): https://docs.temporal.io/nexus/operations
- Backup consistente e atomicidade SQLite: https://sqlite.org/backup.html e https://sqlite.org/atomiccommit.html

Gate mínimo: teste de contraprova transitiva com rótulos corretos; exportar→restaurar preservando IDs/provas/tempos/perfil; falha no meio da importação sem perda; erro parcial visível por serviço; retomada sem duplicação; temporizador sem contar sono/background; QA físico posterior. Não marcar esses gates como aprovados antes de executá-los.

### Complemento: pacote conferido, relógios e uso pelo capacete
Verificação posterior desta mesma rodada, sem instalação: materializado o ZIP AURION_LAB_EU3_20261009.zip (12.454.396 bytes, SHA256 fa80e1d64b51f82bebb4ee2ccb7d9d30287a764a35fed6b0da96f640d6c03e1c). CRC íntegro; os 20 itens declarados em SHA256SUMS.txt conferem. O módulo assets/research_eu3.js em ambos os APKs tem 6092 bytes, SHA256 2b770cc991479bcda27cbc8797604b94a21d0e22779cefef0ad1c13f5e583f76 e corresponde byte a byte ao conteúdo Git auditado. Diferença inicial de um newline era da cópia de auditoria, não do pacote. Isso comprova identidade dos bytes, não instalação ou funcionamento físico.

A prévia tem SHA256 23138ba5d7e71cdbecd1cf818253662c7e8568b96d5dc867bb70ca528c4fd3b5; o release sem assinatura tem SHA256 8e1068a40c83a506b1b8949dc4666ce26d916f8cc20092389009670c264cec1c. O release sem assinatura não é instalador pronto. O ZIP continua sendo o pacote anterior; estas anotações não são um APK novo.

Nova contraprova sintética no dedication.js exato da PR #42 (blob 178366abb43b2ac53ebd2982d7afb4ab0d27e69f): iniciar em Date.now=0, disparar callback de 1s em 1000, próximo callback em 61000, document.hidden=false, encerrar. Saída: start=0/end=61000/seconds=61. Um intervalo não observado de 60s entra no total. A união de intervalos elimina sobreposição quando relógios estão alinhados, mas não corrige saltos de relógio nem lacunas de observação. Não houve suspensão real do POCO neste teste.
Correção proposta: timestamps UTC para contexto, duração por relógio monotônico local e eventos de atividade; guardar início/fim, clockDomain/bootId, elapsedMs, lastObservedAt e interrupções. Não comparar diretamente performance.now de PC e POCO/reinícios. Incerteza de relógio entre aparelhos precisa ficar visível antes de chamar a soma de exata. Espera de automação é uma categoria separada.

Tela apagada não significa ausência de estudo por áudio. Separar TEMPO_DE_SESSAO_OBSERVADO, TEMPO_DE_REPRODUCAO_AUDIO, PROGRESSO_OBSERVADO, CARGA_HORARIA_DO_CURSO, HORAS_DECLARADAS_CERTIFICADO e RESULTADO_DE_EXERCICIO. Somar segundos de dedicação sem duplicar uma sessão simultânea PC/POCO; não somar essas categorias heterogêneas como se fossem todas horas medidas. Áudio reproduzido prova reprodução, não compreensão; avaliação/projeto/contraprova documentam aplicação.

Código do capacete auditado no MainActivity.java exato da PR #42 (blob e674db0cb4369018c67ff0d9728b09a8016c378e): o callback de HEADSETHOOK/MEDIA_PLAY_PAUSE chama listenVoice; onResume ativa a MediaSession e onPause a desativa. Ditado usa Activity de reconhecimento; fala usa TextToSpeech. Isso não demonstra assistente sempre ativo em background. Manifest/build.gradle atuais não declaram MediaSessionService de áudio nem dependência Media3. Não prometer “tudo funcionando no capacete” sem teste físico.

Proposta baseada em documentação oficial: sessão de mídia em serviço para estudo por áudio, recibos das transições isPlaying/pausa/buffering/erro, conteúdo e posição, controles do fone e retomada explícita. Não usar diferença de posição após seek como segundos de estudo; em velocidade 2x, registrar separadamente tempo real e extensão do conteúdo. Manter áudio em background não exige marcar todo tempo de tela apagada como estudo. Microfone e comandos contínuos exigem implementação própria e validação; MediaSessionService de reprodução, sozinho, não entrega conversa livre nem reconhecimento sempre ativo.

Gates adicionais antes de contadores “precisos”: salto de relógio para frente/trás; suspensão sem visibilitychange; reinício; áudio pausado/buffering/seek/2x; falha de rede; duas sessões simultâneas; perfis separados; restore sem perder recibos. Capturar testes físicos do fone parado quando disponível, sem pedir interação durante o trajeto.

Fontes primárias adicionais:
- Relógios Android: https://developer.android.com/reference/android/os/SystemClock
- Tempo monotônico/contextos: https://www.w3.org/TR/hr-time/
- Eventos de reprodução: https://developer.android.com/media/media3/exoplayer/listening-to-player-events
- Sessão em background/controles Bluetooth: https://developer.android.com/media/media3/session/background-playback

### Matriz de reaproveitamento dos estudos
O laboratório de fusão/Octane localizado é um protótipo que declara registrar referências sem ler os bytes e perder o estado ao fechar. Deve alimentar a fila persistente por importação verificável, não ser tratado como executor já conectado. Para cada experimento digital, preservar origens A/B, versões, objetivo, critério, configuração, saída e contraprova. Em comparação de render, manter cena/resolução/samples/denoiser/driver/GPU comparáveis; em rig/personagem, critério e teste devem ser próprios do objetivo. Não confundir diferenças de configuração com descoberta reproduzida.
O documento compartilhado de IAs é passagem histórica de contexto; seus estados datados não substituem recibos atuais. Cruzar cada alegação com sua prova e versão, mantendo “relatado”, “observado por ferramenta”, “testado sinteticamente” e “testado no aparelho” separados. Documentos podem contradizer-se sem apagar a evidência mais antiga.

### Ordem dos scripts: voz e laboratório automático legado
Conferência adicional do index.html/aurion6.js/aurion64.js no mesmo head auditado:
- aurion6.js implementa voiceCommand, atalhos, envio e aurionVoiceReplyPending para fala da resposta; atribui window.aurionVoiceResult=voiceCommand.
- Depois de carregar esses scripts, o script inline final do index.html reatribui window.aurionVoiceResult a outra função: preenche o campo e envia somente quando o opt-in local está habilitado e o provedor é offline/local. Essa função não chama voiceCommand nem define aurionVoiceReplyPending. Assim, o caminho final do ditado não é o dispatcher de comandos definido no módulo. Achado por leitura de ordem de execução; teste em aparelho ainda pendente.
- Existe startAutoLab legado: usa rotas configuradas com mesmo prompt, avança até duas respostas ou esgotar rotas e grava experiment. Essa automação A/B existe no código, mas não valida experimentos físicos, não lê fontes automaticamente e não integra a fila EU3. Portanto “EU3 manual” não significa que toda automação anterior esteja ausente.
- profile_scope.js é carregado primeiro e prefixa getItem/setItem/removeItem de perfis secundários; a chave EU3 usa essa camada. O isolamento por perfil descrito não depende de uma chave diferente definida diretamente no research_eu3.js. Isso não soluciona os gates de backup/restauração.

Proposta de correção futura da voz: um único dispatcher final, que respeite permissões e opt-ins, interprete atalhos, registre o comando e encaminhe resposta falada sem atribuições que se sobrescrevem. Critérios: ditado chega ao dispatcher; atalho abre destino permitido; pergunta gera a resposta esperada; erro é falado/registrado; botão com app em background é testado fisicamente. Não ativar gastos, ações ou envio externo apenas porque o reconhecimento ouviu uma frase.

Regressões originais do test_research_eu3.cjs também foram reproduzidas sobre o módulo extraído do APK: dependências, campos de prova, timer limitado, persistência, sessão pausada ao reabrir e dependência desconhecida passaram. A contraprova adicional sobre esse mesmo módulo reproduziu B.status=VALIDADO com B.ready=false.

### Atualização permanente: o que o código atual realmente oferece
MainActivity.java auditado: checkForUpdate interrompe quando o nome do pacote contém .preview e informa uma versão literal 7.0.0-preview; a prévia EU3 é 7.0.2-preview. O cabeçalho HTML ainda diz V7.0.1 FIX. Esses rótulos precisam ser derivados da versão instalada, para evitar recibos inconsistentes.
No pacote principal, a instalação oferecida confere URL limitada ao canal publicado, SHA256, packageName, versionCode e certificado do APK, e abre a tela de instalação Android com ACTION_VIEW. Isso é oferta de atualização conferida, não instalação silenciosa nem reboot automático comprovado. O trecho usa GET_SIGNING_CERTIFICATES/signingInfo, disponíveis a partir de API28, enquanto minSdk é26; o tratamento dessa diferença também exige revisão antes de afirmar suporte a todas as versões mínimas. Não houve teste de atualização nesta rodada.

Documentação Android prevê instalação sem ação em condições específicas de PackageInstaller.SessionParams (API31+), incluindo configuração explícita, requisitos de versão/ownership ou autoatualização e permissão declarada. Ainda exige tratar STATUS_PENDING_USER_ACTION. A abordagem atual ACTION_VIEW não implementa esse contrato. Proposta: canal assinado estável, migração de dados testada, callbacks de instalação/erro e confirmação quando o Android exigir; diferenciar reinício do app de reboot do telefone. Fonte primária: https://developer.android.com/reference/android/content/pm/PackageInstaller.SessionParams

### Marcos observados da rodada (UTC)
- 19:03:03: início registrado.
- 19:12:40: readback confirmou a primeira anotação do diário e o relatório Git.
- 19:13:34: contraprova de lacuna no contador de dedicação.
- 19:15:13: ZIP/CRC/APK e diferença de newline examinados; depois conferência exata de bytes e 20 hashes.
- 19:17:12: commit e59727e91a8c3382b26aa58e8b08ed255ca3c2f8 registrado.
- 19:18:15–19:18:30: encadeamento de voz e laboratório A/B legado conferidos.
- 19:19:34: início da conferência das regras Android para atualização.
Esses marcos são registros do trabalho desta IA, não eventos de estudo de Cleiton, nem instrumentação segundo a segundo de um aparelho. A duração de fechamento deve usar o último timestamp efetivamente observado, sem preencher tempo inexistente.

Checkpoint final observado: 2026-10-09T19:22:50Z. Janela desde 19:03:03Z: 19min47s, incluindo leitura, testes, gravações e conferências. Meta de 20min não foi lançada como tempo humano ou duração fictícia. Prefixo original do relatório e 747 blocos anteriores do diário nativo preservados na conferência. APK permaneceu sem alteração; resultados e gates pendentes estão documentados acima.
