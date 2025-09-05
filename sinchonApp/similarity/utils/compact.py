# similarity/utils/compact.py
from datetime import datetime

def clip(s: str, n: int) -> str:
    return (s[:n] + "…") if len(s) > n else s

def compact_case_row(row: dict) -> dict:
    """
    row 예시: {"id": "...", "title": "...", "body": "...", "created_at": datetime, "like_count": 3}
    PII 마스킹 후 3~4줄 카드 형태로 축약
    """
    from similarity.utils.pii import mask_all
    body = mask_all(row["body"] or "")
    body_line = " ".join(body.split())  # 개행/다중 공백 정리
    created = row["created_at"]
    when = created.strftime("%Y-%m-%d") if isinstance(created, datetime) else str(created)
    return {
        "id": str(row["id"]),
        "when": when,
        "title": clip(row["title"] or "", 60),
        "summary": clip(body_line, 160),
        "like": int(row.get("like_count", 0)),
    }
