# AURION: Cinema 4D 2023 + Octane 2022.1 ORIGINAL no POCO

Data: 2026-10-14. Estado: escopo verificado, streaming ainda NÃO configurado nem testado.

## Requisito original (não substituir por protótipo)

O operador quer o MESMO Cinema 4D Windows com os mesmos menus e ferramentas, projetos C4D, Octane e Live Viewer. O aplicativo mobile-c4d-agent v1.1 é um protótipo separado: NÃO é port do C4D nem contém o motor Octane. Não chamá-lo de entrega do requisito literal.

## REA: estudo real da ferramenta

Repositório oficial: https://github.com/morluto/rea
Package.json consultado: rea-agents 6.5.0, MIT para a própria ferramenta, Node 22.19+ ou 24.11+ ou 26+.
REA liga agentes via MCP à análise de binários nativos por Ghidra/Hopper/IDA, Android por JADX e outros formatos. Pode gerar evidências e ajudar a reconstruir comportamentos. Não converte executável Windows x64 e bibliotecas CUDA automaticamente em um binário Android ARM64, não recupera fonte proprietária literal e não concede licença de outros programas.

## Comparação de caminhos

1. C4D verdadeiro e Octane verdadeiro na tela do Android: Sunshine no Windows transmite vídeo e recebe entrada do Moonlight no POCO; GPU NVIDIA e programas rodam no PC. Experiência do aplicativo original, porém exige PC ligado.
2. Mesmo C4D e Octane como programa nativo offline no POCO: não existe port oficial identificado; não é viável simplesmente recompilar DLLs. Depende de fornecedores ou reimplementação independente muito extensa com renderizador Android diferente, que não seria o Octane original.
3. Editor AURION offline: protótipo próprio independente, não atende ao pedido literal.

## Procedimento seguro para permitir o programa original

- Verificar no PC Cinema 4D 2023, plugin Octane compatível, licença oficial e NVIDIA em funcionamento. Inventário histórico AURION menciona RTX 2060, mas estado atual NÃO foi verificado.
- Instalar Sunshine da origem oficial no Windows x64: https://github.com/LizardByte/Sunshine/releases
- Abrir no próprio PC https://localhost:47990 para configurar Sunshine e credenciais. Não expor o painel à internet.
- Adicionar Cinema 4D 2023 em Applications, apontando para EXE local verificado, ou usar Desktop.
- Instalar Moonlight original no POCO: https://play.google.com/store/apps/details?id=com.limelight
- Conectar PC e POCO na LAN ou Tailscale, adicionar no Moonlight o IP privado ATUAL do host e confirmar o PIN no Sunshine.
- Abrir a mesma cena C4D via Moonlight, executar Live Viewer Octane no PC, conferir imagem, controles, performance, latência e salvar projeto no disco.
- Só afirmar que funciona após teste real, screenshots e logs. O PC precisa permanecer ligado.

Documentação: https://docs.lizardbyte.dev/projects/sunshine/master/md_docs_2getting__started.html
https://github.com/moonlight-stream/moonlight-docs/wiki/Setup-Guide

## Aceite: evidência vs promessa

[ ] C4D original no POCO e interface idêntica à do PC
[ ] Octane Live Viewer original renderiza na NVIDIA do PC
[ ] Mesma cena .c4d aberta e salva com inputs enviados via Moonlight
[ ] Tailscale ou LAN pareado com acesso revogável; sem credenciais públicas
[ ] Medidas reais de conexão, GPU, latência, FPS e erros
[ ] Modo offline SEM PC corretamente rotulado NÃO ATENDIDO na solução streaming

## Engenharia reversa responsável

REA pode orientar análise autorizada de funcionalidades e investigação de compatibilidade; não usar para violar licenças, executar arquivos suspeitos ou tentar contornar controles. Histórico YellowStar/cracks não é dependência aprovada para distribuição Android.
