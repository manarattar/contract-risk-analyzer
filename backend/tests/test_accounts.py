import json
import pytest
from .test_review_v2 import client, auth
from app.review.settings import settings
from app.review.store import transaction

@pytest.fixture
def account_client(client,monkeypatch):
    monkeypatch.setenv('REVIEW_ACCOUNTS_ENABLED','true')
    principals=json.loads(settings().principals_json)
    principals[0]['role']='owner'
    monkeypatch.setenv('REVIEW_PRINCIPALS_JSON',json.dumps(principals))
    settings.cache_clear()
    return client

def invitation(c,name='synthetic-reviewer'):
    r=c.post('/api/v2/accounts/invites',headers=auth(),json={'login':name})
    assert r.status_code==201,r.text
    return r.json()['invite']

def activate(c,code,name='synthetic-reviewer',password='Synthetic violet river 2026!'):
    return c.post('/api/v2/accounts/redeem',json={'login':name,'invite':code,'password':password})

def test_accounts_lifecycle_and_isolation(account_client):
    c=account_client;code=invitation(c)
    r=activate(c,code);assert r.status_code==201,r.text
    token=r.json()['token'];headers={'Authorization':'Bearer '+token}
    assert c.get('/api/v2/session',headers=headers).status_code==200
    assert c.get('/api/v2/accounts',headers=headers).status_code==403
    assert activate(c,code).status_code==400
    assert c.post('/api/v2/accounts/logout',headers=headers).status_code==200
    assert c.get('/api/v2/session',headers=headers).status_code==401
    r=c.post('/api/v2/accounts/login',json={'login':'synthetic-reviewer','password':'Synthetic violet river 2026!'})
    assert r.status_code==200,r.text
    headers={'Authorization':'Bearer '+r.json()['token']}
    identifier=c.get('/api/v2/accounts',headers=auth()).json()['accounts'][0]['id']
    assert c.post(f'/api/v2/accounts/{identifier}/revoke',headers=auth('bob')).status_code==403
    assert c.post(f'/api/v2/accounts/{identifier}/revoke',headers=auth()).status_code==200
    assert c.get('/api/v2/session',headers=headers).status_code==401
    with transaction() as conn:
        stored=conn.execute('SELECT password_hash FROM accounts').fetchone()[0]
        assert stored.startswith('scrypt-v1:') and 'Synthetic' not in stored
        assert conn.execute('SELECT count(*) FROM account_sessions').fetchone()[0]==0

def test_recovery_suspends_old_password_and_redeems_once(account_client):
    c=account_client;activate(c,invitation(c))
    identifier=c.get('/api/v2/accounts',headers=auth()).json()['accounts'][0]['id']
    code=c.post(f'/api/v2/accounts/{identifier}/reset',headers=auth()).json()['invite']
    assert c.post('/api/v2/accounts/login',json={'login':'synthetic-reviewer','password':'Synthetic violet river 2026!'}).status_code==401
    r=activate(c,code,password='Replacement orange river 2026!');assert r.status_code==201,r.text
    assert activate(c,code,password='Replacement orange river 2026!').status_code==400
    assert c.get('/api/v2/session',headers={'Authorization':'Bearer '+r.json()['token']}).status_code==200

def test_idle_expiry_validation_and_disabled_gate(account_client,monkeypatch):
    c=account_client;r=activate(c,invitation(c));headers={'Authorization':'Bearer '+r.json()['token']}
    with transaction() as conn:conn.execute('UPDATE account_sessions SET last_seen=0')
    assert c.get('/api/v2/session',headers=headers).status_code==401
    secret='NEVER-ECHO-THIS'*20
    response=c.post('/api/v2/accounts/login',json={'login':'synthetic-reviewer','password':secret})
    assert response.status_code==422 and secret not in response.text
    monkeypatch.setenv('REVIEW_ACCOUNTS_ENABLED','false');settings.cache_clear()
    assert c.post('/api/v2/accounts/login',json={'login':'synthetic-reviewer','password':'anything'}).status_code==404


def test_public_registration_isolated_and_bounded(account_client,monkeypatch):
    c=account_client
    payload={'login':'public-person','password':'Synthetic violet river 2026!','acknowledged':True}
    assert c.post('/api/v2/accounts/register',json=payload).status_code==404
    monkeypatch.setenv('REVIEW_PUBLIC_SIGNUP_ENABLED','true');settings.cache_clear()
    assert c.post('/api/v2/accounts/register',json=payload|{'acknowledged':False}).status_code==422
    first=c.post('/api/v2/accounts/register',json=payload)
    assert first.status_code==201,first.text
    second=c.post('/api/v2/accounts/register',json=payload|{'login':'public-person-two'})
    assert second.status_code==201,second.text
    users=[]
    for response in [first,second]:
        h={'Authorization':'Bearer '+response.json()['token']}
        users.append(c.get('/api/v2/session',headers=h).json()['principal'])
        assert c.get('/api/v2/accounts',headers=h).status_code==403
    assert users[0]['workspace_id'] != users[1]['workspace_id']
    assert c.post('/api/v2/accounts/register',json=payload).status_code==409
    monkeypatch.setenv('REVIEW_MAX_ACCOUNTS','2');settings.cache_clear()
    assert c.post('/api/v2/accounts/register',json=payload|{'login':'capacity-person'}).status_code==429
