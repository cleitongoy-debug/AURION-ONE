#!/usr/bin/env python3
"""Build-time additive patch for Mobile Fixo v2.0.0. Run from android/.

The tracked original index.html and MainActivity.java on main are NOT overwritten
in Git; this script edits the isolated checkout only. It fails closed if anchors
change instead of guessing or silently producing a broken APK.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'app/src/main/assets'
HTML = ASSETS / 'index.html'
JAVA = ROOT / 'app/src/main/java/one/aurion/app/MainActivity.java'
EDITOR = ASSETS / 't8i.html'
BRIDGE = ROOT / 'app/src/main/java/one/aurion/app/T8iBridge.java'


def checked_replace(s, old, new, label):
    if new in s:
        return s
    if s.count(old) != 1:
        raise RuntimeError(f'{label}: expected exactly one anchor, got {s.count(old)}')
    return s.replace(old, new, 1)


def main():
    assert EDITOR.is_file() and BRIDGE.is_file(), 'Editor/bridge missing'
    html = HTML.read_text(encoding='utf-8')
    java = JAVA.read_text(encoding='utf-8')
    pattern = re.compile(r'<section id="t8i" class="page">.*?(?=<section id="agent" class="page">)', re.S)
    replacement = '''<section id="t8i" class="page"><div class="card"><h1>Canon T8i · Oficina fotográfica</h1><p>RAW intacto, edição em prévia, LUT, receitas e pasta de entrega escolhida no Android.</p><button class="primary" onclick="location.href='t8i.html'">ABRIR OFICINA T8i DENTRO DO APK</button><p class="muted">CR3: apenas prévia incorporada se disponível; revelação RAW completa exige ferramenta compatível no PC.</p></div></section>\n\n'''
    if 'ABRIR OFICINA T8i DENTRO DO APK' not in html:
        if len(pattern.findall(html)) != 1:
            raise RuntimeError('T8i section anchors changed; refusing to patch')
        html = pattern.sub(lambda _m: replacement, html, count=1)
    java = checked_replace(java, '    private WebView web;', '    private WebView web;\n    private T8iBridge t8iBridge;', 'bridge field')
    java = checked_replace(java,
        '        web.addJavascriptInterface(new Bridge(), "AurionAndroid");',
        '        web.addJavascriptInterface(new Bridge(), "AurionAndroid");\n        t8iBridge = new T8iBridge(this, web);\n        web.addJavascriptInterface(t8iBridge, "AurionT8i");', 'bridge register')
    java = checked_replace(java,
        '        super.onActivityResult(request, result, data);',
        '        super.onActivityResult(request, result, data);\n        if (t8iBridge != null && t8iBridge.onActivityResult(request, result, data)) return;', 'bridge result')
    java = checked_replace(java,
        '        web.setWebViewClient(new WebViewClient() {\n',
        '        web.setWebViewClient(new WebViewClient() {\n'
        '            @Override public void onPageStarted(WebView v, String url, android.graphics.Bitmap favicon) {\n'
        '                if (t8iBridge != null) t8iBridge.setEditorActive("file:///android_asset/t8i.html".equals(url));\n'
        '            }\n'
        '            @Override public void onPageFinished(WebView v, String url) {\n'
        '                if (t8iBridge != null) t8iBridge.setEditorActive("file:///android_asset/t8i.html".equals(url));\n'
        '            }\n', 'bridge page scope')
    if '--check' in sys.argv:
        print('T8i patch anchors OK; dry run only')
        return
    backups = ROOT / 'build/t8i-prepatch'
    backups.mkdir(parents=True, exist_ok=True)
    if not (backups / 'index.html').exists():
        (backups / 'index.html').write_bytes(HTML.read_bytes())
    if not (backups / 'MainActivity.java').exists():
        (backups / 'MainActivity.java').write_bytes(JAVA.read_bytes())
    HTML.write_text(html, encoding='utf-8')
    JAVA.write_text(java, encoding='utf-8')
    print('T8i injected into existing APK; original sources backed up under android/build/t8i-prepatch')


if __name__ == '__main__':
    main()
