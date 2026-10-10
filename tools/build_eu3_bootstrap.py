#!/usr/bin/env python3
"""Bundle local UI assets; optional private context stays outside source control."""
import argparse,json
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--context',type=Path);a=ap.parse_args()
assets=Path(__file__).resolve().parents[1]/'android/app/src/main/assets'
x=json.loads((a.context or assets/'eu3_context.json').read_text())
assert x['schema']=='aurion-eu3-context-1'
(assets/'eu3_bootstrap.js').write_text('window.AurionEU3Context='+json.dumps(x,ensure_ascii=False)+';\nwindow.AurionEU3Markup='+json.dumps((assets/'eu3_dashboard.html').read_text(),ensure_ascii=False)+';\n')
