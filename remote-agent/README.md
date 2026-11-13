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


## Ponte Telegram independente para o TITAN

O worker scripts/telegram_titan_bridge.py faz long polling do Telegram no PC e aceita somente o chat autorizado. Não abre porta local, não executa comandos do sistema e não envia e-mails.

Configure no .env local (nunca commitar valores):
- TELEGRAM_BOT_TOKEN: token do bot existente.
- O worker aceita exclusivamente o Chat ID `2028747281`, fixado no código; outros chats são ignorados.
- AURION_TITAN_CHAT_URL: URL completa de /backend/v1/titan/chat (opcional para contingência).
- AURION_TITAN_CACHE_URL: URL completa de /backend/v1/titan/cache.
- AURION_API_KEY: chave de serviço guardada no ambiente local e no servidor; nunca no bundle do navegador.
- TITAN_OLLAMA_URL e TITAN_OLLAMA_MODEL: endpoint e modelo já instalados no Ollama local.

O worker atualiza o cache local a cada 5 minutos enquanto a API está acessível. Se o painel/API cair, ele tenta responder pelo Ollama local com esse cache; se o Ollama também estiver indisponível, devolve um resumo factual do cache e avisa que não fez pesquisa nova. O bot continua recebendo mensagens enquanto o PC e a conexão com Telegram permanecerem ligados.

### Executar manualmente

```powershell
.\.venv\Scripts\python.exe .\scripts\telegram_titan_bridge.py
```

### Inicialização automática no Windows

Depois de configurar o .env, execute uma vez:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_telegram_titan_task.ps1
```

O instalador registra uma tarefa do Agendador do Windows no logon do usuário, com reinício automático após falha. Isso não foi instalado no PC do Capitão por este commit; é um instalador local a executar quando o PC estiver disponível.
