"""오프라인 스모크 테스트: 네트워크·API 키 없이 파이프라인 4단계 전체를 검증한다.

- collect._http_get을 픽스처 RSS/HTML로 monkeypatch
- LLM은 MOCK 모드(config.MOCK_LLM=True)
- send는 토큰 미설정 폴백 경로 확인 + 분할/HTML 변환 단위 검증

실행: python tests/offline_smoke.py
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from news_brief import collect, config, report, send, summarize  # noqa: E402

TEST_DATE = "1999-01-01"  # 실데이터와 절대 겹치지 않는 날짜 폴더


def rfc822(hours_ago: float) -> str:
    return format_datetime(datetime.now(timezone.utc) - timedelta(hours=hours_ago))


def make_rss(source: str, items: list[tuple[str, str, float, str]]) -> bytes:
    """items: (title, link, hours_ago, description)"""
    xml_items = "".join(
        f"""
    <item>
      <title>{t}</title>
      <link>{l}</link>
      <pubDate>{rfc822(h)}</pubDate>
      <description>{d}</description>
    </item>"""
        for t, l, h, d in items
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{source}</title>{xml_items}
</channel></rss>""".encode()


LONG_DESC = "This is a sufficiently long factual description of the event. " * 8
ARTICLE_HTML = (
    b"<html><body>"
    + b"<p>This paragraph is part of the full article body and is long enough to keep after filtering short fragments.</p>" * 10
    + b"</body></html>"
)

FIXTURES: dict[str, bytes] = {
    # Fox: 정상 2건 + 24시간 밖 1건(제외되어야 함)
    "https://moxie.foxnews.com/google-publisher/latest.xml": make_rss(
        "Fox News",
        [
            ("Senate passes defense bill", "https://foxnews.com/a1", 2, LONG_DESC),
            ("White House unveils chip policy", "https://foxnews.com/a2", 5, "short desc"),
            ("Old story beyond window", "https://foxnews.com/old", 30, LONG_DESC),
        ],
    ),
    # NY Post: Fox와 중복 제목 1건(dedup 대상) + 고유 1건
    "https://nypost.com/feed/": make_rss(
        "New York Post",
        [
            ("Senate Passes Defense Bill!", "https://nypost.com/b1", 3, LONG_DESC),
            ("Markets rally on earnings", "https://nypost.com/b2", 4, LONG_DESC),
        ],
    ),
    # BBC: 크로스체크 1건
    "https://feeds.bbci.co.uk/news/world/rss.xml": make_rss(
        "BBC World",
        [("Defense bill passes US Senate", "https://bbc.com/c1", 1, LONG_DESC)],
    ),
    # Reuters: Google News 우회 (제목에 " - Reuters" 꼬리표)
    config.GOOGLE_NEWS_SITE_RSS.format(domain="reuters.com"): make_rss(
        "Google News",
        [("Chip export rules updated - Reuters", "https://news.google.com/rss/articles/x1", 6, LONG_DESC)],
    ),
    # Washington Examiner: 직접 피드는 죽음 → Google News 폴백이 동작해야 함
    config.GOOGLE_NEWS_SITE_RSS.format(domain="washingtonexaminer.com"): make_rss(
        "Google News",
        [("Examiner exclusive report - Washington Examiner", "https://news.google.com/rss/articles/x2", 7, LONG_DESC)],
    ),
    # 짧은 본문 기사의 페이지 (재추출 대상)
    "https://foxnews.com/a2": ARTICLE_HTML,
}


def fake_http_get(url: str) -> bytes:
    if url in FIXTURES:
        return FIXTURES[url]
    raise ConnectionError(f"(fixture) blocked: {url}")


def check(cond: bool, msg: str) -> None:
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        sys.exit(1)


def main() -> None:
    ddir = config.DATA_DIR / TEST_DATE
    if ddir.exists():
        shutil.rmtree(ddir)

    collect._http_get = fake_http_get
    config.MOCK_LLM = True
    config.TELEGRAM_BOT_TOKEN = ""
    config.TELEGRAM_CHAT_ID = ""

    print("1) collect")
    collect.run(date=TEST_DATE)
    raw = json.loads((ddir / "raw.json").read_text(encoding="utf-8"))
    titles = [a["title"] for a in raw["articles"]]
    check(raw["count"] == 6, f"수집 6건 (중복 1건 제거, 24h 밖 1건 제외): {raw['count']}건")
    check("Old story beyond window" not in titles, "24시간 밖 기사 제외")
    check("Senate Passes Defense Bill!" not in titles, "제목 정규화 중복 제거 (NY Post 중복본)")
    check(any(a["source"] == "Washington Examiner" for a in raw["articles"]), "직접 피드 실패 → Google News 폴백")
    check(any(a["source"] == "Reuters" for a in raw["articles"]), "Reuters Google News 우회 수집")
    a2 = next(a for a in raw["articles"] if a["link"] == "https://foxnews.com/a2")
    check(len(a2["body"]) >= config.MIN_BODY_CHARS, f"짧은 본문 재추출 ({len(a2['body'])}자)")

    print("2) summarize (mock LLM)")
    summarize.run(date=TEST_DATE)
    sums = json.loads((ddir / "summaries.json").read_text(encoding="utf-8"))["summaries"]
    check(len(sums) == 6, f"요약 6건 생성: {len(sums)}건")
    check(all(s["category"] in config.CATEGORIES for s in sums), "카테고리 태그 파싱")
    check(all(s["group"] in ("conservative", "crosscheck") for s in sums), "그룹 보존")

    print("3) report (mock LLM)")
    report.run(date=TEST_DATE)
    md = (ddir / "report.md").read_text(encoding="utf-8")
    check("오늘 한눈에 보기" in md, "리포트 파일 생성 + 섹션 포함")

    print("4) send (토큰 미설정 폴백)")
    result = send.run(date=TEST_DATE)
    check(result.endswith("report.md"), "발송 건너뛰고 report.md 경로 반환")

    print("5) send 단위 검증 (분할·HTML 변환)")
    long_md = "\n\n".join(f"## 섹션 {i}\n" + ("내용 줄입니다. " * 300) for i in range(5))
    chunks = send.split_sections(long_md)
    check(all(len(c) <= 3900 for c in chunks) and len(chunks) > 1, f"4096자 분할: {len(chunks)}개 청크")
    html_out = send.md_to_telegram_html("## 제목\n**볼드** [링크](https://x.com/a?b=1&c=2) < >")
    check(
        "<b>제목</b>" in html_out
        and "<b>볼드</b>" in html_out
        and '<a href="https://x.com/a?b=1&amp;c=2">링크</a>' in html_out
        and "&lt; &gt;" in html_out,
        "Telegram HTML 변환(헤딩·볼드·링크·이스케이프)",
    )

    shutil.rmtree(ddir)
    print("\n모든 스모크 테스트 통과")


if __name__ == "__main__":
    main()
