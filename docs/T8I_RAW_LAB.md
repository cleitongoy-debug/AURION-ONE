# AURION ONE · ABA T8I RAW / CR3

## Objetivo

A aba **T8I RAW / CR3** transforma a área de fotografia do painel em um laboratório persistente para arquivos Canon RAW. Ela não altera o CR3 original.

A Canon documenta a EOS 850D / Rebel T8i gravando RAW como **.CR3** e recomenda o Digital Photo Professional para processamento RAW. No AURION a leitura local usa **rawpy/LibRaw**, mantendo o original separado do JPEG/PNG derivado.

> Importante: foto CR3 da T8i é RAW de sensor, não C-Log. C-Log/Rec.709 é um fluxo de vídeo diferente.

## Estrutura de cada projeto

```text
Projeto_T8I/
├── .aurion_t8i/
│   ├── manifest.json
│   ├── settings.json
│   └── files.jsonl
├── originals/
├── previews/
├── exports/
├── metadata/
├── conversations/
│   └── conversation.jsonl
├── logs/
│   └── actions.jsonl
└── snapshots/
```

Características:

- seleção de pasta pelo Windows;
- criação do projeto onde o operador escolher;
- scan limitado a CR3/CR2 na pasta escolhida;
- cópia opcional dos originais para `originals/`;
- SHA-256 no ingresso;
- revelado RAW para sRGB;
- exposição, balanço de branco, contraste, saturação, temperatura visual, tint e nitidez;
- sidecar JSON para cada revelado;
- conversa do agente e notas em JSONL append-only;
- snapshots manuais;
- autosave dos ajustes;
- botão para abrir a pasta física do projeto;
- nenhuma rota de exclusão.

## Dependências

Núcleo:

```text
rawpy
numpy
Pillow
```

O botão **INSTALAR/CORRIGIR DEPENDÊNCIAS** usa o mesmo Python que executa o AURION e não substitui arquivos do painel.

ExifTool é opcional. Se estiver no PATH, metadados EXIF adicionais entram no sidecar; sem ele o revelado continua funcionando com os metadados oferecidos pelo LibRaw.

## Teste de aceite

1. Abrir a aba T8I.
2. Escolher uma pasta base.
3. Criar um projeto.
4. Escolher a pasta das fotos.
5. Localizar CR3.
6. Importar/copy original.
7. Revelar o arquivo.
8. Conferir JPEG/PNG em `previews/`.
9. Salvar nota e conversar com o agente.
10. Reabrir o projeto e confirmar que ajustes, arquivos, conversas e snapshots continuam disponíveis.

## Segurança de dados

- CR3 original nunca é sobrescrito.
- Escritas JSON usam troca atômica.
- Conversas e índices são append-only.
- Não há botão de apagar.
- Ações são registradas em `logs/actions.jsonl`.
