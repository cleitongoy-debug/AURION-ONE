# Lote 5 — comparação documental parcial (19/09/2026)

Estado: PARCIAL; não declarar protocolos históricos implementados ou ausentes.

## Fontes e escopo
- `historicos.txt`, exportação declarada de 12/11/2025, campo `memory` em uma linha extensa: a recuperação de `DUMP` retornou 9 correspondências, mas o trecho exibido foi truncado e não isolou uma definição contextual verificável. Busca literal `PROTOCOLO_BASE` e `PROTOCOLO_MENTE` retornou zero na recuperação com aviso de fallback do leitor; zero não prova inexistência. `BASE` e `MENTE` têm usos genéricos; ainda não é possível atribuir-lhes semântica protocolar. `STBY_SYNC` e `GATILHO` seguem não localizados na recuperação anterior, não comprovadamente inexistentes.
- `ADAPTA.py` da Biblioteca do ChatGPT, versão 1; não foi comprovado que corresponde à cópia executada no PC. Os arquivos locais não foram alterados.

## Comparação específica de código
1. Memória: `ADAPTA.py` linhas 29 e 39–47 define `BRAIN_FILE=PROJECT/'aurion_brain.json'` e carrega JSON para `STATE['brain']`. Linhas 980–988 expõem `GET /api/memory/list`, `POST /api/memory/save`, `POST /api/memory/load`; `save` escreve texto em `MEMORY_DIR/title`. Isso demonstra rotinas de persistência e gerenciamento de arquivos na versão consultada; não comprova equivalência ao protocolo histórico `MENTE` nem execução atual.
2. Geração: linhas 417–435 definem `agent_generation_plan` com seleção de checkpoint e parâmetros; linhas 1062–1082 iniciam `POST /api/image/generate`, verificam prompt, porta ComfyUI, checkpoints e constroem workflow antes de enviar a `/prompt`. Isso demonstra código de geração; não demonstra protocolo `BASE`, `DUMP`, `GATILHO` ou `STBY_SYNC`.
3. Busca por `STBY_SYNC|GATILHO|DUMP` no `ADAPTA.py` retornou correspondências para a palavra genérica `json.dumps` (serialização JSON), não evidência do protocolo histórico `DUMP`. Não usar correspondência lexical como implementação.

## Pendências verificáveis
- Extrair janelas curtas e contextualizadas de cada ocorrência histórica de `DUMP`, `BASE` e `MENTE`, com origem, data e definição explícita, sem divulgar dados privados; o arquivo possui linha física enorme e respostas truncadas.
- Conferir versão/hash/caminho da cópia operacional em E: antes de comparação definitiva.
- Comparar cada protocolo somente após obter definição histórica, com funções e testes específicos; não afirmar ausência por busca negativa.

Nenhum teste do PC, geração de imagem, modificação do painel ou sincronização local ocorreu neste lote. Mensagem ao AURION#ONE é repassada manualmente por Cleiton.