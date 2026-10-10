# AURION EU3 / Maestro 7.1.0

A abertura do perfil ANARK agora usa o painel industrial inspirado nas referências EU3: barra de recursos, navegação lateral, árvore com dependências, inspeção, fila, agentes e chat. As ferramentas anteriores continuam acessíveis. O painel registra fontes, provas, contraprovas e tempo observado; respostas de IA não aprovam pesquisas automaticamente. Os agentes externos começam OFF.

O atualizador usa a publicação `main/android/updates/latest.json`, informa erros HTTP/rede, confere SHA-256, pacote, versão e certificado e só então abre o instalador Android. Há importação de APK local com a mesma verificação de identidade. A permissão de instalar apps é solicitada pelo Android; a instalação exige confirmação do titular. O código mantém o pacote `one.aurion.poco.v6`, o banco SQLite e o cofre existentes. A versão é 73 / 7.1.0.

## Contexto e privacidade

O código e o APK do canal público incluem uma base operacional resumida. Snapshots privados do Drive não entram no Git público. `tools/build_eu3_bootstrap.py --context /caminho/privado/contexto.json` permite preparar o APK pessoal com contexto documental; o snapshot é guardado no perfil local para sobreviver às atualizações públicas seguintes. A chave de assinatura e as senhas ficam fora do repositório e do APK. Documentos e pautas são continuidade de registros, não consciência transferida.

## Verificação

- Compilação `:app:assembleRelease` e lint vital do Android 35.
- Certificado da linhagem original: `51dd52d9f49e39e2c045f81fb3b70f2a1dd59807d40edba71cd2ae7ea25c9d43`.
- Testes de pesquisa: dependências, invalidação, revalidação, backup, restauração, ciclos de 20 minutos e limites do tempo observado.
- Testes de perfis e do contrato de navegação/ponte WebView.
- Navegador Chromium: abertura, estudo, registro de prova, desbloqueio, persistência após reabrir, retorno de Contas à base, consulta local, botões do atualizador e ausência de overflow horizontal em 412 px. Ponte Android simulada neste teste.
- Não houve instalação nem teste físico no POCO nesta sessão.

As contas Google/API e as tomadas PC/USB/Band dependem de configuração e recibo real no aparelho. Uma fonte histórica ou referência localizada não comprova conexão atual.
