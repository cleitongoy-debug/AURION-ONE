# AURION ONE — Blueprint de coordenação

Data declarada: 19/09/2026. Mensagem de AURION#ONE encaminhada pelo operador Cleiton. Este documento registra o plano, sem afirmar testes não realizados.

## Estado declarado
- `ADAPTA.py` (~117 KB): base indicada como funcional, preservada e sem alterações; não testada nesta etapa.
- `ADAPTA_BASE_TRAVADA.py`: backup indicado como idêntico; hashes atuais no disco E: ainda não conferidos.
- `PAINEL_QUERO.png`: referência de HUD azul-marinho e ciano `#00d4ff`.
- Lotes históricos 1–6 revisados; cronologia completa pendente.
- Decisão A: localizar a base correta em E: **antes** de testes ou HUD.
- Preservar `AURION_AUTO.ps1`; sem referências militares; botões com ações reais.
- Não existe comunicação automática entre IAs: repasses dependem do operador.

## Ordem obrigatória
1. **Lote 7, somente leitura:** localizar `ADAPTA.py` e `ADAPTA_BASE_TRAVADA.py` nas pastas AURION de E:, registrar caminhos completos, tamanhos e SHA-256 e **examinar o conteúdo do inicializador** para identificar a cópia utilizada. A inspeção anterior identificou pastas na raiz de E:, mas não seus interiores. A varredura foi proposta; nenhum resultado local foi recebido aqui.
2. Testar o painel original de forma controlada, sem alterar arquivos.
3. Aplicar o HUD azul/ciano conforme `PAINEL_QUERO.png`, com backup, reversão e botões funcionais. Preservar e testar separadamente a geração de imagem.
4. Consolidar a **Ata Viva**: decisões, erros anteriores, evidências e pendências.
5. Entregar o **CD do jogo**: inicializador para painel, ComfyUI e Tailscale, abrindo navegador após validar caminhos, permissões e dependências.

## Regras
- Inventário não é leitura completa; métrica simulada não é aprendizagem real.
- Preservado não significa testado agora; termo encontrado não demonstra protocolo implementado.
- Não repetir diagnósticos concluídos nem publicar credenciais, tokens ou transcrições privadas integrais.
- Mudanças pequenas, autorizadas e reversíveis. Não alterar `ADAPTA.py`, backup ou `AURION_AUTO.ps1` antes de validar a base.
- Sem referências militares.

## Responsabilidades
- **AURION#ONE:** coordena, revisa lotes, cruza com `ADAPTA.py` e aplica HUD.
- **ChatGPT:** lê `historicos.txt` em lotes, registra no GitHub e entrega relatórios, conforme ferramentas disponíveis.
- **Cleiton:** autoridade final e responsável por repasses quando necessários.

## Retomada
**E: → comparar caminhos/hashes → identificar inicializador → testar painel original → HUD → Ata Viva → CD do jogo.** Nunca pular etapas. Lote 7 depende da saída real da varredura local; ChatGPT não possui acesso direto ao disco E: do PC. O comando compartilhado lista inicializadores, mas não lê seu conteúdo, que ainda precisará de inspeção somente leitura.