# AURION ONE — Canal do Pulso (POCO → Notify for Xiaomi Pro → Mi Band 9 Pro)
Data documental: 2026-10-09. Linha de trabalho: PR #41, branch `fix/one-memoria-offline-integridade-20261009`.

## Escopo implementado no código (não é teste físico)
- O aplicativo AURION ONE · PRÉVIA cria um canal de notificação Android `aurion_one_pulso_v1`, sem Bluetooth direto ou acesso à conta Notify.
- O operador ativa ou pausa alertas no painel Band; teste de notificação exige permissão Android e opt-in.
- A UI mostra permissão, status Android, último envio e recibo **informado manualmente pelo operador**. Envio ao Android não prova entrega no relógio.
- O aplicativo verifica se `com.mc.xiaomi1` está instalado e abre a instância existente sem instalar, migrar ou mexer em licença.
- O verificador WorkManager existente (aprox. 1 hora, quando houver condições de rede e execução Android) envia alertas ao canal somente em transições detectadas por consulta efetiva: nova versão indicada, mudança de commit, listagem do Drive, índice HF, ou snapshot PC. Não declara sync, estudo ou agente online apenas pela emissão.
- Títulos e conteúdos das notificações vêm de catálogo fixo: **sem nomes de clientes, chaves, ID privados, prompts ou conteúdo de arquivos**.
- ChatGPT tem cronograma documental separado: boletim horário não significa que a plataforma exibiu push Android, nem que Notify entregou no pulso.

## Validação exigida antes de afirmar canal real ativo
1. Instalar APK de **prévia de teste** sem remover o app assinado antigo. Confirmar versão e pacote no Android.
2. Em aparelho parado, abrir **Band → CANAL DO PULSO → ATIVAR CANAL** e autorizar notificações Android.
3. No **Notify for Xiaomi Pro já configurado**, permitir notificações da aplicação **AURION ONE · PRÉVIA**, sem resetar/parear de novo e sem alterar licença.
4. Usar **ENVIAR TESTE AO POCO**. Capturar horário da notificação Android e conferir visualmente na Band 9 Pro. Tocar **CONFIRMEI NO PULSO** apenas se apareceu. Esse clique é RELATO de teste físico, não protocolo ACK BLE.
5. Verificar se o WorkManager executou, qual URL realmente respondeu, qual diferença gerou evento e se notificação espelhou no relógio. Se não houver diferença, não há alerta de mudança.
6. Nunca usar menus, testar respostas ou interagir com telefone/relógio enquanto pilota moto.

## Estado de evidência
CÓDIGO LIDO: integrações Android e UI incluídas na branch da PR #41.
TESTE SINTÉTICO: workflow de testes JS, não equivale a instalação.
TESTE FÍSICO NO POCO / RECEBIMENTO NA BAND: NÃO TESTADO.
CONTAS/SYNC AO VIVO: NÃO CONFIRMADOS.
WhatsApp/LUZ: PAUSADO, fora do escopo.
Fontes públicas oficiais de compatibilidade (não contêm dados pessoais):
https://play.google.com/store/apps/details?id=com.mc.xiaomi1
https://www.mi.com/global/support/faq/details/KA-515561/
