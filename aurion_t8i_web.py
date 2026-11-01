# -*- coding: utf-8 -*-
"""Web UI + rotas da aba T8I RAW/CR3 para AURION ONE."""
from __future__ import annotations

from flask import jsonify, request, render_template_string, send_file


PAGE = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AURION ONE · T8I RAW / CR3</title>
<style>
:root{--bg:#07090d;--panel:#11151e;--line:#5a3c2a;--accent:#ff7300;--txt:#fff;--muted:#bfc3cd;--ok:#49d58a;--bad:#ff6277}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#080b10,#050505);color:var(--txt);font:14px Segoe UI,Arial,sans-serif}
header{position:sticky;top:0;z-index:5;display:flex;gap:12px;align-items:center;justify-content:space-between;padding:12px 16px;background:#0b0e13e8;border-bottom:1px solid var(--line);backdrop-filter:blur(10px)}
header b{color:var(--accent);letter-spacing:1px}main{max-width:1500px;margin:auto;padding:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.card{background:linear-gradient(145deg,#161a21,#090b10);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:12px;box-shadow:0 0 16px #0008}.card h3{margin:0 0 10px;color:#fff}.card p,small,label{color:var(--muted)}
input,textarea,select{width:100%;background:#090d14;color:#fff;border:1px solid #493747;border-radius:8px;padding:9px;margin:5px 0}textarea{min-height:90px}
.row{display:flex;gap:8px;align-items:center}.row>*{flex:1}button{background:#281925;color:#fff;border:1px solid #69442f;border-radius:8px;padding:9px 12px;font-weight:700;cursor:pointer;margin:3px}button.primary{background:linear-gradient(100deg,#7d3100,#ff7300);border-color:#ff9a50}.danger{border-color:#a43b42!important}
pre{white-space:pre-wrap;overflow:auto;background:#07090d;border:1px solid #333b48;border-radius:8px;padding:10px;max-height:280px}.chat{height:280px;overflow:auto;background:#07090d;border:1px solid #333b48;border-radius:8px;padding:10px}.msg{padding:8px;margin:6px 0;border-radius:8px}.user{background:#1c1f25}.assistant{background:#15100b;border-left:3px solid var(--accent)}
.preview{display:flex;align-items:center;justify-content:center;min-height:430px;background:#050505;border:1px solid #333b48;border-radius:10px}.preview img{max-width:100%;max-height:72vh;border-radius:8px}
.pill{display:inline-block;padding:3px 8px;border-radius:999px;background:#1b212c;color:#ddd;margin:2px}.on{color:var(--ok)}.off{color:var(--bad)}
@media(max-width:900px){.grid{grid-template-columns:1fr}.row{flex-direction:column;align-items:stretch}}
</style>
</head>
<body>
<header><div><b>AURION#ONE · T8I RAW / CR3</b><div><small>Original preservado · autosave · conversa persistente · snapshots</small></div></div><div><button onclick="location.href='/'">← PAINEL</button><button onclick="status()">DEPENDÊNCIAS</button></div></header>
<main>
<div class="card"><h3>REVELAÇÃO CORRETA DO CR3</h3><p>Na EOS Rebel T8i / EOS 850D, o arquivo .CR3 é RAW de sensor. Esta aba revela RAW para sRGB. Não aplica C-Log/Rec.709 em foto estática.</p><div class="row"><button onclick="status()">VERIFICAR</button><button class="primary" onclick="installDeps()">INSTALAR / CORRIGIR rawpy + Pillow + numpy</button></div><pre id="deps">Aguardando.</pre></div>

<div class="grid">
<div class="card"><h3>1 · PROJETO / DEPÓSITO</h3>
<label>Pasta base</label><div class="row"><input id="base" placeholder="Escolha onde criar a pasta do projeto"><button onclick="pick('base')">ESCOLHER</button></div>
<label>Nome do projeto</label><input id="name" placeholder="Ex.: Ensaio_T8I_Cliente">
<button class="primary" onclick="createWs()">CRIAR / ABRIR PROJETO</button>
<hr style="border-color:#322">
<label>Workspace existente</label><input id="ws" placeholder="Caminho de um projeto T8I já criado">
<div class="row"><button onclick="loadWs()">CARREGAR</button><button onclick="openFolder()">ABRIR PASTA</button><button onclick="snapshot()">SNAPSHOT</button></div>
<pre id="wsinfo">Nenhum projeto carregado.</pre></div>

<div class="card"><h3>2 · ORIGEM DOS CR3</h3>
<label>Pasta das fotos</label><div class="row"><input id="sourceFolder" placeholder="Pasta que contém CR3"><button onclick="pick('source')">ESCOLHER</button></div>
<button onclick="discover()">LOCALIZAR CR3</button>
<label><input id="copyOriginal" type="checkbox" checked style="width:auto"> Copiar original para o projeto antes de trabalhar</label>
<select id="found" size="10" multiple style="min-height:220px"></select>
<div class="row"><button onclick="ingest(false)">IMPORTAR SELECIONADOS</button><button onclick="ingest(true)">IMPORTAR TODOS</button></div>
<pre id="sourceStatus"></pre></div>
</div>

<div class="grid">
<div class="card"><h3>3 · REVELAÇÃO RAW</h3>
<label>Arquivo importado</label><select id="renderSource"></select>
<label>WB</label><select id="wb" onchange="autosave()"><option value="camera">Como capturado · câmera</option><option value="auto">Auto WB</option><option value="daylight">Daylight</option></select>
<label>Exposição EV <b id="exposureLabel">0.0</b></label><input id="exposure" type="range" min="-2" max="3" step="0.1" value="0" oninput="labels();autosave()">
<label>Contraste <b id="contrastLabel">0</b></label><input id="contrast" type="range" min="-100" max="100" value="0" oninput="labels();autosave()">
<label>Saturação <b id="saturationLabel">0</b></label><input id="saturation" type="range" min="-100" max="100" value="0" oninput="labels();autosave()">
<label>Temperatura visual <b id="temperatureLabel">0</b></label><input id="temperature" type="range" min="-100" max="100" value="0" oninput="labels();autosave()">
<label>Tint <b id="tintLabel">0</b></label><input id="tint" type="range" min="-100" max="100" value="0" oninput="labels();autosave()">
<label>Nitidez <b id="sharpnessLabel">0</b></label><input id="sharpness" type="range" min="-100" max="100" value="0" oninput="labels();autosave()">
<div class="row"><select id="format" onchange="autosave()"><option>JPEG</option><option>PNG</option></select><input id="quality" type="number" min="70" max="100" value="92" oninput="autosave()"></div>
<label><input id="half" type="checkbox" checked style="width:auto" onchange="autosave()"> Prévia rápida em meia resolução</label>
<div class="row"><button onclick="saveSettings()">SALVAR AJUSTES</button><button class="primary" onclick="renderRaw()">REVELAR CR3</button></div>
<pre id="renderStatus"></pre></div>

<div class="card"><h3>4 · PRÉVIA + METADADOS</h3><div class="preview"><img id="preview" style="display:none"></div><pre id="metadata">Nenhum revelado ainda.</pre></div>
</div>

<div class="grid">
<div class="card"><h3>5 · AGENTE T8I · TODA CONVERSA SALVA</h3><div id="chat" class="chat">Carregue um projeto.</div>
<textarea id="chatInput" placeholder="Pergunte sobre revelação, seleção, organização ou tratamento"></textarea>
<div class="row"><select id="model"><option value="">Modelo padrão do AURION</option></select><button class="primary" onclick="sendChat()">ENVIAR + SALVAR</button></div></div>

<div class="card"><h3>6 · NOTAS / SALVAMENTO</h3>
<textarea id="note" placeholder="Anotação do ensaio, erro, decisão ou ajuste"></textarea><button onclick="saveNote()">SALVAR NOTA APPEND-ONLY</button>
<textarea id="projectNote" placeholder="Resumo permanente do projeto" oninput="autosave()"></textarea>
<button onclick="saveSettings()">SALVAR AGORA</button>
<pre id="saveStatus"></pre>
<p><span class="pill">manifest.json</span><span class="pill">settings.json</span><span class="pill">files.jsonl</span><span class="pill">conversation.jsonl</span><span class="pill">actions.jsonl</span><span class="pill">snapshots/</span></p>
</div>
</div>
</main>
<script>
var DISCOVERED=[],SAVE_TIMER=null;
function e(v){return String(v==null?'':v).replace(/[&<>"']/g,function(m){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]})}
function ws(){return document.getElementById('ws').value.trim()}
function labels(){['exposure','contrast','saturation','temperature','tint','sharpness'].forEach(function(id){document.getElementById(id+'Label').textContent=document.getElementById(id).value})}
function settings(){return {wb_mode:document.getElementById('wb').value,exposure_ev:Number(document.getElementById('exposure').value),contrast:Number(document.getElementById('contrast').value),saturation:Number(document.getElementById('saturation').value),temperature:Number(document.getElementById('temperature').value),tint:Number(document.getElementById('tint').value),sharpness:Number(document.getElementById('sharpness').value),half_size:document.getElementById('half').checked,output_format:document.getElementById('format').value,jpeg_quality:Number(document.getElementById('quality').value||92),copy_original:document.getElementById('copyOriginal').checked,source_folder:document.getElementById('sourceFolder').value,project_note:document.getElementById('projectNote').value,last_source:document.getElementById('renderSource').value}}
async function status(){try{var d=await (await fetch('/api/one/t8i/status',{cache:'no-store'})).json();document.getElementById('deps').textContent=JSON.stringify(d,null,2)}catch(x){document.getElementById('deps').textContent=String(x)}}
async function installDeps(){if(!confirm('Instalar dependências no mesmo Python do AURION?'))return;document.getElementById('deps').textContent='Instalando...';try{var r=await fetch('/api/one/t8i/dependencies/install',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirm:'INSTALAR_T8I'})});var d=await r.json();document.getElementById('deps').textContent=JSON.stringify(d,null,2)}catch(x){document.getElementById('deps').textContent=String(x)}}
async function pick(kind){var input=document.getElementById(kind==='base'?'base':'sourceFolder');try{var d=await (await fetch('/api/one/t8i/pick-folder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({initial:input.value})})).json();if(d.ok){input.value=d.path;if(kind==='source')autosave()}}catch(x){alert(String(x))}}
async function createWs(){try{var r=await fetch('/api/one/t8i/workspace/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base_dir:document.getElementById('base').value,name:document.getElementById('name').value})});var d=await r.json();if(!r.ok)throw Error(d.error||r.status);document.getElementById('ws').value=d.workspace;localStorage.setItem('aurion_t8i_workspace',d.workspace);applyWs(d)}catch(x){document.getElementById('wsinfo').textContent='ERRO: '+x.message}}
async function loadWs(){if(!ws())return;try{var r=await fetch('/api/one/t8i/workspace?path='+encodeURIComponent(ws()),{cache:'no-store'});var d=await r.json();if(!r.ok)throw Error(d.error||r.status);localStorage.setItem('aurion_t8i_workspace',d.workspace);applyWs(d)}catch(x){document.getElementById('wsinfo').textContent='ERRO: '+x.message}}
function applyWs(d){document.getElementById('wsinfo').textContent=JSON.stringify({workspace:d.workspace,manifest:d.manifest,paths:d.paths,originais:d.originals.length,previews:d.previews.length,conversas:d.conversations.length},null,2);var s=d.settings||{};if(s.wb_mode)document.getElementById('wb').value=s.wb_mode;[['exposure','exposure_ev'],['contrast','contrast'],['saturation','saturation'],['temperature','temperature'],['tint','tint'],['sharpness','sharpness'],['quality','jpeg_quality']].forEach(function(p){if(s[p[1]]!==undefined)document.getElementById(p[0]).value=s[p[1]]});if(s.output_format)document.getElementById('format').value=s.output_format;document.getElementById('half').checked=s.half_size!==false;document.getElementById('copyOriginal').checked=s.copy_original!==false;if(s.source_folder)document.getElementById('sourceFolder').value=s.source_folder;if(s.project_note!==undefined)document.getElementById('projectNote').value=s.project_note;labels();var rs=document.getElementById('renderSource');rs.innerHTML=(d.originals||[]).filter(function(x){return x.extension==='.cr3'||x.extension==='.cr2'}).map(function(x){return '<option value="'+e(x.path)+'">'+e(x.name)+'</option>'}).join('');var chat=document.getElementById('chat');chat.innerHTML=(d.conversations||[]).map(function(x){return '<div class="msg '+(x.role==='user'?'user':'assistant')+'"><b>'+e((x.role||'').toUpperCase())+'</b><br>'+e(x.text)+'</div>'}).join('')||'Nenhuma conversa salva ainda.';chat.scrollTop=chat.scrollHeight;loadModels()}
async function discover(){document.getElementById('sourceStatus').textContent='Procurando CR3...';try{var r=await fetch('/api/one/t8i/discover',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({folder:document.getElementById('sourceFolder').value,max_files:1200})});var d=await r.json();if(!r.ok)throw Error(d.error||r.status);DISCOVERED=d.files||[];document.getElementById('found').innerHTML=DISCOVERED.map(function(x,i){return '<option value="'+i+'">'+e(x.name+' · '+x.path)+'</option>'}).join('');document.getElementById('sourceStatus').textContent=JSON.stringify({encontrados:DISCOVERED.length,limite:d.truncated,erros:d.errors},null,2);autosave()}catch(x){document.getElementById('sourceStatus').textContent='ERRO: '+x.message}}
async function ingest(all){if(!ws())return alert('Crie ou carregue o projeto primeiro.');var sel=document.getElementById('found');var ids=all?DISCOVERED.map(function(_,i){return i}):Array.from(sel.selectedOptions).map(function(o){return Number(o.value)});var files=ids.map(function(i){return DISCOVERED[i]&&DISCOVERED[i].path}).filter(Boolean);if(!files.length)return alert('Selecione CR3.');document.getElementById('sourceStatus').textContent='Importando + SHA-256...';try{var r=await fetch('/api/one/t8i/ingest',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workspace:ws(),files:files,copy_original:document.getElementById('copyOriginal').checked})});var d=await r.json();document.getElementById('sourceStatus').textContent=JSON.stringify(d,null,2);await loadWs()}catch(x){document.getElementById('sourceStatus').textContent='ERRO: '+x.message}}
async function saveSettings(){if(!ws())return;try{var r=await fetch('/api/one/t8i/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workspace:ws(),settings:settings()})});var d=await r.json();document.getElementById('saveStatus').textContent=r.ok?'Salvo em disco.':'Falha: '+(d.error||r.status)}catch(x){document.getElementById('saveStatus').textContent=String(x)}}
function autosave(){clearTimeout(SAVE_TIMER);SAVE_TIMER=setTimeout(saveSettings,700)}
async function renderRaw(){var src=document.getElementById('renderSource').value;if(!ws()||!src)return alert('Selecione um CR3 importado.');document.getElementById('renderStatus').textContent='Revelando RAW...';await saveSettings();try{var r=await fetch('/api/one/t8i/render',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workspace:ws(),source:src,settings:settings()})});var d=await r.json();if(!r.ok)throw Error(d.error||r.status);document.getElementById('renderStatus').textContent='OK · '+d.width+'x'+d.height+' · '+d.sha256;document.getElementById('metadata').textContent=JSON.stringify(d.raw_metadata,null,2);var img=document.getElementById('preview');img.src='/api/one/t8i/artifact?workspace='+encodeURIComponent(ws())+'&rel='+encodeURIComponent(d.relative_preview)+'&v='+Date.now();img.style.display='block';await loadWs()}catch(x){document.getElementById('renderStatus').textContent='ERRO: '+x.message}}
async function appendConversation(role,text,model,kind){var r=await fetch('/api/one/t8i/conversation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workspace:ws(),role:role,text:text,model:model,kind:kind})});var d=await r.json();if(!r.ok)throw Error(d.error||r.status);return d}
async function sendChat(){var input=document.getElementById('chatInput'),msg=input.value.trim();if(!msg||!ws())return;var model=document.getElementById('model').value,chat=document.getElementById('chat');input.value='';chat.innerHTML+='<div class="msg user"><b>VOCÊ</b><br>'+e(msg)+'</div><div class="msg assistant">AURION: processando...</div>';chat.scrollTop=chat.scrollHeight;try{await appendConversation('user',msg,model,'chat');var r=await fetch('/api/one/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg,model:model})});var d=await r.json();chat.lastElementChild.remove();if(!r.ok)throw Error(d.reply||d.error||r.status);chat.innerHTML+='<div class="msg assistant"><b>AURION · '+e(d.model||'agente')+'</b><br>'+e(d.reply)+'</div>';await appendConversation('assistant',d.reply,d.model||model,'chat')}catch(x){if(chat.lastElementChild&&chat.lastElementChild.textContent.indexOf('processando')>=0)chat.lastElementChild.remove();chat.innerHTML+='<div class="msg assistant">ERRO: '+e(x.message||x)+'</div>';try{await appendConversation('system','ERRO: '+String(x.message||x),model,'error')}catch(_){}}chat.scrollTop=chat.scrollHeight}
async function saveNote(){var n=document.getElementById('note'),v=n.value.trim();if(!v||!ws())return;try{await appendConversation('user',v,null,'note');n.value='';document.getElementById('saveStatus').textContent='Nota anexada ao conversation.jsonl.';await loadWs()}catch(x){document.getElementById('saveStatus').textContent='Falha: '+x.message}}
async function snapshot(){if(!ws())return;try{var d=await (await fetch('/api/one/t8i/snapshot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workspace:ws(),label:'manual'})})).json();document.getElementById('saveStatus').textContent=d.ok?'Snapshot: '+d.snapshot:'Falha: '+d.error}catch(x){document.getElementById('saveStatus').textContent=String(x)}}
async function openFolder(){if(!ws())return;try{var d=await (await fetch('/api/one/t8i/open-folder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workspace:ws()})})).json();if(!d.ok)alert(d.error||'Falha')}catch(x){alert(String(x))}}
async function loadModels(){try{var d=await (await fetch('/api/one/nodes',{cache:'no-store'})).json();var s=document.getElementById('model');s.innerHTML='<option value="">Modelo padrão do AURION</option>'+(d.ollama_models||[]).map(function(x){return '<option value="'+e(x)+'">'+e(x)+'</option>'}).join('')}catch(_){}}
status();labels();loadModels();var remembered=localStorage.getItem('aurion_t8i_workspace');if(remembered){document.getElementById('ws').value=remembered;loadWs()}
</script>
</body></html>"""


def register_t8i(app, logger=None):
    import aurion_t8i_lab as t8i

    def _log(message, error=False):
        if logger:
            try:
                logger(message, error)
            except Exception:
                pass

    @app.get("/t8i")
    def t8i_page():
        return render_template_string(PAGE)

    @app.get("/api/one/t8i/status")
    def t8i_status():
        return jsonify({"ok": True, "dependencies": t8i.dependency_status()})

    @app.post("/api/one/t8i/dependencies/install")
    def t8i_install():
        data = request.get_json(silent=True) or {}
        if str(data.get("confirm", "")) != "INSTALAR_T8I":
            return jsonify({"ok": False, "error": "Confirmação exigida: INSTALAR_T8I"}), 409
        result = t8i.install_dependencies()
        _log("T8I dependencias: " + ("OK" if result.get("ok") else "FALHA"), not result.get("ok"))
        return jsonify(result), (200 if result.get("ok") else 500)

    @app.post("/api/one/t8i/pick-folder")
    def t8i_pick_folder():
        data = request.get_json(silent=True) or {}
        return jsonify(t8i.pick_directory(str(data.get("initial", ""))))

    @app.post("/api/one/t8i/workspace/create")
    def t8i_workspace_create():
        data = request.get_json(silent=True) or {}
        try:
            return jsonify(t8i.create_workspace(str(data.get("base_dir", "")), str(data.get("name", ""))))
        except Exception as exc:
            _log("T8I workspace: " + str(exc), True)
            return jsonify({"ok": False, "error": str(exc)[:1000]}), 400

    @app.get("/api/one/t8i/workspace")
    def t8i_workspace_get():
        try:
            return jsonify(t8i.load_workspace(str(request.args.get("path", ""))))
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)[:1000]}), 400

    @app.post("/api/one/t8i/discover")
    def t8i_discover():
        data = request.get_json(silent=True) or {}
        try:
            return jsonify(t8i.discover_cr3(str(data.get("folder", "")), int(data.get("max_files", 1200))))
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)[:1000]}), 400

    @app.post("/api/one/t8i/ingest")
    def t8i_ingest():
        data = request.get_json(silent=True) or {}
        files = data.get("files", [])
        if not isinstance(files, list):
            return jsonify({"ok": False, "error": "files deve ser lista"}), 400
        try:
            return jsonify(t8i.ingest_files(str(data.get("workspace", "")), files, bool(data.get("copy_original", True))))
        except Exception as exc:
            _log("T8I ingest: " + str(exc), True)
            return jsonify({"ok": False, "error": str(exc)[:1000]}), 400

    @app.post("/api/one/t8i/render")
    def t8i_render():
        data = request.get_json(silent=True) or {}
        try:
            settings = data.get("settings") if isinstance(data.get("settings"), dict) else {}
            return jsonify(t8i.render_preview(str(data.get("workspace", "")), str(data.get("source", "")), settings))
        except Exception as exc:
            _log("T8I render: " + str(exc), True)
            return jsonify({"ok": False, "error": str(exc)[:1200]}), 400

    @app.post("/api/one/t8i/settings")
    def t8i_settings():
        data = request.get_json(silent=True) or {}
        try:
            settings = data.get("settings") if isinstance(data.get("settings"), dict) else {}
            return jsonify(t8i.save_settings(str(data.get("workspace", "")), settings))
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)[:1000]}), 400

    @app.post("/api/one/t8i/conversation")
    def t8i_conversation():
        data = request.get_json(silent=True) or {}
        try:
            return jsonify(t8i.save_conversation(
                str(data.get("workspace", "")),
                str(data.get("role", "user")),
                str(data.get("text", "")),
                data.get("model"),
                str(data.get("kind", "chat")),
            ))
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)[:1000]}), 400

    @app.post("/api/one/t8i/snapshot")
    def t8i_snapshot():
        data = request.get_json(silent=True) or {}
        try:
            return jsonify(t8i.snapshot_workspace(str(data.get("workspace", "")), str(data.get("label", "manual"))))
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)[:1000]}), 400

    @app.post("/api/one/t8i/open-folder")
    def t8i_open_folder():
        data = request.get_json(silent=True) or {}
        try:
            result = t8i.open_workspace(str(data.get("workspace", "")))
            return jsonify(result), (200 if result.get("ok") else 500)
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)[:1000]}), 400

    @app.get("/api/one/t8i/artifact")
    def t8i_artifact():
        try:
            path = t8i.artifact_path(str(request.args.get("workspace", "")), str(request.args.get("rel", "")))
            return send_file(path)
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)[:1000]}), 404

    return app
