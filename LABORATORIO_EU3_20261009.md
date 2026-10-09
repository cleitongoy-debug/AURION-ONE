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


## Pesquisa histórica ampliada — ANARK / Caveiras / núcleo vivo EU3
Registro: 2026-10-09. Escopo: fontes públicas, comunicados, comentários de veteranos, código de ferramentas comunitárias, busca direcionada na conta Gmail disponível e documentos acessíveis do projeto. Este complemento leva descobertas ao protocolo de estudos; não modifica APK nem lança tempo nos contadores humanos.

### Identidade e memória do Capitão
Cleiton declara que ANARK era seu personagem, que figurou entre os top globais e que os Caveiras foram clan top 1 global do seu servidor. Declara também estudo solo, APK e avisos no celular naquela época. Preservar como história pessoal fornecida pelo próprio participante. Não atribuir técnicas de outros clãs a ele. Buscas públicas por ANARK, variantes do nome, Caveira/Caveiras e EU3 não localizaram ranking identificável nesta rodada. Isso não refuta o relato. Ainda faltam identificação do reino/temporada, ranking datado, print ou mensagem original para vincular as conquistas à documentação histórica.

### Linha histórica e estado dos servidores
- **Dezembro de 2012:** comunicado Looki arquivado pela AFJV anuncia beta fechada; edição publicada em 20/12. Fonte: [anúncio da beta](https://jeuvideo.afjv.com/news/6931_empire_universe_3.htm).
- **Maio de 2013:** comunicado de abertura prevê reset na noite 28–29 e compensação de Ikolium; apresenta mudanças de personagens e comandantes. Fonte: [comunicado arquivado](https://jeuvideo.afjv.com/news/7705_empire_universe_3.htm). Não confundir beta, abertura regional e datas de catálogos.
- **Dezembro de 2015:** Gamigo anuncia Infinity multilíngue, combate terrestre revisado, mais de 100 equipamentos e ajuste dos tempos de pesquisa/construção. Fonte: [Infinity](https://corporate.gamigo.com/en/presse/empire-universe-3-world-server-launched-with-new-features/).
- **Janeiro de 2016:** Gamigo anuncia Meridian com inglês, espanhol e português brasileiro. Fonte: [Meridian](https://corporate.gamigo.com/en/presse/new-servers-and-languages-for-empire-universe-3-and-desert-operations/).
- **Maio de 2016:** atualização oficial apresenta Save Mode, missões e outras melhorias. Fonte: [atualização](https://corporate.gamigo.com/en/presse/empire-universe-3-fire-at-will-in-the-new-content-update/). Logo, lembrança em fórum de encerramento geral em 2015 contradiz comunicados posteriores.
- **Encerramento:** [F2PG](https://www.f2pg.com/empire-universe-3/) cataloga o jogo como terminado; o autor do [Ikopit](https://github.com/mgemard/ikopit) também descreve EU3 como encerrado. Data oficial de fechamento e destino das bases de contas não encontrados. Falha de acesso aos antigos domínios, wiki, fórum Looki e tentativa no Wayback não comprova sozinha a extinção de cada servidor.
- **Reconstrução comunitária EU4:** o desenvolvedor declara reconstrução própria, do zero; não é evidência de continuidade do banco de contas antigo. [Apresentação e discussão](https://www.reddit.com/r/4Xgaming/comments/1mnlwku/empire_universe_4_alpha_3/). Comentário em agosto de 2026 anuncia Alpha 5: [discussão de lançamento](https://www.reddit.com/r/4Xgaming/comments/1ilpjoz/empire_universe_4_the_alpha_is_live_join_the/). Hoje o endereço [Empire Universe](https://www.empire-universe.com/) responde com login. Não houve autenticação nem verificação de partida, população, migração ou reutilização das credenciais antigas.
- **Outra reconstrução citada:** comunidade aponta [Universe Dawn](https://www.reddit.com/r/4Xgaming/comments/1d8x0zb/empire_universe_123_remake/); endereço universe-dawn.com não pôde ser carregado nesta rodada. Operação atual e relação com dados antigos permanecem desconhecidas.

Esses marcos documentam evolução e expansão. Não medem o “auge” por população, nem comprovam a posição histórica de qualquer clã.

### Tutoriais, comentários e pistas internas
Localizado [Gameplay 1 no YouTube](https://www.youtube.com/watch?v=ejF3hGqOLFg). Apenas identificação e metadados recuperados; não se declara vídeo integral assistido, transcrição analisada ou técnica extraída dele. Páginas com players incorporados não forneceram conteúdo audiovisual legível nesta pesquisa. Excluir resultados de Empire Earth, Endless Space, Stellaris e outros jogos homônimos.

Em [discussão de veteranos](https://www.reddit.com/r/4Xgaming/comments/1f6jzkz/empire_universe_4/), participante que se identifica como Neuromanc312 relata coordenação entre fusos, proteção noturna das frotas e mapa comunitário de wormholes atualizado semanalmente. É memória desse participante, não regra universal confirmada do motor nem experiência atribuível a ANARK. Uso AURION: sincronizar relógios, versionar mapas de capacidades e salvar estado antes de afastamento.

Busca Gmail direcionada por assunto Empire Universe e remetentes Looki/Empire Universe: zero mensagens pertinentes na conta conectada disponível. Busca mais ampla trouxe resultado sem relação demonstrada com o jogo. Não houve leitura de todas as caixas, acesso a contas adicionais, envio de e-mail ou recuperação de contas.

Documento privado do projeto NOVO#REGISTRO#ANARK contém referências repetidas ao nome EU3Installer-W3.20.21.0.exe. O nome sozinho não distingue jogo, versão, origem ou integridade; o binário não foi obtido nem executado. Evitar publicar caminhos locais privados e qualquer credencial. Registro existente pode ser investigado por hash, assinatura e metadados se o arquivo aparecer.

### Fórmulas recuperadas do Ikopit e adaptação proposta
Fonte fixa: commit 936e7d8c52ffe67f4a2ac080867db94879f07d54, ferramenta comunitária não oficial. Nenhuma destas fórmulas certifica o motor servidor.

1. **Rotas:** coordenadas x=ceil(n/100), y=n mod 100, com resto zero convertido em 100. Distância direta d=sqrt((x2-x1)^2+(y2-y1)^2). A busca compara trechos e wormholes até limite de saltos; não é implementação de Dijkstra nem converte distância em ETA real. Há typo routesTmp.lenght, que impede a limpeza pretendida. [Código de rotas](https://github.com/mgemard/ikopit/blob/936e7d8c52ffe67f4a2ac080867db94879f07d54/war/WEB-INF/route-planner.jsp).
   **AURION:** escolher caminho de tarefas por custo observado (tempo, tokens, energia), capacidades verificadas e orçamento; registrar validade temporal de cada atalho. Pesos exigem unidades e critérios explícitos. Modelo sem saldo não equivale a rota disponível.

2. **Triangulação:** enumera grade 100×100 e aceita pontos cuja distância arredondada coincide com três medições. Conjunto S={p: round(||p-a_i||)=r_i, i=1..3}. Para r positivo, distância pertence à faixa [r-0,5;r+0,5), não a uma circunferência exata. Podem existir zero, um ou vários candidatos. [Código de localização](https://github.com/mgemard/ikopit/blob/936e7d8c52ffe67f4a2ac080867db94879f07d54/war/WEB-INF/planet-finder.jsp).
   **AURION:** cruzar evidências independentes e conservar alternativas quando dados não distinguem hipóteses. Analogia metodológica, não soma numérica da “confiança” de três IAs. Cópias da mesma fonte não são três provas.

3. **Relatórios de combate:** taxa de acerto deriva de acertos/tentativas; dano médio do código usa tentativas como denominador. Agregação deve somar numeradores e denominadores, em vez de fazer média simples das porcentagens. Denominador zero é indefinido. O analisador lê resultados; não demonstra simulação completa do combate. [Analisador](https://github.com/mgemard/ikopit/blob/936e7d8c52ffe67f4a2ac080867db94879f07d54/dev/jsx/battle_analyser.jsx).
   **AURION:** sucesso=saídas que passam o critério/execuções elegíveis, com erro, latência e custo próprios. HTTP 200 ou resposta fluente não validam descoberta.

4. **Composição modular:** componentes somam propriedades multiplicadas pelas quantidades; velocidade tem regra específica de multiplicação ou soma conforme configuração. [Construtor](https://github.com/mgemard/ikopit/blob/936e7d8c52ffe67f4a2ac080867db94879f07d54/war/inc/ship_build.js).
   **AURION:** composição de agentes respeita soma de recursos dentro da capacidade. Não presumir que qualidade, velocidade e confiabilidade cresçam linearmente com o número de agentes.

5. **Pesquisa e dependências:** calculador usa faixas discretas de progresso para estimar duração; árvores tecnológicas representam pré-requisitos. [Tempo de pesquisa](https://github.com/mgemard/ikopit/blob/936e7d8c52ffe67f4a2ac080867db94879f07d54/war/WEB-INF/research-time.jsp) e árvore Graphviz no repositório.
   **AURION:** separar estimativa, tempo observado e conteúdo concluído. Evidências de progresso não provam segundos de dedicação. Mudança de premissa invalida dependentes atuais, preservando seus recibos históricos.

### Protocolo de estudos #AURION#EU3 — aplicação concreta
Fluxo documental: fonte/versionamento → hipótese → critério verificável → pré-requisitos → orçamento → execução → recibo → contraprova → revalidação dos dependentes → checkpoint e retomada.

- Cada fonte guarda autor, origem, período, versão e conteúdo realmente lido. Indicar trecho indisponível; não dizer “aprendido tudo” só por indexar links.
- Cada experiência guarda operationId estável, attemptId por tentativa, hipótese, entradas, versão de fonte/modelo, ambiente, limite de custo/tempo, saída, erro e decisão.
- Contraprova marca dependentes como revisão pendente; não apaga a descoberta anterior e não mantém etiqueta “validado” junto de ready=false.
- Rotas alternativas só entram após teste real de capacidade/modelo; sem saldo ou rate limit provoca classificação do erro e tentativa limitada de outra rota elegível. Não prometer continuidade infinita.
- Sono, espera, background e parada de agentes exigem checkpoint verificável. Retomada não repete operação concluída e não conta ausência como estudo humano.
- Na moto, áudio exige evidência de reprodução, pausa, buffering e posição; comandos e resposta falada dependem de QA físico do headset. Nenhuma atuação no capacete foi comprovada nesta pesquisa.
- Horas pessoais: intervalos observados com atividade pertinente; duração de conteúdo e horas certificadas em campos separados. Não multiplicar porcentagem por carga horária para fabricar segundos já estudados.
- Memória de ANARK/Caveiras é uma trilha própria, com relatos preservados e espaço para ranking, e-mail, print e documentos originais. Isso integra a raiz histórica do método, sem substituir prova por ficção.

### Pendências identificadas
Restam: nome/época do servidor dos Caveiras; evidência histórica dos rankings; anúncio oficial de encerramento; conteúdo de fóruns e wiki inacessíveis; transcrições dos vídeos; identidade do instalador; acesso autenticado a uma plataforma ainda operante e prova de continuidade de dados. Alterações de aplicativo, automação e testes físicos não realizados nesta extensão documental.


## Pauta 2 — retomada pelo sinal >, atualizações e resolução de problemas
Registro de continuidade: 2026-10-09, solicitação às 17:01:51 em America/Sao_Paulo. Cleiton está na rua e prevê chegar a partir das 18h; isso é previsão, não comprovação de chegada, conexão ou estudo. Cada mensagem > significa retomar o próximo trabalho pendente nesta conversa. Não significa execução permanente entre mensagens, monitoramento do telefone ou tarefa agendada às 18h.

### Sequência recuperada
1. Primeiro núcleo >: estudo em deslocamento, bate/rebate, sleep/step/tempo real, referências no Git/Drive e origem EU3 da automação AURION.
2. Pesquisa ampliada: história, tutoriais, comentários, fórmulas comunitárias, situação dos servidores e memória ANARK/Caveiras. Extensão histórica anterior preservada neste relatório.
3. Pauta 2 atual: cruzar descobertas e problemas reais, especificar resoluções e seus critérios; manter assuntos, evidências e tempos em registros distintos. Continuidade usa o checkpoint atual, sem apagar fontes ou reiniciar contadores.

### Ordem de resolução e critérios concretos
| Ordem | Problema observado | Resolução proposta | Prova exigida antes de chamar resolvido |
|---|---|---|---|
| 1 | Contraprova em A bloqueia B/C, mas mantém rótulo VALIDADO | Marcar dependentes transitivos REVISAO_PENDENTE; guardar recibos originais e causa de invalidação; pausar dependente ativo | A→B→C aprovados; reprovar A; B/C bloqueados e com rótulo coerente; reaprovar A não revalida B/C automaticamente |
| 2 | EU3 exporta JSON sem caminho de restauração | Importação com versão/perfil, validação e commit atômico; IDs e recibos preservados; rejeitar ciclos, referências inexistentes e números inválidos | Exportar→restaurar em estado novo; conteúdo/tempos/recibos equivalentes; JSON inválido não muda nada |
| 3 | Backup geral exclui dedicação, memória documental e EU3 | Manifesto por domínio, perfil, versão, hash e quantidade; cópia segura antes da substituição | Restaurar todos os domínios em perfil compatível; falha mantém estado anterior; eventos de datas diferentes não se fundem por título igual |
| 4 | Resultado geral de conexão pode ocultar falhas parciais | Recibo separado de cada rota e resultado final após sincronização; distinguir metadados de conteúdo lido | Uma rota aprovada e outra falha aparecem separadas; Drive metadata-only não aparece como conteúdo aprendido |
| 5 | Contador geral aceita salto sem observação | Relógio monotônico para duração; horário civil apenas para data; heartbeat/atividade; lacunas separadas e preservação dos totais históricos | Gap, background, alteração do relógio, reboot e duas sessões concorrentes não fabricam segundos; recibo informa exclusões |
| 6 | Voz do capacete perde sessão fora do primeiro plano e dispatcher é sobrescrito | Unificar despacho de atalhos/voz e ciclo de vida; registrar entrada, decisão, ação e resposta falada | QA físico em casa: botão, microfone, tela apagada, interrupção e reconexão; execução única e retorno audível |
| 7 | Laboratório A/B recebe respostas, sem provar descoberta EU3 | Critério antes do teste, fonte fixa, orçamento, tentativa identificada e contraprova independente | Repetição comparável; erro preservado; nenhuma promoção por HTTP 200, fluência ou voto de modelos |
| 8 | Canal de atualização da prévia difere do principal | Manifesto compatível com pacote/assinatura/versão; backup e migração verificados; changelog por release | Atualização sobre instalação de teste preserva dados e retoma corretamente; aprovação do Android não tratada como instalação silenciosa |

Situação desta pauta: resoluções especificadas e documentação atualizada. Nenhum item foi promovido a correção implementada por este texto. APK/código permanecem preservados nesta fase de estudo e auditoria.

### Assuntos e tempos — contrato para PC e POCO
Cada sessão futura precisa de sessionId, deviceId, assunto, curso/conteúdo, projeto, tipo de atividade, horário de início/fim com fuso, intervalos observados, pausas/lacunas e referência da evidência. operationId identifica a ação e attemptId cada tentativa. Sincronização deve ser idempotente por ID; mesmo texto em outra data não é duplicata automática.

Assuntos já trabalhados nesta sequência: história EU3 e ANARK/Caveiras; dependências de pesquisa; rotas/wormholes; triangulação; composição modular; taxas e denominadores; contraprova; backup/restauração; sincronização e falhas parciais; dedicação e áudio; voz do capacete; atualização e retomada. Estes são assuntos desta pesquisa, não certificação de domínio nem prova de horas pessoais.

Tempo total humano confirmado = medida da união dos intervalos confirmados entre dispositivos. Sobreposição PC/POCO conta uma vez no total global. Por assunto, intervalos recebem marcações; categorias sobrepostas não devem ser somadas cegamente ao global. Espera de IA, download, sleep, buffering e cronômetro sem atividade não comprovam atenção humana.

Exemplo didático, sem lançamento real: intervalo PC 10:00–10:20 e POCO 10:10–10:30 somam 30 minutos únicos, e não 40. O número é apenas teste de definição. Áudio: separar tempo real reproduzido de posição/duração de conteúdo; avanço manual não soma estudo. Porcentagem de curso, carga horária e certificado conservam valores próprios e fonte; não viram segundos exatos por inferência.

Na falta de dados históricos, marcar desconhecido/relatado. Receber prints e certificados com fonte e data observável; não transformar sua pesquisa atual em reconstrução fictícia do ano inteiro. Não houve lançamento de 20 minutos, de 10+5 minutos ou de tempo até as 18h nesta pauta.

### Checkpoint para o próximo >
Próximo estudo documental: contrato de restauração completa e invalidação transitiva, com casos de falha/reversão; depois recibos de conexão, contador e voz. Preservar LUZ pausada. Ao chegar em casa, conexão PC↔POCO e voz só passam a comprovadas após evidência dos dispositivos. Fontes encontradas e conclusões anteriores permanecem; repetir verificação apenas diante de alteração, falha ou lacuna nova.


## Pauta 2 — checkpoint: restauração e contraprova transitiva
Data: 2026-10-09. Retomada solicitada por > às 17:12:33 America/Sao_Paulo. Estudo/auditoria documental; nenhum código de produção ou APK alterado. Nenhum tempo humano lançado.

### Novas falhas identificadas
Fontes atuais conferidas na branch: [AurionStore.java](https://github.com/cleitongoy-debug/AURION-ONE/blob/feature/laboratorio-eu3-20261009/android/app/src/main/java/one/aurion/app/AurionStore.java), blob e2164c0ad4975c35617586fbd4a6a25788c9342d; [research_eu3.js](https://github.com/cleitongoy-debug/AURION-ONE/blob/feature/laboratorio-eu3-20261009/android/app/src/main/assets/research_eu3.js), blob 3679012e859a2709d73d80fd3c0ee5ef0ead01b8.

**Dependente ativo continua contando após contraprova.** Teste sintético no módulo auditado: validar A→B→C, iniciar D dependente de C em t=100, reprovar A e executar tick em t=1100. Resultado: A EXPERIMENTAL; B/C VALIDADO com ready=false; D EM_ESTUDO com ready=false, milliseconds=1000 e active ainda presente. Portanto, bloqueio calculado não pausa a sessão ativa nem corrige os rótulos. Ao reabrir o motor, active=null e os dois recibos de A permanecem. A reprodução é de lógica JavaScript, não teste no aparelho.

**Perfil aninhado não é conferido junto dos registros.** importAll aceita root.memory.records, mas sourceProfile vem de root.profile. Exemplo sintético {memory:{profile:"outro",records:[...]}} não tem perfil na raiz e não aciona a rejeição por diferença. Confirmado pelo fluxo do código e pela extração do campo no exemplo; nenhuma restauração real SQLite foi executada.

**Identidade por conteúdo perde distinção temporal.** recordFingerprint usa type/title/body/meta, omitindo createdAt/updatedAt e identificador de origem. Duas ocorrências com conteúdo igual em datas diferentes podem ser tratadas como duplicatas. O import também cria novos IDs locais; não preserva automaticamente a identidade exportada. Ausência de timestamps recebe o horário atual, que precisa ser marcado como horário de importação, não inventado como acontecimento histórico.

### Contrato de restauração proposto
1. Identificar o envelope primeiro: direto ou memory aninhado. Perfil, formato, contagem e registros devem ser lidos do mesmo envelope. Perfil ausente/desconhecido exige classificação de legado; não inferir silenciosamente perfil atual.
2. Validar antes de gravar: estrutura, versão, perfil, IDs, tipos, timestamps conhecidos, números finitos não negativos, integridade e dependências. Ciclo/referência desconhecida bloqueia importação EU3; manter arquivo de origem para diagnóstico.
3. Preparar snapshot e staging dos domínios: memória nativa, interface, dedicação, memória documental e pesquisas EU3. Credenciais não entram como texto em backup; disponibilidade/necessidade de reconfiguração recebe campo próprio.
4. Não chamar transação SQLite de transação global: SQLite e localStorage são destinos distintos. Propor geração de snapshot com journal de recuperação; todos os domínios validam antes de promover a geração, com rollback após interrupção.
5. Identidade: chave de origem/perfil/ID estável; repetição da mesma exportação é idempotente. Ocorrências iguais de dias diferentes são conservadas. Mesmo ID com versões divergentes exige regra explícita e recibo de conflito, não substituição oculta.
6. Datas desconhecidas continuam desconhecidas; importedAt separado de occurredAt. Não fabricar horas estudadas para preencher campos.
7. Retomar sempre pausado até atividade confirmada. Importação não inicia cronômetro, ação remota ou experiência automaticamente.
8. Recibo final inclui operationId, perfil, versões, domínios, recebidos/importados/duplicatas/conflitos, hashes e resultado de cada etapa. Só declarar restaurado após readback coerente de todos os domínios incluídos.

### Contrato de invalidação proposto
Contraprova registra novo recibo em A; calcula conjunto de dependentes transitivos com detecção de ciclos; pausa sessão ativa afetada no mesmo evento; marca dependentes REVISAO_PENDENTE e guarda causa/revisão de origem. Provas históricas, assuntos e tempos legítimos anteriores permanecem.

Depois de invalidar A, reaprovar A não reaprova B/C/D automaticamente. Cada dependente precisa de nova avaliação contra a versão atual de suas premissas. O seletor de pré-requisitos precisa excluir rótulos antigos que não estejam prontos. A pausa automática deve registrar motivo sem cobrar tempo posterior à invalidação. Trecho anterior até o evento só conta se observado, pertinente e dentro do limite de heartbeat.

### Casos de aceitação preparados, ainda sem implementação
| Caso | Resultado exigido |
|---|---|
| Perfil direto diferente e perfil memory aninhado diferente | Ambos rejeitados sem mutação |
| JSON inválido, versão desconhecida, ciclo ou referência inexistente | Falha explícita; estado anterior íntegro |
| Mesma exportação aplicada duas vezes | Segunda execução não duplica; recibos das duas tentativas |
| Mesmo texto em duas datas | Duas ocorrências preservadas |
| Mesmo ID e conteúdo divergente | Conflito rastreável; nenhuma perda silenciosa |
| Falha após gravar um domínio / reboot durante promoção | Recuperação para geração consistente, sem metade do backup |
| A→B→C→D com D ativo e contraprova de A | Dependentes em revisão e sessão de D pausada; zero tempo posterior |
| Reaprovação de A | B/C/D continuam pendentes até revalidação |
| Exportar/restaurar EU3 | Fontes, IDs, dependências, tempos e recibos equivalentes; nenhuma sessão ativa |
| Exportação acima de 500 memórias | Contagem integral no backup, sem confundir limite da listagem |

### Próximo ponto de retomada
Recibos por conexão e aprendizado real: identificar o resultado final de Drive/Git/PC/API, separar metadados de conteúdo lido e impedir status verde geral de ocultar falha parcial. Depois, contador e voz do capacete. LUZ permanece pausada. Situação atual: novas falhas reproduzidas ou verificadas por leitura, contratos escritos; correções não implementadas.


## Pauta 2 — comando >: conexões, recibos e conteúdo realmente lido
Registro: 2026-10-09, retomada solicitada às 17:15:04 America/Sao_Paulo. > é comando de estudo nesta conversa. Esta rodada executa leitura/auditoria e consolidação documental; não faz lançamento de dedicação humana nem altera APK.

### Código conferido e novas conclusões
Fontes na branch feature/laboratorio-eu3-20261009:
- [AurionHourlyWorker.java](https://github.com/cleitongoy-debug/AURION-ONE/blob/feature/laboratorio-eu3-20261009/android/app/src/main/java/one/aurion/app/AurionHourlyWorker.java), blob 050a2c60ba1238642032363fa7025b143cb4c044.
- [AurionPcMemorySync.java](https://github.com/cleitongoy-debug/AURION-ONE/blob/feature/laboratorio-eu3-20261009/android/app/src/main/java/one/aurion/app/AurionPcMemorySync.java), blob 966fb3ab089480599ed1e24e9b8b32c80000ccfb.

1. Worker usa ok acumulado: sucesso de uma consulta ao manifesto/Git basta para Result.success(), mesmo se Drive/PC falharem. “Ciclo concluído” significa que alguma rota respondeu, não todas as conexões corretas.
2. sync_event é salvo antes de executar pcMemorySync. O resultado posterior vai para r enviado à Band, mas não para o JSON já persistido em sync_event. Diário e resumo podem representar fases diferentes do mesmo ciclo.
3. Drive consulta uma página de metadados por rodada; contentRead=false explícito e permissionState não verificado pela consulta. driveComplete significa ausência de nextPageToken nessa página; não comprova leitura integral do Drive, snapshot imutável ou conhecimento aprendido.
4. Consulta Git lê HEAD; detectar SHA novo não lê arquivos alterados. Hugging Face whoami e lista de modelos detectam identidade/metadados; não comprovam geração de imagem, download ou inferência.
5. PC snapshot online não equivale a transferência de memória. Memory-sync separado exige loopback via ADB, token, POST, importação e GET de conferência.
6. Memory-sync monta payload e backup com profile="anark" fixo, enquanto exportAll exporta perfil atual. Para perfil diferente, pode enviar registros com rótulo de origem incorreto antes de importAll rejeitar retorno. Correção proposta: carregar e validar perfil de origem e destino antes de POST; preservar escopo real.
7. Readback compara contagens, não hashes/IDs/conteúdo. Duas coleções diferentes do mesmo tamanho podem satisfazer igualdade numérica. O recibo exige escopo mais restrito: contagens confirmadas não significam equivalência integral.
8. Tipos filtrados e limites de tamanho excluem material: relatório já inclui excludedLocal. Portanto, memória sincronizada não pode ser apresentada como todas as dependências do projeto. Credenciais continuam fora do conteúdo público.

Conclusões por leitura do código; nenhuma chamada a PC/POCO/Band executada nesta sessão.

### Contrato proposto de estados por operação
| Estado | Evidência mínima | Não equivale a |
|---|---|---|
| CONFIGURADO | Campo/configuração existente | Credencial válida |
| AUTENTICADO | Resposta pertinente à identidade/escopo | Geração ou acesso a todos os recursos |
| LOCALIZADO | ID e metadados do recurso | Conteúdo baixado |
| CONTEUDO_OBTIDO | Bytes/exportação recebidos com origem e hash | Texto decodificado integralmente |
| DECODIFICADO | Extração com páginas/trechos cobertos e lacunas | Conhecimento assimilado |
| ESTUDADO | Trecho efetivamente analisado, assunto, síntese e limites | Técnica validada |
| VALIDADO | Critério definido e prova reproduzível pertinente | Validação eterna após mudança da premissa |
| SINCRONIZADO_NO_ESCOPO | Recibos dos lados, perfil, IDs/versões/hashes equivalentes no conjunto definido | Backup completo de tudo |

Conexão é resultado por operação e instante: authenticatedAt, checkedAt, endpoint/escopo, erro, latência, operationId e attemptId. Sucesso antigo fica como lastSuccessAt; estado atual requer consulta atual. Expiração deve ser específica ao tipo de prova, sem inventar um prazo universal.

### Resolução proposta para recibos
Acumular resultados de todas as etapas; persistir recibo final depois de pcMemorySync e demais ações, preservando também falhas e tentativas. Separar execução do agendador de integridade de cada rota. Uma etapa opcional desativada é NAO_SOLICITADA; credencial ausente é AGUARDA_CONFIGURACAO; falha é FALHOU; não há promoção global de verde por uma única resposta.

Validação de memória: comparar conjunto de IDs de origem, perfil, revisão e hashes dos registros normalizados. Contagem serve como verificação adicional. Readback divergente produz erro e recibo de possível aplicação parcial; nova tentativa usa identidade estável para não duplicar. Definir primeiro política de conflitos/rollback conforme checkpoint anterior.

### Casos preparados
- Git responde e Drive falha: Git sucesso, Drive falha, ciclo parcial explícito.
- Consulta Drive lista 100 arquivos: 100 metadados localizados, zero arquivos estudados nessa consulta.
- PC snapshot responde, memory-sync falha: PC acessível na consulta; memória não confirmada.
- Duas coleções distintas com mesma contagem: sincronização rejeitada pela diferença de IDs/hashes.
- Perfil ativo diferente de anark: bloquear rótulo indevido antes do envio.
- Resultado pcMemorySync chega após etapa inicial: recibo final persistido contém o resultado verdadeiro.
- Credencial expira depois de sucesso antigo: manter histórico; mostrar falha atual.
- Fonte muda após estudo: conservar síntese anterior com versão, marcar reanálise pendente.

### Checkpoint seguinte
Próximo comando >: contador de estudo/áudio, intervalos entre PC e POCO, lacunas e relógios. Depois, voz e botão do capacete. Situação: auditoria e propostas documentadas; sem implementação, geração de APK ou teste físico.


## Pauta 2 — comando >: contadores, áudio e segundos comprováveis
Registro: 2026-10-09; comando recebido às 17:16:51 America/Sao_Paulo. Rodada de estudo/auditoria, sem alterações no aplicativo e sem lançamento de horas pessoais.

### Fontes atuais e resultados
[POCO dedication.js](https://github.com/cleitongoy-debug/AURION-ONE/blob/feature/laboratorio-eu3-20261009/android/app/src/main/assets/dedication.js), blob 178366abb43b2ac53ebd2982d7afb4ab0d27e69f.
[PC dedication.js](https://github.com/cleitongoy-debug/AURION-ONE/blob/feature/laboratorio-eu3-20261009/pc-package-v3/aurion_superstudio/static/dedication.js), blob 7367acd5da069b512a1b57317d3022be8149099d.
[MainActivity.java](https://github.com/cleitongoy-debug/AURION-ONE/blob/feature/laboratorio-eu3-20261009/android/app/src/main/java/one/aurion/app/MainActivity.java), blob e674db0cb4369018c67ff0d9728b09a8016c378e.

- **Acerto preservado:** dedUnion/cleanIntervals já unem intervalos sobrepostos. Teste sintético na função dedUnion: [0,1200000] e [600000,1800000] produzem 1800000ms (30min), não 40min. Não reimplementar o que já funciona.
- **Lacuna:** ambos os timers usam Date.now e atualizam last em cada callback; duração é last-start. Gap entre callbacks entra no intervalo. Revisão do PC confirma o mesmo padrão previamente reproduzido no POCO. Horário civil alterado pode distorcer duração.
- **Conflito oculto:** dedMerged usa Map de IDs com eventos remotos antes dos locais; evento local vence sem conferir equivalência. Teste real da função: mesmo ID remoto com end=2000 e local com end=1000 resulta somente na versão local de 1000. Identidade igual não comprova conteúdo igual.
- **Porcentagem vazia no PC:** pcProgress aplica Number ao campo sem rejeitar string vazia; Number('')=0, logo curso preenchido e porcentagem vazia podem gerar 0%. POCO já verifica campo vazio. Desconhecido não deve ser convertido em zero observado.
- **Certificados:** painel POCO consulta getMemories com limite 500; AurionStore.list também limita a 500. Contagem e soma desse recorte não comprovam acervo integral. Hash identifica arquivo idêntico, não equivalência entre dois certificados exportados em formatos diferentes. Horas declaradas continuam separadas de segundos medidos.
- **Áudio e tela apagada:** o timer de dedicação para ao ocultar o painel; não é contador de reprodução de mídia. TTS existe, mas nos arquivos analisados não há ligação de callbacks/posição de reprodução a sessões de dedicação. Falar uma resposta não demonstra que ela foi ouvida ou estudada. Cobertura desta conclusão restrita aos arquivos examinados.
- **Tempo ativo no painel PC:** renderPcLedger calcula total sobre pcEvents; sessão ativa aparece em texto próprio, sem integrar total global ao vivo como no POCO. Pode produzir aparência divergente durante a sessão, embora após gravação o intervalo passe a integrar o diário.
- **Histórico importado:** existem sementes de porcentagem observada com observedDate separado de at. Preservar essa distinção e as fontes originais; não usar data de importação como data exata do estudo nem inferir duração da porcentagem.

Não houve teste físico de reprodução, microfone, PC/POCO ou relógio do aparelho.

### Resoluções propostas e provas
1. **Medição:** duração por relógio monotônico e intervalos observados; horário UTC/fuso para posicionar eventos. Cada lacuna guarda início/fim, razão e incerteza. Não contabilizar lacuna apenas porque a janela continuava aberta; visibilidade sozinha também não comprova atenção.
2. **Histórico:** conservar bruto original e marcar versão/base de cálculo. Novo total comprovado não apaga o total legado. Mudança de método recebe recibo e explicação; não corrigir retroativamente anos de dedicação sem fonte.
3. **Sincronização:** por ID, revisar/hash do payload e recibo. Mesmo ID + mesmo conteúdo é repetição; mesmo ID + conteúdo diferente é conflito com as duas versões preservadas. Não escolher local silenciosamente.
4. **Campos:** porcentagem vazia permanece desconhecida; exigir evidência para “observada”. completed não mede tempo; horas de certificado não somam ao cronômetro.
5. **Categorias:** total global por união; categorias/assuntos podem sobrepor. Exibir essa sobreposição, sem apresentar soma das categorias como total global quando coincidem.
6. **Áudio:** registrar recurso/versão, play/pause/end/buffering/error, velocidade, posição e relógio monotônico. Pausas, seek e buffering não contam como reprodução. A 2x, 10min reais podem abranger 20min de conteúdo: campos distintos, exemplo didático sem lançamento real. Reprodução é evidência de entrega, não compreensão; estudo por áudio deve ter base explicitada.
7. **Background:** dados de reprodução exigem caminho nativo/lifecycle que sobreviva à tela apagada quando suportado. Antes de implementação, preservar cronômetro atual e não prometer medição em background.
8. **Certificados:** contagem paginada integral com escopo, originais, hashes e horas declaradas; tratar sobreposição/duplicidade de curso separadamente de duplicata binária.
9. **Painéis:** alinhar “total fechado”, “sessão atual observada”, “lacunas” e “horas declaradas” em PC/POCO. Desconhecido não vira zero; dado antigo não vira tempo real.

Casos de aceitação preparados: salto para frente/para trás no relógio; gap de callback; background/reboot; duas sessões sobrepostas; mesmo ID conflitante; porcentagem vazia; 501 certificados; áudio pausado/buffering/seek/2x; perda de conexão e retomada sem duplicação. Testes de produção dessas resoluções ainda pendentes.

### Checkpoint seguinte
Próximo comando >: voz, atalhos e botão do fone/capacete — rastrear entrada, despacho, ação e resposta falada; preparar critérios de interrupção e tela apagada. LUZ pausada. Esta etapa deixa novos achados e resoluções documentados, não implementados.
