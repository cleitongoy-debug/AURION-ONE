# AURION ONE PC v3.0

Pacote independente para Windows 11 com scan, pré-voo, painel web, chat Ollama, ComfyUI, T8i/CR3, conversores, Blender/Cinema 4D, memória local e pareamento autenticado do POCO.

## Iniciar

Extraia na Área de Trabalho. O ZIP cria `AURION_ONE_PC_v3`; execute o `INICIAR_AURION.cmd` somente dentro dessa pasta nova. Não misture com `painelseguro#1 - Copia`.

O inicializador detecta Python 3.11–3.13, instala Python 3.12 por `winget` quando necessário, cria `.venv`, instala dependências, valida os arquivos, escaneia o PC e só abre o navegador após confirmar o servidor. Se a porta 5060 estiver ocupada por uma versão antiga, usa automaticamente 5061–5069.

## Celular

Após iniciar, use `CONECTAR_CELULAR.txt` para preencher o endereço e token no APK. PC e POCO precisam estar na mesma rede Wi-Fi. Caso o Firewall do Windows pergunte, permita apenas **Rede privada**.

## Logs

- `logs\startup.log`
- `logs\aurion-errors.log`
- `_aurion_superstudio\LOGS\server.log`

Leia `LABORATORIO_ERROS_TESTES.md` antes de alterar o inicializador.
