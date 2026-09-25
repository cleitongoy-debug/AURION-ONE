# NOVO AURION FINAL PART · Super Studio PC v2.0

Complemento desktop aditivo para a base real em:

`C:\Users\ADM_PESS\Desktop\painelseguro#1 - Copia`

## Regra de segurança

Este pacote **não edita, renomeia nem substitui** `ADAPTA.py` ou
`ADAPTA_BASE_TRAVADA.py`. Ele cria somente `_aurion_superstudio` dentro da base
para memória, workspace, registros e exportações. O servidor próprio usa
`127.0.0.1:5060`; o painel real continua na porta configurada, inicialmente
`5058`.

## Abrir

1. Extraia a pasta inteira.
2. Dê dois cliques em `INSTALAR_E_ABRIR_SUPER_STUDIO_PC.cmd`.
3. Mantenha a janela aberta enquanto estiver usando o Studio.
4. Para CR3, execute uma vez `INSTALAR_SUPORTE_T8I.cmd`.

O ambiente `.venv` é isolado. Apagá-lo remove apenas as dependências desta
peça. Os arquivos importados e a memória ficam em
`_aurion_superstudio\workspace` e `_aurion_superstudio\aurion_memory.sqlite3`.

## Abas e funcionamento

- Projetos, memória, presets, experimentos, recursos e entregas: SQLite local.
- Foto: processamento e exportação JPG com Pillow.
- Canon T8i: cópia do CR3 e revelação opcional com rawpy/LibRaw.
- Vídeo e áudio: conversão real quando FFmpeg está no PATH.
- Cor: histograma RGB, waveform e vectorscope da prévia.
- FX, timeline e motion: edição de presets/projetos, sem declarar render final.
- Ollama: catálogo `/api/tags` e geração `/api/generate`.
- ComfyUI: status, catálogo de checkpoints em `/object_info` e fila `/prompt`.
- Blender 5.2: diagnóstico do caminho real, abertura local, render de imagem/animação em segundo plano, acompanhamento de tarefas e bibliotecas de Nodes, Texturas, Rigs e Roupas/Acessórios.
- Cinema 4D/Octane: diagnóstico de processo, caminhos, binários R2023, duplicatas, BugReport e soluções orientadas, sem apagar ou substituir plugins.
- POCO, Mi Band, áudio e Tailscale: permanecem **não verificados** até teste real.

## Reversão

Feche a janela do servidor. Se quiser remover o complemento, apague somente a
pasta extraída. Para manter memórias e exportações, preserve
`_aurion_superstudio` da base real.
