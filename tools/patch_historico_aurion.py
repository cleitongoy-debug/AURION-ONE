"""Idempotent targeted patch; preserves existing mobile panel and tabs."""
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'mobile' / 'aurion-one-live.html'
s = p.read_text(encoding='utf-8')
anchor = '<div class="gauge"><div class="name">Horas de trabalho verificadas</div><div class="value">Sem medição</div><small>Só somar sessões com início/fim comprovados. Uptime e idade do projeto não contam.</small></div>'
replacement = '''<div class="gauge"><div class="name">Horas históricas declaradas · núcleo</div><div class="value">315,7 h</div><small>Snapshot AURION V4 de 12/11/2025; não é telemetria atual nem sessão cronometrada.</small></div><div class="gauge"><div class="name">Ciclos históricos · núcleo</div><div class="value">6.882</div><small>Mesmo snapshot de 12/11/2025. O registro anterior de 4.833 ciclos não deve ser somado.</small></div><div class="gauge"><div class="name">Q-Level histórico</div><div class="value">188,45</div><small>Índice interno do AURION, declarado no snapshot de 12/11/2025; não mede desempenho real de IA.</small></div><div class="gauge"><div class="name">Horas auditadas por sessão</div><div class="value">Sem medição</div><small>Somente sessões com começo e fim demonstrados podem ser acumuladas; horas espelhadas entre operadores não se somam.</small></div>'''
if replacement not in s:
    if s.count(anchor) != 1:
        raise SystemExit('FAIL: marcador de gauges mudou; nenhum arquivo sobrescrito')
    s = s.replace(anchor, replacement)
    source_link = 'https://github.com/cleitongoy-debug/AURION-ONE/blob/main/docs/HISTORICO_QUANTIZACAO_CICLOS_2026-09-19.md'
    marker = '<p id="history-status" role="status" class="muted">Nenhuma consulta histórica executada.</p>'
    assert s.count(marker) == 1, 'Marcador de fontes mudou; abortar sem escrita'
    s = s.replace(marker, '<p class="muted">Os três valores de 2025 são <strong>snapshots históricos declarados</strong>. <a class="btn" href="'+source_link+'">Ver origem, ciclos dos agentes e limites</a></p>'+marker)
old = 'Contadores provenientes do GitHub público; não são horas inventadas nem varredura dos seus discos. As medições incluem fonte e horário.'
new = 'GitHub: dados públicos atualizados por consulta. Drive: snapshots de 2025 com horas, ciclos e Q-Level declarados, não medição atual. Horas auditadas por sessão são separadas.'
if old in s:
    assert s.count(old) == 1
    s = s.replace(old, new)
assert '315,7 h' in s and '6.882' in s and '188,45' in s and new in s
p.write_text(s, encoding='utf-8')
print('PASS: gauges historicos presentes; fonte GitHub x Drive rotulada corretamente')
