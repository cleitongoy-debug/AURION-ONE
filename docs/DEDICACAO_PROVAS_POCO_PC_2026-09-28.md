# Registro de dedicação, cursos e provas · 28/09/2026

## Contrato factual

- **Sessão medida:** início/fim do cronômetro de estudo/projeto/pesquisa/prática, em milissegundos e com tópico, projeto, origem e motivo de encerramento. Mostra segundos inteiros. Para o total humano, intervalos simultâneos do POCO e PC são unidos; cada segundo conta uma vez. O valor por área pode sobrepor outra área se duas sessões simultâneas foram classificadas em áreas diferentes.
- **Progresso observado:** porcentagem e estado concluído da página de curso, nome de curso/módulo, data de registro e fonte. Percentual não fornece duração. Aulas marcadas como concluídas podem ser catalogadas individualmente. A captura `GUERRA#STARTER#58.png` mostra 58% do 3D Start e Cinema 4D em uso; `cursos.png` mostra 50% do Compositor HighEnd e 52% do Combo Dose Diária de AudioVisual. Os demais cartões demonstram acesso e serão aprofundados com prova de módulos.
- **Certificado/print:** original PDF ou imagem, SHA-256, curso/projeto, horas que o documento informa e referência do campo. A soma documental é exibida separada das sessões medidas, evitando misturar dois modos de prova e reconhecer o mesmo arquivo nos dois aparelhos. Certificados diferentes podem documentar horas sobrepostas; antes de apresentar uma soma de estudo histórico sem duplicidade, conferir turma, período e escopo.
- **Marco de projeto:** descrição com data, origem e projeto; não aumenta duração se não houver sessão medida.
- **Legado:** 315,7 h e 6.882 ciclos são snapshots declarados em documento de 12/11/2025. Não se somam automaticamente às sessões novas nem se incrementam com o relógio. Horas de agentes são outro universo.

## Implementação neste lote

- O Super Studio PC (porta padrão **5060**) mantém a tabela SQLite `dedication_events` com ID estável, gravação idempotente e rotas autenticadas `GET/POST /api/mobile/dedication`; a área Certificados armazena originais em `_aurion_superstudio/workspace/CERTIFICADOS` e metadados/checksum na memória, `GET/POST /api/mobile/certificates`.
- O POCO guarda eventos locais, sincroniza lotes autenticados de até 200 itens e reenvia pendências. O token do Super Studio PC é colocado no cofre Android; não é incluído no diário nem na URL. Certificados importados por seletor Android mantêm URI de leitura persistente, SHA-256 e são enviados ao PC autorizado quando a conexão fica disponível. O registro local permanece se o PC estiver desligado.
- Os temporizadores param ao sair da tela. A recuperação após encerramento inesperado usa apenas o último checkpoint escrito, sem preencher o período em que o aplicativo ficou fechado. O PC também guarda fila local de eventos até o servidor responder.
- Abas exclusivas **Dedicação** e **Certificados** no POCO e no painel PC. A História conserva fontes e métricas legadas separadas.

## Limites de observação e próximo teste no equipamento

Os aplicativos não têm acesso automático a cada página privada dos provedores de cursos ou a todas as abas do navegador. Ao abrir uma página dentro de um navegador externo, o POCO não recebe seu percentual ou tempo de reprodução. O campo de progresso aceita a leitura mostrada na página, com URL/print; importar páginas autenticadas em escala exige integrações oficiais ou exportações do operador. A duração de uma aula concluída só entra em horas históricas se houver horário/duração documentado ou registro próprio de sessão, nunca pela porcentagem isolada.

Validar em POCO físico e PC: emparelhamento com IP/Tailscale e token do Super Studio, importação PDF/imagem e abertura do original, SHA igual após transferência, lote offline seguido de sincronização, sessão sobreposta em dois aparelhos, atualização por cima com mesma assinatura. Neste ambiente foram verificados sintaxe JS/Python e armazenamento SQLite isolado; não houve compilação Android nem teste físico da nova versão. Não anunciar APK pronto antes desses gates.

## Pesquisa dos professores

O mapa detalhado está em `ANALISE_FORMACAO_CLEITON_2026-09-28.md`, com criadores, campos ensinados, provas e limites. O desenho de personagem segue `docs/DIGITALPEN_BIBLIA_VISUAL_MODULOS_REFERENCIAS_3D_COR_CINEMA_2026-09-20.md`: vistas, poses, topologia, UV, materiais/nós, rig, câmera, render e composição com artefatos reais.
