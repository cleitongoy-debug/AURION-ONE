# AURION ONE · Atualizações e laboratório · 28/09/2026

## Registro da v6.3

- O aplicativo confere `android/updates/latest.json` ao abrir e na aba Configuração. Quando há `versionCode` maior, baixa o APK por HTTPS, confere SHA-256, package ID, versão e assinatura do APK instalado e entrega a instalação ao Android.
- O Android exige confirmação de instalação e, no primeiro uso, autorização para esta fonte. Não existe instalação silenciosa nem reinício forçado do telefone. Após a confirmação, o Android substitui o app; ao abri-lo, a nova versão entra em funcionamento preservando o banco e as chaves.
- O laboratório escolhe até duas respostas válidas entre rotas configuradas, limita chamadas, registra tentativas/erros e salva respostas no SQLite. Um ciclo inicia ao abrir o app, no máximo uma vez por 24 horas com rede. Respostas geradas são hipóteses até validação física; erro de API não vira descoberta.
- Chat tenta provedores alternativos configurados quando uma rota falha por crédito, modelo ou rede, e por fim responde com a memória offline. O campo Modelo específico não é repassado de OpenAI para Groq/NVIDIA.
- Ditado pelo reconhecedor do Android, leitura por TTS, atalhos de voz locais e tentativa de usar o botão do headset com o app ativo. O roteamento real do botão e microfone depende do Android, da conexão Bluetooth e dos outros apps de mídia.
- Geração de imagem por Hugging Face Inference Providers no telefone com token/cota compatíveis. Arquivo real vai para a galeria. Não há modelo de difusão offline embutido. ChatGPT Plus, Gemini Pro e Adapta em outros aplicativos não concedem automaticamente acesso de API a este APK.

## Publicação de versões futuras

1. Aumentar `versionCode` e `versionName`; atualizar o registro de mudanças nesta documentação e na aba Configuração.
2. Compilar APK no CI. Assinar **fora do repositório público** com a mesma chave privada da v6.3, mantida em arquivo privado do operador no Drive. Nunca publicar keystore, senha, tokens ou credenciais no Git ou dentro do APK.
3. Validar assinatura e SHA-256; publicar o APK assinado em `android/updates/`, depois atualizar `latest.json` com a versão, URL, hash e notas. O manifesto só aponta para uma publicação concluída.
4. O app consulta o manifesto ao abrir; o operador confirma no instalador Android. Não desinstalar para atualizar, pois a desinstalação remove memória e cofre local. Exportar backup antes de mudanças grandes.

A publicação de código no PR rascunho não entrega automaticamente um APK assinado. O fluxo de assinatura e publicação deve ser seguido em cada nova versão. O arquivo `latest.json` é a fonte que o app verifica. Não alterar a identidade `one.aurion.poco.v6` nem a chave de assinatura.

## Evidência pendente

A compilação e a assinatura podem ser verificadas no artefato; instalação, atualização sobre a versão anterior, botão do capacete, cota real das APIs e geração de imagem devem ser testados no POCO. Status visual não substitui resposta real.

## Publicação confirmada da v6.3

- GitHub Actions run `36383209496` compilou o código no commit `5f36ad661750837f3be855a73d5d336c04d28f7a` com sucesso.
- APK final: 2.065.958 bytes; SHA-256 `ba2278ec8855226f8deb6c20d435e412c8caae63508b887cece97a74a62af4d5`. A ferramenta Android confirmou assinatura v2 e v3 com certificado SHA-256 `51dd52d9f49e39e2c045f81fb3b70f2a1dd59807d40edba71cd2ae7ea25c9d43`.
- Binário publicado em `android/updates/AURION-ONE-POCO-v6.3.0.apk` no Git; manifesto com o hash exato publicado em `android/updates/latest.json`. A cópia assinada também foi entregue no Drive.
- A chave privada de assinatura está em arquivo privado no Drive do operador; seu conteúdo não está no Git. Guardá-la é necessário para futuras atualizações compatíveis.
- A v6.2 foi assinada por chave debug distinta. Se o Android impedir instalar a v6.3 por cima, faça backup de memória, desinstale a v6.2 uma vez e instale a v6.3 assinada; a partir dela mantenha o pacote e a chave para atualizar por cima.
