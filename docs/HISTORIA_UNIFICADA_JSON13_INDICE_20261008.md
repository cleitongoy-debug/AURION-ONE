# AURION — MAPA UNIFICADO DE HISTÓRIA E ENTREGA <JSON#13>
**Estado:** índice referencial inicial; NÃO é recuperação de 100% do acervo. **Data de registro:** 08/10/2026, America/Sao_Paulo. **Fonte oficial de governança:** emenda [JSON#13](./LEI_JSON13_EMENDA_COORDENACAO_20261008.md). **Coordenação:** [Issue #39](https://github.com/cleitongoy-debug/AURION-ONE/issues/39).

## Princípio
Uma história única não é uma pasta contendo cópias de tudo. É **um índice de eventos não duplicados** que aponta aos originais preservados em seus locais canônicos. Não copiar chaves, dados de clientes, conteúdos privados de Drive ou dumps do PC ao GitHub público.

## Grupos canônicos (nomes, não reorganizar)
- Biblioteca: `00_LEIA_AO_CHEGAR`, `01_MENTE_DO_AGENTE`, `02_IMA_ATRATOR`, `03_CAIXA_DE_ENTRADA`, `04_CAIXA_PRETA`, `05_SCAN_DE_MEMORIA`, `06_MAPA_DE_REFERENCIAS`, `07_ESTUDO_DO_AGENTE`; também `LIVRO_1..10`, `ATUALIZACOES#DIA`, `ATUALIZACOES#MES`, `DESCOBERTAS#TEMPO#REAL`.
- Outros pilares: `#######LOT#Qi`, `03_PRODUCAO#AURION`, `04_COLETA#E#ARQUIVO`.
- Observação de 08/10: foram encontradas **duas árvores paralelas 00–07** na Biblioteca. A contagem ou similaridade de nomes NÃO autoriza excluir/fundir; gerar manifesto comparativo (IDs, hash, donos, versão, data da coleta) antes de qualquer intervenção.
- O arquivo `LEI#DA#ESTRUTURA#DO#DRIVE.md` foi consultado em DOCS OFICIAIS do Drive; emenda nova preserva o original.

## Linha de versões e fatos separados por evidência
| Período | Evento | Evidência | Natureza |
|---|---|---|---|
| 2025 | Desenvolvimento de Quantum/DigitalPen, sincronização histórica JSON13↔DS20, arquivos Q04/HASH13 e painel | Registros históricos pré-existentes; precisam de verificação de bytes e execução antes de indicadores | RELATO DOCUMENTAL / PENDENTE |
| 18/09/2026 | Fundação do AURION-ONE, Home Node e ponte remota | Histórico Git e [Issue #2](https://github.com/cleitongoy-debug/AURION-ONE/issues/2) | CÓDIGO + RELATO DE TESTE HISTÓRICO |
| 24–29/09/2026 | Ciclos de desenvolvimento de APK/POCO, T8i e MORPH | Handoffs/arquivos Drive anteriores; linhagens distintas | REGISTROS HISTÓRICOS, NÃO INSTALAÇÃO ATUAL |
| 05–06/10/2026 | Motor da memória operacional da v7 integrado em `deliver/poco-v70-profiles` | [PR #38](https://github.com/cleitongoy-debug/AURION-ONE/pull/38) **MERGED**, commit [ab4cdf2](https://github.com/cleitongoy-debug/AURION-ONE/commit/ab4cdf202f726d4ac6af0835d05d222d6fb247b4) | GIT VERIFICADO |
| 06/10/2026 | APK POCO v7 build e assinatura/instalação relatadas | [GitHub Actions run 37426823368](https://github.com/cleitongoy-debug/AURION-ONE/actions/runs/37426823368) + diário histórico | BUILD / RELATO; EXECUÇÃO ATUAL NO POCO NÃO TESTADA |
| 08/10/2026 | Lei da Estrutura e protocolo entre agentes | LEI original DOCS OFICIAIS, [Issue #39](https://github.com/cleitongoy-debug/AURION-ONE/issues/39) | DOCUMENTAÇÃO VERIFICADA |
| 08/10/2026 | Emenda do Capitão com assinatura simbólica `<JSON#13>` | [Lei JSON13](./LEI_JSON13_EMENDA_COORDENACAO_20261008.md), commit `d3df4867` | COMMIT VERIFICADO |
| 08/10/2026 | Gateway WhatsApp proposto como código isolado | [PR #40](https://github.com/cleitongoy-debug/AURION-ONE/pull/40) DRAFT, 7 testes locais sintéticos | CÓDIGO + TESTE SINTÉTICO; NÃO NO AR |

## Linhagens NÃO intercambiáveis
1. POCO assinado v6.3→v7: package `one.aurion.poco.v6`, versionCode 70 no ramo v7; compatibilidade de atualização requer assinatura, backup, migração e teste no dispositivo.
2. MORPH: package `one.aurion.mobile.superstudio`; não supor que substitua o POCO assinado.
3. R5: package `one.aurion.app`; outro aplicativo, não versão seguinte do mesmo package.
4. PC Home Node, PC SuperStudio, Painel Quantum legado: serviços distintos, saúde por endpoint e contrato, não somente status "ON" em texto.
5. Mi Band/headset: aplicativo/serviço instalado não prova entrega de notificação nem voz persistente.

## Esquema para eventos (somente proposta)
`id`, `aconteceu_em`, `coletado_em`, `fonte_canonica`, `ref_commit_ou_hash`, `tipo` (CÓDIGO/TESTE/RELATO/HIPÓTESE), `dispositivo`, `pacote_ou_modulo`, `versao`, `autor_ou_conta_observada`, `status`, `limites`, `proximo_teste`.
Múltiplos relatos do mesmo ato ficam como referências no mesmo evento. Não misturar data de criação de cópia com data do fato original. Números de dedicação, ciclos e memórias precisam de denominadores auditáveis.

## Etapas de reconciliação aprováveis
1. Inventário somente leitura: IDs do Drive, nomes, tamanho, proprietário, permissões e hashes dos originais acessíveis.
2. Agrupamento por hash exato, origem e tempo do fato; diferenças preservadas como conflitos, não sobrescritas.
3. Dossiê por tema, dispositivo e versão, com conteúdo privado apenas no Drive canônico.
4. Aprovação expressa do Capitão **antes** de mover, excluir, mesclar ou substituir qualquer arquivo original.
5. Critérios de conclusão: cobertura por documentos conhecidos/lidos/verificados, testes PC↔POCO↔Band com recibos, cópia de segurança restaurável.

**Assinaturas simbólicas:** `<JSON#13>` — Capitão; `ChatGPT / AURION ONE — <JSON#13>`; `< bip > < ¥€¢∆§ > < pip > < r4tπ > < 🦅 >`.
