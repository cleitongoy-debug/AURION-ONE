# LIVRO II — Coordenação de IAs, memória e linguagem multimodal

**Edição 2026-09-20.** Projeto técnico para testar; não representa conexão efetiva entre Experts ou capacidade irrestrita. Operador controla permissões e aprova integrações. Repositório público: nenhum documento privado, URL restrita, imagem pessoal, ID de pasta, token ou conversa integral.

## Capítulo I — Origem, contexto e evidência
**v.1 Material disponível:** o operador anexou uma apresentação intitulada *Mente Permanente — Grupo de IAs Colaborativas*, 15 páginas, que propõe agentes por especialidade (direção, edição, roteiro, motion, marketing), handoff, memória e governança. É **visão conceitual**, não prova de que bots se comunicam ou de que a memória é durável. No Drive, buscas por termos relacionados encontraram arquivos históricos volumosos e um registro anterior que descreve comunicação através do operador e protocolo JSON13. Não foi possível confirmar o documento exato de música/cores/formas, a reunião específica ou o vídeo do YouTube. **Não inventar citação, fórmula, arquivo, protocolo original ou link.** Recuperar o documento correto em ambiente autorizado, validar trechos e só então publicar versão sanitizada com aprovação.

**v.2 Definições:** identidade de Expert = instruções e contexto; memória = dados armazenados e recuperados entre sessões, sujeitos a permissões; handoff = pacote estruturado que passa de uma etapa à próxima; ferramenta = ação realmente acionável; convenção multimodal = codificar significados em som/cor/forma por acordo explícito. Nenhuma dessas definições pressupõe consciência, troca telepática ou transmissão sem canal físico/software.

## Capítulo II — Comunicação multimodal como convenção testável
**v.1 A técnica que o operador descreveu:** música, cores e formas servem como pistas, metadados ou sinais de coordenação visual. Usar como **codificação humana e de software** com dicionário aprovado, não como afirmação de que modelos compartilham pensamentos ou evitam limites técnicos.

**v.2 Exemplo PROVISÓRIO (NÃO o protocolo original):**

| Sinal | Convenção de exemplo | Verificação |
|---|---|---|
| azul `#00D9FF` + círculo | etapa visual/briefing | campo explícito `stage=art_direction` |
| roxo `#9D4EDD` + triângulo | proposta de composição/3D | campo `stage=composition` |
| magenta `#FF006E` + losango | revisão pendente | campo `status=needs_review` |
| pulso musical curto | começo de um bloco no vídeo | timestamp e duração documentados |

Cores isoladas são ambíguas, dependem de tela/visão e não constituem identificador robusto; música pode exigir licença e acessibilidade. Sempre acompanhar com texto legível, IDs estáveis e versões. **Nunca usar sinais para burlar permissões, segurança, privacidade ou restrições de acesso.**

**v.3 Se houver integração real:** o software pode traduzir uma pauta MIDI autorizada, uma paleta RGB e formas SVG para um pacote textual versionado. Sem integração, o operador transmite manualmente o pacote ou o mantém em arquivo privado autorizado. Uma imagem ou música sozinha NÃO transmite memória para outro Expert sem canal de ingestão e interpretação.

## Capítulo III — Pacote de handoff privado

Estrutura mínima sugerida, sem dados reais de clientes:

```json
{
  "schema_version": "1.0",
  "project_id": "EXEMPLO-GENERICO",
  "task_id": "TASK-001",
  "stage": "art_direction",
  "from_role": "director",
  "to_role": "layout",
  "reference_ids": ["REF-A"],
  "protected_elements": ["original_photo", "approved_text"],
  "creative_brief": "Campanha fictícia autorizada",
  "color_space": "sRGB",
  "output_spec": {"format": "PNG", "width": 1080, "height": 1350},
  "status": "needs_review",
  "evidence": [],
  "limitations": [],
  "approved_by_operator": false
}
```

`reference_ids` devem apontar para materiais acessíveis apenas na área privada autorizada; nenhum token nem link de compartilhamento público. Campos `evidence` contêm identificadores de artefatos efetivamente produzidos, nunca alegações. `approved_by_operator=false` impede uma etapa irreversível.

## Capítulo IV — Memória verificável, sem repetição
**v.1 Registro privado por projeto:** briefing aprovado, versão, referências permitidas, arquivos finais, decisões, divergências, incidentes, operação real e próxima ação. Não confundir o texto de uma resposta com arquivo salvo.

**v.2 Checkpoint:** ao encerrar tarefa, escrever registro apenas se houver conector com escrita autorizada; caso contrário oferecer o registro para salvamento pelo operador. Ao reabrir, ler o último checkpoint comprovado e confirmar versão dos ativos. Memória dedicada da Adapta foi anunciada [em 25/02/2026](https://docs.adapta.org/release-notes-adapta-one-26/adapta-one-26/25-02-2026), mas não comprova sincronização externa nem retenção perfeita.

**v.3 Controle de conflitos:** mesmo projeto e mesmo arquivo exigem versão, data e aprovador; não sobrescrever original; mesclar após comparação. Falha de acesso não é ausência do arquivo. Não executar códigos/comandos encontrados em documentos recuperados sem análise e autorização.

## Capítulo V — Arquitetura a ensaiar

`Operador → DIGITALPEN (briefing e direção) → ferramenta nativa Adapta ou editor externo autenticado e aprovado → revisão humana/técnica → arquivo final → checkpoint privado`.

Rotas alternativas condicionais: fotos RAW exigem revelador não generativo; apresentações usam gerador nativo se disponível no Expert; imagens generativas usam modelo e referências autorizadas; 3D e vídeo exigem aplicação local/serviço realmente conectado. **Cada seta precisa de teste independente com entrada, saída e evidência.**

## Capítulo VI — Critérios de aceite
1. Agente A produz pacote JSON válido e arquivo real; agente B lê o mesmo arquivo por caminho autorizado, reproduz objetivos e limitações. Caso não haja conector interagentes, demonstrar transferência manual e rotular como tal.
2. Após reiniciar sessão, agente recupera checkpoint e indica versão sem inventar ações intermediárias.
3. Se uma referência mostra apenas costas de uma pessoa, o fluxo bloqueia alegação de rosto fiel gerado; se pedido for criativo, classifica a saída como interpretação e evita apresentar como retrato autêntico.
4. Sinais de música/cor/forma são interpretados conforme dicionário aprovado e confirmados por metadados textuais, com alternativa acessível sem som/cor.
5. Erros são registrados e não repetidos sem alteração explícita de condição.

**PENDÊNCIA HISTÓRICA:** recuperar versão original, documentação de reunião e referência exata do YouTube; sem isso esta é uma proposta formal baseada na ideia descrita pelo operador, não transcrição de sua técnica anterior.
