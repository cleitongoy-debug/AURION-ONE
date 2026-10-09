# AURION ONE — PREPARO DO ALMOCO, PC ↔ POCO USB

ESTADO: CODIGO IMPLEMENTADO, TESTE FISICO PENDENTE. Painel original V14 preservado.

1. Extraia pc-package-v3 em pasta SEPARADA, sem misturar com a base canonica ou C4D.

2. Abra Super Studio PC por procedimento conhecido (porta 5060). Verifique no navegador http://127.0.0.1:5060. O iniciador existente pode instalar dependencias e nao foi executado pelo ChatGPT.

3. Com POCO no USB e depuracao autorizada, rode manualmente POCO_CABO_SYNC.cmd. Ele prepara ADB reverse 5060 e 5058, nao instala APK nem abre painéis.

4. No painel PC, SYNC POCO ↔ PC > SOLICITAR SYNC NO POCO e COPIAR TOKEN PRIVADO. Pedido nao transfere dados ate sincronizacao ser iniciada pelo telefone.

5. No APK PREVIA, CONEXOES > SYNC POCO ↔ PC, preencha http://127.0.0.1:5060 e token DO PC, nunca chave de API. Clique SYNC AGORA.

6. Confira recibos em ambos: enviados, excluidos, novos no PC, importados no POCO e readback. Em caso de bloqueio/error, NAO declarar sincronizado.

7. Repita sincronizacao: com dados inalterados deve acrescentar zero novos registros. Modo automatico so se habilita apos o primeiro sync com sucesso, e depende de cabo/PC e agendamento Android sem horario exato.

8. Sem cabo ou PC, SQLite e referencias do POCO continuam. Ollama e painel do PC nao rodam no telefone por este tunel.

ESCOPO: somente registros textuais memory/reference/conversation/project/preset/evidence/sync_event/experiment; sem arquivos, imagens, credenciais ou chats de terceiros.

Segredos suspeitos sao excluidos do envio. Tokens historicos expostos precisam rotacao pelo titular.

PC espelha em _aurion_superstudio/mobile_sync/mirror.sqlite3 dentro da pasta do pacote, nao na raiz Drive.

Limite seguro: 4000 registros e 3MB, erro explicito sem truncamento. Sync Google Drive/ChatGPT NAO implementado aqui.

V14 original na porta 5058 nao foi editado; botao PC esta no Super Studio na porta 5060.

WHATSAPP/LUZ PAUSADO. TESTE FISICO NAO EXECUTADO.

TESTE SINTETICO: python -m unittest discover -s tests -p test_mobile_sync.py -v

PROVAS: PR #41 https://github.com/cleitongoy-debug/AURION-ONE/pull/41

REGISTRO FUTURO: se o teste fisico passar, registrar contagens e recibos no diario ATUALIZACOES#DIA. Nao inventar.