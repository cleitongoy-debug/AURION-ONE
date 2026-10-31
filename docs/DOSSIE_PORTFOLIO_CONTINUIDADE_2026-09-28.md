# AURION ONE — continuidade do Dossiê / Portfólio profissional

Data: 2026-09-28  
Branch: `feat/dossie-portfolio-v31`

## Objetivo

Transformar a Seção 8 do dossiê formal em uma área real do APK sem misturar dados privados de clientes e sem inventar horas, certificados ou conclusões.

## Fonte

Documento-base: **ONG DIGITALPEN · REGISTRO DE CAPACIDADES TÉCNICAS E AUDITORIA DE HORAS**, elaborado em 28/09/2026.

## Implementação

- novo asset `portfolio_dossie.json` com:
  - perfil profissional;
  - métricas auditadas por blocos independentes;
  - 3 cursos com percentuais registrados e horas totais nulas;
  - 10 capacidades profissionais;
  - 8 projetos catalogados;
  - 3 grupos de pendências probatórias;
  - regras de prova.
- nova tela Android `AurionPortfolio.show()`;
- novo botão **Portfólio** no menu principal;
- cartão de Portfólio no dashboard;
- atalhos da tela para **Estudos** e **Clientes**;
- botão para copiar resumo comercial sem valores de clientes.

## Regras preservadas

1. Não converter 58%/50%/52% em horas.
2. Não somar horas do sistema com horas do operador.
3. Não publicar valores/status financeiros de clientes no módulo de portfólio.
4. Não marcar professor/curso/certificado como confirmado quando ainda está pendente.
5. Certificados futuros: preservar original + SHA-256.
6. A tela é leitura estruturada do dossiê; registros vivos continuam nas áreas Estudos/Clientes/Depósitos.

## Próxima evolução

- anexar certificados e evidências por hash;
- vincular projetos a arquivos de prova;
- modo cliente exportável;
- gerar página web pública a partir do mesmo JSON sem expor dados privados.
