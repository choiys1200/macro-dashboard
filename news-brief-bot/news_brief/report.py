"""최종 브리핑 리포트 생성 (상위 모델, 1회 호출) → data/YYYY-MM-DD/report.md"""

from __future__ import annotations

import json
import logging

from . import config, llm

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 해외 뉴스를 한국 독자에게 브리핑하는 시니어 에디터입니다.

입력으로 두 그룹의 기사 요약이 주어집니다:
- [보수 매체]: 미국 보수 성향 매체 (Fox News, Breitbart, NY Post, Washington Examiner, Daily Wire, National Review, Daily Caller, Washington Times)
- [크로스체크]: BBC, Reuters — 사실 확인용 기준 소스

작성 원칙:
1. 존댓말로 작성합니다.
2. '확인된 사실'과 '매체의 주장·해석'을 반드시 구분해 서술합니다.
   크로스체크(BBC·Reuters) 소스에도 보도된 내용은 사실 신뢰도가 높다고 보고,
   보수 매체 단독 보도는 "~라고 보도했습니다/주장했습니다"로 출처를 명시합니다.
3. 출처 링크는 마크다운 링크 [매체명](URL) 형식으로 답니다.
4. 아래 고정 포맷과 섹션 순서를 정확히 지킵니다.

출력 포맷(마크다운):

## 오늘 한눈에 보기
(가장 중요한 흐름 5줄 불릿)

## 오늘의 주요 뉴스 Top 5
(각 뉴스마다:)
### N. 제목
- **무슨 일**: ...
- **확인된 사실**: ... (크로스체크 소스 여부 언급)
- **주의할 점**: ... (단독 보도/프레이밍/미확인 주장 등)
- 출처: [매체명](URL) 형식 링크들

## 보수 매체에서만 눈에 띈 뉴스
(크로스체크 소스에는 없고 보수 매체에서 비중 있게 다룬 뉴스 2~3건, 각 2~3문장 + 출처 링크)

## 한국 독자에게 중요한 포인트
- **시장·투자**: ...
- **반도체·AI**: ...
- **외교안보**: ...

## 오늘 추가로 볼 뉴스 3건
(한 줄씩 + 출처 링크)"""


def _format_articles(summaries: list[dict]) -> str:
    lines = []
    for group, label in (("conservative", "보수 매체"), ("crosscheck", "크로스체크")):
        lines.append(f"\n===== [{label}] =====")
        for s in (x for x in summaries if x["group"] == group):
            lines.append(
                f"- ({s['id']}) [{s['category']}] {s['source']} | {s['title']}\n"
                f"  요약: {s['summary']}\n"
                f"  링크: {s['link']}"
            )
    return "\n".join(lines)


def run(date: str | None = None) -> str:
    date = date or config.today_kst()
    ddir = config.date_dir(date)
    sum_path = ddir / "summaries.json"
    if not sum_path.exists():
        raise FileNotFoundError(f"{sum_path} 없음 — 먼저 summarize를 실행하세요.")
    summaries = json.loads(sum_path.read_text(encoding="utf-8"))["summaries"]
    if not summaries:
        raise ValueError("요약이 0건입니다 — 리포트를 생성할 수 없습니다.")

    user = (
        f"오늘 날짜: {date} (KST)\n"
        f"아래는 최근 24시간 기사 요약 {len(summaries)}건입니다. "
        f"이를 바탕으로 데일리 브리핑을 작성해 주세요.\n"
        + _format_articles(summaries)
    )
    body = llm.chat(
        model=config.REPORT_MODEL,
        system=SYSTEM_PROMPT,
        user=user,
        max_tokens=config.REPORT_MAX_TOKENS,
        temperature=config.REPORT_TEMPERATURE,
    )

    report = f"# 해외 보수 언론 데일리 브리핑 — {date}\n\n{body}\n"
    path = ddir / "report.md"
    path.write_text(report, encoding="utf-8")
    log.info("리포트 생성 완료 → %s", path)
    return str(path)
