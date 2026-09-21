# Reunião operacional — 21/09/2026 — Continuação da reunião 1 e 2

Referências: `docs/REUNIAO_OPERACIONAL_2026-09-19.md`, `docs/AUDITORIA_BIBLIA_REUNIAO_PAINEL_2026-09-19.md`, `LABORATORIO_IA.md` e Bíblia Visual DigitalPen. Registro do estado observado pelo operador, não auditoria independente do Windows.

## Padrão de produto travado pelo operador
Preservar o HUD visual aprovado (preto/laranja/roxo, esfera, menu, operadores JSON13, DS20, GB, BB, JR com status e horas, chat, abas e serviços). TOMIM é projeto, não operador. Evolução ADITIVA: nunca retirar abas, cartões, funções ou substituir a identidade por blocos genéricos. F5 preserva preferências e deve atualizar dados descobertos sem executar ou instalar código por conta própria. Base `ADAPTA_BASE_TRAVADA.py` intocável. Qualquer estado ONLINE requer verificação real.

## Evidência do operador e problema atual
Capturas em 21/09 mostram AURION ONE abrindo, aba EDITOR PY SEGURO com identificação da versão e aba GERAR IMAGEM com seletor de checkpoints vazio. Operador confirma que a interface e opções novas abriram, mas modelos, programas, logins e geração ainda não estão comprovadamente funcionais. O editor atual recebe texto-fonte Python, não instruções em linguagem natural; instrução textual colada não executa correção. Versões anteriores v0.5, v0.6, v0.7 foram entregues como ZIP no chat; não presumir que qualquer uma foi testada com sucesso ponta a ponta no PC.

## Contrato da próxima versão — evolução pelo próprio painel
1. Inventariar de modo LIMITADO os arquivos Python existentes na pasta do painel, SKILL#PAINEL e backups conhecidos, sem repetir scan histórico completo nem executar versões antigas. Ler SKILL 1 quando acessível e tratá-la como documentação, não código confiável a executar.
2. Cruzar funções e hashes de versões anteriores com o PY ativo, preservar originais e registrar origem/limites. Arquivo encontrado ou sintaxe válida NÃO significa versão funcional.
3. Preparar proposta e backup reversível com diff e manifesto. Aplicação/sobrescrita apenas após testes de inicialização e funções relevantes e aprovação explícita do operador; nunca substituir ADAPTA/ADAPTA_BASE_TRAVADA.py. Uma versão histórica copiada não equivale a reparo sintetizado.
4. F5 reconsulta status, catálogo e alterações; não reexecuta varredura pesada, não reinicia serviços, não instala nem aplica atualizações automaticamente. Configuração de atualização precisa distinguir estudar, propor, testar e promover.
5. Para geração, validar ComfyUI `/object_info` e nomes reais de checkpoint, fila `/prompt`, histórico e saída. Não declarar geração funcional só por `/system_stats` HTTP 200.
6. Log privado de cada tentativa, hash, caminho, teste, falha e rollback. GitHub público recebe apenas estado resumido e código sem segredos, inventário local privado e documentos privados permanecem locais/Drive autorizado.

## Entrega local preparada nesta etapa
Pacote AURION ONE v0.8 acrescenta módulo `aurion_evolver.py` e controles no EDITOR PY SEGURO para estudo estrutural limitado, comparação de funções, seleção de versão histórica e criação de backup/proposta/diff/manifesto. Não há síntese automática de correções por LLM, execução de PY histórico, promoção automática nem teste de geração no Windows. Status: CÓDIGO PREPARADO; SINTAXE LOCAL A VERIFICAR/REGISTRAR NO PACOTE; EXECUÇÃO WINDOWS PENDENTE. Preservar esse limite em comunicações futuras.

Próxima ação: testar o estudo e a proposta no PC; identificar modelo ausente por API real; depois implementar testes isolados e promoção reversível com autorização, sem reiniciar o sistema no F5.