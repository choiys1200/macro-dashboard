"""기사별 요약 (저비용 모델) → data/YYYY-MM-DD/summaries.json

- 한국어 3문장, 사실 중심·논평 금지, 고유명사는 영어 유지.
- 카테고리 태그([정치][외교안보][경제][기술][사회]) 1개 부여.
- summaries.json이 이미 있으면 남은 기사만 이어서 처리(재실행 안전).
"""

from __future__ import annotations

import json
import logging
import re

from . import config, llm

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "당신은 국제 뉴스 요약 어시스턴트입니다. 규칙:\n"
    "1) 기사를 한국어 정확히 3문장으로 요약합니다.\n"
    "2) 확인된 사실만 서술하고 논평·해석·과장을 넣지 않습니다. "
    "기사 속 주장(claim)은 '~라고 주장했다/보도했다'로 출처를 밝혀 서술합니다.\n"
    "3) 인명·기관명·지명 등 고유명사는 영어 원문을 유지합니다.\n"
    f"4) 첫머리에 카테고리 태그를 정확히 1개 붙입니다: "
    + " ".join(f"[{c}]" for c in config.CATEGORIES) + " 중 하나.\n"
    "출력 형식: [카테고리] 문장1 문장2 문장3"
)

_TAG_RE = re.compile(r"^\s*\[(" + "|".join(config.CATEGORIES) + r")\]\s*")


def _summarize_one(article: dict) -> dict:
    body = article["body"][: config.FULLTEXT_MAX_CHARS] or "(본문 없음 — 제목만으로 요약)"
    user = (
        f"매체: {article['source']}\n"
        f"제목: {article['title']}\n"
        f"본문: {body}"
    )
    text = llm.chat(
        model=config.SUMMARY_MODEL,
        system=SYSTEM_PROMPT,
        user=user,
        max_tokens=config.SUMMARY_MAX_TOKENS,
        temperature=config.SUMMARY_TEMPERATURE,
    )
    m = _TAG_RE.match(text)
    category = m.group(1) if m else "사회"
    summary = _TAG_RE.sub("", text).strip()
    return {
        "id": article["id"],
        "source": article["source"],
        "group": article["group"],
        "title": article["title"],
        "link": article["link"],
        "published": article["published"],
        "category": category,
        "summary": summary,
    }


def run(date: str | None = None) -> str:
    date = date or config.today_kst()
    ddir = config.date_dir(date)
    raw_path = ddir / "raw.json"
    if not raw_path.exists():
        raise FileNotFoundError(f"{raw_path} 없음 — 먼저 collect를 실행하세요.")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))

    out_path = ddir / "summaries.json"
    done: dict[str, dict] = {}
    if out_path.exists():
        prev = json.loads(out_path.read_text(encoding="utf-8"))
        done = {s["id"]: s for s in prev.get("summaries", [])}
        if done:
            log.info("기존 요약 %d건 재사용", len(done))

    summaries: list[dict] = []
    for article in raw["articles"]:
        if article["id"] in done:
            summaries.append(done[article["id"]])
            continue
        try:
            summaries.append(_summarize_one(article))
            log.info("요약 완료: %s (%s)", article["id"], article["source"])
        except Exception as e:  # noqa: BLE001
            log.warning("요약 실패 %s: %s — 건너뜀", article["id"], e)
        # 중간 저장: 도중에 실패해도 재실행 시 이어서 처리
        out_path.write_text(
            json.dumps({"date": date, "summaries": summaries}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    log.info("요약 완료: %d/%d건 → %s", len(summaries), raw["count"], out_path)
    return str(out_path)
