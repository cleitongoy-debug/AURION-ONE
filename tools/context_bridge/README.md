# AURION ONE — Context Bridge (revisão, não instalação)

Código experimental **somente local** para indexar fragmentos do ecossistema sem mover originais nem enviar documentos a nuvens ou IAs automaticamente. Origem da correção: no blueprint AURION DYNAMIC V5 recebido em 17/10, o exemplo `ler_contexto()` usava `f.read(300)`, por isso não lia integralmente os documentos citados.

## Execução no Windows quando houver autorização e operador parado

```powershell
py -3 tools/context_bridge/index_local.py --root "D:\\AURION_SYNC" --output "C:\\AURION_PRIVATE\\context_index"
```

**Substitua os exemplos pelos caminhos realmente existentes e privados do seu PC.** O padrão coleta apenas metadados e hashes dos arquivos elegíveis; nenhuma saída é escrita nos originais. Os arquivos `manifest.jsonl` e `report.json` ficam **privados** e reportam explicitamente o escopo percorrido. Não representa inventário automático dos dois PCs, telefones, Band ou Drive inteiro. Não habilite o script sobre a unidade C:\ inteira sem revisar o escopo.

Para gerar `chunks_privados.jsonl` em disco local, inclua `--include-text` explicitamente. **Não publique ou sincronize automaticamente esse arquivo**: os fragmentos podem conter informações sensíveis mesmo com filtro de nomes. Para PDFs legíveis como texto, instale `pypdf` somente no ambiente isolado de teste; PDF só imagem é marcado pendente de OCR. O filtro não é um mecanismo de proteção perfeito.

Testes offline e sintéticos:
```powershell
py -3 -m unittest discover -s tools/context_bridge/tests -v
```

Valida hash/deduplicação, escolha explícita para conteúdo, rejeição de saída em pasta de entrada e preservação de originais. Passar nos testes NÃO confirma Tailscale, APK instalado ou qualquer canal remoto.

## PC ↔ POCO ↔ headset ↔ Notify/Band — fronteira de evidência

O nó em `remote-agent/aurion_remote/app.py` já fornece `/health`, `/api/status`, `/api/device` e `/api/prompt`. Em `remote-agent/aurion_remote/config.py`, ele **escuta `127.0.0.1:8765` por padrão**, exige token em rotas privadas e bloqueia prompts remotos por padrão. Ter Tailscale ligado NÃO prova acesso HTTP do POCO a um servidor que só escuta loopback.

Roteiro seguro do próximo teste, só quando alguém puder fazê-lo parado: primeiro observar `tailscale status` local sem expor IPs/tokens em logs; verificar `http://127.0.0.1:8765/health` no PC; só então estabelecer ponte em rede privada com autenticação comprovada e verificar do POCO `/health` mais chamada autenticada a `/api/status`. Um recibo real deve conter `event_id`, origem, horário com fuso, latência medida no dispositivo se aplicável, `ack` e desfecho. Nenhuma abertura de porta pública, serviço Tailscale Serve ou mudança de bind é feita por este PR.

**Headset:** entrada/saída áudio depende de pareamento Android, permissão de microfone e reconhecimento de voz; não foi testada. **Notify for Xiaomi Pro / Mi Band 9 Pro:** entrega ao pulso depende de permissões, encaminhamento de notificações e recibo observado; e-mail recebido no navegador ≠ push no POCO ≠ notificação na Band. Enquanto o usuário se desloca, usar somente acompanhamento passivo — nenhum pedido de confirmação manual, comando interativo de direção ou teste da Band.

## Três vias, registros e limites

1. **Interface/dispositivos:** PC/POCO/headset/Band, status `NÃO TESTADO` até recibo real da ponta.
2. **Memória Drive Studio:** leis + `MASTER_INDEX`/`AGENTS_STATUS`; `ATUALIZACOES#DIA`, `ATUALIZACOES#MES`, `DESCOBERTAS#TEMPO#REAL`. Deduplicação por `event_id`, nenhuma alteração estrutural ou de raiz.
3. **Engenharia GitHub:** issue #39 contém coordenação e histórico sanitizado. Nunca enviar endereços de Tailscale, tokens, dados pessoais, imagens privadas nem chunks à issue pública.

Fontes: `docs/PROTOCOLO_PASSAGEM_DE_TURNO_IA.md` e `docs/PLANO_OPERACIONAL_REMOTO.md`; <https://github.com/cleitongoy-debug/AURION-ONE/issues/39>. O recibo cruzado do ONE existe no Drive, mas não comprova sincronização automática instantânea entre plataformas.

**Estado desta branch:** testes sintéticos preparados; runtime dos PCs, Tailscale, APK, Notify/Band e comunicação por voz **não executados** aqui. Não mesclar/instalar sem revisão do fluxo de privacidade e testes em ambiente isolado.
