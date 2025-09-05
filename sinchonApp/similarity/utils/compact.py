from datetime import datetime
from similarity.utils.pii import mask_all  # 함수 안 import보다 이게 낫습니다(성능/가독성)

def clip(s: str | None, n: int) -> str:
    s = (s or "").strip()
    return (s[:n] + "…") if len(s) > n else s

def compact_case_row(row: dict) -> dict:
    """
    row 예시: {"id": "...", "title": "...", "body": "...", "created_at": datetime|str|None, "like_count": 3}
    PII 마스킹 후 3~4줄 카드 형태로 축약
    """
    body = mask_all(row.get("body") or "")
    body_line = " ".join(body.split())

    created = row.get("created_at")
    when = (
        created.strftime("%Y-%m-%d") if isinstance(created, datetime)
        else (str(created) if created else "")
    )

    return {
        "id": str(row.get("id", "")),
        "when": when,
        "title": clip(row.get("title"), 60),
        "summary": clip(body_line, 160),
        "like": int(row.get("like_count") or 0),
    }