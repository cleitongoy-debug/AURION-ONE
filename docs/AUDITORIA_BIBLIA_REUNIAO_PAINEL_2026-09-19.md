# AURION ONE — auditoria de recuperação (19/09/2026)

## Escopo e evidência
Leitura da Bíblia `Biblia_da_Inteligencia_Artificial_AURION_ONE.docx` (32 páginas, edição 18/09/2026), `docs/REUNIAO_OPERACIONAL_2026-09-19.md`, `LABORATORIO_IA.md`, árvore do repositório e `index.html`/`mobile/aurion-launcher.html`. A Bíblia é especificação consolidada e contém estados históricos; execução recente prevalece quando divergir. Esta auditoria **não é prova de teste de UI no PC ou POCO**.

## Causa da divergência de produto
- Bíblia Livro 2 e Livro 3: base ADAPTA funcional protegida, Flask 5000, Open WebUI 8080, painel com imagem/vídeo/agentes/memória/configuração, chat flutuante sem cobrir controles. O registro recente prova **outro** serviço/portal em 8765 e chat separado no CMD. Não tratar a existência do portal 8765 como substituição validada da base ADAPTA 5000.
- `index.html` apenas redireciona a `mobile/aurion-launcher.html`; o launcher é uma central de links com campo HTTPS, não o painel completo e não prova APK, rede PC↔POCO, OAuth ou integração Mi Fitness.
- Bíblia Livro 9: identidade HÍBRIDO QUANTUM com esfera luminosa, núcleo branco, microcircuitos, azul profundo/azul claro/mostarda/branco, contraste e controles visíveis. Um fundo azul genérico não cumpre a identidade visual especificada.
- Bíblia Livro 3, capítulo 4: problemas históricos nomeados `agent_generation_plan` (500), ComfyUI stats (503), checkpoint duplicado, FFmpeg, 409 de concorrência e `pollImage` sem fim. São hipóteses de regressão a verificar na base atual, **não** falhas atuais automaticamente confirmadas.
- Bíblia Livro 5 e reunião: GitHub público é para código sem segredos; Drive para documentos/backups; memória privada e inventário não devem ser publicados. Preservar `.venv/`, `AURION_AUTO.ps1`, `mobile/aurion-one-live.html.bak-20260918T221803Z` e `remote-agent/aurion_remote_agent.egg-info/`.

## Contrato de produto antes de promover uma versão
1. Identificar e preservar a base ADAPTA real (`FINAL FUNCIONAL ADAPTA.py`) e comparar sua UI/rotas com o portal 8765; não sobrescrever a base sem cópia, teste e rollback. A Bíblia cita esse arquivo, mas sua presença no Git atual não foi comprovada.
2. Painel desktop responsivo com abas Produção, Imagem, Vídeo, Agentes, Memória e Configuração; agente selecionado e chat acessível sem obstrução; estado verdadeiro e controles funcionais ou claramente indisponíveis.
3. Testar ponta a ponta imagem: catálogo real ComfyUI → checkpoint exato → prompt positivo/negativo → fila → progresso com timeout/cancelamento → prévia → salvar resultado. Sem prometer geração só por HTTP 200 em `/system_stats`.
4. Vídeo: só habilitar montagem quando FFmpeg e pipeline forem validados; sem baixar/executar dependências desconhecidas automaticamente.
5. Mobile: reutilizar UI responsiva onde possível; conexão PC por endereço privado HTTPS autenticado, verificação real e fallback offline. Links ChatGPT/Gemini/Adapta não são integração de APIs nem acesso às assinaturas; autenticação em serviços oficiais separadamente. Mi Fitness não equivale a API de relógio.
6. Memória: SQLite privado com origem e revisão; `/biblia` precisa indexar o DOCX real e apresentar contagem/erros; cinco testes unitários passaram no Windows conforme log fornecido, mas indexação real ainda não foi demonstrada.
7. Testar interface em desktop e Android, online/offline, resolução pequena, status degradado, e registrar captura/log e resultado por função. Só então mudar o rótulo para funcional.

## Ordem de execução sem repetição
**A.** Localizar o ponto de entrada do painel azul e a base ADAPTA, mapear rotas e capturar comportamento existente; **B.** construir versão paralela com identidade visual e contratos de API reais; **C.** testes automatizados e inspeção visual; **D.** teste autorizado no PC e POCO; **E.** promoção com rollback. Não repetir scan histórico de 74.089 arquivos, nem testes SQLite já aprovados sem mudança relevante. Não usar `git clean` ou `git reset --hard`. Não afirmar entrega completa, APK instalado ou conexões OAuth sem evidência.

## Estado desta auditoria
Leitura documental e inspeção dos arquivos citados: realizadas. Modificação de painel, validação da Bíblia no Ollama local, teste real de geração, build APK e conexão POCO: **não realizados por esta auditoria**. Este registro evita confundir planejamento com execução.
