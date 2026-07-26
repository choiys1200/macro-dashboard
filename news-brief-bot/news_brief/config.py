"""소스 리스트, 모델명, 상한값, .env 로드.

모든 비용 관련 상한(소스당 기사 수, 요약/리포트 max_tokens)은 이 파일에서만 관리한다.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 경로 / 환경변수
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

load_dotenv(PROJECT_ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")  # 프록시/호환 API 사용 시만 설정
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# 1이면 LLM 호출 없이 결정적(mock) 응답을 반환 — 오프라인 파이프라인 점검용
MOCK_LLM = os.getenv("NEWS_BRIEF_MOCK_LLM", "") == "1"

# ---------------------------------------------------------------------------
# 시간대: 브리핑 기준은 항상 KST
# ---------------------------------------------------------------------------
KST = timezone(timedelta(hours=9))


def today_kst() -> str:
    """KST 기준 오늘 날짜 (data/ 하위 폴더명)."""
    return datetime.now(KST).strftime("%Y-%m-%d")


def date_dir(date: str | None = None) -> Path:
    d = DATA_DIR / (date or today_kst())
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# 수집 설정
# ---------------------------------------------------------------------------
LOOKBACK_HOURS = 24          # 최근 24시간 기사만
MAX_PER_SOURCE = 8           # 소스당 최대 기사 수 (비용 상한)
FEED_TIMEOUT = 20            # RSS/본문 HTTP 타임아웃(초)
MIN_BODY_CHARS = 300         # RSS 본문이 이보다 짧으면 기사 페이지에서 재추출 시도
FULLTEXT_MAX_CHARS = 2500    # 재추출 본문 상한 (요약 입력 비용 통제)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 news-brief-bot/0.1"
)

# 소스 직접 RSS가 죽었거나 0건일 때 사용하는 Google News 우회 템플릿
GOOGLE_NEWS_SITE_RSS = (
    "https://news.google.com/rss/search?"
    "q=site:{domain}+when:1d&hl=en-US&gl=US&ceid=US:en"
)

# 각 소스: name(표시명), rss(직접 피드; None이면 Google News 우회가 기본),
# domain(Google News 폴백용), group은 SOURCES 키로 부여된다.
SOURCES: dict[str, list[dict]] = {
    "conservative": [
        {
            "name": "Fox News",
            "rss": "https://moxie.foxnews.com/google-publisher/latest.xml",
            "domain": "foxnews.com",
        },
        {
            "name": "Breitbart",
            "rss": "https://feeds.feedburner.com/breitbart",
            "domain": "breitbart.com",
        },
        {
            "name": "New York Post",
            "rss": "https://nypost.com/feed/",
            "domain": "nypost.com",
        },
        {
            "name": "Washington Examiner",
            "rss": "https://www.washingtonexaminer.com/feed",
            "domain": "washingtonexaminer.com",
        },
        {
            "name": "Daily Wire",
            "rss": "https://www.dailywire.com/feeds/rss.xml",
            "domain": "dailywire.com",
        },
        {
            "name": "National Review",
            "rss": "https://www.nationalreview.com/feed/",
            "domain": "nationalreview.com",
        },
        {
            "name": "Daily Caller",
            "rss": "https://dailycaller.com/feed/",
            "domain": "dailycaller.com",
        },
        {
            "name": "Washington Times",
            "rss": "https://www.washingtontimes.com/rss/headlines/news/politics/",
            "domain": "washingtontimes.com",
        },
    ],
    "crosscheck": [
        {
            "name": "BBC World",
            "rss": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "domain": "bbc.com",
        },
        {
            # Reuters는 2020년 이후 공개 RSS를 제공하지 않음 → Google News 우회
            "name": "Reuters",
            "rss": None,
            "domain": "reuters.com",
        },
    ],
}

# ---------------------------------------------------------------------------
# LLM 설정 (모델 교체는 여기서만)
# ---------------------------------------------------------------------------
SUMMARY_MODEL = "gpt-4o-mini"    # 기사별 요약: 저비용 모델
REPORT_MODEL = "gpt-4o"          # 최종 리포트: 상위 모델
SUMMARY_MAX_TOKENS = 350
REPORT_MAX_TOKENS = 4000
SUMMARY_TEMPERATURE = 0.2
REPORT_TEMPERATURE = 0.4

CATEGORIES = ["정치", "외교안보", "경제", "기술", "사회"]
