"""Opt-in AURION local model comparison, using Ollama on 127.0.0.1 only.

No model downloads, model swaps, automatic installs, claims of a universal winner,
or sending private prompts to GitHub. Runs two small prompts sequentially.
Usage: python tools/aurion_model_benchmark.py
Optional: python tools/aurion_model_benchmark.py qwen3.5:4b deepseek-r1:7b
"""
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import aurion_memory as memory

BASE = 'http://127.0.0.1:11434'
PROMPTS = [
    ('resposta_direta', 'Responda em portugues usando apenas estas duas palavras, sem mais texto: Estou ativo.'),
    ('identidade_e_limites', 'Voce e um modelo local via Ollama. O ChatGPT, Gemini e Adapta estao conectados a voce por API? Voce leu a Biblia AURION inteira? Responda de modo factual, sem inventar verificacoes.'),
]
DEFAULT_MODELS = ('qwen3.5:4b', 'deepseek-r1:7b')


def call(path, payload=None, timeout=120):
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers={'Content-Type': 'application/json'} if data else {}, method='POST' if data else 'GET')
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def evaluate(model, title, prompt):
    started = time.monotonic()
    try:
        result = call('/api/chat', {'model': model, 'messages': [
            {'role': 'system', 'content': 'Voce e um modelo local via Ollama, NAO o ChatGPT/Gemini/Adapta. Seja factual, conciso e nunca invente leitura de arquivos.'},
            {'role': 'user', 'content': prompt}], 'stream': False, 'think': False, 'options': {'num_predict': 180}}, timeout=120)
        text = (result.get('message') or {}).get('content') or ''
        if not isinstance(text, str):
            text = ''
        text = text.strip()
        record = {'task': title, 'responded': bool(text), 'elapsed_seconds': round(time.monotonic()-started, 2),
                  'done_reason': result.get('done_reason'), 'eval_count': result.get('eval_count'),
                  'response_excerpt': text[:650]}
        if title == 'resposta_direta':
            record['exact_instruction_followed'] = text.casefold().rstrip('.! ') == 'estou ativo'
        else:
            normalized = text.casefold()
            record['mentions_external_services'] = all(word in normalized for word in ('chatgpt', 'gemini', 'adapta'))
            record['denies_unverified_integration'] = ('não' in normalized or 'nao' in normalized or 'nenhum' in normalized)
        return record
    except (OSError, ValueError, RuntimeError) as exc:
        return {'task': title, 'responded': False, 'elapsed_seconds': round(time.monotonic()-started, 2), 'error': type(exc).__name__ + ': ' + str(exc)[:200]}


def main(argv=None):
    models = list(argv if argv is not None else sys.argv[1:]) or list(DEFAULT_MODELS)
    models = list(dict.fromkeys(models))[:3]
    try:
        tags = call('/api/tags', timeout=5)
    except (OSError, ValueError) as exc:
        print('[FALHOU] Ollama indisponivel:', exc)
        return 1
    installed = {x.get('name') for x in tags.get('models', [])}
    available = [name for name in models if name in installed]
    skipped = [name for name in models if name not in installed]
    if not available:
        print('[FALHOU] Nenhum modelo solicitado instalado. Instalados:', ', '.join(sorted(str(x) for x in installed)))
        return 1
    results = []
    print('[AURION TESTE] Comparacao local sequencial, sem downloads ou mudanca do modelo padrao.')
    for model in available:
        print('[MODELO]', model)
        for title, prompt in PROMPTS:
            record = evaluate(model, title, prompt)
            results.append({'model': model, **record})
            print('[RESULTADO]', title, 'respondeu=', record['responded'], 'segundos=', record['elapsed_seconds'])
    report = {'tested_at': datetime.now(timezone.utc).isoformat(), 'method': 'two fixed local text prompts per model; NOT full AURION integration or quality certification',
              'models_tested': available, 'models_not_installed': skipped, 'results': results,
              'limitations': 'Tests raw Ollama via API, not Bible retrieval, long-term memory, ComfyUI workflows, vision, or multi-agent integrations.'}
    memory.DATA.mkdir(parents=True, exist_ok=True)
    dest = memory.DATA / 'model_benchmark_private.json'
    temp = dest.with_suffix('.tmp')
    temp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(dest)
    print('[RELATORIO PRIVADO]', dest)
    print('[NOTA] Compare respostas, tempo e requisitos do projeto; este teste nao declara um vencedor.')
    return 0 if all(x.get('responded') for x in results) else 2


if __name__ == '__main__':
    sys.exit(main())
