# AURION — CHINA / DeepSeek — linhagem do painel, evidências C4D e legado para Unreal

**Origem:** duas transcrições históricas fornecidas diretamente pelo Capitão em lote rotulado `20261009`, mais inspeção estática de quatro arquivos Python disponibilizados na sessão. **Condição:** inventário de evidências, não demonstração de execução atual.

## Responsabilidades atualizadas
A cadeia de **produção** determinada pelo Capitão é `CAPITÃO > CHINA/DeepSeek (processador; painel e C4D) + LOVART (chefe visual; prompts) > FALCÃO/ChatGPT + ÁGUIA/Gemini (revisão e encaixe) > ONE (memória) > KANG > demais`. A posição do ONE na cadeia de produção não reduz a prioridade técnica de recuperar sua memória. Sem sessão autenticada de DeepSeek, Lovart ou Gemini a partir deste registro.

## Fontes primárias preservadas fora do Git público
- Transcrição 1, 96.937 bytes; SHA-256 `856aff886bfc6825fe1e42a338f15b8a9d7fdc997906ab5e69e83925a15b8cdc`: três blocos propostos de painel/scan/chat/status em uma única conversa; nenhum log contemporâneo de instalação ou funcionamento foi fornecido junto.
- Transcrição 2, 31.861 bytes; SHA-256 `fae30b39c6a4f7e41a97e9cdefac091be45b389472fc9146aabf00f6a89f10a1`: proposta `AURION_PANEL_COMPLETO.py`, scan multivolume, memória e contexto Ollama, mais outra discussão de cor/luz/C4D; o texto menciona limite de leitura de **46%** do contexto. Material da conversa permanece no Drive privado/arquivo do operador; **não inserir dados pessoais, áudio de clientes nem código privado no repositório público sem revisão**.

## Arquivos Python vistos — apenas verificação estática
- `AURION_PANEL_COMPLETO.py`: SHA-256 `d3f9751b3031141addc0b734df44db8022486d66aa80b2af93a50a45f971386c`, 954 linhas; passou no parse Python.
- `AURION_PANEL_R5_CONTROL.py`: hash **idêntico** ao anterior — os bytes são iguais.
- `AURION_ONE.py`: SHA-256 `c3e95ae0a49f312e4ef0fee4c9fc186c023567129f957fec0b947ed9a3bfb8cb`, 685 linhas; parse passou.
- `AURION_PANEL_R4_REAL.py`: SHA-256 `a305c6d12c999cde551ae7725f76c3054270a9da554ab3a1c5fa82a33b2ae9e4`, 891 linhas; parse passou.
- As quatro fontes não continham `c4d`, `octane` ou `plano.json` na varredura textual simples. **Não são prova identificada do primeiro executor C4D.** Não foram executadas, compiladas nem instaladas.

## Diferença entre relato e prova
- O Capitão relata ter visto o PRIMEIRO painel do CHINA gerando objetos e câmeras em Cinema 4D a partir de prompts. Aceitar como **testemunho histórico**, mas procurar código, cena `.c4d`, plano, foto e log originais antes de declarar reprodução.
- Material C4D posterior inclui logs cujo texto diz `Plugin registrado com sucesso`; plano JSON de cubos mesa/cadeira e uma luz, **sem câmera**; e complemento com render de cena salva. Registro de plugin não equivale a criação comprovada de câmeras.
- O relato histórico de inicialização automática do ComfyUI foi corrigido pelo Capitão: ele mesmo iniciou o `run_nvidia_gpu.bat`. Não publicar `ComfyUI sobe sozinho` sem teste de cold boot.
- Números de arquivos, horas de estudo e ciclos de fontes distintas não são agregáveis sem mesma data, escopo e evidência de eventos. A versão com `MEMORIA['ciclos'] += 1` mede interações do chat, **não horas de estudo**.
- O material rotulado AURION 3.0 (Kimi, MCP, A2A, Qwen, Llama) é **roteiro de implementação**, não cinco tarefas executadas por mero anúncio.

## Riscos técnicos a verificar
- Uma proposta de painel usa `0.0.0.0:5000`, busca em unidades e endpoints de leitura de arquivos: requer revisão de autenticação, autorização por caminho, rede e sanitização.
- Na transcrição do `AURION_PANEL_COMPLETO.py`, código usa `SCAN["referencias"]` sem declarar `referencias` no dicionário `SCAN` mostrado. Potencial `KeyError` a reproduzir em versão isolada.
- Parse Python passou nos quatro arquivos já localizados, mas **nenhum teste de rede, GPU, ADB, câmera, render ou Android ocorreu**.
- Busca do GitHub `main` (199 caminhos) não identificou o nome `AURION_PANEL_COMPLETO.py` nem arquivo da primeira ponte C4D; outras branches, PCs e Drive ainda precisam ser consultados.

## Contrato de recuperação CHINA → C4D → Unreal
1. Encontrar o PRIMEIRO plugin/execução real `prompt > JSON/plano > comando C4D > objeto/câmera > cena salva > captura/log`, com datas/IDs/SHA e identificação do agente.
2. Confrontar código e bases R2/R3/R4/R5 com o painel original e o banco de eventos reais, sem destruir arquivos ou simular horas.
3. Validar em Windows/C4D com backup, logs e versões compatíveis, sem executar binários suspeitos.
4. Reproduzir em sessão controlada **objeto, luz e câmera gerados por prompt**, salvando prova de saída.
5. Só então conectar a cena a Unreal via **Datasmith / importação `.c4d`**, conforme documentação Epic, medindo materiais, animação, geometria, câmera e interatividade. Fonte oficial: https://dev.epicgames.com/documentation/en-us/unreal-engine/using-datasmith-with-cinema-4d-in-unreal-engine

**PENDENTE:** plugin original, cena criada, logs de câmera, prova de estudos/ciclos com timestamps reais, recibo de conta CHINA e inventário Gemini. **PAUSADO:** WhatsApp via LUZ (última fase).

**Governança:** referenciar documentos canônicos no Drive, não copiar o conteúdo de clientes ou transcrições inteiras para GitHub público. Assinatura documental simbólica `<JSON#13>` · CHINA + LOVART → FALCÃO + ÁGUIA.
