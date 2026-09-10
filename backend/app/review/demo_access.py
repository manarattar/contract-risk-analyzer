"""Short-lived, isolated public demo identities. They never authorize uploads."""
import hashlib
import hmac
import re
import secrets
import time

from fastapi import HTTPException, Request

from app.review.settings import settings
from app.review.store import transaction


def demo_identity(token):
    cfg = settings()
    if not cfg.public_demo_enabled or not token.startswith('demo.'):
        return None
    parts = token.split('.')
    if len(parts) != 4 or not re.fullmatch(r'[a-f0-9]{32}', parts[1]) or not parts[2].isdigit():
        return None
    message = '.'.join(parts[:3])
    signature = hmac.new(cfg.demo_signing_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, parts[3]) or not time.time() < int(parts[2]) <= time.time()+1801:
        return None
    return 'demo-' + parts[1]


def issue_demo(request: Request):
    cfg = settings()
    if not cfg.public_demo_enabled or cfg.mode == 'disabled':
        raise HTTPException(404, 'Public demo is unavailable.')
    # Use the trusted ASGI client address; never trust arbitrary forwarded headers.
    peer = request.client.host if request.client else 'unknown'
    key = 'demo-start-' + hmac.new(cfg.demo_signing_key.encode(), peer.encode(), hashlib.sha256).hexdigest()
    minute = int(time.time()//60)
    with transaction() as conn:
        for identity, limit in [(key, 5), ('demo-start-global', 30)]:
            row = conn.execute('SELECT count FROM rate_limits WHERE principal=? AND minute=?',(identity,minute)).fetchone()
            if row and row[0] >= limit:
                raise HTTPException(429, 'Demo is busy. Please retry in a minute.', headers={'Retry-After':'60'})
            conn.execute('INSERT INTO rate_limits VALUES(?,?,1) ON CONFLICT(principal,minute) DO UPDATE SET count=count+1',(identity,minute))
        total = conn.execute("SELECT count(*) FROM documents WHERE owner LIKE 'demo-%' AND tombstone IS NULL").fetchone()[0]
        if total >= 200:
            raise HTTPException(503, 'Demo capacity reached. Please try later.')
    message = f'demo.{secrets.token_hex(16)}.{int(time.time())+1800}'
    signature = hmac.new(cfg.demo_signing_key.encode(),message.encode(),hashlib.sha256).hexdigest()
    return {'token': message+'.'+signature, 'expires_in':1800}
