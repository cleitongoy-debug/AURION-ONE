# AURION ONE PC v3.0

Pacote independente para Windows 11 com scan, pré-voo, painel web, chat Ollama, ComfyUI, T8i/CR3, conversores, Blender/Cinema 4D, memória local e pareamento autenticado do POCO.

## Iniciar

Extraia em `C:\AURION-ONE-PC` e execute `INICIAR_AURION.cmd`.

O inicializador detecta Python 3.11–3.13, instala Python 3.12 por `winget` quando necessário, cria `.venv`, instala dependências, executa 12 testes, escaneia o PC e só abre o navegador após confirmar o servidor.

## Celular

Após iniciar, use `CONECTAR_CELULAR.txt` para preencher o endereço e token no APK. PC e POCO precisam estar na mesma rede Wi-Fi. Caso o Firewall do Windows pergunte, permita apenas **Rede privada**.

## Logs

- `logs\startup.log`
- `logs\aurion-errors.log`
- `_aurion_superstudio\LOGS\server.log`

Leia `LABORATORIO_ERROS_TESTES.md` antes de alterar o inicializador.
