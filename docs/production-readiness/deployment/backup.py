"""Host-only encrypted backups and restore rehearsals; run as root.

No live datastore is overwritten. A live deletion ledger is required for rehearsal.
AES-256-CBC/PBKDF2 encryption is authenticated with an independent HMAC-SHA256 key.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone

ROOT=Path('/srv/backup/contracts-v2')
ENC=Path('/srv/stack/env/contracts-v2-backup.key')
MAC=Path('/srv/stack/env/contracts-v2-backup.mac')


def command(args, **kwargs):
    return subprocess.check_output(args, **kwargs)


def authenticate(path):
    digest=hmac.new(MAC.read_bytes(),digestmod=hashlib.sha256)
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def helper(stage, arguments):
    image=command(['docker','inspect','contracts-v2','--format','{{.Config.Image}}']).decode().strip()
    os.chown(stage,10001,10001)
    return command(['docker','run','--rm','--network','none','--read-only','--user','10001:10001',
                    '--memory','768m','--cpus','1','--pids-limit','64','--cap-drop','ALL',
                    '--security-opt','no-new-privileges','--tmpfs','/tmp:rw,size=32m',
                    # SQLite opens mode=ro, but WAL shared-memory coordination may
                    # need a writable directory. This helper never parses uploads.
                    '-e','REVIEW_DATA_DIR=/data','-v','contracts_review_v2_data:/data',
                    '-v',str(stage)+':/staging',image,'python']+arguments)


def backup():
    name='contracts-v2-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.tar.enc'
    output=ROOT/name
    if output.exists():raise ValueError('Backup name already exists')
    with tempfile.TemporaryDirectory(prefix='contracts-backup-') as temp:
        temp=Path(temp)
        manifest=json.loads(helper(temp,['-m','app.review.recovery','prepare','/staging/snapshot']))
        archive=temp/'snapshot.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:tar.add(temp/'snapshot',arcname='snapshot')
        command(['openssl','enc','-aes-256-cbc','-pbkdf2','-iter','200000','-salt',
                 '-in',str(archive),'-out',str(output),'-pass','file:'+str(ENC)])
    metadata={'hmac_sha256':authenticate(output),'created':manifest['created'],
              'private_documents':manifest['private_documents'],'demo_records_excluded':True}
    output.with_suffix('.json').write_text(json.dumps(metadata))
    for path in ROOT.iterdir():
        if re.fullmatch(r'contracts-v2-\d{8}T\d{6}\.tar\.(enc|json)',path.name) and not path.is_symlink() and path.is_file() and path.stat().st_mtime<time.time()-14*86400:
            path.unlink()
    return {'backup':name,'private_documents':manifest['private_documents'],'encrypted_and_authenticated':True,'retention_days':14}


def rehearse():
    backups=sorted(ROOT.glob('contracts-v2-*.tar.enc'))
    if not backups:raise ValueError('No backups available')
    archive=backups[-1]
    metadata=json.loads(archive.with_suffix('.json').read_text())
    if not hmac.compare_digest(authenticate(archive),metadata['hmac_sha256']):
        raise ValueError('Backup authentication failed; decryption refused')
    with tempfile.TemporaryDirectory(prefix='contracts-rehearse-') as temp:
        temp=Path(temp)
        decrypted=temp/'snapshot.tar.gz'
        command(['openssl','enc','-d','-aes-256-cbc','-pbkdf2','-iter','200000',
                 '-in',str(archive),'-out',str(decrypted),'-pass','file:'+str(ENC)])
        with tarfile.open(decrypted) as tar:
            members=tar.getmembers()
            if len(members)>5000 or sum(m.size for m in members)>2*1024**3:raise ValueError('Archive limits exceeded')
            for m in members:
                parts=Path(m.name).parts
                if not parts or parts[0]!='snapshot' or '..' in parts or not (m.isfile() or m.isdir()):raise ValueError('Unsafe archive entry')
            tar.extractall(temp,members=members,filter='data')
        for item in [temp/'snapshot',*(temp/'snapshot').rglob('*')]:
            os.chown(item,10001,10001)
            item.chmod(0o700 if item.is_dir() else 0o600)
        ledger=helper(temp,['-c','import json,sqlite3; db=sqlite3.connect("file:/data/reviews.sqlite3?mode=ro",uri=True); print(json.dumps([r[0] for r in db.execute("SELECT document_id FROM deletions")])); db.close()'])
        (temp/'ledger.json').write_bytes(ledger)
        os.chown(temp/'ledger.json',10001,10001); (temp/'ledger.json').chmod(0o600)
        report=json.loads(helper(temp,['-m','app.review.recovery','restore','/staging/snapshot','/staging/restored','/staging/ledger.json']))
    report['backup']=archive.name
    return report


if __name__=='__main__':
    if os.geteuid()!=0:raise SystemExit('Run as root')
    os.umask(0o077); ROOT.mkdir(parents=True,exist_ok=True,mode=0o700)
    for key in (ENC,MAC):
        if not key.exists():
            fd=os.open(key,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as stream:stream.write(secrets.token_hex(32))
    print(json.dumps(rehearse() if '--rehearse' in sys.argv else backup()))
