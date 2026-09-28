# AURION ONE — coletor local do PC

Coloque **AURION_COLETOR.bat** e **AURION_COLETOR.ps1** juntos em:

`C:\Users\ADM_PESS\Desktop\painelseguro#1 - Copia`

Abra o BAT com dois cliques e escolha **1**. Ele varre os discos prontos do PC, unidades externas e de rede acessíveis pelo Windows. Não move, apaga nem altera os arquivos de origem. Não exige acesso de administrador. Cada rodada para em 25 minutos ou 20.000 arquivos novos/alterados; rode novamente para continuar. O resultado fica em `AURION_COLETA\NOME-DO-PC` ao lado do BAT. A pasta é local e pode conter nomes de arquivo e trechos pessoais: não publique nem suba ao Git.

No menu **2**, adicione quantos links públicos quiser de Drive, GitHub, Hugging Face, portfólio e redes; os 12 campos iniciais se expandem. O menu **3** confere disponibilidade HTTPS, mas **não baixa nem lê os conteúdos remotos**. Links privados precisam de um conector autorizado posteriormente. Não ponha tokens nem senhas nos links. O menu **4** abre o JSON onde você pode definir `extra_roots`, limites e `profile_roots` dos quatro perfis. Por padrão toda autoria fica `UNASSIGNED`; nomes de pasta apenas geram pistas. Ao confirmar as raízes de ANARK, DS, DAVI e SPECTRA, o próximo ciclo atribui novos arquivos desses caminhos. Não coloque dados dos quatro na mesma raiz de perfil.

O menu **6** cria tarefa local a cada 15 minutos; o **7** a remove. A execução simultânea é bloqueada. Pode deixar agendar para depois do primeiro teste. Não há envio automático ao Drive, Git ou a um servidor. A varredura contabiliza arquivos e pistas, mas **não converte data de arquivo nem percentual de curso em horas estudadas**. Horas comprovadas dependem de registro de sessões, material do curso e evidência identificada. O inventário de chaves registra só nome/caminho/metadados das credenciais reconhecidas; nunca o valor nem o hash delas. Trechos de outros arquivos recebem filtro de linhas de credenciais, mas revise os relatórios antes de compartilhar.

Saídas principais: `RESUMO_ATUAL.json`, `ARQUIVOS.jsonl`, `TRECHOS_E_PISTAS.jsonl`, `CHAVES_INVENTARIO.jsonl`, `CRUZAMENTOS_DUPLICATAS.json`, `REPOSITORIOS_LOCAIS.json`, `PROGRAMAS_INSTALADOS.json`, `SERVICOS_E_PROCESSOS.json`, `ERROS_WINDOWS_7_DIAS.json`, `LINKS_ESTADO.json`. O índice JSONL guarda histórico de versões; `RESUMO_ATUAL.json` mostra a última rodada. Copie o pacote inteiro se quiser usar no segundo PC; cada PC grava em sua própria subpasta pelo nome da máquina.
