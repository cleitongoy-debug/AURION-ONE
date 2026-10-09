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
