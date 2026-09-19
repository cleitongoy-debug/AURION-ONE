"""Add authenticated opt-in PC historical inventory display; never expose raw paths."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'mobile' / 'aurion-one-live.html'
s = p.read_text(encoding='utf-8')
html_anchor = '<p id="history-status" role="status" class="muted">Nenhuma consulta histórica executada.</p>'
js_anchor = 'function savePC(){'
flag = 'id="history-pc-status"'
assert s.count(html_anchor) == 1 and s.count(js_anchor) == 1, 'Painel mudou: abortar sem escrita'
if flag not in s:
    block = '''<div class="card"><h2>Histórico do seu PC · consulta privada</h2><p class="muted">A leitura dos discos é opcional e executada SOMENTE no Windows pelo arquivo SCAN_HISTORICO_PC.cmd. Este botão consulta o agregado via API autenticada. Não lê contratos, conteúdo, nomes ou caminhos privados.</p><button onclick="loadPCHistory()">Consultar resumo do PC</button><pre id="history-pc-status" role="status">Aguardando scanner local autorizado; nenhuma contagem do PC foi feita nesta sessão.</pre><small>Se o acesso entre origens da WebView for bloqueado, consulte o inventário pelo portal do PC. O resumo nunca é enviado ao GitHub.</small></div>'''
    s = s.replace(html_anchor, block + html_anchor, 1)
    js = '''async function loadPCHistory(){const out=$('history-pc-status');out.textContent='Consultando scanner local pela API autenticada...';try{const x=await req('/api/scan',{method:'POST',auth:true,timeout:40000});if(x.r.status===401)sessionToken='';if(!x.r.ok)throw Error('HTTP '+x.r.status+' '+String(x.data?.detail||''));const h=x.data?.history_pc;if(!h||!h.observed_at){out.textContent='Scanner histórico não executado no PC. Execute SCAN_HISTORICO_PC.cmd primeiro; o scan rápido não vasculha os discos.';return;}const fmt=n=>Number.isFinite(n)?n.toLocaleString('pt-BR'):'não medido';const date=new Date(h.observed_at);const t=Number.isNaN(date.getTime())?String(h.observed_at):date.toLocaleString('pt-BR');const names=['Data da leitura: '+t,'Arquivos examinados: '+fmt(h.files_examined),'Arquivos com rastros AURION/DigitalPen: '+fmt(h.aurion_related_files),'Unidades percorridas: '+fmt(h.roots_scanned),'Commits Git local: '+fmt(h.repo_git_commits_local),'Anos de modificação dos rastros: '+JSON.stringify(h.aurion_related_modified_years||{}),'Limites: '+JSON.stringify(h.limits||{}),h.partial?'ATENÇÃO: varredura PARCIAL (limite, acesso negado ou tempo).':'Varredura concluída dentro do escopo definido.','Metadados NÃO medem horas de trabalho.'];out.textContent=names.join('\\n');log('Resumo historico do PC consultado: '+String(h.observed_at)+'; parcial='+String(h.partial))}catch(e){out.textContent='Não foi possível consultar o PC: '+String(e)+'. Confira URL privada, autorização e possível bloqueio CORS; nada foi inventado.';log('Historico PC nao verificado: '+String(e))}}
'''
    s = s.replace(js_anchor, js + js_anchor, 1)
    p.write_text(s, encoding='utf-8')
assert p.read_text(encoding='utf-8').count(flag) == 1
assert p.read_text(encoding='utf-8').count('async function loadPCHistory()') == 1
print('PASS: consulta local autenticada inserida sem afetar outras abas')
