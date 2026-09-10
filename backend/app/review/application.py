import asyncio
import hashlib
import hmac
import json
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.review.routes import router
from app.review.auth import resolve_principal
from app.review import pages  # noqa: F401 — registers authenticated page routes
from app.review.settings import settings
from app.review.store import transaction


class Admission:
    """Bound bytes before multipart spooling; authorize before reading bodies."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        path = scope["path"]
        if path.startswith("/api/v2/") and path not in {'/api/v2/demo-session', '/api/v2/public-config'} and scope["method"] != "OPTIONS":
            auth = headers.get(b"authorization", b"").decode("latin1")
            token = auth[7:] if auth.lower().startswith("bearer ") else ""
            if resolve_principal(token) is None:
                return await JSONResponse({"detail": "A valid workspace access token is required."}, status_code=401)(scope, receive, send)
        limit = settings().max_bytes + 65536 if path == "/api/v2/documents" else 65536
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Invalid request length."}, status_code=400)(scope, receive, send)
        if declared > limit:
            return await JSONResponse({"detail": "Request body exceeds the allowed size."}, status_code=413)(scope, receive, send)
        consumed = 0

        async def bounded_receive():
            nonlocal consumed
            try:
                message = await asyncio.wait_for(receive(), timeout=30)
            except asyncio.TimeoutError:
                raise HTTPException(408, "Upload timed out. Retry with the same request key.")
            consumed += len(message.get("body", b""))
            if consumed > limit:
                raise HTTPException(413, "Request body exceeds the allowed size.")
            return message

        async def private_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [
                    (b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"content-security-policy", b"default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'"),
                ]
            await send(message)
        return await self.app(scope, bounded_receive, private_send)


app = FastAPI(title="Contract Review Assistant", version="2.0.0", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(Admission)
app.add_middleware(CORSMiddleware, allow_origins=settings().allowed_origins.split(","),
                   allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "DELETE"],
                   allow_headers=["Authorization", "Content-Type", "Idempotency-Key"])
app.include_router(router)


@app.exception_handler(sqlite3.Error)
async def storage_unavailable(_request, _exc):
    return JSONResponse({"detail": "Review storage unavailable. Ask the operator to check readiness."}, status_code=503)


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": settings().mode, "version": "2"}


@app.get("/api/ready")
def ready():
    try:
        with transaction() as conn:
            version = conn.execute("SELECT version FROM schema_version").fetchone()[0]
        if version != 1:
            raise ValueError("schema")
    except (sqlite3.Error, ValueError, TypeError):
        raise HTTPException(503, "Review datastore is not initialized or available.")
    return {"status": "ready", "mode": settings().mode, "note": "Worker activity and release gates must be checked separately."}
