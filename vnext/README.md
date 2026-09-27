# AURION ONE vNext 0.5 — painel paralelo

Esta versão não altera `AURION_ONE.py`, `ADAPTA.py`, a base travada ou o painel
estável. Foi feita para a reunião de 24/09/2026, como etapa verificável.

## Abrir no Windows

1. Coloque esta pasta em `C:\FINAL#PAINEL#ONE\vnext`.
2. Clique em `START_VNEXT.cmd`. Python 3 instalado é suficiente; nenhuma
   dependência é instalada. O navegador abre `http://127.0.0.1:8766`.
3. Ollama, ComfyUI e Open WebUI existentes são reutilizados. O iniciador tenta
   iniciar somente os executáveis conhecidos quando porta e endpoint estão livres.
4. Escolha um modelo real no chat. O histórico é salvo em `data/aurion.sqlite3`.
   O agente consulta trechos das fontes listadas em **CHAT & AGENTES**. O resumo
   inicial fica em `knowledge/PROJECT_CONTEXT.md`. Se existir `C:\AURION-ONE`,
   a Bíblia DOCX, LABORATORIO e reuniões conhecidas são indexados automaticamente.
   Para importar outros documentos, coloque arquivos .md, .txt ou .docx em
   `data/context` e clique **RELER FONTES** ou F5. Não copia nem altera originais.
5. Para render, coloque uma cena `.c4d` configurada com Octane em
   `data/projects`, escolha a cena e clique **RENDER FRAME 0**. Saídas e logs
   ficam em `data/renders` e `data/logs`.

O painel é ligado apenas a `127.0.0.1`. As rotas de dados exigem um token
gerado a cada inicialização e injetado somente na página local. Não expõe
contas externas, licenças, chaves ou arquivos do PC pela rede. Não importa
plugins, não faz `git pull` e não altera arquivos antigos.

## Estados reais e limites

- Ollama/ComfyUI/WebUI verdes: endpoint HTTP respondeu na última consulta.
- Chat: só mostra resposta salva após retorno de um modelo listado pelo Ollama.
- C4D/Octane detectados: arquivos presentes; isso não confirma licença.
- Render confirmado: código zero, PNG válido novo e Octane citado no log.
- Imagem/vídeo, Google Drive, GitHub OAuth, POCO e Mi Band aparecem como
  indisponíveis até haver integração e teste específico. Não há APK nesta etapa.
- Nota manual e histórico persistem localmente. O chat ainda não indexa a Bíblia
  quando o repositório `C:\AURION-ONE` não existe; nesse caso a aba mostra
  exatamente as fontes carregadas. Nenhum documento do Drive é baixado sozinho.

## Testes e reversão

`python -m unittest discover -s tests -v` roda testes isolados sem Ollama.
O bootstrap não foi executado em Windows neste ambiente. Fechar a janela do
CMD encerra o servidor do painel. Remover apenas esta pasta reverte esta etapa,
mas faça backup de `data` se quiser manter conversas e renders.
