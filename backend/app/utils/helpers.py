from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def sanitize_filename(filename: str) -> str:
    return "".join(c for c in filename if c.isalnum() or c in (".", "_", "-")).strip()
