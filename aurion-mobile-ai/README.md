# AURION ONE HUD v3.0.0

APK Android independente do painel de PC, mantendo o mesmo applicationId `one.aurion.mobileai.hud` para atualização sobre o HUD v2.

## Módulos no APK

- **Início**: resumo de IA, memória, estudos, clientes e T8i.
- **Chat + Voz**: roteamento por endpoints configurados, TTS e botão de headset.
- **Memória**: caixas locais autorizadas.
- **Criar / Estúdio / Imagem / Converter**: funções móveis existentes preservadas.
- **T8i**: seleção de CR3/MP4, preservação do original, depósito escolhido pelo operador, verificação/instalação opcional do suporte RAW no Super Studio do PC e revelação CR3 → JPEG quando o PC estiver conectado.
- **Estudos**: curso, professor, assunto, tópico, progresso informado, conclusão manual, notas e cronômetro persistente.
- **Clientes**: cliente, projeto, serviço, status, prazo, notas e cronômetro de trabalho.
- **Portfólio**: matriz de 10 capacidades, 8 projetos catalogados, progresso de cursos auditado e pendências probatórias do dossiê de 28/09/2026.
- **Depósitos**: escolha de raiz/pastas pelo seletor oficial do Android, exportação de conversas, estudos, clientes e backup ZIP.
- **Conexões / PC / Bíblia / Contas**: preservados.

## Persistência

Os registros críticos são gravados primeiro no armazenamento interno do app em JSONL:

- `conversations.jsonl`
- `study_sessions.jsonl`
- `clients.jsonl`
- `t8i_assets.jsonl`
- `events.jsonl`

Os depósitos externos são opcionais e escolhidos pelo operador via Storage Access Framework. O backup não exporta chaves de API.

## Canon T8i

Um arquivo **CR3 é RAW fotográfico**, não C-Log. A revelação RAW do PC usa o módulo `pc-package-v3` e as dependências fixadas em `requirements-t8i.txt` (rawpy/LibRaw, NumPy, imageio e tifffile). O original nunca é sobrescrito.

Fluxo previsto:

1. selecionar CR3 no APK;
2. copiar o original para o depósito escolhido;
3. conectar ao Super Studio do PC;
4. verificar dependências;
5. instalar suporte T8i somente com confirmação explícita;
6. revelar no PC;
7. trazer o JPEG para o depósito T8i EXPORTS no Android.

Se o PC estiver offline, o arquivo e o registro local permanecem preservados.

## Build

O workflow `.github/workflows/aurion-mobile-ai.yml` compila o APK e publica o artefato:

`AURION-ONE-HUD-v3.0.0.apk`

Também executa `py_compile` no bridge T8i do Super Studio antes do build Android.

## Limites técnicos

- O APK não afirma conclusão de curso automaticamente; progresso/conclusão são dados informados pelo operador.
- O APK não varre pastas que não foram escolhidas pelo operador.
- A integração T8i com o PC exige Super Studio online, URL/token local e ambiente Python isolado preparado.
- Qwen-Image, Wan e outros modelos pesados continuam dependentes do PC/GPU ou de endpoints externos adequados.
- Mi Band 9 Pro depende das capacidades expostas pelo Android/Mi Fitness; não é tratada como microfone genérico.


## Dossiê / Portfólio

A tela **Portfólio** usa `app/src/main/assets/portfolio_dossie.json` como fonte estruturada. Percentuais de cursos não são convertidos em horas e blocos de horas de natureza diferente não são somados. Dados financeiros de clientes não são publicados nesta tela.
