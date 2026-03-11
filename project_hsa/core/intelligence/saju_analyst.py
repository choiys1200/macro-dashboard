from __future__ import annotations

from typing import Dict

from openai import OpenAI

from core.intelligence.knowledge_manager import KnowledgeManager


class SajuAnalyst:
    def __init__(self, knowledge_manager: KnowledgeManager, model: str = "gpt-4o-mini") -> None:
        self.knowledge_manager = knowledge_manager
        self.client = OpenAI()
        self.model = model

    def generate_report(self, saju_profile: Dict[str, object], mbti_profile: Dict[str, str]) -> str:
        query = "오행 점수와 MBTI를 함께 해석하는 데이터 기반 기질 분석"
        context = self.knowledge_manager.retrieve_context(query)

        system_prompt = (
            "당신은 인간 시스템 분석 엔지니어다. 반드시 제공된 검색 결과(Context)만을 근거로 "
            "엔지니어링/데이터 관점에서 서술하라. Context에 없는 내용은 추측하지 마라."
        )

        user_prompt = (
            f"[입력 데이터]\n사주 프로필: {saju_profile}\nMBTI 프로필: {mbti_profile}\n\n"
            f"[검색 결과 Context]\n{context}\n\n"
            "요구사항: 1) 강점 2) 과부하 리스크 3) 적합한 환경을 항목별로 요약."
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
