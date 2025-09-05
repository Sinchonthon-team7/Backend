# similarity/services/db_read.py
from django.db import connection

def fetch_cases_by_tag(tag: str):
    sql = """
    SELECT id, category, title, body, created_at
    FROM cases
    WHERE category = %s
    ORDER BY created_at DESC
    LIMIT 200;  -- 더미 적을 땐 넉넉히 불러오기
    """
    with connection.cursor() as cur:
        cur.execute(sql, [tag])
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
