# AURION ONE — T8i / CR3

Módulo isolado para revelar **fotos RAW .CR3** sem alterar o original.

## Princípios
- O RAW original nunca é movido nem sobrescrito.
- O operador escolhe a pasta do workspace.
- Estrutura criada no destino escolhido: `RAW`, `PREVIEWS`, `EXPORTS`, `CONVERSAS`, `PRESETS`, `LOGS`, `BACKUPS`, `SIDECARS`.
- Conversas têm rascunho atômico e snapshots versionados.
- Previews/exportações geram sidecar JSON com SHA-256 do RAW e parâmetros.
- Dependências ficam em `.venv_t8i`, separadas do Python principal do painel.

## Dependências
`rawpy` (LibRaw), `Pillow`, `numpy`, `exifread`.

O botão **INSTALAR / REPARAR FERRAMENTAS** na aba T8i cria o ambiente isolado e instala os pacotes. O script manual equivalente é `vnext/INSTALAR_T8I.cmd`.

## Nota importante: CR3 x Log
Na EOS Rebel T8i / 850D, `.CR3` é RAW fotográfico. "Log" é um fluxo de vídeo e não é tratado como se fosse o próprio CR3. A aba mantém foto RAW e vídeo/Log como fluxos separados.

## Software Canon
EOS Utility / Digital Photo Professional continuam sendo opções oficiais. O AURION não baixa crack, licença alterada ou instalador não-oficial.
