# Ata operacional — AURION ONE / Escola de módulos — 21/09/2026

## Diagnóstico do erro principal
A v0.8 local `aurion_evolver.py` executa análise AST e compara nomes de funções; `stage()` copia uma versão histórica inteira para proposta. **Não faz fusão semântica, correção por IA, teste de integração, promoção nem reinicialização.** Encontrar 14 PYs não implica 14 componentes compatíveis ou ativos. A prévia do editor aceitava fonte vazia, exibindo diff de exclusão total; a v0.9 adiciona bloqueio de proposta vazia/incompleta, mas não resolve ainda integração automática de código.

## Evidências e preservação
Referências do operador: screenshots do HUD e favoritos do navegador; PDF `PALET#COLOR.pdf` com 20 páginas de propostas de paleta e módulos, incluindo monitoramento, analytics, finanças, CRM, DevOps, segurança, IA, dados, automação, redes e marketing. O PDF é **referência de design**, não comprovação de integrações. Não remover HUD aprovado, abas existentes, esfera, operadores JSON13/DS20/GB/BB/JR; TOMIM permanece projeto. Não tocar em `ADAPTA_BASE_TRAVADA.py`.

## Entrega local v0.9 (não publicada no repositório)
Pacote criado na conversa: acrescenta aba FAVORITOS & ESTUDOS com importação explícita de bookmarks Chrome/Edge/Brave (somente URLs/títulos/pastas), deduplicação por URL, busca e registro manual de progresso/horas em `config/aurion_favorites_private.json`. Não lê cookies, senhas nem histórico; não acessa cursos pagos nem comprova compras/conclusão. Bloqueia proposta vazia no editor. Sintaxe Python e JavaScript verificadas localmente; execução Windows/Flask e integrações não verificadas. Dados privados de favoritos ficam fora do Git.

## Pendências críticas
1. Identificar processo PY efetivamente ativo na porta 5058 e estabelecer mapa de dependências de módulos e skills com proveniência.
2. Testar importação de bookmarks e interface no Windows real; instalar Flask somente com consentimento se ausente.
3. Implantar mecanismo seguro de merge de funções com análise de imports/rotas/colisões, testes isolados, aprovação e rollback; não copiar PY antigo inteiro automaticamente.
4. ComfyUI: distinguir modelos em disco, modelos registrados na API e workflows compatíveis; não declarar geração funcional sem resultado.
5. Programas After Effects, Nuke, Blender, C4D, NVIDIA e outros: inventário por executável/versão, conectores por documentação e autorização; nenhum status ONLINE sem teste.
6. Cursos pagos, e-mails, Drive, horas, gastos e conclusões: somente por integrações autorizadas e fontes verificadas; não inferir compra a partir de bookmark. Não publicar dados pessoais ou empresariais no GitHub público.
7. F5 recarrega interface; não atualiza código Python em execução. Implementar supervisor de atualização com health check e rollback antes de anunciar atualização automática.

Status congelado: **v0.9 entregue como pacote local de melhorias incrementais; automerge, agente controlador, cursos autenticados, scan integral e execução Windows NÃO CONFIRMADOS.**