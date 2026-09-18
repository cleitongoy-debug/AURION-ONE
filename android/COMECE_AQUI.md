# AURION ONE Android — COMECE AQUI

> Estado em 18/09/2026: **APK ainda não compilado nem publicado. Não existe link de instalação válido.** Este documento é a entrada única e será atualizado no mesmo endereço. Não baixe HTMLs como se fossem APKs.

## Links permanentes

- [Esta página — instalação e progresso](https://github.com/cleitongoy-debug/AURION-ONE/blob/main/android/COMECE_AQUI.md)
- [Releases — futuro APK assinado e verificado](https://github.com/cleitongoy-debug/AURION-ONE/releases) — **sem APK confirmado nesta data**. Só instalar quando houver release com APK, versão, SHA-256 e testes registrados.
- [Código do projeto](https://github.com/cleitongoy-debug/AURION-ONE)
- [Arquitetura Android](https://github.com/cleitongoy-debug/AURION-ONE/blob/main/docs/AURION_ONE_ANDROID_RECOMECO.md)
- [Laboratório de erros e testes](https://github.com/cleitongoy-debug/AURION-ONE/blob/main/LABORATORIO_IA.md)
- [Painel anterior preservado](https://github.com/cleitongoy-debug/AURION-ONE/blob/main/mobile/aurion-launcher.html) — link para código, **não** promessa de site online.

## Quando existir APK

1. Abra **Releases** no POCO, confira versão e registro de testes, e baixe **um único APK** da release oficial do repositório.
2. Abra o APK pelo Android e confirme a instalação. Se o Android exigir autorização para instalar por essa fonte, decida no aviso do sistema; não desative proteções gerais nem conceda acesso indiscriminado.
3. Abra AURION ONE e autorize somente as permissões necessárias quando a função correspondente for usada. Câmera, microfone, fotos/arquivos e notificações devem ser opcionais e solicitados no contexto.
4. Em Configurações > Conexões, conecte cada serviço pelo login oficial/OAuth, quando a integração estiver implementada. **Nunca digite senha de ChatGPT, Gemini, Google ou GitHub em um formulário criado pelo AURION.** Não colocar tokens, credenciais nem dados privados neste repositório público.
5. Em Configurações > Agente PC, associe o PC por canal privado autenticado. O PC precisa estar ligado e com o serviço autorizado ativo; não abrir portas públicas nem expor o agente diretamente à internet.
6. O painel deverá mostrar estados distintos: `não configurado`, `autorização pendente`, `conectando`, `conectado (verificado)`, `indisponível` e `erro`. Apenas uma resposta autenticada do serviço comprova conexão.
7. O orquestrador poderá escolher entre provedores **já conectados** segundo tarefa, capacidades e permissões. Publicar no GitHub, enviar arquivos e outras ações com efeitos externos exigirão confirmação explícita antes de executar.

## O que não é automático

O navegador não instala APK silenciosamente, não concede permissões por conta própria e não compartilha sessões de outros aplicativos. Assinatura Plus/Pro não equivale a chave de API. A integração com serviços depende das APIs e autorizações oficiais disponíveis; alguns recursos podem não oferecer integração. Mi Fitness/Mi Band dependem de permissões e interfaces efetivamente disponíveis. Geração de imagem/vídeo só será indicada como funcional após teste real de ponta a ponta.

## Critérios para publicar a primeira release

- Projeto Android compilável e APK produzido por build registrada;
- instalação e abertura verificadas em Android compatível;
- configuração, chat e diagnóstico testados sem credenciais embutidas;
- conexões e geração identificadas com estado real, sem simulação;
- hash SHA-256 e limitações descritos na release;
- nenhuma alteração destrutiva no painel V2 existente.

**Não existe botão de baixar APK aqui enquanto esses critérios não forem cumpridos.** Atualizações futuras devem preservar o mesmo aplicativo e sua configuração, com versão e migração testadas.