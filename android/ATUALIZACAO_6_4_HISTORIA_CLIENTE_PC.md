# AURION ONE POCO v6.4.0 — história, cliente e sonda PC

Data: 28/09/2026 (UTC; registros históricos mantêm o fuso e a precisão de cada fonte).

## O que mudou

- Painel: quatro métricas separadas — 315,7 horas declaradas no snapshot TCR de 12/11/2025; 6.882 ciclos naquele snapshot; sessões cronometradas v6.4; 20 verbetes e assuntos da enciclopédia. A diferença entre 4.833 ciclos de 02/11 e 6.882 de 12/11 é 2.049, **não** atividade posterior comprovada.
- História: busca e filtro por assunto, estados da evidência, fonte em cada verbete; diário de erros e tratamentos do arquivo, junto aos eventos novos do POCO com horário. Não soma horas de agentes às humanas, nem dias de calendário a horas trabalhadas.
- Cronômetro: cada sessão traz início, fim, assunto e milissegundos medidos enquanto o app está visível. A passagem ao segundo plano encerra a sessão. Valor legado v6.3 fica separado porque podia incluir tempo com app fechado. Marcos têm data e horário; não há retrocálculo de horas sem sessões originais.
- Projeto: seletor oficial importa múltiplas fotos do cliente com referência persistente no aparelho. A direção do personagem e as sete etapas (foto, direção, model sheet, 3D, cena trap, revisão, entrega) ganham registro local e horário. Uma confirmação manual não prova um arquivo 3D: conferir exportação em outra ferramenta antes da entrega. Fotos e tokens ficam fora do Git.
- PC: sonda de **leitura** consulta `/health`, `/api/status`, `/api/inventory` com Bearer onde exigido, ComfyUI `/system_stats` e Ollama `/api/tags`. Registra HTTP e hora, sem despejar o corpo privado. Aceita endereços Tailscale 100.64.0.0/10 além dos privados já aceitos. Não inicia scan nem altera o PC.
- Agente: contexto de até quatro verbetes pertinentes, com fontes e limites de evidência, nas consultas com memória e no guia offline.

## Fontes e limites

A curadoria deriva de `docs/HISTORICO_QUANTIZACAO_CICLOS_2026-09-19.md`, `docs/CRUZAMENTO_RASTROS_HISTORICOS_2026-09-19.md`, `docs/VELOCIMETROS_HISTORICOS_METODO_2026-09-19.md`, `docs/REUNIAO_HANDOFF_PC_POCO_2026-09-19.md`, `docs/DIGITALPEN_BIBLIA_VISUAL_MODULOS_REFERENCIAS_3D_COR_CINEMA_2026-09-20.md`, registros Android e Índice Mestre/Pipeline T8i do Drive. Os 74.089 arquivos/11.535 candidatos eram scan de metadados do PC de 18/09, não conteúdo estudado. O arquivo de 206,68 horas nominais de agentes, 308 ciclos e 107 descobertas é de trechos diferentes e não vira total atual.

## Atualização

Mesmo `applicationId` (`one.aurion.poco.v6`), `versionCode` 64 e mesma chave privada da v6.3. Publicar APK assinado, SHA-256 e manifesto **nessa ordem**. O app compara versão, hash, pacote e assinatura; o Android pede confirmação da instalação. Atualizar por cima preserva SQLite, cofre e projetos. Sem teste físico no POCO nem conexão real com o PC nesta edição.

## Próxima verificação no aparelho

Abrir Configuração → Nós, informar URL privada e token do Home Node, salvar e tocar “SONDA PC · LEITURA”. Um 401 indica autenticação ausente; conexão recusada pode significar serviço parado ou escuta só em 127.0.0.1. Para o cliente, abrir Projeto, importar fotos recebidas e salvar briefing; gerar e verificar os arquivos 3D/cena na ferramenta apropriada antes de marcar etapas concluídas.
