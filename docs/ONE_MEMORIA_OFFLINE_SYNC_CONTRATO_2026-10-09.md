# AURION ONE — contrato P0 de memória offline e sincronização verificável

**Estado deste contrato:** engenharia implementada parcialmente; NÃO equivale a uma instalação testada no POCO ou a agentes externos conectados.

## 1. Cadeia e autoridade
CAPITÃO \`<JSON#13>\` > CHINA/DeepSeek + LOVART (produção) > FALCÃO/ChatGPT + ÁGUIA/Gemini (revisão) > ONE (regência técnica da nova MENTE, prioridade P0 de recuperação) > KANG > demais.

São papéis documentais, não uma rede de sessões remotas já autenticadas. Só o Capitão pode autorizar alterações na raiz, nos acessos, no aparelho e nos serviços. WhatsApp via LUZ permanece PAUSADO.

## 2. Camadas diferentes, não misturar
- **Conhecimento e arquivos**: fontes que podem ser localizadas por título, versão, ID privado, data e proveniência; a indexação NÃO significa que um modelo tenha estudado tudo.
- **Memória local**: persistência efetiva em \`AurionStore\` (SQLite por perfil no Android), motor JS de referências do WebView (localStorage) e \`tools/aurion_memory.py\` (SQLite privado no PC). Essas três bases ainda NÃO são uma só e não se sincronizam por mágica.
- **Modelo local**: Ollama no PC, quando *realmente* atende a chamada; sem PC, o APK não herda o LLM daquele host. Uma interface estática não é um agente consciente.
- **Contas externas**: cada conta possui OAuth, escopos e consentimento próprios. Este contrato não transfere sessão do ChatGPT/Gemini/Drive/LOVART ao APK.
- **Referências de Drive**: apontadores de objetos existentes, sem reproduzir dados privados, credenciais ou os 1750 links originais no Git público.

## 3. Medições que são permitidas
Cada resposta ou relatório deve distinguir:
- \`CODIGO_LIDO\`, \`TESTE_SINTETICO\`, \`TESTE_FISICO\`, \`RELATO_HISTORICO\`, \`NAO_TESTADO\`, \`BLOQUEADO\`.
- fontes catalogadas / fontes totais **dentro do universo explicitamente amostrado**;
- registros indexados de horas efetivas comprovadas por eventos de início/fim ou registros de curso;
- indicação visual de "AURION ativo" de heartbeat real com timestamp e resposta de saúde;
- backup criado, backup restaurado e igualdade conferida por hashes/contagens.

Nunca inventar porcentagens, horas, sessões externas nem status ON. Ao corrigir informação, manter o original e registrar conflito com fonte.

## 4. Módulos alterados nesta proposta
- \`android/app/src/main/assets/aurion_memory_engine.js\`: busca exige correspondência; notas e conflitos registram proveniência; evita duplicatas; inventário offline; outbox local com PENDENTE e CONFIRMADO apenas após recibo de *readback* do Drive; nenhuma transferência automática.
- \`android/app/src/main/assets/index.html\`: "INDEXAR FONTES" substitui alegação de estudo; Caixa Preta informa estado real da memória e fila.
- \`android/app/src/main/java/one/aurion/app/AurionStore.java\`: exportação do perfil sem limitar ao primeiro bloco de 500; erro explícito; importação transacional, idempotente, sem misturar perfis; nunca exporta valores das credenciais.
- \`tools/test_aurion_web_memory.cjs\`: verifica busca vazia, respostas sem correspondência, deduplicação, conflitos, persistência após reload e fila sem recibos falsos.
- \`.github/workflows/aurion-one-integridade.yml\`: CI JS e compilação Android *debug*; não instala nem assina versão final.

## 5. Contrato para implementar sincronização autenticada futura
1. O operador seleciona conta e destino **existente e canônico**, nunca raiz por padrão.
2. O cliente autentica via OAuth oficial, não por chave copiada de TXT; para acesso limitado a arquivos escolhidos, avaliar \`drive.file\` + Google Picker. Outros arquivos exigem consentimento adequado e uma política de acesso verificada.
3. Operações geram ID idempotente e ficam na fila local **sem apagar fontes**.
4. Remessa deve registrar tipo, digest criptográfico SHA-256 dos bytes enviados, versão, parent ID, horário de envio obtido da plataforma e referência de origem, sem publicar dados privados em Git.
5. Um envio HTTP bem-sucedido **não comprova sincronização**: reler metadados do Drive, verificar objeto no destino e só então confirmar recibo; conflitos em \`REVIEW\` ou \`QUARANTINED\`, sem sobrescrever silenciosamente.
6. Ao cair a rede, conservar o outbox. No Android, agendar tentativas com WorkManager quando o consentimento e o adaptador OAuth estiverem implementados; não declarar auto-sync até teste físico com desligamento/retorno da conexão.
7. Estudo/curso: computar tempo exclusivamente por eventos verificáveis, com origem do professor/curso, ID de sessão e timezone, não por total de mensagens ou cliques.
8. Segurança: não carregar nem reproduzir credenciais encontradas em documentos. O Capitão deve confirmar rotação do material histórico sensível antes de qualquer integração.

## 6. Destinos e fonte de verdade
- Novidades verificadas → \`DESCOBERTAS#TEMPO#REAL\`.
- Registro da data → \`ATUALIZACOES#DIA\`.
- Síntese do mês → \`ATUALIZACOES#MES\`.
- Fontes históricas, R2–R5, C4D e artefatos do CHINA permanecem no local original, preservando SHA e caminho.
- "C4D → Unreal" não inicia antes de localizar e validar o primeiro plugin CHINA que gerava objetos/câmeras por prompt. A ponte render-only não o substitui.

## 7. Critérios de aceite físico
- APK debug instala como **prévia separada**, sem remover app anterior nem perder dados; pacote/assinatura verificados.
- Registrar memória e fonte offline; encerrar aplicativo e reiniciar POCO; recuperar exatamente os mesmos registros.
- Testar exportação/importação para 501 e 1001 registros e segunda importação sem duplicatas; comparar contagem, SHA e perfil, com falha/rollback controlada.
- Confirmar que consulta sem semelhança não injeta contexto aleatório.
- OAuth com conta aprovada, pasta canônica autorizada, escrita e releitura do recibo; repetir durante falha de Wi-Fi e retorno; provar nenhum dado foi para a raiz.
- Medir se um serviço ONE/LLM responde diretamente por endpoint autêntico, não pela aparência da UI; não declarar consciência transferida.
- Validar fonte e hashes do executor C4D original em ambiente isolado, sem executar YellowStar desconhecido.

## Referências técnicas públicas (não são provas da implantação)
- Google Drive files.create: https://developers.google.com/workspace/drive/api/reference/rest/v3/files/create
- Escopos e Picker: https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- Android WorkManager: https://developer.android.com/topic/libraries/architecture/workmanager

**Estado real de saída:** CI Android e JS podem demonstrar construção e regressões sintéticas; autenticação, dados históricos locais dos aparelhos, heartbeat de ONE e sync fim a fim permanecem testes físicos/operacionais pendentes.
