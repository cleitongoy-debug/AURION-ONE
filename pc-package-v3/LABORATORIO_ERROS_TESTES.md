# Laboratório AURION ONE v3

## Correções desta versão

- inicialização não depende apenas do comando `py`;
- instala Python 3.12 via winget quando necessário;
- cria ambiente isolado e executa testes antes de abrir;
- se o painel já estiver ligado, abre a instância existente;
- servidor e erros ficam em `logs` e `_aurion_superstudio/LOGS`;
- gera `CONECTAR_CELULAR.txt` com endereço e token do POCO;
- permite conexão autenticada do aplicativo móvel na mesma rede Wi-Fi;
- painel continua local e não abre portas no roteador.

## Diagnóstico

Se algo falhar, envie os arquivos `logs/startup.log`, `logs/aurion-errors.log` e `_aurion_superstudio/LOGS/server.log`.
