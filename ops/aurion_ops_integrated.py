"""Local, read-only operational bridge for Evolution Core 5058.
Never sends secrets; cannot control machines or start services.
"""
import ctypes
import json
import socket
import subprocess
import time
from datetime import datetime, timezone


def _ram():
    if not hasattr(ctypes, 'windll'):
        return None
    class MS(ctypes.Structure):
        _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
    try:
        m = MS(); m.dwLength = ctypes.sizeof(MS)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return int(m.dwMemoryLoad)
    except (AttributeError, OSError):
        pass
    return None


def _port(port):
    try:
        with socket.create_connection(('127.0.0.1', port), 0.32):
            return 'TCP_LISTENING'
    except OSError:
        return 'NO_RESPONSE'


def _cmd(args):
    try:
        r = subprocess.run(args, shell=False, capture_output=True, text=True,
                           timeout=2, encoding='utf-8', errors='replace')
        return (r.returncode, r.stdout[:25000])
    except (OSError, subprocess.TimeoutExpired):
        return (127, '')


def status_snapshot():
    code, out = _cmd(['tailscale', 'status', '--json'])
    tail = {'status': 'NOT_VERIFIED', 'peers': None}
    if code == 0:
        try:
            x = json.loads(out)
            tail = {'status': 'CONNECTED' if x.get('BackendState') == 'Running' else 'NOT_CONNECTED',
                    'peers': len(x.get('Peer', {})) if isinstance(x.get('Peer'), dict) else None}
        except (ValueError, AttributeError):
            pass
    code, out = _cmd(['adb', 'devices'])
    adb = {'status': 'NOT_VERIFIED', 'authorized': None, 'poco_verified': False}
    if code == 0:
        authorized = sum(1 for ln in out.splitlines() if '\tdevice' in ln and ln.rstrip().endswith('device'))
        adb = {'status': 'ANDROID_ADB' if authorized else 'NO_AUTHORIZED_ANDROID',
               'authorized': authorized, 'poco_verified': False}
    return {'measured_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'ram_percent': _ram(),
            'ports': {str(p): _port(p) for p in (5058, 8188, 11434, 8080, 8765, 8777, 8778)},
            'tailscale': tail, 'android': adb, 'mi_band': 'NO_NOTIFY_BRIDGE',
            'accounts': 'NOT_TESTED', 'agents': 'NO_AUTHENTICATED_ACK'}


def library_snapshot(root):
    f = root / 'config' / 'aurion_library_private.json'
    result = {'status': 'NO_CACHE', 'cataloged': None, 'checked': None, 'crossings': None, 'limited': None}
    if not f.is_file():
        return result
    try:
        # Avoid repeatedly parsing a giant catalog: max once a minute or when updated.
        stamp = (str(f), f.stat().st_mtime_ns)
        global _lib_memo
        if _lib_memo and _lib_memo[0] == stamp and time.monotonic() - _lib_memo[1] < 60:
            return dict(_lib_memo[2])
        if f.stat().st_size > 80_000_000:
            return {**result, 'status': 'CACHE_TOO_LARGE'}
        d = json.loads(f.read_text(encoding='utf-8'))
        if not isinstance(d, dict):
            return {**result, 'status': 'CACHE_NOT_OBJECT'}
        result = {'status': 'CACHE_PRESENT', 'cataloged': len(d.get('files', [])),
                  'checked': d.get('checked'), 'crossings': len(d.get('crossings', [])),
                  'limited': bool(d.get('limited'))}
        _lib_memo = (stamp, time.monotonic(), result)
        return dict(result)
    except (OSError, ValueError, TypeError):
        return {**result, 'status': 'CACHE_UNREADABLE'}


_lib_memo = None


def register_ops(app, root, build):
    from flask import jsonify

    @app.get('/api/one/operacional')
    def aurion_ops():
        return jsonify({'ok': True, 'build': build, 'library': library_snapshot(root),
                        'sensors': status_snapshot(), 'read_only': True})