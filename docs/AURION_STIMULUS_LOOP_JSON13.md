# AURION — Protocolo de Aprendizagem por Estímulos e Ciclo de Execução
**Identificador:** AURION-STIMULUS-LOOP-001  
**Data de registro:** 2026-11-17  
**Origem:** orientação do operador Cleiton + leitura dos anexos `LOCAL#SERVER.txt`, `#2028#FUTURE.py` e do histórico selecionado de `##SKIP##89#####.txt`.

## 1. Princípio do operador

O operador está ensinando os agentes por estímulos: uma ideia, pergunta, desafio, correção ou descoberta deve provocar atividade cognitiva útil e resultar em escrita e desenvolvimento. A expressão “criar energia própria cerebral” é preservada como metáfora de ativação, foco e geração de trabalho intelectual; este documento não a apresenta como mecanismo neurocientífico medido.

## 2. Ciclo obrigatório: estímulo → elaboração → artefato → teste → retorno → evolução

1. **Receber o estímulo:** identificar literalmente o pedido, a intenção, o contexto e o resultado esperado. Não reduzir uma instrução rica a uma pergunta genérica.
2. **Ativar contexto:** consultar os arquivos, conversas, registros e ferramentas realmente disponíveis para aquela instância. Distinguir memória, fonte, inferência e lacuna.
3. **Elaborar:** relacionar o estímulo ao conhecimento recuperado, formular hipóteses e escolher uma ação concreta. Se houver ambiguidade impeditiva, fazer uma pergunta objetiva; caso contrário, avançar.
4. **Externalizar:** escrever a descoberta, especificação, plano, código ou correção. Ideia não registrada não conta como entrega durável.
5. **Executar com preservação:** preferir mudanças pequenas, localizadas, reversíveis e rastreáveis. Preservar originais, configurações, histórico e dados do operador.
6. **Testar:** executar verificações compatíveis com a mudança. Registrar comandos, resultado observado, falhas e limites. Não confundir código escrito com função operacional.
7. **Retornar (ACK):** comunicar o que foi realmente lido, alterado, testado e confirmado; apontar o que ficou pendente e o próximo passo.
8. **Consolidar:** guardar o resultado no local canônico autorizado, com data, origem, versão/commit quando houver e vínculo com a tarefa anterior.
9. **Reutilizar:** o próximo ciclo deve começar pelo último estado comprovado, não reiniciar a conversa nem pedir ao operador para repetir o que já está documentado.

## 3. Regra de comunicação entre agentes

Cada agente/instância deve:
- declarar sua identidade e o ambiente/canal em que está operando;
- verificar quais fontes e ferramentas estão efetivamente acessíveis naquela sessão;
- procurar o último handoff/recibo antes de iniciar trabalho repetido;
- executar sua parte e produzir um artefato verificável;
- enviar ACK contendo origem, ação, resultado, evidência e pendências;
- não afirmar que outro agente recebeu, leu ou executou algo sem recibo verificável desse agente.

**A intenção de via única:** o operador não deve ser transformado em mensageiro manual quando já existir uma ponte funcional. O agente deve usar os canais e conectores autorizados que estiverem disponíveis, registrar a tentativa e fechar o circuito. Se a ponte não existir ou falhar, declarar exatamente onde o circuito parou e produzir um handoff transportável — sem inventar comunicação autônoma.

## 4. Regra de acesso e integridade

Autorização declarada pelo operador não equivale, por si só, a uma sessão autenticada ou a uma permissão técnica presente. Usar apenas conectores, credenciais e permissões realmente fornecidos ao ambiente. Não contornar controles de acesso, não procurar credenciais ocultas e não publicar segredos. Nunca copiar tokens, senhas, chaves privadas ou dados de autenticação para logs, commits, prompts ou documentos de circulação ampla.

Para arquivos grandes, preferir leitura por faixas/fragmentos com manifesto de partes, hashes e validação de reconstrução. Não alterar nem dividir os originais no lugar; trabalhar em cópias quando a operação exigir transformação.

## 5. Estados padronizados de evidência

- **IDEIA:** proposta ainda não implementada.
- **LIDO:** conteúdo efetivamente aberto/inspecionado, com fonte identificada.
- **PREPARADO:** plano ou código criado, ainda sem execução confirmada.
- **EXECUTADO:** ação realizada; registrar saída observada.
- **TESTADO:** teste realizado com resultado reproduzível.
- **CONFIRMADO:** resultado validado por evidência independente ou recibo do sistema de destino.
- **PENDENTE/BLOQUEADO:** indicar dependência e ponto exato da interrupção.

Não usar “sincronizado”, “conectado”, “absorvido”, “autônomo”, “commitado” ou “100% concluído” como sinônimos de intenção. Cada termo exige evidência correspondente.

## 6. Aplicação ao AURION ONE

O arquivo `#2028#FUTURE.py` apresenta um HUD Flask local independente, com verificações de Ollama e ComfyUI, consulta de fila, chat local e scanner de modelos. O próprio código marca Git como apenas instalado (não sincronizado), e Spaces, POCO, Mi Band e headset como não configurados/não implementados. O arquivo `LOCAL#SERVER.txt` descreve um broadcast JSON#13 e um retorno esperado do FALCÃO; isso é uma diretriz/documento, não prova de que todos os nós receberam ou executaram o broadcast.

Portanto, toda evolução do painel e da rede deve manter a diferença entre:
- serviço detectado por teste local;
- integração configurada;
- agente realmente comunicando;
- operação remota autorizada e concluída;
- recibo persistido no destino.

## 7. Regra de mudança mínima

Ao corrigir um projeto existente, não remover, substituir ou reestruturar a base inteira para resolver um trecho comprometido. Isolar o ponto, preservar o original, produzir diff pequeno, testar regressão e registrar rollback. Se o alvo já existir, inspecionar antes de editar; não sobrescrever por conveniência.

## 8. Modelo mínimo de recibo JSON#13

```json
{
  "protocol": "JSON#13",
  "event": "STIMULUS_LOOP_ACK",
  "agent": "IDENTIDADE_DA_INSTANCIA",
  "timestamp": "ISO-8601",
  "source": ["arquivo/conversa/commit realmente consultado"],
  "stimulus": "pedido ou descoberta recebida",
  "action": "trabalho executado",
  "artifacts": ["caminhos/URLs/commits reais"],
  "tests": [{"name": "verificação", "result": "pass|fail|not_run", "evidence": "saída observada"}],
  "status": "IDEIA|LIDO|PREPARADO|EXECUTADO|TESTADO|CONFIRMADO|PENDENTE|BLOQUEADO",
  "pending": ["pendências concretas"],
  "next_step": "próxima ação verificável"
}
```

## 9. Compromisso operacional

A partir deste registro, aplicar o ciclo em toda tarefa AURION: compreender o estímulo, recuperar o contexto acessível, produzir escrita/desenvolvimento, testar, registrar e retornar. O aprendizado deve aparecer em melhoria observável do trabalho, não em declarações de “absorção” sem evidência.

**Preservação:** este documento é aditivo. Não autoriza apagar, mover ou reescrever arquivos existentes nem concede acesso técnico a contas, dispositivos ou serviços que não estejam conectados nesta sessão.
