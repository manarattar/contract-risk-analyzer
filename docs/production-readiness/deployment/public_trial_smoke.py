"""Synthetic-only public account/upload smoke test; no credentials are printed."""
import io,json,secrets,sys,time,uuid,zipfile
from pathlib import Path
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'backend'))
from app.review.sample import pdf_bytes
base=sys.argv[1].rstrip('/')
c=httpx.Client(base_url=base,timeout=30)
name='release-'+secrets.token_hex(8)
password=secrets.token_urlsafe(32)
r=c.post('/api/v2/accounts/register',json={'login':name,'password':password,'acknowledged':True});assert r.status_code==201,r.text
h={'Authorization':'Bearer '+r.json()['token']}
r=c.post('/api/v2/accounts/register',json={'login':name+'-other','password':password,'acknowledged':True});assert r.status_code==201,r.text
other={'Authorization':'Bearer '+r.json()['token']}
identity=c.get('/api/v2/session',headers=h).json()
assert identity['upload_enabled']
context={'contract_type':'Services agreement','party':'Synthetic customer','role':'Customer','governing_law':'Unknown','forum':'Unknown','objectives':['Liability'],'confirmed':True}
records=[];checks=[]
try:
 for filename,content,mime in [('synthetic.pdf',pdf_bytes(),'application/pdf'),('synthetic.txt',b'Synthetic services agreement. Payment is due in thirty days. Liability is limited to fees paid.','text/plain')]:
  r=c.post('/api/v2/documents',headers=h|{'Idempotency-Key':uuid.uuid4().hex},files={'file':(filename,content,mime)},data={'context':json.dumps(context),'privacy_acknowledged':'true'})
  assert r.status_code==202,r.text
  identifier=r.json()['id'];records.append(identifier);path='/api/v2/documents/'+identifier
  for _ in range(40):
   d=c.get(path,headers=h).json()
   if d['status'] not in ['queued','processing']:break
   time.sleep(1)
  assert d['status']=='ready',d
  if identity['mode']=='trial':
   assert d['result']['provenance']['mode']=='trial'
   if filename.endswith('pdf'): assert d['result']['findings']
  assert c.get(path,headers=other).status_code==404
  assert c.get(path+'/export',headers=h).status_code==200
  answer=c.post(path+'/questions',headers=h,json={'question':'What are the liability terms?'})
  assert answer.status_code==200 and answer.json()['sources'],answer.text
  if identity['mode']=='trial':assert answer.json()['status']=='answered',answer.text
  if filename.endswith('pdf'):
   r=c.get(path+'/pages/1',headers=h);assert r.status_code==200,r.text
   assert r.json()['image'].startswith('data:image/png;base64,')
  checks.append(filename+' upload, processing, ownership, questions and export')
 r=c.post('/api/v2/comparisons',headers=h,json={'baseline_id':records[0],'revised_id':records[1]})
 assert r.status_code==200,r.text
 checks.append('two-document comparison')
finally:
 for identifier in records:
  r=c.delete('/api/v2/documents/'+identifier,headers=h);assert r.status_code==202,r.text
  assert c.get('/api/v2/documents/'+identifier,headers=h).status_code==404
 for identifier in records:
  for _ in range(20):
   r=c.get('/api/v2/deletions/'+identifier,headers=h)
   if r.json()['state']=='complete':break
   time.sleep(1)
  assert r.json()['state']=='complete',r.text
 c.post('/api/v2/accounts/logout',headers=h)
 c.post('/api/v2/accounts/logout',headers=other)
checks.append('deletion, purge and logout')
print(json.dumps({'passed':True,'base':base,'checks':checks,'live_ai':identity['mode']=='trial'},indent=2))
