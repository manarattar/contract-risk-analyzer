"""Consistent backup preparation and fail-closed restore to a NEW directory.

Encryption/authentication and backup expiry are handled by the host wrapper.
Public/demo records are excluded. No provider calls are made.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

from app.review.ingestion import object_path
from app.review.settings import settings
from app.review.store import database_path, now


def scrub(conn, identifiers):
    for identifier in identifiers:
        for table in ('decision_events','decisions','jobs','deletions'):
            conn.execute(f'DELETE FROM {table} WHERE document_id=?',(identifier,))
        conn.execute('DELETE FROM documents WHERE id=?',(identifier,))


def prepare(destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('Backup destination must be new')
    destination.mkdir(parents=True)
    uploads = destination/'uploads'; uploads.mkdir()
    backup = destination/'reviews.sqlite3'
    with sqlite3.connect(database_path().as_uri()+'?mode=ro',uri=True) as source:
        with sqlite3.connect(backup) as target:
            source.backup(target)
    with sqlite3.connect(backup) as target:
        target.row_factory = sqlite3.Row
        target.execute('PRAGMA secure_delete=ON')
        excluded = [r[0] for r in target.execute("SELECT id FROM documents WHERE mode='demo' OR tombstone IS NOT NULL OR retention_until<=?",(now(),))]
        scrub(target, excluded)
        target.execute('DELETE FROM rate_limits')
        rows = target.execute('SELECT id,kind,hash FROM documents').fetchall()
        for row in rows:
            source = object_path(row['id'],row['kind'])
            if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=row['hash']:
                raise ValueError('Original missing or changed; backup is incomplete')
            shutil.copyfile(source, uploads/source.name)
        target.commit()
        target.execute('PRAGMA journal_mode=DELETE')
        target.execute('VACUUM')
    manifest={'version':1,'created':now(),'private_documents':len(rows),'excluded_documents':len(excluded),
              'database_sha256':hashlib.sha256(backup.read_bytes()).hexdigest()}
    (destination/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    return manifest


def restore(snapshot, destination, purged_ids):
    snapshot, destination = Path(snapshot).resolve(), Path(destination).resolve()
    if destination.exists() or destination == settings().data_dir.resolve():
        raise ValueError('Restore requires a new, non-live destination')
    if not isinstance(purged_ids,list):
        raise ValueError('A current deletion ledger is required')
    manifest=json.loads((snapshot/'manifest.json').read_text(encoding='utf-8'))
    backup=snapshot/'reviews.sqlite3'
    if manifest.get('version') != 1 or hashlib.sha256(backup.read_bytes()).hexdigest()!=manifest['database_sha256']:
        raise ValueError('Backup integrity check failed')
    destination.mkdir(parents=True)
    uploads=destination/'uploads'; uploads.mkdir()
    shutil.copyfile(backup,destination/'reviews.sqlite3')
    with sqlite3.connect(destination/'reviews.sqlite3') as target:
        target.row_factory=sqlite3.Row
        target.execute('PRAGMA secure_delete=ON')
        expired=[r[0] for r in target.execute('SELECT id FROM documents WHERE retention_until<=?',(now(),))]
        scrub(target,set(purged_ids+expired))
        rows=target.execute('SELECT id,kind,hash FROM documents').fetchall()
        for row in rows:
            # object_path validates the identifier and suffix without reading live files.
            name=object_path(row['id'],row['kind']).name
            original=snapshot/'uploads'/name
            if not original.is_file() or original.is_symlink() or hashlib.sha256(original.read_bytes()).hexdigest()!=row['hash']:
                raise ValueError('Backup original failed integrity check')
            shutil.copyfile(original,uploads/name)
        target.execute("UPDATE documents SET epoch=epoch+1,status='queued' WHERE status='processing'")
        target.execute("UPDATE jobs SET state='queued',epoch=(SELECT epoch FROM documents WHERE id=document_id),lease_token=NULL,lease_until=NULL WHERE state='running'")
        target.commit(); target.execute('VACUUM')
        assert target.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    return {'restored_documents':len(rows),'purged_before_restore':len(set(purged_ids+expired)),
            'note':'Restore rehearsal only; no live directory changed or provider enabled.'}


if __name__=='__main__':
    import sys
    if sys.argv[1]=='prepare':
        result=prepare(sys.argv[2])
    elif sys.argv[1]=='restore':
        result=restore(sys.argv[2],sys.argv[3],json.loads(Path(sys.argv[4]).read_text()))
    else:
        raise SystemExit('Use prepare DEST or restore SNAPSHOT NEW_DEST CURRENT_DELETION_LEDGER.json')
    print(json.dumps(result))
