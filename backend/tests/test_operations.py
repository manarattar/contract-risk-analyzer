import json
import time
from types import SimpleNamespace

from .test_review_v2 import client,processed  # noqa: F401
from app.review import operations
from app.review.settings import settings


def test_monitor_fails_on_missing_or_stale_worker_without_leaking_content(client,monkeypatch):
    monkeypatch.setattr(operations.shutil,'disk_usage',lambda _:SimpleNamespace(free=1024**3))
    processed(client)
    report=operations.snapshot()
    assert not report['healthy'] and not report['checks']['worker_recent']
    operations.heartbeat()
    report=operations.snapshot()
    assert report['healthy']
    assert 'Synthetic services' not in json.dumps(report)
    (settings().data_dir/'worker-heartbeat.json').write_text(json.dumps({'time':time.time()-120}))
    assert not operations.snapshot()['healthy']
    operations.heartbeat()
    monkeypatch.setattr(operations.shutil,'disk_usage',lambda _:SimpleNamespace(free=1024))
    assert not operations.snapshot()['checks']['storage_headroom']
