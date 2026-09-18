# AURION ONE — LABORATÓRIO COMPARTILHADO DE IAs

Atualizado em 2026-09-18. Documento de passagem de contexto para ChatGPT, Gemini, Adapta, agentes locais e demais colaboradores. **Leia antes de sugerir qualquer teste ou alteração.** Este arquivo registra evidências relatadas e observadas, não é um teste automatizado nem substitui os arquivos originais do projeto.

## Protocolo obrigatório para cada IA
1. Ler este documento, `docs/STATUS_MOBILE_2026-09-18.md`, README e código relevante antes de agir. Verificar se há novos commits e não presumir que o registro está atualizado.
2. Consultar a seção de testes antes de propor passos. Não repetir teste concluído sem mudança concreta de código, ambiente ou hipótese; explicar por que a repetição é necessária.
3. Distinguir `CONFIRMADO POR CAPTURA/USUÁRIO`, `CONFIRMADO POR FERRAMENTA`, `RELATADO`, `NÃO TESTADO`, `FALHOU` e `BLOQUEADO`. Não converter intenção em implementação.
4. Registrar cada alteração com data, caminho, commit, resultado e próxima ação. Não afirmar que há commit, publicação, instalação, integração ou conexão sem evidência.
5. Nunca registrar credenciais, tokens, cookies, chaves de API, dados pessoais ou conteúdo privado neste repositório público. Autenticação exclusivamente nos serviços oficiais ou mecanismos seguros apropriados.
6. Preservar arquivos e funcionalidades existentes. Antes de autorreparo, criar backup, pedir confirmação para mudanças destrutivas e fornecer reversão. Não expor agente do PC diretamente à internet.
7. Enquanto o PC estiver desligado, NÃO solicitar testes de servidor, Ollama ou ComfyUI. Priorizar tarefas que possam ser feitas no celular/GitHub.

## Identidade e ambiente informados
- Projeto: `cleitongoy-debug/AURION-ONE`, branch `main`; nome de sistema AURION ONE / LÚMEN. Repositório público: cuidado com segredos.
- Celular: POCO X7; Termux e Mi Fitness instalados; relógio Mi Band 9 Pro. PC Windows desligado no último relato do usuário.
- Objetivo: painel móvel com atalhos para serviços oficiais (ChatGPT, Gemini, Adapta, GitHub, Drive), seleção de serviços e rede, chat do agente, mídia e conversores; conexão privada com PC, ComfyUI e notificações compatíveis com Mi Fitness. Objetivos não são recursos concluídos.
- Usuário trabalha em entregas: jamais exigir uso da tela em movimento. Configurar e testar somente parado em local seguro.

## Linha do tempo de testes e erros (18/09/2026)
| ID | Componente | Evidência e resultado | Estado | Não repetir sem nova hipótese |
|---|---|---|---|---|
| T01 | Repositório GitHub | Usuário abriu `https://github.com/cleitongoy-debug/AURION-ONE` no POCO. | CONFIRMADO POR USUÁRIO | Não perguntar novamente se o repositório abre. |
| T02 | GitHub Pages URL de arquivo | Captura do celular mostrou 404 em `https://cleitongoy-debug.github.io/AURION-ONE/mobile/aurion-launcher.html`. | FALHOU | Não dizer que Pages está ativo só porque HTML existe. |
| T03 | GitHub Pages URL raiz | Usuário relatou 404 ao testar painel; não há confirmação de deploy. | FALHOU/SEM DEPLOY VERIFICADO | Investigar configuração/deploy, não repetir links indefinidamente. |
| T04 | Configurações GitHub | Capturas mostram `/settings` da CONTA pessoal e 404 em tentativa de abrir configurações do REPOSITÓRIO; repositório abre. | CONFIRMADO POR CAPTURA | Não confundir configurações da conta com as do repositório. Verificar sessão/permissões e URL exata. |
| T05 | HTML móvel V2 local | Captura mostra `AURION ONE MOBILE V2` aberto no POCO via `content://media/external...`, com abas, botões e indicadores. | CONFIRMADO POR CAPTURA | Não pedir novamente teste de abertura do HTML. Abrir não comprova funções de backend. |
| T06 | Rede no HTML V2 | Tela indica rede do navegador aparentemente disponível; não equivale a acesso ao PC. | INDICADOR LOCAL | Não marcar PC online por este sinal. |
| T07 | PC Windows | Usuário informou que está desligado. | RELATADO | Não solicitar teste remoto até informar que ligou. |
| T08 | Mi Band 9 Pro | Mi Fitness identificado; pareamento, permissões e integração AURION não foram demonstrados. | NÃO TESTADO | Não afirmar leitura de dados ou controle do relógio. |
| T09 | Agente Windows | Documento anterior registra código FastAPI com `/health`, `/api/status`, `/api/device`, `/api/prompt` e token; execução e acesso remoto não demonstrados nesta sessão. | CÓDIGO RELATADO / EXECUÇÃO NÃO TESTADA | Inspecionar código e testar quando PC ligado. |
| T10 | Serviços pagos e logins | Usuário deseja atalhos e autenticação em ChatGPT, Gemini, Adapta, Drive e redes sociais; nenhum login integrado ao AURION foi confirmado. | NÃO TESTADO | Não presumir sessão, API, plano ou permissões. |
| T11 | Autorreparo, mídia e conversores | Áreas e indicadores anunciados no HTML V2; não há teste funcional de processamento, correção automática ou geração. | NÃO TESTADO | Não apresentar botões como serviços operacionais. |

## Alterações registradas no GitHub (conferir commits antes de reutilizar)
- `mobile/aurion-launcher.html`: criação anteriormente reportada com commit `294fedace91378f86f7c091152338b2e42193ca1`.
- `index.html`: criação anteriormente reportada com commit `0dc8086e7f9d1c531b4ff1990bc986e12fc1512a`; arquivo de entrada não habilita Pages sozinho.
- `docs/STATUS_MOBILE_2026-09-18.md`: criação confirmada por leitura da API GitHub; commit anteriormente reportado `5c9ddc1e0418365c658509ae0e93a6396b3734f1`.
- `AURION_ONE_MOBILE_V2.html`: arquivo local compartilhado no chat e aberto por captura no POCO; **não presumir que foi enviado ao GitHub**.

## Fila de trabalho sem repetição
1. Inspecionar repositório e o estado real de Pages/deploy por evidências, não por suposição. Se a configuração administrativa não estiver disponível via conector, informar exatamente a limitação e oferecer alternativa de hospedagem somente com autorização.
2. Versionar a V2 no repositório apenas após obter o arquivo real e comparar conteúdo; não reconstruir às cegas.
3. Preparar PWA HTTPS com manifest e service worker quando hospedagem estiver funcionando; HTML `content://` não equivale a APK nem recebe atualizações automáticas.
4. Definir contrato de API autenticada entre painel e agente PC; usar rede privada/HTTPS e tokens fora do Git. Não armazenar senhas de terceiros no painel.
5. Verificar capacidades documentadas do Mi Fitness/Android antes de prometer notificações ou dados do relógio.
6. Testar imagens, vídeos, conversões, logs e autorreparo individualmente; indicadores devem refletir verificações reais.

## Modelo de novo registro
`ID | data/hora e fuso | IA/operador | ambiente e versão | hipótese | passos executados | resultado e evidência (URL/commit/log sem segredos) | status | próximo passo | reversão`.

### Pendências e limitações
Este documento não é a totalidade da 'bíblia' histórica. Para recuperar fatos antigos, ler documentos originais e acrescentar somente o que for verificado. Nenhuma IA tem acesso automático às sessões pagas das outras. GitHub Pages, PC, relógio, login unificado e autorreparo completo NÃO estão confirmados como funcionais.
