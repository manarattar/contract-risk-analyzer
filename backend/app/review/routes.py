import hashlib
import html
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.review.auth import Principal, can_write, owned, principal
from app.review.ingestion import object_path, receive
from app.review.jobs import tombstone
from app.review.models import Annotation, Compare, CompleteReview, Context, Decision, Question
from app.review.pipeline import source_search
from app.review.settings import settings
from app.review.store import now, transaction

router = APIRouter(prefix="/api/v2")


@router.get('/public-config')
def public_config():
    return {'public_demo': settings().public_demo_enabled and settings().mode != 'disabled', 'accounts':settings().accounts_enabled, 'public_signup':settings().public_signup_enabled}


@router.post('/demo-session')
def public_demo(request: Request):
    from app.review.demo_access import issue_demo
    return issue_demo(request)


def public_document(doc):
    return {k: doc[k] for k in ("id", "filename", "status", "mode", "created", "retention_until", "error_code", "revision", "review_complete")}


def enqueue(identifier, kind, filename, digest, context, mode, key, user):
    key = key.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,100}", key):
        raise HTTPException(400, "A stable idempotency key of 16–100 safe characters is required.")
    encoded = context.model_dump_json()
    with transaction() as conn:
        existing = conn.execute("SELECT * FROM documents WHERE workspace=? AND owner=? AND idempotency=?", (user.workspace_id, user.id, key)).fetchone()
        if existing:
            if existing["tombstone"]:
                raise HTTPException(409, "This request was deleted. Start a new review.")
            if existing["hash"] != digest or existing["context"] != encoded:
                raise HTTPException(409, "Idempotency key already used for different content/context.")
            return public_document(existing)
        if conn.execute("SELECT count(*) FROM documents WHERE tombstone IS NULL").fetchone()[0] >= settings().max_active_documents:
            raise HTTPException(429, "Trial document capacity reached. Please retry later.")
        count = conn.execute("SELECT count(*) FROM documents WHERE workspace=? AND tombstone IS NULL", (user.workspace_id,)).fetchone()[0]
        if count >= (2 if user.demo else settings().max_documents):
            raise HTTPException(429, "Workspace document quota reached.")
        if user.demo and conn.execute("SELECT count(*) FROM documents WHERE owner LIKE 'demo-%' AND tombstone IS NULL").fetchone()[0] >= 200:
            raise HTTPException(429, 'Public demo capacity reached. Please retry later.')
        created = now()
        expiry = (datetime.now(timezone.utc) + (timedelta(minutes=30) if user.demo else timedelta(days=settings().retention_days))).isoformat()
        conn.execute("""INSERT INTO documents(id,workspace,owner,filename,kind,hash,context,mode,status,created,retention_until,idempotency)
        VALUES(?,?,?,?,?,?,?,?,'queued',?,?,?)""", (identifier, user.workspace_id, user.id, filename, kind, digest, encoded, mode, created, expiry, key))
        conn.execute("INSERT INTO jobs(id,document_id,state,stage,updated) VALUES(?,?,'queued','waiting_for_worker',?)", (uuid.uuid4().hex, identifier, created))
        return public_document(conn.execute("SELECT * FROM documents WHERE id=?", (identifier,)).fetchone())


@router.get("/session")
def session(user: Principal = Depends(principal)):
    cfg = settings()
    return {"principal": {"id": user.id, 'display_name':'Demo reviewer' if user.demo else user.display_name or user.id, "workspace_id": user.workspace_id, "role": user.role},
            "mode": 'demo' if user.demo else cfg.mode, "demo": user.demo, "upload_enabled": cfg.upload_enabled and not user.demo, "retention_days": cfg.retention_days,
            "privacy": cfg.privacy_description, "provider": cfg.provider_name,
            "provider_retention": cfg.provider_retention, "backup_retention": cfg.backup_retention,
            "limitations": ["Issue spotting for human review, not legal advice.",
                            "Q&A returns matching source passages, not legal conclusions.",
                            "PDF original pages require renderer approval. OCR and legal-quality certification are not available."]}


@router.get("/documents")
def library(offset: int = Query(0, ge=0), user: Principal = Depends(principal)):
    with transaction() as conn:
        rows = conn.execute("SELECT * FROM documents WHERE workspace=? AND owner=? AND tombstone IS NULL AND retention_until>? ORDER BY created DESC LIMIT 21 OFFSET ?", (user.workspace_id, user.id, now(), offset)).fetchall()
    return {"items": [public_document(r) for r in rows[:20]], "next_offset": offset+20 if len(rows)>20 else None}


@router.post("/documents", status_code=202)
async def upload(file: UploadFile = File(...), context: str = Form(...),
                 privacy_acknowledged: bool = Form(False), idempotency_key: str = Header(...),
                 user: Principal = Depends(principal)):
    can_write(user)
    if user.demo:
        raise HTTPException(403, 'Public demo accepts synthetic examples only. Sign in privately to upload.')
    if not settings().upload_enabled:
        raise HTTPException(403, "Uploads are disabled until parser isolation and data handling are approved.")
    if not privacy_acknowledged:
        raise HTTPException(422, "Acknowledge the configured data handling before upload.")
    try:
        ctx = Context.model_validate_json(context)
    except ValidationError:
        raise HTTPException(422, "Review context is invalid.")
    if settings().mode == "live" and (not ctx.confirmed or ctx.contract_type == "Unknown"):
        raise HTTPException(422, "Confirm supported contract context before live issue spotting.")
    identifier, kind, filename, digest = await receive(file)
    try:
        result = enqueue(identifier, kind, filename, digest, ctx, settings().mode, idempotency_key, user)
        if result["id"] != identifier:
            object_path(identifier, kind).unlink(missing_ok=True)
        return result
    except BaseException:
        object_path(identifier, kind).unlink(missing_ok=True)
        raise


@router.post("/sample", status_code=202)
def sample(idempotency_key: str = Header(...), pdf: bool = False, user: Principal = Depends(principal)):
    can_write(user)
    if settings().mode == "disabled":
        raise HTTPException(403, "Review service is disabled.")
    from app.review.sample import TEXT, pdf_bytes
    identifier = uuid.uuid4().hex
    kind = 'pdf' if pdf else 'txt'
    content = pdf_bytes() if pdf else TEXT.encode('utf-8')
    path = object_path(identifier, kind)
    path.write_bytes(content)
    try:
        result = enqueue(identifier, kind, f"Synthetic services agreement.{kind}", hashlib.sha256(content).hexdigest(), Context(contract_type="Services agreement", party="Example Customer", role="Customer", objectives=["Liability"], confirmed=True), "demo", idempotency_key, user)
        if result["id"] != identifier:
            path.unlink(missing_ok=True)
        return result
    except BaseException:
        path.unlink(missing_ok=True)
        raise


@router.get("/documents/{document_id}")
def document(document_id: str, user: Principal = Depends(principal)):
    with transaction() as conn:
        doc = owned(conn, document_id, user)
        job = dict(conn.execute("SELECT id,state,stage,attempts,updated FROM jobs WHERE document_id=?", (document_id,)).fetchone())
        decisions = [dict(r) for r in conn.execute("SELECT * FROM decisions WHERE document_id=?", (document_id,))]
    source = json.loads(doc["source"]) if doc["source"] else None
    result = json.loads(doc["result"]) if doc["result"] else None
    # A failed/retried run never appears complete merely because checkpoints exist.
    if result and doc["status"] not in {"ready", "partial"}:
        result["coverage"] = "partial"
    return {**public_document(doc), "hash": doc["hash"], "context": json.loads(doc["context"]),
            "job": job, "result": result, "decisions": decisions,
            "source": {k: v for k, v in source.items() if k != "blocks"} | {"block_count": len(source["blocks"])} if source else None}


@router.get("/documents/{document_id}/source")
def source(document_id: str, offset: int = Query(0, ge=0), block_id: str | None = None, user: Principal = Depends(principal)):
    with transaction() as conn:
        doc = owned(conn, document_id, user)
    if not doc["source"]:
        raise HTTPException(409, "Source extraction is not ready.")
    blocks = json.loads(doc["source"])["blocks"]
    if block_id is not None:
        matches = [i for i, b in enumerate(blocks) if b["id"] == block_id]
        if not matches:
            raise HTTPException(404, "Source span not found.")
        offset = matches[0]
    return {"blocks": blocks[offset:offset+10], "offset": offset, "next_offset": offset+10 if offset+10<len(blocks) else None}


@router.post("/documents/{document_id}/retry", status_code=202)
def retry(document_id: str, user: Principal = Depends(principal)):
    can_write(user)
    with transaction() as conn:
        doc = owned(conn, document_id, user)
        job = conn.execute("SELECT * FROM jobs WHERE document_id=?", (document_id,)).fetchone()
        if doc["status"] not in {"failed", "cancelled"} or job["attempts"] >= 3:
            raise HTTPException(409, "This job cannot be retried. Check the error or replace the file.")
        conn.execute("UPDATE documents SET status='queued',error_code=NULL WHERE id=?", (document_id,))
        conn.execute("UPDATE jobs SET state='queued',stage='retry_queued',epoch=?,updated=? WHERE document_id=?", (doc["epoch"], now(), document_id))
    return {"status": "queued"}


@router.post("/documents/{document_id}/cancel")
def cancel(document_id: str, user: Principal = Depends(principal)):
    can_write(user)
    with transaction() as conn:
        doc = owned(conn, document_id, user)
        if doc["status"] in {"queued", "processing"}:
            conn.execute("UPDATE documents SET epoch=epoch+1,status='cancelled' WHERE id=?", (document_id,))
            conn.execute("UPDATE jobs SET state='cancelled',stage='cancelled',updated=? WHERE document_id=?", (now(), document_id))
    return {"status": "cancelled", "note": "Late results cannot be saved. An already sent provider request may still incur cost."}


@router.patch("/documents/{document_id}/findings/{finding_id}")
def decide(document_id: str, finding_id: str, payload: Decision, user: Principal = Depends(principal)):
    can_write(user)
    if payload.status in {"dismissed", "edited", "escalated"} and not payload.note:
        raise HTTPException(422, "Explain this decision in a reviewer note.")
    with transaction() as conn:
        doc = owned(conn, document_id, user)
        if doc["status"] not in {"ready", "partial"}:
            raise HTTPException(409, "Wait for processing before saving decisions.")
        result = json.loads(doc["result"])
        if finding_id not in {f["id"] for f in result["findings"]}:
            raise HTTPException(404, "Finding not found.")
        old = conn.execute("SELECT version FROM decisions WHERE document_id=? AND finding_id=?", (document_id, finding_id)).fetchone()
        version = old[0] if old else 0
        if version != payload.version:
            raise HTTPException(409, "This decision changed. Refresh and reconcile your saved draft.")
        timestamp = now()
        conn.execute("""INSERT INTO decisions VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(document_id,finding_id) DO UPDATE SET actor=excluded.actor,status=excluded.status,
        note=excluded.note,revision_text=excluded.revision_text,version=excluded.version,updated=excluded.updated""",
                     (document_id, finding_id, user.id, payload.status, payload.note, payload.revision_text, version+1, timestamp))
        conn.execute("INSERT INTO decision_events VALUES(?,?,?,?,?,?)", (uuid.uuid4().hex, document_id, finding_id, user.id, payload.model_dump_json(), timestamp))
        conn.execute("UPDATE documents SET revision=revision+1,review_complete=0 WHERE id=?", (document_id,))
    return {"version": version+1, "status": payload.status, "updated": timestamp}


@router.post("/documents/{document_id}/complete")
def complete(document_id: str, payload: CompleteReview, user: Principal = Depends(principal)):
    can_write(user)
    with transaction() as conn:
        doc = owned(conn, document_id, user)
        if doc["revision"] != payload.revision or doc["status"] not in {"ready", "partial"}:
            raise HTTPException(409, "Refresh the review before completing it.")
        if not payload.acknowledge_incomplete:
            raise HTTPException(422, "Acknowledge that completing a review does not approve signing or prove document completeness.")
        result = json.loads(doc["result"])
        decisions = {r["finding_id"]: r["status"] for r in conn.execute("SELECT * FROM decisions WHERE document_id=?", (document_id,))}
        if any(decisions.get(f["id"], "unreviewed") == "unreviewed" for f in result["findings"]):
            raise HTTPException(409, "Decide or explicitly escalate every observation first.")
        conn.execute("UPDATE documents SET review_complete=1,revision=revision+1 WHERE id=?", (document_id,))
    return {"review_complete": True}


@router.post("/documents/{document_id}/annotations", status_code=201)
def annotate(document_id: str, payload: Annotation, user: Principal = Depends(principal)):
    can_write(user)
    with transaction() as conn:
        doc = owned(conn, document_id, user)
        if doc["status"] not in {"ready", "partial"}:
            raise HTTPException(409, "Wait for extraction to finish before annotating.")
        source = json.loads(doc["source"])
        block = next((b for b in source["blocks"] if b["id"] == payload.block_id), None)
        if block is None:
            raise HTTPException(404, "Source block not found.")
        result = json.loads(doc["result"])
        if len(result["findings"]) >= 200:
            raise HTTPException(422, "This review has reached its observation limit.")
        identifier = "human-" + uuid.uuid4().hex
        result["findings"].append({"id": identifier, "title": payload.title,
            "explanation": payload.note, "impact": "Not assessed", "uncertainty": "Reviewer-authored note; legal interpretation has not been independently verified.",
            "action": "Review this note and record a decision.", "business_preference": "Unknown",
            "evidence_status": f"Human annotation by {user.id}",
            "citations": [{"block_id": block["id"], "quote": block["text"], "start": 0,
                           "end": len(block["text"]), "location": block["location"]}]})
        conn.execute("UPDATE documents SET result=?,revision=revision+1,review_complete=0 WHERE id=?", (json.dumps(result), document_id))
        conn.execute("INSERT INTO decision_events VALUES(?,?,?,?,?,?)", (uuid.uuid4().hex, document_id, identifier, user.id, payload.model_dump_json(), now()))
    return {"finding_id": identifier}


@router.post("/documents/{document_id}/questions")
def question(document_id: str, payload: Question, user: Principal = Depends(principal)):
    with transaction() as conn:
        doc = owned(conn, document_id, user)
    if not doc["source"]:
        raise HTTPException(409, "Source extraction is not ready.")
    if re.search(r"sign|enforceab|legal advice|compliant", payload.question, re.I):
        return {"status": "abstained", "answer": "This assistant cannot determine legal enforceability or whether you should sign. Ask a qualified legal reviewer.", "sources": []}
    matches = source_search(json.loads(doc["source"]), payload.question)
    return {"status": "passages" if matches else "abstained",
            "answer": "Matching passages below. Verify whether they answer your question; no synthesized conclusion was generated." if matches else "I could not locate matching support in the extracted text. This does not establish that the term is absent.",
            "sources": matches, "coverage": json.loads(doc["source"])["coverage"], "mode": doc["mode"]}


@router.post("/comparisons")
def compare(payload: Compare, user: Principal = Depends(principal)):
    with transaction() as conn:
        a = owned(conn, payload.baseline_id, user)
        b = owned(conn, payload.revised_id, user)
    if not a["source"] or not b["source"]:
        raise HTTPException(409, "Both documents need readable source text.")
    if a["context"] != b["context"]:
        raise HTTPException(409, "Comparison requires matching review context.")
    blocks_a = json.loads(a["source"])["blocks"]
    blocks_b = json.loads(b["source"])["blocks"]
    # Sequence alignment preserves repeated clauses and split/merged groups. It is
    # intentionally labelled a candidate, never a semantic equivalence claim.
    matcher = SequenceMatcher(None, [x["text"] for x in blocks_a], [x["text"] for x in blocks_b], autojunk=False)
    changes = []
    for tag, i, j, k, l in matcher.get_opcodes():
        if tag == "equal":
            continue
        old, new = blocks_a[i:j], blocks_b[k:l]
        text_a, text_b = "\n".join(x["text"] for x in old), "\n".join(x["text"] for x in new)
        changed_values = re.findall(r"\b\d+(?:[.,]\d+)?\b|\b(?:days?|months?|years?|shall|must|may|not|except|unless)\b", text_a, re.I) != re.findall(r"\b\d+(?:[.,]\d+)?\b|\b(?:days?|months?|years?|shall|must|may|not|except|unless)\b", text_b, re.I)
        changes.append({"kind": {"replace": "Changed", "insert": "Added", "delete": "Removed"}[tag],
                        "baseline": old, "revised": new,
                        "assessment": "Potential amount, timing, duty or exception change; verify meaning." if changed_values else "Wording or structure changed; substantive effect needs human review.",
                        "alignment": "Candidate alignment; moved or split clauses may require manual reconciliation."})
    return {"baseline": public_document(a), "revised": public_document(b), "changes": changes,
            "limitations": "Text-based candidate alignment, not a legal risk comparison. No overall winner. Unreadable material is excluded."}


@router.get("/documents/{document_id}/export", response_class=HTMLResponse)
def export(document_id: str, include_dismissed: bool = False, user: Principal = Depends(principal)):
    with transaction() as conn:
        doc = owned(conn, document_id, user)
        decisions = {r["finding_id"]: dict(r) for r in conn.execute("SELECT * FROM decisions WHERE document_id=?", (document_id,))}
    if not doc["result"]:
        raise HTTPException(409, "No review record is available yet.")
    result = json.loads(doc["result"])
    esc = lambda value: html.escape(str(value), quote=True)
    if doc["status"] not in {"ready", "partial"}:
        result["coverage"] = "partial — processing did not complete"
    sections = []
    for f in result["findings"]:
        d = decisions.get(f["id"], {})
        if d.get("status") == "dismissed" and not include_dismissed:
            continue
        citations = "".join(f"<blockquote>{esc(c['quote'])}<footer>{esc(c['location'])} · {esc(c['block_id'])}</footer></blockquote>" for c in f["citations"])
        sections.append(f"<section><h2>{esc(f['title'])}</h2><p>{esc(f['explanation'])}</p>{citations}<p>Uncertainty: {esc(f['uncertainty'])}</p><p>Suggested action for review: {esc(f['action'])}</p><p>Decision: {esc(d.get('status','unreviewed'))} · {esc(d.get('actor',''))} · {esc(d.get('updated',''))}</p><p>Reviewer note: {esc(d.get('note',''))}</p><p>Reviewer draft: {esc(d.get('revision_text',''))}</p></section>")
    status = "Human review recorded; not approval to sign" if doc["review_complete"] else "Incomplete human review"
    content = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Contract review record</title>
    <style>body{{max-width:850px;margin:2rem auto;padding:1rem;font:1rem/1.6 system-ui;color:#172c31}}blockquote{{border-left:3px solid #155b50;padding:1rem}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}section{{border-top:1px solid #aaa;padding-top:1rem}}</style>
    <main><h1>{esc(doc['filename'])}</h1><p><strong>{status}</strong></p><p>Issue spotting for human review. Not legal advice. {esc(doc['mode'])} mode.</p>
    <p>Generated {esc(now())} · source hash {esc(doc['hash'])} · review revision {doc['revision']}</p><h2>Context and coverage</h2><pre>{esc(doc['context'])}</pre><p>Processing state: {esc(doc['status'])}. Coverage: {esc(result['coverage'])}. Source completeness requires human confirmation.</p>
    <pre>{esc(json.dumps(result['provenance'],indent=2))}</pre><ul>{''.join('<li>'+esc(x)+'</li>' for x in result['limitations'])}</ul>
    {''.join(sections) or '<p>No generated observations. This does not establish the absence of issues.</p>'}</main></html>"""
    return HTMLResponse(content, headers={"Content-Disposition": 'attachment; filename="review-record.html"'})


@router.delete("/documents/{document_id}", status_code=202)
def delete(document_id: str, user: Principal = Depends(principal)):
    can_write(user)
    with transaction() as conn:
        doc = owned(conn, document_id, user, deleted=True)
        tombstone(conn, doc)
    return {"document_id": document_id, "status": "pending", "note": "Access revoked. Worker will purge remaining local files. Backup/provider policies still apply."}


@router.get("/deletions/{document_id}")
def deletion(document_id: str, user: Principal = Depends(principal)):
    with transaction() as conn:
        row = conn.execute("SELECT * FROM deletions WHERE document_id=? AND workspace=? AND owner=?", (document_id, user.workspace_id, user.id)).fetchone()
    if not row:
        raise HTTPException(404, "Receipt not found.")
    return dict(row)
