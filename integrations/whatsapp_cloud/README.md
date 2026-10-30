# AURION WhatsApp Cloud Gateway — TESTE / NÃO IMPLANTADO

Protocolo <JSON#13>. Gateway de webhook da [Meta WhatsApp Business Platform](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api), sem comandos remotos, instalado somente depois de autorização do Capitão.

## Estado
- Código em branch de proposta; não foi executado no PC do operador nem associado a WABA.
- Testes locais offline cobrem desafio GET, HMAC SHA-256 da assinatura POST, rejeição de JSON inválido e corpos excessivos, allowlist/opt-in, comandos restritos e idempotência SQLite.
- A aplicação inicia vinculada a `127.0.0.1:8780`; **nenhuma exposição à Internet** sem reverse proxy HTTPS de confiança.
- Respostas automáticas **desligadas por padrão**. Apenas mensagens recebidas de contatos explicitamente permitidos; comandos aceitos: `status` e `ajuda`. O comando `status` não inventa telemetria do PC.
- NÃO acessar arquivos do operador, WhatsApp pessoal, GitHub, Drive ou executar comando remoto. Nenhum token embutido no código.

## Como testar sem qualquer conta/custo
```powershell
cd integrations\whatsapp_cloud
python -m unittest -v test_gateway.py
```

## Para ativar com consentimento do Capitão
1. Criar/confirmar **Meta Business Portfolio**, **WhatsApp Business Account (WABA)** e número comercial de propriedade do operador, avaliando se a associação afetará o WhatsApp existente. A validação/registro usa fluxo oficial da Meta.
2. Obter o App Secret, Verify Token escolhido, Phone Number ID, Access Token com permissões adequadas e versão Graph atual na conta oficial. **Nunca copiar valores para GitHub, chats ou Drive**. Guardar apenas em variáveis de ambiente/gestor de segredos, com acesso mínimo.
3. Definir variáveis no ambiente de execução sem registrar os valores em scripts compartilhados: `AURION_WA_VERIFY_TOKEN`, `AURION_WA_APP_SECRET`, `AURION_WA_DB`. Quando autorizado e testado, configurar também `AURION_WA_ACCESS_TOKEN`, `AURION_WA_PHONE_NUMBER_ID`, `AURION_WA_GRAPH_VERSION`, `AURION_WA_ALLOWED_CONTACTS` em formato somente dígitos, e só então `AURION_WA_ENABLE_REPLIES=true`.
4. Executar `python gateway.py` em ambiente isolado. O processo local responde em `GET /health` e `GET /webhook` (handshake), `POST /webhook` (assinatura HMAC). Expor **somente** `/webhook` por um proxy/túnel HTTPS com limitação de tráfego e logs redigidos; não abrir porta no roteador.
5. Configurar webhook público no painel Meta e assinar eventos `messages`. Fazer teste de entrada com o número autorizado e validar o recibo **na Meta**; o servidor responde somente aos comandos permitidos. Verificar orçamento e políticas da Meta antes de habilitar saída.
6. Só depois integrar um adaptador autenticado ao painel AURION, sempre sem ações destrutivas via mensagens.

## Limites P0 para produção
- A versão inicial envia resposta **sincronamente** no webhook; precisa de fila durável de envio, retentativas limitadas e métricas para suportar falha da API Meta. O registro de mensagem recebida ocorre antes da entrega de resposta e pode não reenviar após falha — **não usar em produção antes de corrigir**.
- Ainda faltam testes de integração ponta a ponta, TLS/host público, credenciais válidas, custos, retenção de dados e runbook.
- Receber um webhook válido não é autorização para enviar mensagens proativas. Respeitar opt-in, janela de atendimento, templates e descadastro conforme política oficial da Meta: https://business.whatsapp.com/policy/preview?lang=pt_BR
- Não confundir o bot com controle de PC, voz do capacete, APK ou Mi Band; essas conexões dependem de etapas independentes verificáveis.

**Assinaturas simbólicas:** <JSON#13> | ChatGPT / AURION ONE — <JSON#13> | < bip > < ¥€¢∆§ > < pip > < r4tπ > < 🦅 >
