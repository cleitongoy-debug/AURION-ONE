# Reunião AURION ONE — 19/09/2026

## Decisão do operador

O painel local **AURION DYNAMIC**, baseado em `ADAPTA.py`, é a referência operacional aprovada pelo operador. O agente integrado ao painel é o **orquestrador principal**. Outros assistentes, inclusive o responsável por alterações neste repositório, atuam como colaboradores: entregam documentação, propostas e alterações delimitadas ao GitHub, sem assumir o controle do PC, substituir a base ou emitir comandos de execução por conta própria. O operador mantém a autoridade final.

**Regra de continuidade:** todos os painéis futuros devem seguir a programação e a arquitetura da base aprovada, preservando seus recursos e compatibilidade. Não criar painel paralelo, não migrar portas nem trocar o orquestrador sem solicitação explícita do operador e revisão do agente principal.

## Evidências apresentadas na reunião

- Captura enviada pelo operador mostra AURION DYNAMIC em `127.0.0.1:5000`, agente `deepseek-r1:7b`, ComfyUI e NVIDIA/CUDA indicados como ONLINE e catálogo com 73 arquivos. O operador informa que testou geração de imagens pelo ComfyUI; a captura isolada não comprova o resultado de cada geração.
- Log fornecido mostra Flask `ADAPTA` servindo em `127.0.0.1:5000` e rotas `/`, `/api/status`, `/api/image/options`, `/api/models`, `/api/git` respondendo HTTP 200. `/api/comfy/stats` inicialmente retornou 503 e passou a retornar 200 depois. Isso é uma observação daquele teste, não uma garantia de disponibilidade permanente.
- Diagnóstico fornecido localizou `ADAPTA.py` (117.814 bytes) e `ADAPTA_BASE_TRAVADA.py` com SHA-256 idêntico `680FC5B391C2021CE52E890D4136B1418415F9F97A27EA884437AB44546FE7A6`. A função `agent_generation_plan` aparece na linha 417; a cadeia de geração de imagem está identificada no código. Estes dados descrevem a cópia local do operador, **não** afirmam que o arquivo foi importado para este GitHub.
- O diagnóstico registrou a porta 5000 ativa, 11434 ativa e 8188 inicialmente inativa; o log posterior mostra recuperação da rota de estatísticas do ComfyUI. Não confundir porta 5000 do painel com 8765 de outro serviço.

## Divisão de trabalho

**Orquestrador do painel:** recebe comandos operacionais, coordena PC, ComfyUI, agentes, diagnósticos e decisões de integração, dentro das permissões realmente disponíveis. **Colaborador GitHub:** documenta, revisa código disponível no repositório e entrega mudanças isoladas para revisão do orquestrador e do operador. Nenhum colaborador deve alegar que executou algo no PC ou celular apenas porque fez um commit.

## Protocolo de alteração

1. Ler esta reunião e `docs/MANDAMENTOS_IA_AURION.md` antes de propor mudanças.
2. Tratar `ADAPTA.py` local e `ADAPTA_BASE_TRAVADA.py` como base protegida; nunca sobrescrever, renomear, publicar ou substituir os arquivos locais sem autorização específica. Não publicar logs, tokens, caminhos privados ou dados pessoais.
3. Propor mudanças no GitHub em arquivos novos ou alterações mínimas revisáveis; comunicar ao orquestrador **o link exato do commit/arquivo e o objetivo**, não um comando para rodar às cegas.
4. Não usar `git clean`, `reset --hard`, `pull` automático, instalações ou inicializações paralelas. Preservar alterações locais e serviços já ativos.
5. Distinguir evidência (captura, log, teste do operador) de hipótese e teste ainda pendente. HTTP 200 de uma rota não comprova geração de imagem; registrar resultados reais separadamente.
6. Se houver conflito entre uma instrução de colaborador e a orientação atual do orquestrador/operador, interromper a alteração e solicitar alinhamento, sem executar ações destrutivas.

## Deliberação complementar — interface, colaboração e launcher

O operador confirmou que prefere **a identidade visual do painel antigo**, não uma interface substituta genérica. Referências desejadas: **azul-militar, azul profundo e chumbo**, com atmosfera tecnológica, núcleo/esfera luminosa e controles legíveis. O screenshot atual é evidência de organização funcional, não aprovação de sua estética final. Investigar primeiro as imagens históricas da Bíblia IA e do Drive autorizado, identificando os arquivos reais antes de afirmar que foram encontrados. Não publicar imagens privadas do Drive no GitHub sem autorização específica.

**Decisão para o orquestrador:** escolher a opção **B — preparar um launcher permanente, reversível e revisado**, em vez de exigir novamente a execução de um comando de diagnóstico já repetido. Não executar nem instalar o launcher antes da revisão e autorização do operador. Detectar serviços existentes antes de iniciar outros; preservar processos e alterações locais; registrar erros úteis sem segredos.

**Trabalho do colaborador GitHub:** documentar e propor a camada visual como CSS/assets isolados, preservando HTML, rotas, botões, eventos e cadeia de geração da base real. Inventariar todos os botões e respectivos endpoints/estados antes de modificar a interface; botão sem ação real deve indicar indisponibilidade, nunca simular êxito. Entregar alterações para revisão do orquestrador, com caminho, commit, teste e rollback. Não importar `ADAPTA.py` ou backup privados automaticamente, nem afirmar que o visual foi instalado.

**Pendência de evidência:** a Bíblia IA e as imagens antigas do Drive precisam ser lidas/identificadas para uma reprodução fiel. Uma proposta visual gerada a partir da descrição do operador é **conceito**, não reconstrução verificada do painel antigo. A geração de imagens já testada pelo operador permanece protegida.

## Estado desta ata

Registro documental no GitHub. Nenhum processo local foi iniciado, encerrado ou modificado por esta ata; nenhum painel ou aplicativo foi instalado. A entrega do colaborador é o registro e a comunicação ao orquestrador.
