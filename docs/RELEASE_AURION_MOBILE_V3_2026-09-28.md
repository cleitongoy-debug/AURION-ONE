# AURION ONE HUD v3.0.0 — registro de evolução

Data: 2026-09-28  
Branch de validação: `feat/t8i-lifehub-v3`  
Application ID preservado: `one.aurion.mobileai.hud`  
Version code: `300`  
Version name: `3.0.0`

## Objetivo desta evolução

Consolidar no APK as funções que já apareceram na evolução do painel de PC e os requisitos solicitados para uso móvel sem perder registros:

- Canon T8i / CR3 / MP4;
- dependências RAW controladas no PC;
- depósitos escolhidos pelo operador;
- conversas com salvamento e backup;
- clientes e projetos;
- estudos, professores, assuntos, tópicos, progresso e conclusão manual;
- cronômetros persistentes para estudo e trabalho;
- exportação de dados e backup sem chaves de API.

## Arquivos alterados

- `aurion-mobile-ai/app/src/main/java/one/aurion/mobileai/MainActivity.java`
- `aurion-mobile-ai/app/src/main/java/one/aurion/mobileai/AurionLifeHub.java` (novo)
- `aurion-mobile-ai/app/build.gradle`
- `aurion-mobile-ai/README.md`
- `pc-package-v3/aurion_superstudio/app.py`
- `.github/workflows/aurion-mobile-ai.yml`

## Dados persistentes

O Life Hub grava em armazenamento interno do APK, de forma append-only em JSONL:

| Arquivo | Conteúdo |
|---|---|
| `conversations.jsonl` | mensagens enviadas e respostas recebidas |
| `study_sessions.jsonl` | início/fim de sessões, professor, assunto, tópico, notas, progresso informado e conclusão manual |
| `clients.jsonl` | cliente, projeto, serviço, status, prazo, notas e tempo trabalhado |
| `t8i_assets.jsonl` | seleção/cópia/revelação/retorno de CR3/MP4 |
| `events.jsonl` | configuração de depósitos e exportações |

Cronômetros ativos também ficam em preferências locais, permitindo retomar após fechar/reabrir o app.

## Depósitos

O operador escolhe as raízes pelo seletor oficial do Android. O APK cria, dentro do local autorizado:

- `AURION_CONVERSAS`
- `AURION_T8I_RAW`
- `AURION_T8I_EXPORTS`
- `AURION_ESTUDOS`
- `AURION_CLIENTES`
- `AURION_BACKUPS`

Existe opção de raiz mestre ou escolha separada por categoria. O backup ZIP não inclui segredos/chaves.

## T8i

Regra factual: **CR3 é RAW fotográfico, não C-Log**.

Fluxo implementado no candidato v3:

`selecionar CR3 → registrar → copiar original → verificar suporte PC → instalar dependências com confirmação → revelar via rawpy/LibRaw → retornar JPEG ao depósito Android`

Dependências controladas pelo arquivo já existente:

`pc-package-v3/requirements-t8i.txt`

O endpoint de instalação aceita somente a confirmação literal `INSTALAR_T8I` e executa o `pip` do `.venv` do Super Studio com a lista fixa do projeto.

Novas rotas do Super Studio:

- `GET /api/mobile/t8i/status`
- `POST /api/mobile/t8i/deps/install`
- `GET /api/mobile/t8i/export/<nome>`
- rota preservada: `POST /api/t8i/develop`

Rotas `/api/mobile/*` exigem `X-Aurion-Token`.

## Estudos

Cada sessão pode registrar:

- curso/livro;
- professor/escola/plataforma;
- assunto;
- módulo/capítulo/tópico;
- URL;
- carga horária total **informada**;
- progresso **informado** de 0–100;
- conclusão marcada manualmente;
- notas/aplicação;
- início, fim e segundos medidos pelo relógio do APK.

Nenhuma conclusão ou carga horária é inventada a partir de uma página externa.

## Clientes

Cada registro pode conter:

- cliente;
- projeto;
- serviço/tarefa;
- status;
- prazo;
- notas;
- início/fim e segundos trabalhados.

## Conversas

Toda mensagem enviada pelo Chat e toda resposta bem-sucedida do provedor são registradas internamente. O operador pode exportar TXT + JSONL para o depósito de conversas.

## Testes obrigatórios antes de main

1. `py_compile` do bridge PC T8i.
2. `:app:assembleDebug` no projeto `aurion-mobile-ai`.
3. APK gerado com tamanho > 0.
4. SHA-256 publicado no artifact.
5. Instalação manual no POCO e teste dos seletores de pasta.
6. Teste de cronômetro: iniciar → fechar app → reabrir → finalizar.
7. Teste CR3 no PC somente com arquivo autorizado, preservando original.
8. Teste de backup ZIP e restauração manual dos JSONL.

## Estado inicial deste documento

O código foi preparado em branch de validação. O estado **CI PASS / APK GERADO** só deve ser registrado depois que o GitHub Actions concluir com sucesso.
