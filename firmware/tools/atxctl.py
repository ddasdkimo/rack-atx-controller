#!/usr/bin/env python3
"""Reference client for the controller API (PROTOCOL.md). Standard library only.

  export ATX_URL=http://192.168.10.20 ATX_NODE=A ATX_KEY=<64 hex>
  atxctl.py ping | status | heartbeat | lease acquire|renew|release | press <host> power|reset <ms> | log [since]
"""
import hashlib, hmac, json, os, secrets, sys, time, urllib.request, urllib.error

URL = os.environ.get('ATX_URL', 'http://192.168.10.20')
NODE = os.environ.get('ATX_NODE', 'A')
KEY = bytes.fromhex(os.environ.get('ATX_KEY', '00' * 32))
TS_FILE = os.path.expanduser(f'~/.atxctl_ts_{NODE}')


def next_ts():
    """Strictly increasing per node, survives clock steps backwards."""
    last = 0
    try:
        last = int(open(TS_FILE).read().strip() or 0)
    except FileNotFoundError:
        pass
    ts = max(int(time.time()), last + 1)
    with open(TS_FILE, 'w') as f:
        f.write(str(ts))
    return ts


def call(method, path, body=None, auth=True, timeout=20):
    data = json.dumps(body).encode() if body is not None else b''
    req = urllib.request.Request(URL + path, data=data if method == 'POST' else None, method=method)
    req.add_header('Content-Type', 'application/json')
    if auth:
        ts, nonce = str(next_ts()), secrets.token_hex(8)
        p = path.split('?', 1)[0]
        msg = f'{NODE}\n{ts}\n{nonce}\n{method}\n{p}\n'.encode() + data
        sig = hmac.new(KEY, msg, hashlib.sha256).hexdigest()
        for k, v in (('X-Node', NODE), ('X-Ts', ts), ('X-Nonce', nonce), ('X-Sig', sig)):
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b'{}')
        except json.JSONDecodeError:
            return e.code, {}


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == 'ping':
        st, r = call('GET', '/v1/ping', auth=False)
    elif cmd == 'status':
        st, r = call('GET', '/v1/status')
    elif cmd == 'heartbeat':
        st, r = call('POST', '/v1/heartbeat', {'node': NODE})
    elif cmd == 'lease':
        st, r = call('POST', '/v1/lease', {'node': NODE, 'action': argv[2]})
    elif cmd == 'press':
        st, r = call('POST', '/v1/press', {'node': NODE, 'host': int(argv[2]), 'button': argv[3], 'ms': int(argv[4])})
    elif cmd == 'log':
        st, r = call('GET', f'/v1/log?since={argv[2] if len(argv) > 2 else 0}')
    else:
        print(__doc__)
        return 2
    print(st, json.dumps(r, indent=1))
    return 0 if st == 200 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
