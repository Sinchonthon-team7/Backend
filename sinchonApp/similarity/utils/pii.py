# similarity/utils/pii.py
import re
from urllib.parse import urlparse

PHONE_RE = re.compile(r'(?:\+?82[- ]?)?0?1[0-9][- ]?\d{3,4}[- ]?\d{4}')
ACCOUNT_RE = re.compile(r'\b\d{2,4}[- ]?\d{2,6}[- ]?\d{2,6}\b')

def mask_phone(text: str) -> str:
    def _m(m):
        digits = re.sub(r'\D', '', m.group())
        # 뒤 4자리만 노출
        return f"***-****-{digits[-4:]}"
    return PHONE_RE.sub(_m, text)

def mask_account(text: str) -> str:
    def _m(m):
        digits = re.sub(r'\D', '', m.group())
        return f"****-****-{digits[-4:]}"
    return ACCOUNT_RE.sub(_m, text)

def mask_urls(text: str) -> str:
    # 도메인만 남기고 경로는 제거
    def repl(m):
        u = urlparse(m.group(0))
        host = u.netloc or u.path
        return f"{host}/…"
    return re.sub(r'https?://[^\s)]+', repl, text)

def mask_all(text: str) -> str:
    return mask_urls(mask_account(mask_phone(text)))
