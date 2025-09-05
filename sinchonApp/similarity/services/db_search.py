# similarity/services/db_search.py
from django.db import connection

def fetch_candidates_mysql(category: str, query_text: str, limit: int = 20):
    """
    1순위: MySQL FULLTEXT(title, body) 점수로 상위 K개
    2순위: FULLTEXT 미구성/오류 시 -> 최신순 LIMIT K (카테고리 필수)
    """
    q = (query_text or "").strip()
    try:
        # FULLTEXT 시도
        sql = """
        SELECT id, category, title, content, created_at
        FROM wasscam_post
        WHERE category = %s
        ORDER BY MATCH(title, body) AGAINST (%s IN NATURAL LANGUAGE MODE) DESC, created_at DESC
        LIMIT %s;
        """
        with connection.cursor() as cur:
            cur.execute(sql, [category, q, limit])
            cols = [c[0] for c in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        # FULLTEXT가 점수 0으로만 나올 경우 보완
        if not rows:
            raise RuntimeError("no rows from fulltext")
        return rows
    except Exception:
        # 폴백: 최신순
        sql = """
        SELECT id, category, title, content, created_at
        FROM wasscam_post
        WHERE category = %s
        ORDER BY created_at DESC
        LIMIT %s;
        """
        with connection.cursor() as cur:
            cur.execute(sql, [category, limit])
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]