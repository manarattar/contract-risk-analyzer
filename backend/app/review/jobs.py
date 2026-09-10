import json
import logging
import subprocess
import sys
import time
import uuid

from app.review import pipeline
from app.review.ingestion import object_path
from app.review.settings import settings
from app.review.store import now, transaction

logger = logging.getLogger(__name__)
LEASE_SECONDS = 180


def parse_in_process(document):
    cfg = settings()
    result = subprocess.run(
        [sys.executable, "-B", "-m", "app.review.parser", str(object_path(document["id"], document["kind"])),
         document["kind"], str(cfg.max_pages), str(cfg.max_chars)],
        capture_output=True, text=True, encoding="utf-8", timeout=cfg.parser_timeout,
    )
    output = json.loads(result.stdout)
    if result.returncode or "error" in output:
        raise ValueError(output.get("error", "extraction_failed"))
    return output


def claim():
    with transaction() as conn:
        row = conn.execute("""SELECT j.* FROM jobs j JOIN documents d ON d.id=j.document_id
        WHERE d.tombstone IS NULL AND j.attempts<3 AND
        (j.state='queued' OR (j.state='running' AND j.lease_until<?)) ORDER BY j.updated LIMIT 1""", (time.time(),)).fetchone()
        if not row:
            conn.execute("""UPDATE documents SET status='failed',error_code='retry_budget_exhausted'
            WHERE id IN (SELECT document_id FROM jobs WHERE state='running' AND attempts>=3 AND lease_until<?)
            AND tombstone IS NULL""", (time.time(),))
            conn.execute("UPDATE jobs SET state='failed',stage='retry_budget_exhausted' WHERE state='running' AND attempts>=3 AND lease_until<?", (time.time(),))
            return None
        token = uuid.uuid4().hex
        conn.execute("UPDATE jobs SET state='running',attempts=attempts+1,lease_token=?,lease_until=?,updated=? WHERE id=?", (token, time.time() + LEASE_SECONDS, now(), row["id"]))
        conn.execute("UPDATE documents SET status='processing',error_code=NULL WHERE id=?", (row["document_id"],))
        job = dict(row)
        job["lease_token"] = token
        return job


def checkpoint(job, stage, source=None, result=None, final=False, error=None):
    with transaction() as conn:
        active = conn.execute("""SELECT d.* FROM documents d JOIN jobs j ON j.document_id=d.id
        WHERE d.id=? AND d.epoch=? AND d.tombstone IS NULL AND j.state='running' AND j.lease_token=?""",
                              (job["document_id"], job["epoch"], job["lease_token"])).fetchone()
        if not active:
            return False
        state = "failed" if error else "complete" if final else "running"
        conn.execute("UPDATE jobs SET stage=?,state=?,lease_until=?,updated=? WHERE id=?", (stage, state, time.time()+LEASE_SECONDS, now(), job["id"]))
        if source is not None:
            conn.execute("UPDATE documents SET source=? WHERE id=?", (json.dumps(source), job["document_id"]))
        if result is not None:
            conn.execute("UPDATE documents SET result=? WHERE id=?", (json.dumps(result), job["document_id"]))
        if final or error:
            status = "failed" if error else "partial" if result and result.get("coverage") == "partial" else "ready"
            conn.execute("UPDATE documents SET status=?,error_code=? WHERE id=?", (status, error, job["document_id"]))
        return True


def reserve_call(job):
    with transaction() as conn:
        cursor = conn.execute("""UPDATE documents SET ai_calls=ai_calls+1 WHERE id=? AND epoch=?
        AND tombstone IS NULL AND ai_calls<? AND EXISTS(
        SELECT 1 FROM jobs WHERE document_id=? AND state='running' AND lease_token=?)""",
                              (job["document_id"], job["epoch"], settings().max_ai_calls_per_document,
                               job["document_id"], job["lease_token"]))
        return cursor.rowcount == 1


def run_once():
    job = claim()
    if job is None:
        return False
    try:
        with transaction() as conn:
            doc = dict(conn.execute("SELECT * FROM documents WHERE id=?", (job["document_id"],)).fetchone())
        if not checkpoint(job, "extracting"):
            return True
        source = json.loads(doc["source"]) if doc["source"] else parse_in_process(doc)
        result = json.loads(doc["result"]) if doc["result"] else {
            "findings": [], "completed_blocks": [], "coverage": source["coverage"],
            "provenance": pipeline.provenance(doc["mode"]),
            "limitations": list(source["warnings"]),
        }
        if not checkpoint(job, "source_ready", source, result):
            return True
        if doc["mode"] == "demo":
            from app.review.sample import findings
            result["findings"] = findings(source)
            result["limitations"].append("Synthetic fixture only; no AI provider was used.")
        elif doc["mode"] == "manual":
            result["limitations"].append("Manual review mode: no AI issue spotting or legal assessment was performed.")
        elif source["coverage"] != "readable":
            result["coverage"] = "partial"
            result["limitations"].append("AI analysis withheld because source extraction is incomplete.")
        else:
            # Small batches bound input size. Each checkpoint preserves validated work.
            blocks = source["blocks"]
            for offset in range(0, len(blocks), 4):
                batch = blocks[offset:offset+4]
                if all(b["id"] in result["completed_blocks"] for b in batch):
                    continue
                if not checkpoint(job, "issue_spotting"):
                    return True
                if not reserve_call(job):
                    raise ValueError("ai_budget_or_cancellation")
                observations = pipeline.generate(batch, json.loads(doc["context"]))
                if len(result["findings"]) + len(observations) > 200:
                    raise ValueError("observation_limit")
                for f in observations:
                    f["id"] = f"{offset}-{f['id']}"
                result["findings"].extend(observations)
                result["completed_blocks"].extend(b["id"] for b in batch)
                if not checkpoint(job, "validating_evidence", result=result):
                    return True
        checkpoint(job, "ready_for_human_review", result=result, final=True)
    except Exception as exc:
        allowed = {"no_readable_text", "page_limit", "extracted_text_limit", "invalid_text_encoding",
                   "password_protected", "archive_limit", "archive_expansion_limit", "invalid_docx",
                   "external_relationship_not_supported", "malformed_document", "ai_budget_or_cancellation"}
        code = str(exc) if str(exc) in allowed else "processing_failed"
        checkpoint(job, code, error=code)
        logger.warning("review_job_failed job=%s code=%s", job["id"], code)
    return True


def tombstone(conn, doc):
    timestamp = now()
    conn.execute("""UPDATE documents SET tombstone=?,status='deleted',epoch=epoch+1,
    source=NULL,result=NULL,context='{}',filename='Deleted document',hash='',error_code=NULL
    WHERE id=? AND tombstone IS NULL""", (timestamp, doc["id"]))
    conn.execute("UPDATE jobs SET state='cancelled',stage='deleted',updated=? WHERE document_id=?", (timestamp, doc["id"]))
    conn.execute("DELETE FROM decisions WHERE document_id=?", (doc["id"],))
    conn.execute("DELETE FROM decision_events WHERE document_id=?", (doc["id"],))
    conn.execute("""INSERT OR IGNORE INTO deletions(document_id,workspace,owner,requested,state,backup_policy,provider_policy)
    VALUES(?,?,?,?,'pending',?,?)""", (doc["id"], doc["workspace"], doc["owner"], timestamp,
                                     settings().backup_retention, settings().provider_retention if doc["mode"] == "live" else "No provider calls for this document."))


def sweep():
    with transaction() as conn:
        for row in conn.execute("SELECT * FROM documents WHERE tombstone IS NULL AND retention_until<=?", (now(),)).fetchall():
            tombstone(conn, dict(row))
        pending = [dict(r) for r in conn.execute("SELECT d.id,d.kind FROM documents d JOIN deletions x ON x.document_id=d.id WHERE x.state!='complete'")]
    for doc in pending:
        try:
            object_path(doc["id"], doc["kind"]).unlink(missing_ok=True)
            with transaction() as conn:
                conn.execute("UPDATE deletions SET state='complete',completed=?,error_code=NULL WHERE document_id=?", (now(), doc["id"]))
        except OSError:
            with transaction() as conn:
                conn.execute("UPDATE deletions SET error_code='file_purge_pending' WHERE document_id=?", (doc["id"],))
    # Files written before a failed DB commit are reconciled after a grace period.
    directory = settings().data_dir.resolve() / "uploads"
    for path in directory.glob("*.*"):
        if path.is_file() and path.stat().st_mtime < time.time()-3600:
            with transaction() as conn:
                exists = conn.execute("SELECT 1 FROM documents WHERE id=?", (path.stem,)).fetchone()
            if not exists:
                path.unlink(missing_ok=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if "--once" in sys.argv:
        sweep()
        run_once()
    else:
        while True:
            sweep()
            if not run_once():
                time.sleep(2)
