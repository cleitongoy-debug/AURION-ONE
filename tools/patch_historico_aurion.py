"""Idempotent targeted patch; keeps the current mobile panel, auth and tabs intact."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'mobile' / 'aurion-one-live.html'
s = p.read_text(encoding='utf-8')
anchor = '<div class="gauge"><div class="name">Horas de trabalho verificadas</div><div class="value">Sem medição</div><small>Só somar sessões com início/fim comprovados. Uptime e idade do projeto não contam.</small></div>'
replacement = '''<div class="gauge"><div class="name">Horas históricas declaradas · núcleo</div><div class="value">315,7 h</div><small>Snapshot AURION V4 de 12/11/2025; não é telemetria atual nem sessão cronometrada.</small></div><div class="gauge"><div class="name">Ciclos históricos · núcleo</div><div class="value">6.882</div><small>Mesmo snapshot de 12/11/2025. O registro anterior de 4.833 ciclos não deve ser somado.</small></div><div class="gauge"><div class="name">Q-Level histórico</div><div class="value">188,45</div><small>Índice interno do AURION, declarado no snapshot de 12/11/2025; não mede desempenho real de IA.</small></div><div class="gauge"><div class="name">Horas auditadas por sessão</div><div class="value">Sem medição</div><small>Somente sessões com começo e fim demonstrados podem ser acumuladas; horas espelhadas entre operadores não se somam.</small></div>'''
if replacement in s:
    print('PASS: gauge historico ja aplicado; nenhuma mudanca')
elif s.count(anchor) == 1:
    s = s.replace(anchor, replacement)
    source_link = 'https://github.com/cleitongoy-debug/AURION-ONE/blob/main/docs/HISTORICO_QUANTIZACAO_CICLOS_2026-09-19.md'
    marker = '<p id="history-status" role="status" class="muted">Nenhuma consulta histórica executada.</p>'
    assert s.count(marker) == 1, 'Marcador de fonte alterado; abortar sem escrita'
    s = s.replace(marker, '<p class="muted">Os três valores de 2025 são <strong>snapshots históricos declarados</strong>. <a class="btn" href="'+source_link+'">Ver origem, ciclos dos agentes e limites</a></p>'+marker)
    p.write_text(s, encoding='utf-8')
    assert '315,7 h' in p.read_text(encoding='utf-8')
    print('PASS: somente gauges históricos e link de fontes adicionados ao painel')
else:
    raise SystemExit('FAIL: marcador esperado mudou; nenhum arquivo sobrescrito')
