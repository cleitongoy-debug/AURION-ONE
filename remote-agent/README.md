# AURION ONE — Remote Agent Foundation

Primeira base para conectar o PC doméstico ao Poco X7 e, em fases posteriores,
ao microfone Bluetooth e aos dados autorizados da Mi Band 9 Pro.

## Garantias desta fase

- escuta apenas em `127.0.0.1` por padrão;
- exige token nas rotas privadas;
- não oferece shell remoto;
- prompts remotos começam desativados;
- bloqueia comandos quando o telefone informa movimento;
- integra Ollama local sem enviar a Bíblia AURION para serviços externos;
- não registra serviço automático sem decisão explícita do operador.

## Instalação Windows controlada

Abra PowerShell na pasta `remote-agent` e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_windows.ps1
```

Depois, abra `.env`, gere um token longo e defina o modelo já instalado no Ollama.
Para testar localmente:

```powershell
.\.venv\Scripts\python.exe run.py
```

Abra `http://127.0.0.1:8765`.

## Acesso remoto planejado

O serviço continuará ligado ao loopback. O acesso externo deverá passar por
uma rede privada autenticada (por exemplo, VPN mesh), sem encaminhamento de
porta no roteador. A configuração da VPN, inicialização automática e liberação
de prompts serão feitas somente depois do teste local.

## Fases

1. Nó doméstico e Ollama local.
2. Rede privada entre Poco X7 e PC.
3. Painel PWA instalável no Android.
4. Entrada de voz pelo microfone Bluetooth, acionada pelo usuário.
5. Companion Android para Health Connect/Mi Fitness, conforme permissões disponíveis.
6. Fila de trabalhos, aprovações e agentes especializados.
7. Integração ComfyUI e visualização dos resultados no Poco.

O uso durante deslocamento fica limitado a estado passivo; comandos interativos
devem ser feitos quando o usuário estiver parado em local seguro.


## Ponte Telegram para o TITAN (opcional)

O worker `scripts/telegram_titan_bridge.py` faz long polling do Telegram no PC e encaminha mensagens somente do chat autorizado para o endpoint TITAN já existente. Não abre porta local, não executa comandos do sistema e não envia e-mails.

Configure no arquivo `.env` local (nunca commitar valores):
- `TELEGRAM_BOT_TOKEN`: token do bot existente.
- `TELEGRAM_ALLOWED_CHAT_ID`: ID numérico do chat autorizado do Capitão.
- `AURION_TITAN_CHAT_URL`: URL completa de `/backend/v1/titan/chat`.
- `AURION_API_KEY`: chave configurada no servidor TITAN.
- `TITAN_CHAT_MODE`: `CURTO`, `PENSATIVO` ou `PROGRAMADOR`.

Execute com o ambiente virtual ativo:

```powershell
.\\.venv\\Scripts\\python.exe .\\scripts\\telegram_titan_bridge.py
```

O worker persiste o offset de atualizações em `data/telegram_titan_offset.json`, ignora qualquer chat diferente do autorizado e oculta tokens dos logs. Ele só conecta quando as quatro variáveis obrigatórias estão configuradas. A conexão ainda precisa ser validada com o bot e o endpoint reais; o commit não ativa o worker nem configura o serviço de inicialização automática.
