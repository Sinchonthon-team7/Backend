# similarity/views.py
import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response

from similarity.services.db_search import fetch_candidates_mysql
from similarity.services.prompt import SYSTEM_MSG, render_rerank_prompt
from similarity.services.llm import call_llm
from similarity.utils.compact import compact_case_row
from similarity.services.phone_check import check_spam_number
from similarity.utils.phone import normalize_kr_number, extract_first_phone

@method_decorator(csrf_exempt, name="dispatch")
class AssessView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # 0) 입력 파싱
        try:
            data = request.data if isinstance(request.data, dict) and request.data else json.loads(request.body or "{}")
        except Exception:
            return Response({"detail": "invalid JSON"}, status=400)

        category = (data.get("category") or "").strip()
        user_title = (data.get("title") or "").strip()
        user_body = (data.get("body") or "").strip()
        contacts = data.get("contacts", [])

        if not category or not user_title or not user_body:
            return Response({"detail": "category/title/body are required"}, status=400)

        # 1) 후보검색 (카테고리 내 상위 K)
        qtext = (user_title + " " + user_body)[:512]
        rows = fetch_candidates_mysql(category, qtext, limit=50)

        # 2) 카드 요약 (PII 마스킹 & 길이 제한)
        ref_cards = [compact_case_row(r) for r in rows]

        # 3) LLM 평가
        prompt = render_rerank_prompt(user_title, user_body, category, ref_cards)
        llm = call_llm(SYSTEM_MSG, prompt)
        if not llm.ok:
            return Response({"detail": llm.text}, status=502)

        try:
            out = json.loads(llm.text)
        except Exception:
            return Response({"detail": "LLM JSON parse failed", "raw": llm.text[:3000]}, status=502)

        # ranked 상위 3개 ID 추출 (문자열로 통일)
        ranked = out.get("ranked", []) or []
        top_ids = [str(x.get("id")) for x in ranked[:3] if x.get("id") is not None]

        # ref_cards를 id -> card 맵으로
        cards_by_id = {str(card["id"]): card for card in ref_cards}

        # LLM이 고른 순서대로 레퍼런스 구성 (존재하는 것만)
        references = [cards_by_id[i] for i in top_ids if i in cards_by_id]

        # 만약 비어 있으면(LLM이 엉뚱한 id를 준 경우) 안전하게 대체
        if not references:
            references = ref_cards[:3] 

        # 유사도 최대값(없으면 0)
        try:
            sim_top = max((float(x.get("similarity", 0)) for x in ranked), default=0.0)
        except Exception:
            sim_top = 0.0

        # 0) body에서 전화번호 자동 추출
        contact_num = None
        if isinstance(contacts, list) and contacts:
            contact_num = normalize_kr_number(str(contacts[0]))

        # body에서 추출 (contacts가 없을 때만)
        if not contact_num:
            body_phone = extract_first_phone(user_body)
            if body_phone:
                contact_num = normalize_kr_number(body_phone)

        # 전화번호 위험 스코어 계산
        phone_info = None
        def calc_contact_score():
            if not contact_num:
                return 0.0
            r = check_spam_number(contact_num, use_cache=True)
            if not r.ok:
                return 0.0
            base = min(1.0, r.spam_count / 1000.0)  # 신고 1000건 이상이면 1로 캡
            bonus = 0.0
            if (r.spam or "").strip():
                s = r.spam
                if "보이스피싱" in s: bonus = 0.3
                elif "사기" in s:     bonus = 0.2
                elif "광고" in s:     bonus = 0.05
            score = min(1.0, base + bonus)
            return score

        contact_freq = calc_contact_score()

        # 5) 합성 점수/라벨
        risk_score = 0.6 * sim_top + 0.4 * contact_freq
        label = "high" if risk_score >= 0.75 else ("mid" if risk_score >= 0.45 else "low")

        return Response({
            "label": label,
            "risk": round(risk_score, 3),
            "factors": {"sim_text": round(sim_top, 3), "contact_freq": round(contact_freq, 3)},
            "phone_check": phone_info or {},
            "llm": out,                  # ranked/overall 그대로 반환 (FE에서 top_ids 하이라이트)
            "references": references,
        }, status=200)

class PhoneCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    @method_decorator(csrf_exempt)
    def post(self, request):
        try:
            data = request.data if isinstance(request.data, dict) and request.data else json.loads(request.body or "{}")
        except Exception:
            return Response({"detail": "invalid JSON"}, status=400)

        num = (data.get("number") or "").strip()
        if not num:
            return Response({"detail": "number is required"}, status=400)

        res = check_spam_number(num, use_cache=True)
        return Response({
            "data": {
                "number": res.number,
                "spam": res.spam,
                "spam_count": res.spam_count,
                "registed_date": res.registed_date,
                "cyber_crime": res.cyber_crime,
                "success": res.success_code,
            },
            "meta": {"source": res.source}
        }, status=200 if res.ok else 502)
