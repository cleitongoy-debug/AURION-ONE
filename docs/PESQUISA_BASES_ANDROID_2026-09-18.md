# AURION ONE — pesquisa de bases Android (18/09/2026)

Objetivo do operador: um APK clicável no POCO, permissões solicitadas pelo Android, conexões autorizadas, atualizações e continuidade no Git. Esta pesquisa NÃO constitui APK compilado, instalação ou autenticação de contas.

## Projetos públicos para estudar (não copiar sem conferir licença)

- Agora (MIT): https://github.com/newo-ether/Agora — Android Kotlin/Compose, múltiplos provedores BYOK, MCP, agentes, modelos locais, controle remoto; ver limitações de armazenamento de segredos e build SDK 36/JDK 21.
- RikkaHub (AGPL-3.0): https://github.com/rikkahub/rikkahub — Android, múltiplos provedores, MCP, agentes, multimodal. Licença copyleft exige análise antes de incorporar código; build informa necessidade de google-services.json.
- GPT Mobile: https://github.com/Taewan-P/gpt_mobile — Android Kotlin/Compose, OpenAI/Gemini/Ollama, ferramentas opcionais, credenciais no Android Keystore.
- Conduit: https://github.com/mehmetbaykar/conduit-openwebui — cliente móvel para Open WebUI com login no servidor, ferramentas e imagens, depende de backend Open WebUI próprio.
- AndroMate: https://github.com/Anon4You/AndroMate — assistente no Termux, útil como referência técnica mas NÃO atende ao requisito sem Termux.
- Hugging Face: pesquisar SDKs e modelos específicos somente após definir execução local/remota, memória disponível e licença; nenhum Space foi verificado como substituto de APK/contas pagas.

## Dependências e fluxo de entrega

1. Preservar V2 e Bíblia; ler os arquivos completos antes de alterar a arquitetura.
2. Adicionar projeto Android compilável e Gradle Wrapper versionado; baixar SDK/Gradle no GitHub Actions, não inserir SDK, cache ou segredos no Git.
3. Workflow de build acionado manualmente ou por alterações em android/app, com upload do APK de teste como artifact. Verificar assinatura, testes e permissões antes de distribuir; artifact NÃO equivale a APK pronto até workflow concluir.
4. Integrações por OAuth oficial/API quando disponíveis, retorno por deep link, armazenamento seguro; assinaturas de apps não são credenciais de API.
5. Atualizações de conteúdo podem vir do Git após validação; instalação de novo APK exige confirmação do Android. Não executar código remoto arbitrário nem instalar silenciosamente.
6. PC desligado: status desconhecido, não declarar conectado. Mi Fitness/Mi Band: capacidades ainda não verificadas.
7. Nunca armazenar senhas, chaves, tokens, arquivos privados ou dados de celular no repositório público.

## Estado verificável

Pesquisa de projetos públicos realizada; documento criado no GitHub. Nenhuma dependência instalada no POCO por esta ação, nenhum APK compilado e nenhum login integrado comprovado.
