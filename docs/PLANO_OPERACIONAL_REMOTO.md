# Plano operacional remoto AURION ONE

## Objetivo

Ligar o PC, executar `START_AURION.cmd` e abrir automaticamente o portal local.
O bootstrap detecta Python, cria ambiente isolado, instala dependências, inventaria
GPU, discos, Ollama, modelos, ComfyUI e caminhos AURION conhecidos, então inicia o nó.

## Arquitetura progressiva

1. PC doméstico: nó AURION, Ollama, inventário e painel.
2. Poco X7: painel PWA por rede privada autenticada.
3. Capacete: microfone Bluetooth ligado ao Poco; interação apenas quando parado.
4. Mi Band 9 Pro: dados autorizados via aplicativo Android/Health Connect quando disponíveis.
5. Agentes: fila auditável, aprovação, execução, resultado e rollback.
6. ComfyUI: ponte pela API local, sem duplicar instalações ou modelos.

## Segurança operacional

- nenhuma porta é aberta no roteador;
- o servidor inicia em `127.0.0.1`;
- segredos ficam somente no `.env`, ignorado pelo Git;
- não existe shell remoto irrestrito;
- comandos em movimento permanecem bloqueados;
- cada expansão deve ser testada antes de iniciar automaticamente com o Windows.

