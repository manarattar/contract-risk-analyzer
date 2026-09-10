"""Public synthetic-only deployment smoke test. Never reads private documents."""
import json
import html
import sys
import time
import urllib.error
import urllib.request
import uuid

base = sys.argv[1].rstrip('/')
checks = []


def call(path, token='', method='GET', body=None, key=None, expected=200):
    headers = {'Content-Type':'application/json'}
    if token: headers['Authorization']='Bearer '+token
    if key: headers['Idempotency-Key']=key
    request=urllib.request.Request(base+path,headers=headers,method=method,
                                  data=json.dumps(body).encode() if body is not None else None)
    try:
        response=urllib.request.urlopen(request,timeout=25)
    except urllib.error.HTTPError as e:
        response=e
    with response:
        data=response.read()
        assert response.status==expected, (path,response.status,data[:300])
        if path.startswith('/api/v2') and expected==200:
            assert 'no-store' in response.headers.get('Cache-Control','')
        return json.loads(data) if 'json' in response.headers.get('Content-Type','') else data.decode()


assert call('/api/ready')['status']=='ready'
call('/api/v2/documents',expected=401)
checks.append('ready and anonymous documents denied')
access=call('/api/v2/demo-session',method='POST')['token']
other=call('/api/v2/demo-session',method='POST')['token']
identity=call('/api/v2/session',access)
assert identity['mode']=='demo' and not identity['upload_enabled']
checks.append('demo isolated from private uploads and live AI')
started=time.monotonic()
record=call('/api/v2/sample?pdf=true',access,method='POST',key=uuid.uuid4().hex,expected=202)
identifier=record['id']
root='/api/v2/documents/'+identifier
try:
    for _ in range(30):
        doc=call(root,access)
        if doc['status'] not in {'queued','processing'}: break
        time.sleep(1)
    assert doc['status']=='ready', doc['status']
    seconds=round(time.monotonic()-started,2)
    call(root,other,expected=404)
    finding=doc['result']['findings'][0]; cite=finding['citations'][0]
    page=call(root+'/pages/2?block_id='+cite['block_id']+'&start='+str(cite['start'])+'&end='+str(cite['end']),access)
    assert page['match']=='quote' and page['rectangles'] and page['image'].startswith('data:image/png;base64,')
    checks.append('durable PDF processing, exact source highlight and cross-session denial')
    answer=call(root+'/questions',access,method='POST',body={'question':'What are the liability terms?'})
    assert answer['sources']
    call(root+'/findings/'+finding['id'],access,method='PATCH',body={'status':'accepted','version':0,'note':'Synthetic deployment verification','revision_text':''})
    exported=call(root+'/export',access)
    assert 'Synthetic deployment verification' in exported and html.escape(cite['quote'][:20]) in exported
    checks.append('source Q&A, reviewer decision and authenticated export')
finally:
    call(root,access,method='DELETE',expected=202)
    call(root,access,expected=404)
for _ in range(15):
    receipt=call('/api/v2/deletions/'+identifier,access)
    if receipt['state']=='complete':break
    time.sleep(1)
assert receipt['state']=='complete'
checks.append('deletion revocation and worker purge receipt')
print(json.dumps({'base':base,'checks':checks,'synthetic_processing_seconds':seconds,'passed':True},indent=2))
