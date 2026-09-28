# AURION T8i · Quantum Photo Studio — Android v0.1
Primeira build mobile independente. Fluxo funcional: importar imagem via Storage Access Framework, preview responsivo, ajustes não destrutivos de exposição/contraste/saturação, AUTO conservador e entrega JPEG/PNG/WebP. A base visual usa a paleta Quantum recuperada do projeto T8i.

## Limites desta build
CR3/RAW avançado ainda é preservado/detectado, mas o decoder LibRaw não está embarcado nesta primeira build. Exportação atual parte do bitmap original carregado; a aplicação definitiva dos ajustes no arquivo exportado entra no núcleo de processamento seguinte.
