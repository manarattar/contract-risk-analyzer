import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.review.settings import settings
from app.review.store import transaction, now

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    id: str
    workspace_id: str
    role: str
    demo: bool = False
    display_name: str | None = None


def resolve_principal(token):
    if not 32 <= len(token) <= 512:
        return None
    digest = hashlib.sha256(token.encode()).hexdigest()
    for item in json.loads(settings().principals_json):
        if hmac.compare_digest(item['token_sha256'], digest):
            return Principal(item['id'], item['workspace_id'], item['role'])
    from app.review.demo_access import demo_identity
    identity = demo_identity(token)
    if identity:return Principal(identity, identity, 'reviewer', True)
    from app.review.accounts import session_identity
    return session_identity(token)


def principal(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials or len(credentials.credentials) < 32 or len(credentials.credentials) > 512:
        raise HTTPException(401, "A valid workspace access token is required.")
    found = resolve_principal(credentials.credentials)
    if found is None:
        raise HTTPException(401, "A valid workspace access token is required.")
    minute = int(time.time() // 60)
    with transaction() as conn:
        conn.execute("DELETE FROM rate_limits WHERE minute < ?", (minute - 1,))
        conn.execute("INSERT INTO rate_limits VALUES(?,?,1) ON CONFLICT(principal,minute) DO UPDATE SET count=count+1", (found.id, minute))
        count = conn.execute("SELECT count FROM rate_limits WHERE principal=? AND minute=?", (found.id, minute)).fetchone()[0]
    if count > settings().max_requests_per_minute:
        raise HTTPException(429, "Request limit reached. Try again shortly.", headers={"Retry-After": "60"})
    return found


def can_write(user: Principal):
    if user.role not in {"reviewer", "owner"}:
        raise HTTPException(403, "Reviewer access is required.")


def owned(conn, document_id, user, deleted=False):
    # Deliberately strict owner scope until shared-document grants are implemented.
    row = conn.execute("SELECT * FROM documents WHERE id=? AND workspace=? AND owner=?", (document_id, user.workspace_id, user.id)).fetchone()
    if row is None or (not deleted and (row["tombstone"] or row['retention_until'] <= now())):
        raise HTTPException(404, "Document not found.")
    return dict(row)
