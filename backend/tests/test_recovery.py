import json

import pytest

from .test_review_v2 import client, processed  # noqa: F401
from app.review import recovery
from app.review.store import transaction


def test_demo_excluded_and_private_restore_replays_deletion(client,tmp_path):
    identifier,_=processed(client)
    first=recovery.prepare(tmp_path/'demo-backup')
    assert first['private_documents']==0 and first['excluded_documents']==1
    with transaction() as conn: conn.execute("UPDATE documents SET mode='manual' WHERE id=?",(identifier,))
    second=recovery.prepare(tmp_path/'private-backup')
    assert second['private_documents']==1
    restored=recovery.restore(tmp_path/'private-backup',tmp_path/'rehearsal',[])
    assert restored['restored_documents']==1
    deleted=recovery.restore(tmp_path/'private-backup',tmp_path/'deleted-rehearsal',[identifier])
    assert deleted['restored_documents']==0 and not list((tmp_path/'deleted-rehearsal/uploads').iterdir())
    with pytest.raises(ValueError,match='new'):
        recovery.restore(tmp_path/'private-backup',tmp_path/'rehearsal',[])


def test_backup_tamper_and_missing_original_fail_closed(client,tmp_path):
    identifier,_=processed(client)
    with transaction() as conn: conn.execute("UPDATE documents SET mode='manual' WHERE id=?",(identifier,))
    recovery.prepare(tmp_path/'backup')
    manifest=tmp_path/'backup/manifest.json'
    data=json.loads(manifest.read_text()); data['database_sha256']='invalid'; manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='integrity'):
        recovery.restore(tmp_path/'backup',tmp_path/'bad-restore',[])
