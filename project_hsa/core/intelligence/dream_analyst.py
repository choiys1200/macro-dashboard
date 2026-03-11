from __future__ import annotations

from typing import Dict

from openai import OpenAI

from core.intelligence.knowledge_manager import KnowledgeManager


class DreamAnalyst:
    def __init__(self, knowledge_manager: KnowledgeManager, model: str = "gpt-4o-mini") -> None:
        self.knowledge_manager = knowledge_manager
        self.client = OpenAI()
        self.model = model

    def analyze_dream(
        self,
        dream_text: str,
        saju_profile: Dict[str, object],
        mbti_profile: Dict[str, str],
    ) -> str:
        query = "활성화-종합 이론과 신호 처리 관점의 꿈 해석"
        context = self.knowledge_manager.retrieve_context(query)

        system_prompt = (
            "당신은 꿈 신호 분석 엔지니어다. 반드시 제공된 검색 결과(Context)만을 근거로 "
            "엔지니어링/데이터 관점에서 서술하라. Context에 없는 내용은 추측하지 마라."
        )

        user_prompt = (
            f"[입력 데이터]\n꿈 텍스트: {dream_text}\n사주 프로필: {saju_profile}\nMBTI 프로필: {mbti_profile}\n\n"
            f"[검색 결과 Context]\n{context}\n\n"
            "요구사항: 1) 현재 상태 신호 요약 2) 스트레스 원인 후보 3) 즉시 실험 가능한 회복 전략."
        )

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.output_text
