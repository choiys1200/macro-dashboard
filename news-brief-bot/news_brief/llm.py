"""LLM provider 래퍼.

모든 LLM 호출은 chat() 하나로 통일한다. 모델 교체·프로바이더 교체 시
이 파일과 config.py의 모델명만 바꾸면 된다.
NEWS_BRIEF_MOCK_LLM=1 이면 네트워크 없이 결정적 응답을 반환한다(파이프라인 점검용).
"""

from __future__ import annotations

import logging

from . import config

log = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI

        kwargs: dict = {"api_key": config.OPENAI_API_KEY}
        if config.OPENAI_BASE_URL:
            kwargs["base_url"] = config.OPENAI_BASE_URL
        _client = OpenAI(**kwargs)
    return _client


def _mock_response(system: str, user: str, max_tokens: int) -> str:
    if "카테고리" in system or "카테고리" in user:
        return "[정치] (MOCK) 첫 번째 문장입니다. 두 번째 문장입니다. 세 번째 문장입니다."
    return (
        "## 오늘 한눈에 보기\n- (MOCK) 리포트 생성 경로 점검용 응답입니다.\n\n"
        "## 오늘의 주요 뉴스 Top 5\n- (MOCK)\n\n"
        "## 보수 매체에서만 눈에 띈 뉴스\n- (MOCK)\n\n"
        "## 한국 독자에게 중요한 포인트\n- (MOCK)\n\n"
        "## 오늘 추가로 볼 뉴스 3건\n- (MOCK)\n"
    )


def chat(
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float = 0.3,
) -> str:
    """단일 system+user 메시지 호출 후 응답 텍스트를 반환한다."""
    if config.MOCK_LLM:
        log.info("MOCK_LLM=1: %s 호출을 모의 응답으로 대체", model)
        return _mock_response(system, user, max_tokens)

    if not config.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY가 없습니다. .env.example을 복사해 .env를 만들고 키를 넣어주세요."
        )

    resp = _get_client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()
