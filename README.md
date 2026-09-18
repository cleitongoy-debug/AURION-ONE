# AURION ONE

Núcleo local do projeto AURION ONE para iniciar o PC, detectar recursos disponíveis
e abrir um portal autenticado conectado ao Ollama.

## Início rápido no Windows

Abra o CMD:

```cmd
cd /d C:\AURION-ONE && git pull && START_AURION.cmd
```

Nas próximas execuções:

```cmd
C:\AURION-ONE\START_AURION.cmd
```

O inicializador:

- detecta Python;
- cria ambiente isolado;
- instala dependências;
- inicia o Ollama quando instalado;
- seleciona um modelo local compatível;
- examina GPU, discos, projetos AURION e ComfyUI;
- gera a autenticação local;
- abre o portal em `http://127.0.0.1:8765`.

## Estrutura

- `START_AURION.cmd`: inicialização única;
- `remote-agent/`: API, portal, scanner e testes;
- `docs/PLANO_OPERACIONAL_REMOTO.md`: evolução PC, Poco X7, microfone e Mi Band;
- `Biblia_da_Inteligencia_Artificial_AURION_ONE.docx`: documento fundador.

Acesso remoto permanece bloqueado até a rede privada e o dispositivo móvel
serem autenticados. Nenhuma porta precisa ser aberta no roteador.
