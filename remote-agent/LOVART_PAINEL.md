# AURION ONE — Lovart + Instagram (catalogação visual, sem custo)

## Entrega

Este PR adiciona uma seção **LOVART · CHEFE VISUAL** no painel HTML existente em `/`, e uma rota FastAPI `GET /api/lovart` protegida pelo **mesmo token AURION** das demais rotas privadas. A seção lê um pequeno manifesto de **referências** criado localmente — nenhum login no Lovart, Instagram ou Metricool é iniciado pelo servidor.

- **Não** acessa crédito Lovart; não gera imagens; não publica posts; não varre discos; não lê segredos.
- Referências do portfólio público: https://www.instagram.com/studio.digitalpen/
- Reel indicado pelo operador: https://www.instagram.com/reel/DQtWsnngHsz/ (conteúdo do vídeo ainda não auditado).
- Projeto Lovart identificado por screenshot: `velho#amigo`. Propriedade de sessão e assets originais não aferidas por API.
- Atalho de análise externa: https://app.metricool.com/brands/connections?blogId=7488584 (brand retornou **sem redes sociais conectadas** na consulta de 17/10/2026). A ligação de Instagram requer consentimento e autenticação pelo titular, não é realizada por este projeto.

## Teste local (PC parado, no repositório já existente)

**Não rode o launcher legado MORPH** que escuta em todas as interfaces. Esta mudança é direcionada ao `remote-agent` FastAPI, cujo `AURION_BIND_HOST` padrão é `127.0.0.1`.

1. Após revisar o código e obter a branch/PR no repositório, abra `remote-agent`.
2. Copie `remote-agent/data/lovart_manifest.example.json` para `remote-agent/data/lovart_manifest.json` (**somente no PC**); o arquivo local real está ignorado pelo Git em `remote-agent/.gitignore`.
3. Edite somente títulos, tipo e URLs HTTPS públicos de referências autorizadas. Não adicione tokens, nomes privados de clientes ou caminhos de disco de terceiros. Exemplo:

```json
{
  "instagram_profile": "https://www.instagram.com/studio.digitalpen/",
  "assets": [
    {
      "title": "Portfólio Studio DigitalPen",
      "url": "https://www.instagram.com/studio.digitalpen/",
      "kind": "portfolio",
      "source": "operador"
    },
    {
      "title": "Reel informado pelo operador",
      "url": "https://www.instagram.com/reel/DQtWsnngHsz/",
      "kind": "reel",
      "source": "operador"
    }
  ]
}
```

4. Inicie o serviço **somente se já estiver configurado** pelo procedimento seguro em `remote-agent/README.md`, mantendo autenticação e loopback. Abra `http://127.0.0.1:8765/`; entre com token existente e clique em **Consultar acervo visual**.
5. Se não houver manifesto, a seção exibirá `manifest_missing`, zero itens e **API Lovart NÃO CONECTADA / API Instagram NÃO CONECTADA**.
6. A execução desse PR no GitHub Actions é teste sintético: não liga a rede do computador real nem audita a conta do Lovart.

## Política de segurança

O manifesto máximo é 512 KB e 100 itens. O servidor só usa campos públicos `title`, `kind`, `url`, `source`. Links HTTP, localhost, credenciais em URLs e parâmetros de query são rejeitados/removidos para não divulgar links de sessão. A página só usa `textContent` ao renderizar referências, não interpola HTML dinâmico. É proibido inserir tokens, arquivos de clientes, fotos particulares ou chaves no manifesto versionado.

A Meta/Metricool não estão conectados por este código. Para dados reais de métricas e publicações, o dono deverá ligar o perfil profissional do Instagram na conexão Metricool, sem passar login para o AURION. As duas fontes de métricas não devem ser tratadas como iguais: o Instagram público pode ser visto, a API da conta requer autorização.

## Provas

- Unit tests: `cd remote-agent && python -m pytest -q tests/test_lovart_catalog.py tests/test_app.py`
- GitHub workflow: `.github/workflows/lovart-panel-tests.yml`.
- Entrega real ao usuário = branch de código, PR e CI; **implantação no PC/POCO/Notify/Band NÃO efetuada**.
