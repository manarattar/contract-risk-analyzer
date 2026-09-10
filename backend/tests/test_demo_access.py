from .test_review_v2 import client, auth, processed  # noqa: F401
from app.review.settings import settings
from app.review.auth import resolve_principal


def enable(monkeypatch):
    monkeypatch.setenv('REVIEW_PUBLIC_DEMO_ENABLED','true')
    monkeypatch.setenv('REVIEW_DEMO_SIGNING_KEY','synthetic-test-secret-'+'x'*40)
    settings.cache_clear()


def test_demo_disabled_by_default(client):
    assert client.get('/api/v2/public-config').json()['public_demo'] is False
    assert client.post('/api/v2/demo-session').status_code == 404


def test_isolated_demo_denies_private_access_and_upload(client,monkeypatch):
    private,_ = processed(client)
    enable(monkeypatch)
    first = client.post('/api/v2/demo-session').json()['token']
    second = client.post('/api/v2/demo-session').json()['token']
    headers = {'Authorization':'Bearer '+first}
    assert client.get('/api/v2/session',headers=headers).json()['upload_enabled'] is False
    assert client.get('/api/v2/documents',headers=headers).json()['items'] == []
    assert client.get('/api/v2/documents/'+private,headers=headers).status_code == 404
    sample = client.post('/api/v2/sample',headers=headers|{'Idempotency-Key':'public-demo-test-0001'})
    assert sample.status_code == 202
    assert client.get('/api/v2/documents/'+sample.json()['id'],headers={'Authorization':'Bearer '+second}).status_code == 404
    assert resolve_principal(first+'x') is None
    parts=first.split('.'); parts[2]='9999999999'
    assert resolve_principal('.'.join(parts)) is None
    response=client.post('/api/v2/documents',headers=headers|{'Idempotency-Key':'public-upload-test-01'},
                         files={'file':('synthetic.txt',b'Synthetic no confidential content.')},
                         data={'context':'{}','privacy_acknowledged':'true'})
    assert response.status_code == 403


def test_demo_start_rate_limit(client,monkeypatch):
    enable(monkeypatch)
    for _ in range(5): assert client.post('/api/v2/demo-session').status_code == 200
    assert client.post('/api/v2/demo-session').status_code == 429
