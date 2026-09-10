"""Invite-only accounts and revocable, opaque sessions. No email is sent."""
import hashlib
import hmac
import secrets
import time
from threading import BoundedSemaphore
from typing import Literal

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field, SecretStr

from app.review.auth import Principal, principal
from app.review.routes import router
from app.review.settings import settings
from app.review.store import transaction, now

AUTH_SCHEMA = '''
CREATE TABLE IF NOT EXISTS auth_migrations(version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS accounts(
 id TEXT PRIMARY KEY, login TEXT UNIQUE NOT NULL, workspace TEXT NOT NULL,
 role TEXT NOT NULL, password_hash TEXT NOT NULL, created TEXT NOT NULL,
 disabled INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS account_invites(
 digest TEXT PRIMARY KEY, login TEXT NOT NULL, workspace TEXT NOT NULL,
 role TEXT NOT NULL, actor TEXT NOT NULL, expires REAL NOT NULL, used INTEGER NOT NULL DEFAULT 0,
 account_id TEXT
);
CREATE TABLE IF NOT EXISTS account_sessions(
 digest TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id),
 created REAL NOT NULL, last_seen REAL NOT NULL, expires REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS account_sessions_owner ON account_sessions(account_id);
INSERT OR IGNORE INTO auth_migrations VALUES(1);
'''
_password_slots = BoundedSemaphore(1)


class Login(BaseModel):
    login: str = Field(min_length=3,max_length=120,pattern=r'^[A-Za-z0-9_.@-]+$')
    password: SecretStr = Field(min_length=1,max_length=128)


class Redeem(Login):
    invite: SecretStr = Field(min_length=32,max_length=100)


class Invite(BaseModel):
    login: str = Field(min_length=3,max_length=120,pattern=r'^[A-Za-z0-9_.@-]+$')
    role: Literal['reviewer','viewer'] = 'reviewer'


def enabled():
    if not settings().accounts_enabled:
        raise HTTPException(404,'Account sign-in is not enabled.')


def password_digest(password,salt=None):
    # OWASP scrypt fallback profile: N=2^17,r=8,p=1 (128 MiB).
    salt=bytes.fromhex(salt) if salt else secrets.token_bytes(16)
    if not _password_slots.acquire(blocking=False):
        raise HTTPException(503,'Sign-in is busy. Please retry.')
    try:
        digest=hashlib.scrypt(password.encode('utf-8'),salt=salt,n=131072,r=8,p=1,dklen=32,maxmem=256*1024*1024)
        return 'scrypt-v1:'+salt.hex()+':'+digest.hex()
    finally:_password_slots.release()


def check_password(password,stored):
    salt=stored.split(':')[1] if stored else '00'*16
    actual=password_digest(password,salt)
    return bool(stored) and hmac.compare_digest(actual,stored)


def throttle(request,login):
    peer=request.client.host if request.client else 'unknown'
    minute=int(time.time()//60)
    keys=[('signin-peer-'+hashlib.sha256(peer.encode()).hexdigest(),10),
          ('signin-name-'+hashlib.sha256(login.lower().encode()).hexdigest(),5)]
    with transaction() as conn:
        for key,limit in keys:
            row=conn.execute('SELECT count FROM rate_limits WHERE principal=? AND minute=?',(key,minute)).fetchone()
            if row and row[0]>=limit:
                raise HTTPException(429,'Too many sign-in attempts. Retry in one minute.',headers={'Retry-After':'60'})
            conn.execute('INSERT INTO rate_limits VALUES(?,?,1) ON CONFLICT(principal,minute) DO UPDATE SET count=count+1',(key,minute))


def new_session(conn,account_id):
    token=secrets.token_urlsafe(48); stamp=time.time()
    conn.execute('DELETE FROM account_sessions WHERE expires<=? OR last_seen<=?',(stamp,stamp-1800))
    conn.execute('INSERT INTO account_sessions VALUES(?,?,?,?,?)',
                 (hashlib.sha256(token.encode()).hexdigest(),account_id,stamp,stamp,stamp+8*3600))
    return {'token':token,'expires_in':8*3600,'idle_timeout':1800}


def session_identity(token):
    if not settings().accounts_enabled:return None
    stamp=time.time(); digest=hashlib.sha256(token.encode()).hexdigest()
    with transaction() as conn:
        row=conn.execute('''SELECT a.* FROM account_sessions s JOIN accounts a ON a.id=s.account_id
                          WHERE s.digest=? AND s.expires>? AND s.last_seen>? AND a.disabled=0''',
                         (digest,stamp,stamp-1800)).fetchone()
        if row:
            conn.execute('UPDATE account_sessions SET last_seen=? WHERE digest=?',(stamp,digest))
            return Principal(row['id'],row['workspace'],row['role'],False,row['login'])
    return None


@router.post('/accounts/login')
def login(payload:Login,request:Request):
    enabled(); throttle(request,payload.login)
    with transaction() as conn:
        row=conn.execute('SELECT * FROM accounts WHERE login=?',(payload.login.lower(),)).fetchone()
    valid=check_password(payload.password.get_secret_value(),row['password_hash'] if row else None)
    if not valid or row['disabled']:
        raise HTTPException(401,'Sign-in failed. Check your credentials or contact your workspace owner.')
    with transaction() as conn:
        current=conn.execute('SELECT disabled,password_hash FROM accounts WHERE id=?',(row['id'],)).fetchone()
        if current['disabled'] or current['password_hash']!=row['password_hash']:
            raise HTTPException(401,'Account changed. Please sign in again.')
        return new_session(conn,row['id'])


@router.post('/accounts/redeem',status_code=201)
def redeem(payload:Redeem,request:Request):
    enabled(); throttle(request,payload.login)
    password=payload.password.get_secret_value()
    if len(password)<15 or len(set(password))<4 or password.lower() in {'passwordpassword','thisisapassword','123456789012345'}:
        raise HTTPException(422,'Use a unique passphrase of at least 15 characters.')
    digest=hashlib.sha256(payload.invite.get_secret_value().encode()).hexdigest()
    with transaction() as conn:
        invite=conn.execute('SELECT * FROM account_invites WHERE digest=? AND login=? AND used=0 AND expires>?',
                            (digest,payload.login.lower(),time.time())).fetchone()
        existing=conn.execute('SELECT id FROM accounts WHERE login=?',(payload.login.lower(),)).fetchone()
        if not invite or (existing and existing['id']!=invite['account_id']):
            raise HTTPException(400,'Invitation is invalid, expired, or already used.')
    encoded=password_digest(password)
    with transaction() as conn:
        # Claim once after expensive hashing; concurrent redemption cannot race.
        updated=conn.execute('UPDATE account_invites SET used=1 WHERE digest=? AND used=0 AND expires>?',(digest,time.time())).rowcount
        existing=conn.execute('SELECT id FROM accounts WHERE login=?',(payload.login.lower(),)).fetchone()
        if not updated or (existing and existing['id']!=invite['account_id']):
            raise HTTPException(400,'Invitation is invalid, expired, or already used.')
        identifier=invite['account_id'] or 'account-'+secrets.token_hex(16)
        if invite['account_id']:
            conn.execute('UPDATE accounts SET password_hash=?,disabled=0 WHERE id=?',(encoded,identifier))
            conn.execute('DELETE FROM account_sessions WHERE account_id=?',(identifier,))
        else:
            conn.execute('INSERT INTO accounts(id,login,workspace,role,password_hash,created) VALUES(?,?,?,?,?,?)',
                         (identifier,payload.login.lower(),invite['workspace'],invite['role'],encoded,now()))
        return new_session(conn,identifier)


def owner(user):
    enabled()
    if user.demo or user.role!='owner':raise HTTPException(403,'Workspace owner access required.')


@router.post('/accounts/invites',status_code=201)
def invite_account(payload:Invite,user:Principal=Depends(principal)):
    owner(user)
    token=secrets.token_urlsafe(32)
    with transaction() as conn:
        count=conn.execute('SELECT count(*) FROM account_invites WHERE workspace=? AND used=0 AND expires>?',(user.workspace_id,time.time())).fetchone()[0]
        if count>=50:raise HTTPException(429,'Invitation quota reached.')
        if conn.execute('SELECT 1 FROM accounts WHERE login=?',(payload.login.lower(),)).fetchone():
            raise HTTPException(409,'That login name is unavailable.')
        conn.execute('INSERT INTO account_invites(digest,login,workspace,role,actor,expires,used) VALUES(?,?,?,?,?,?,0)',
                     (hashlib.sha256(token.encode()).hexdigest(),payload.login.lower(),user.workspace_id,payload.role,user.id,time.time()+48*3600))
    return {'invite':token,'login':payload.login.lower(),'role':payload.role,'expires_in':48*3600,
            'note':'Share privately with the intended reviewer. No message has been sent.'}


@router.get('/accounts')
def list_accounts(user:Principal=Depends(principal)):
    owner(user)
    with transaction() as conn:
        rows=conn.execute('SELECT id,login,role,disabled,created FROM accounts WHERE workspace=? ORDER BY created LIMIT 200',(user.workspace_id,)).fetchall()
    return {'accounts':[dict(r) for r in rows]}


@router.post('/accounts/{account_id}/reset',status_code=201)
def reset_account(account_id:str,user:Principal=Depends(principal)):
    owner(user)
    token=secrets.token_urlsafe(32)
    with transaction() as conn:
        account=conn.execute('SELECT * FROM accounts WHERE id=? AND workspace=?',(account_id,user.workspace_id)).fetchone()
        if not account:raise HTTPException(404,'Account not found.')
        conn.execute('UPDATE accounts SET disabled=1 WHERE id=?',(account_id,))
        conn.execute('DELETE FROM account_invites WHERE account_id=?',(account_id,))
        conn.execute('DELETE FROM account_sessions WHERE account_id=?',(account_id,))
        conn.execute('INSERT INTO account_invites VALUES(?,?,?,?,?,?,0,?)',
                     (hashlib.sha256(token.encode()).hexdigest(),account['login'],user.workspace_id,account['role'],user.id,time.time()+3600,account_id))
    return {'invite':token,'login':account['login'],'expires_in':3600,
            'note':'Recovery code expires in one hour. Verify the recipient before sharing; current sessions were revoked.'}


@router.post('/accounts/{account_id}/revoke')
def revoke_account(account_id:str,user:Principal=Depends(principal)):
    owner(user)
    with transaction() as conn:
        if not conn.execute('SELECT 1 FROM accounts WHERE id=? AND workspace=?',(account_id,user.workspace_id)).fetchone():
            raise HTTPException(404,'Account not found.')
        conn.execute('UPDATE accounts SET disabled=1 WHERE id=?',(account_id,))
        conn.execute('DELETE FROM account_sessions WHERE account_id=?',(account_id,))
        conn.execute('DELETE FROM account_invites WHERE account_id=?',(account_id,))
    return {'disabled':True}


@router.post('/accounts/logout')
def logout(request:Request,user:Principal=Depends(principal)):
    token=request.headers.get('Authorization','')[7:]
    if settings().accounts_enabled:
        with transaction() as conn:
            conn.execute('DELETE FROM account_sessions WHERE digest=?',(hashlib.sha256(token.encode()).hexdigest(),))
    return {'signed_out':True,'note':'Operator tokens are rotated by the operator; demo tokens expire automatically.'}


class Registration(Login):
    acknowledged: bool = False


@router.post('/accounts/register', status_code=201)
def register(payload: Registration, request: Request):
    enabled()
    if not settings().public_signup_enabled:
        raise HTTPException(404, 'Public registration is not enabled.')
    throttle(request, payload.login)
    password = payload.password.get_secret_value()
    if not payload.acknowledged:
        raise HTTPException(422, 'Acknowledge the trial limitations before creating an account.')
    if len(password) < 15 or len(set(password)) < 4 or password.lower() in {'passwordpassword', 'thisisapassword', '123456789012345'}:
        raise HTTPException(422, 'Use a unique passphrase of at least 15 characters.')
    encoded = password_digest(password)
    with transaction() as conn:
        if conn.execute('SELECT count(*) FROM accounts').fetchone()[0] >= settings().max_accounts:
            raise HTTPException(429, 'Trial capacity reached. Please try again later.')
        if conn.execute('SELECT 1 FROM accounts WHERE login=?', (payload.login.lower(),)).fetchone():
            raise HTTPException(409, 'That login name is unavailable.')
        identifier = 'account-' + secrets.token_hex(16)
        # Workspace is server-generated, never supplied by the visitor.
        conn.execute('INSERT INTO accounts(id,login,workspace,role,password_hash,created) VALUES(?,?,?,?,?,?)',
                     (identifier, payload.login.lower(), 'trial-' + secrets.token_hex(16), 'reviewer', encoded, now()))
        return new_session(conn, identifier)
