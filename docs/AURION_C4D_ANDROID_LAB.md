# AURION Cinema Agent — Android LAB v1.0

Projeto Android independente em `mobile-c4d-agent/`, preservando o APK antigo AURION T8i.

## O que funciona sem PC

- viewport 3D software projetada em Canvas com câmera orbital por toque;
- primitivas: cubo, esfera, cilindro, torus, plano;
- lista de objetos, transformação de posição/escala/rotação e cor;
- gravação da cena JSON no armazenamento WebView do aparelho;
- conversão de cena para scripts Python compatíveis com API do Cinema 4D 2023;
- editor Python, exemplos de objetos/câmera/luz/material;
- notas offline e assistente baseado em regras locais (sem LLM neural);
- salvamento de scripts Python em pasta exclusiva do app.

## O que depende do PC

- modo chat remoto via endpoint AURION ONE existente `/api/prompt` (autenticação por token);
- inventário e status do AURION ONE;
- integração futura com fila aprovada do Cinema 4D em bridge separada; o APK oferece o envio, mas o serviço bridge ainda não está implementado/testado. **Não afirmar que scripts remotos executam.**
- render com plugin OctaneRender válido e compatível no computador.

## O que NÃO está incluído

- binários licenciados Cinema 4D, OctaneRender ou YellowStar;
- Octane/CUDA executável em Android, keygen/cracks, contorno de licenças;
- importação real `.c4d`, rigging/hair, shader Octane, render path traced ou port da aplicação Windows;
- modelo de IA generativa offline; o assistente offline é apenas busca de conhecimento local e regras;
- reprodução de REA dentro do APK: REA é ferramenta distinta de investigação no PC.

## Compilação

`gradle :app:assembleDebug` na pasta `mobile-c4d-agent` com Android SDK 35, Gradle 8.9 e Java 17.

Workflow: `.github/workflows/aurion-c4d-agent-apk.yml` publica artefato `AURION-Cinema-Agent-debug-apk` (APK assinado com chave de debug, não release, uso apenas para testes).

APK usa package `br.com.aurion.c4dagent` e **não substitui** a versão anterior do projeto AURION T8i.

## Pistas verificadas

- GitHub `morluto/rea`: REA analisa aplicações e auxilia reprodução de funcionalidades, não faz conversão automática de executáveis Windows em APK.
- OTOY lista OctaneRender CUDA para Windows/Linux e Octane X para Apple; não existe plugin desktop C4D+Octane Android diretamente compatível.
- Google Drive (14/10/2026): relatórios `RELATORIO_OCTANE_LOCAL` e `AURION_LAB_FUSAO_OCTANE` foram lidos. Relatório contém referência YellowStar.xdl64 bloqueada por malware/spam: não usar esse arquivo.
- Screenshots enviados pelo operador: demonstram projeto `Cinema 4D MVP` no navegador local do autor do vídeo, sem comprovar port do produto oficial.

## QA pendente

- Verificar execução do APK em dispositivo real POCO X7; não declarar instalado sem teste.
- Android GitHub Actions: inspecionar logs/artefato de build.
- Corrigir interface/viewport a partir de vídeo real do teste.
- Para agentes LLM offline reais, criar integração posterior com runtime Android ARM64 (llama.cpp/MLC) e modelo com licença e tamanho adequados.
- Reunir link direto do vídeo Santinello: capturas não informam URL única nem título verificável.

## Segurança

Não expor a API do PC na internet. Android aceita apenas endereços IPv4 privados nos perfis de conexão, com token. Serviços de execução remota exigirão confirmação manual no host. As notas locais ficam no aparelho; nada é enviado automaticamente ao Drive ou ao GitHub.

— Registro de implementação técnica 2026-10-14.
