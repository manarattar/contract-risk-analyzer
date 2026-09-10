import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReviewSettings(BaseSettings):
    # Separate prefix prevents old .env values from enabling a new capability.
    model_config = SettingsConfigDict(env_prefix="REVIEW_", extra="ignore", hide_input_in_errors=True)
    mode: Literal["disabled", "demo", "manual", "live"] = "disabled"
    data_dir: Path = Path("./data/review-v2")
    principals_json: str = "[]"
    upload_enabled: bool = False
    parser_isolation_approved: bool = False
    page_rendering_enabled: bool = False
    public_demo_enabled: bool = False
    demo_signing_key: str = ''
    provider_handling_approved: bool = False
    evaluation_approved: bool = False
    evaluation_report: Path | None = None
    provider_name: str = "Not configured"
    privacy_description: str = "Confidential uploads are not approved."
    provider_retention: str = "Not verified; do not submit confidential documents."
    backup_retention: str = "Not verified. Active deletion does not erase external backups."
    api_key: str = ""
    api_base_url: str = "https://api.openai.com/v1"
    model: str = ""
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    retention_days: int = Field(default=30, ge=1, le=365)
    max_bytes: int = Field(default=10 * 1024 * 1024, ge=1, le=10 * 1024 * 1024)
    max_pages: int = Field(default=50, ge=1, le=50)
    max_chars: int = Field(default=150000, ge=100, le=150000)
    max_documents: int = Field(default=100, ge=1, le=10000)
    max_requests_per_minute: int = Field(default=120, ge=1, le=1000)
    max_ai_calls_per_document: int = Field(default=20, ge=1, le=100)
    parser_timeout: int = Field(default=60, ge=1, le=60)

    @model_validator(mode="after")
    def validate_controls(self):
        if self.public_demo_enabled and len(self.demo_signing_key) < 32:
            raise ValueError('Public demo requires a high-entropy signing key')
        principals = json.loads(self.principals_json)
        seen = set()
        if not isinstance(principals, list):
            raise ValueError("Principals must be a JSON list")
        for p in principals:
            if set(p) != {"id", "workspace_id", "role", "token_sha256"}:
                raise ValueError("Invalid principal fields")
            digest = p["token_sha256"]
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("Use SHA256 of a high-entropy invite token")
            if digest in seen or not p["id"] or not p["workspace_id"]:
                raise ValueError("Duplicate token or empty identity")
            seen.add(digest)
            if p["role"] not in {"viewer", "reviewer", "owner"}:
                raise ValueError("Invalid role")
        if "*" in self.allowed_origins:
            raise ValueError("Explicit origins required")
        if self.upload_enabled and (self.mode not in {"manual", "live"} or not self.parser_isolation_approved):
            raise ValueError("Uploads require manual/live mode and approved parser isolation")
        if self.page_rendering_enabled and not self.parser_isolation_approved:
            raise ValueError("Page rendering requires approved renderer isolation")
        if self.mode == "live" and not all([
            self.provider_handling_approved, self.evaluation_approved,
            self.api_key, self.model, self.api_base_url.startswith("https://"),
        ]):
            raise ValueError("Live analysis requires explicit provider/evaluation approval and HTTPS configuration")
        if self.mode == "live":
            from app.review.evaluation import release_gate
            from app.review.pipeline import PROMPT_HASH
            if not self.evaluation_report or not self.evaluation_report.is_file():
                raise ValueError("Live analysis requires a version-matched adjudicated evaluation report")
            report = json.loads(self.evaluation_report.read_text(encoding="utf-8"))
            if not release_gate(report)["eligible"] or report.get("model_version") != self.model or report.get("prompt_hash") != PROMPT_HASH or report.get("parser_version") != "source-blocks-1":
                raise ValueError("The evaluation report does not approve this pipeline version")
        return self


@lru_cache
def settings():
    return ReviewSettings()
