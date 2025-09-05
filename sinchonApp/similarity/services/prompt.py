# similarity/services/prompt.py
import json
from textwrap import dedent

SYSTEM_MSG = (
    "당신은 한국의 사기, 보이스피싱, 종교 포섭, 마약 권유 등 다양한 피해 사례를 분석하는 전문가입니다. "
    "목표는 사용자가 입력한 사례를 검토하고, DB 후보(ref_cases)를 비교해 "
    "위험 수준, 유사 사례 ID, 공통 수법, 맞춤 대응(actions)을 JSON 하나의 객체로 제안하는 것입니다. "
    "사실 단정 금지, 개인정보(전화/계좌/URL) 복원·추정 금지, 마스킹 유지. "
    "JSON 외 텍스트 금지. 모든 필드는 반드시 채울 것. "
    "유사도(similarity)와 사기 가능성(scam_likelihood)은 0.00~1.00 범위. "
    "reasons/matched_methods는 핵심 키워드 위주. "
    "actions는 사례에 맞는 2~5개 실행 가능한 권고만 제안하세요."
)

def render_rerank_prompt(user_title: str, user_body: str, category: str, ref_cards: list[dict]) -> str:
    # 토큰 절약: 최대 20건
    ref_cards_trimmed = ref_cards[:20]
    return dedent(f"""
    [User]
    # 입력 사례
    카테고리: {category}
    제목: {user_title}
    본문: {user_body}

    # 후보 사례들(요약·마스킹, 최대 20건)
    {json.dumps(ref_cards_trimmed, ensure_ascii=False)}

    # 요구 출력(JSON 스키마)
    {{
      "ranked": [
        {{
          "id": "문자열",
          "similarity": 0.0,
          "scam_likelihood": 0.0,
          "reasons": ["키워드1","키워드2"],
          "matched_methods": ["수법1","수법2"],
          "actions": ["대응1","대응2"]
        }}
      ],
      "overall": {{
        "risk_level": "low|mid|high",
        "top_ids": ["...","..."]
      }}
    }}
    """).strip()
