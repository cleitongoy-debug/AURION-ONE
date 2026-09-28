# AURION ONE v7 — perfis locais

## Identidades

| Pessoa | Identificador | Acesso inicial neste aparelho |
|---|---|---|
| Cleiton / ANARK | `anark` | Titular e configuração completa |
| Daiane / DS | `ds` | Projeto, criação, agente offline, memória, dedicação, certificados, portfólio e cliente |
| Davi | `davi` | Painel, projeto, foto, vídeo, agente offline e memória |
| Brenda / SPECTRA | `spectra` | Painel e portfólio |

Os percentuais 50%, 20% e 5% expressam a intenção inicial. O titular escolhe abas específicas em **Perfil**, com código individual por aparelho. Os perfis Davi e SPECTRA começam desativados até o titular configurar seus códigos. O primeiro uso deste aparelho pode vincular os registros locais anteriores a ANARK ou DS. Registros de fábrica, referências e sincronização histórica não são transferidos automaticamente à DS.

O banco SQLite v1 recebe a coluna `profile_id` na migração v2, sem recriar tabelas. Operações de leitura, escrita, exclusão e exportação usam o perfil ativo. O cofre antigo permanece reservado ao ANARK; novos segredos têm namespace por perfil. As preferências WebView da DS usam prefixo próprio. O APK bloqueia a interface principal até a autenticação local e expõe aos demais perfis apenas uma lista pequena de ações Android permitidas. Atualização por cima mantém pacote, banco e chave do Android Keystore **somente se o APK for assinado com o mesmo certificado da versão instalada**.

## Limites antes de uma publicação final

- A política de abas é local em cada aparelho. A autorização no painel PC, nas APIs, no Drive e no Git ainda exige identidade e ACL no respectivo servidor. Esconder uma aba não concede nem revoga acesso externo.
- O cliente/agente conectado ao PC não foi liberado aos outros perfis. O chat offline usa somente a memória do perfil. Recursos que exigem ponte Android ou GPU podem ficar indisponíveis para eles até que o servidor aceite identidade própria.
- Migração de preferências do aparelho DS atribui os dados locais desse aparelho à DS após escolha explícita; conteúdo de fábrica do ANARK é omitido. Revise o backup antes de vincular um aparelho com dados misturados.
- O artefato do GitHub Actions é assinado pela chave **debug** do runner e serve para revisão. Não atualiza a v6.5 instalada. O binário instalável por cima exige a chave privada correspondente ao certificado SHA-256 `51dd52d9f49e39e2c045f81fb3b70f2a1dd59807d40edba71cd2ae7ea25c9d43`. Não publique `latest.json` até conferir pacote, versão, hash e certificado do APK final.
- Testes físicos POCO, segundo aparelho DS, PC e Tailscale continuam necessários. Não marque verde sem resultado real.

## Cenários de verificação

1. Atualizar um aparelho de teste mantendo banco e cofre; escolher ANARK e conferir registros antigos.
2. Criar DS; alternar perfis e conferir que cada um lê somente os próprios registros, preferências, progresso e cofre.
3. Retirar uma aba da DS e verificar navegação e ponte Android; sair e reentrar.
4. Repetir com DS como titular dos registros legados em **outro aparelho** e verificar ausência dos registros de fábrica do ANARK.
5. Verificar que falhas de código bloqueiam novas tentativas temporariamente, e que o PC rejeita tokens de perfis sem autorização própria.

Estado da entrega: código em revisão no PR #33; artefato debug não é o canal de atualização.
