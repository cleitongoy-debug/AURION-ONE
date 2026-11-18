# SPYDR · ARANHA ORIGINAL, recuperada por vigia incremental

**Não substitui nem executa o motor AURION_COLETOR.ps1**, pertencente à linhagem do projeto. O motor original encontra-se na branch `feat/eu3-lab-factory-c4d-20261010` do GitHub. Este módulo é uma proteção/observador para impedir a repetição do scan descontrolado de 28/09.

Um clique em `REACENDER_SPYDR.cmd` faz 1 varredura limitada e agenda novas rodadas a cada 15 minutos quando o Windows estiver ligado. A primeira rodada usa somente estas pastas EXISTENTES: `C:\######AGENTE#####STATUS######\#BASE##177#`, `C:\######AGENTE#####STATUS######\##BASE#777`, `C:\AURION`, `C:\AURION-ONE`. Se nenhuma existe, encerra sem escanear discos. Nenhuma raiz será criada.

Executa **somente leitura de metadados de arquivos**, com exclusões para arquivos de credenciais e pastas de sistema, limites de 14.000 arquivos examinados, 3.500 pastas e 45 segundos por rodada. Uma rodada limitada NÃO significa inventário completo. Não coleta conteúdo de documentos, senhas, tokens, IPs, dados da Band ou do POCO. Não executa launchers encontrados, scripts antigos nem programas de clientes.

Consulta `main` e os HEADs dos PRs públicos do repositório do AURION (não só main). Usa GitHub API pública sem chave, comparando SHAs locais a cada rodada. Falha de rede gera `UNREACHABLE`, não `ATIVO`.

Relatórios locais: `%LOCALAPPDATA%\AURION_PRIVATE\SPYDR\RESUMO_ATUAL.json`, `EVENTOS_SPYDR.jsonl` e estados privados. O JSON contém diferenças, categorias e alguns **nomes de arquivo locais**: NÃO ENVIAR o arquivo completo ao GitHub ou às outras contas. Drive Studio somente se a pasta de sincronização autorizada for explicitamente configurada e houver recibo remoto; esta entrega não afirma transferência automática.

O que acontece com os agentes: identificamos um quadro documental (GitHub issue #39/Drive Studio); outras sessões não recebem eventos até seus próprios conectores lerem e registrarem ACK. Nenhuma integração com POCO ou Mi Band foi ativada.

## Comando único

Extraia o ZIP em uma pasta à sua escolha e execute:

```cmd
REACENDER_SPYDR.cmd
```

A SPYDR não muda a porta 5058, não reinicia Flask, Ollama, ComfyUI ou Open WebUI, e não altera o painel original.

Para parar apenas o agendamento, execute `PARAR_AGENDAMENTO_SPYDR.cmd`. Os recibos continuam intactos. Para uma rodada pontual: `REACENDER_SPYDR.cmd -NoSchedule`.