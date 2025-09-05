#similarity/utils/phone.py
import re

# 한국 휴대폰 번호 정규식 (010, 011~019)
PHONE_RE = re.compile(
    r"(?:\+?82[- ]?)?0?1[0-9][- ]?\d{3,4}[- ]?\d{4}"
)

def normalize_kr_number(raw: str) -> str:
    """숫자만 남기고, 국내 휴대폰이면 0으로 시작 형태로 정규화."""
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    # +82로 시작하면 국내 형식으로 환원
    if digits.startswith("82") and not digits.startswith("820"):
        digits = "0" + digits[2:]
    # 길이 필터 (대략적인 검증)
    if len(digits) < 9 or len(digits) > 12:
        return digits
    return digits

def mask_phone_tail(num: str) -> str:
    d = re.sub(r"\D", "", num or "")
    if len(d) >= 4:
        return f"***-****-{d[-4:]}"
    return "***-****-****"

def extract_first_phone(text: str) -> str | None:
    """
    본문(text)에서 제일 먼저 등장하는 전화번호를 추출.
    없으면 None 반환.
    """
    if not text:
        return None
    m = PHONE_RE.search(text)
    if not m:
        return None
    return m.group()
