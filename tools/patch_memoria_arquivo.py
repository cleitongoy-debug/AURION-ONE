"""Adds archival aggregate examples, explicitly non-additive and non-live."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'mobile'/'aurion-one-live.html'
s=p.read_text(encoding='utf-8')
anchor='<p class="muted">Os três valores de 2025 são <strong>snapshots históricos declarados</strong>.'
flag='id="memoria-arquivo-v1"'
assert s.count(anchor)==1, 'Historico mudou; abortar sem escrita'
if flag not in s:
    block='''<div class="card" id="memoria-arquivo-v1"><h2>Arquivo de memória · outros marcos antigos</h2><p class="muted">A coletânea histórica preservada até novembro/2025 repete muitos textos e snapshots; NÃO somamos repetições, valores incompatíveis nem versões de momentos diferentes.</p><div class="gauges"><div class="gauge"><div class="name">Horas nominais dos agentes · registro antigo</div><div class="value">206,68 h</div><small>Total declarado num trecho da memória, não tempo humano, não atual e NÃO adicional às 315,7 h do núcleo.</small></div><div class="gauge"><div class="name">Ciclos · registro antigo</div><div class="value">308</div><small>Snapshot do DigitalPen com ciclo interno de 5 minutos mencionado; não combinar com os 4.833/6.882 de outra configuração.</small></div><div class="gauge"><div class="name">Descobertas · registro antigo</div><div class="value">107</div><small>Contador declarativo em trecho da coletânea; não são entregas comprovadas individualmente.</small></div><div class="gauge"><div class="name">Quantum Level do sistema · registro antigo</div><div class="value">2,23</div><small>Índice interno de escala diferente do Q-Level 188,45; não somar, comparar ou converter.</small></div></div><p class="muted">Fonte: arquivo histórico consolidado do Drive; trechos podem ter sido copiados repetidamente e não têm timestamp inequívoco de cada medição. <a class="btn" href="https://github.com/cleitongoy-debug/AURION-ONE/blob/main/docs/CRUZAMENTO_RASTROS_HISTORICOS_2026-09-19.md">Ver método de deduplicação</a></p></div>'''
    s=s.replace(anchor,block+anchor,1)
    p.write_text(s,encoding='utf-8')
assert p.read_text(encoding='utf-8').count(flag)==1
print('PASS: dados adicionais do arquivo inseridos uma vez, sem somar snapshots')
