"""Non-content operational checks for the host monitor; no public metrics route."""
import json
from pathlib import Path
import shutil
import threading
import time
from datetime import datetime, timezone

from app.review.settings import settings
from app.review.store import transaction


def heartbeat():
    path=settings().data_dir.resolve()/'worker-heartbeat.json'
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps({'time':time.time()}))
    temporary.replace(path)


def start_heartbeat():
    def run():
        while True:
            try:heartbeat()
            except OSError:pass  # The external check reports missing/stale heartbeat.
            time.sleep(15)
    threading.Thread(target=run,daemon=True,name='worker-heartbeat').start()


def snapshot():
    current=datetime.now(timezone.utc)
    with transaction() as conn:
        counts={row[0]:row[1] for row in conn.execute('SELECT state,count(*) FROM jobs GROUP BY state')}
        pending=[row[0] for row in conn.execute("SELECT updated FROM jobs WHERE state IN ('queued','running')")]
        purges=[row[0] for row in conn.execute("SELECT requested FROM deletions WHERE state!='complete'")]
        calls=conn.execute('SELECT coalesce(sum(ai_calls),0) FROM documents').fetchone()[0]
    def age(rows):
        return max([max(0,(current-datetime.fromisoformat(value)).total_seconds()) for value in rows],default=0)
    try:
        stamp=json.loads((settings().data_dir/'worker-heartbeat.json').read_text())['time']
        worker_age=max(0,time.time()-stamp)
    except (OSError,ValueError,KeyError):worker_age=None
    free=shutil.disk_usage(settings().data_dir).free
    checks={'worker_recent':worker_age is not None and worker_age<60,
            'queue_not_stalled':age(pending)<300,'purges_not_stalled':age(purges)<60,
            'storage_headroom':free>256*1024*1024}
    return {'healthy':all(checks.values()),'checks':checks,'jobs':counts,
            'oldest_pending_seconds':round(age(pending),1),'pending_purges':len(purges),
            'worker_heartbeat_age_seconds':round(worker_age,1) if worker_age is not None else None,
            'available_storage_bytes':free,'reserved_ai_calls':calls,
            'note':'AI reservations are not a billing measurement. No document content is included.'}


if __name__=='__main__':
    import sys
    try:
        report=snapshot(); print(json.dumps(report)); sys.exit(0 if report['healthy'] else 1)
    except Exception:
        print(json.dumps({'healthy':False,'reason':'operational_check_failed'}));sys.exit(1)
