"""RSS 수집 + 중복 제거 → data/YYYY-MM-DD/raw.json

- 최근 LOOKBACK_HOURS 이내 기사만, 소스당 MAX_PER_SOURCE건.
- 직접 RSS가 실패하거나 0건이면 Google News site: 검색 RSS로 자동 폴백.
- RSS 본문이 너무 짧으면 기사 페이지에서 문단을 재추출(실패해도 계속 진행).
- 개별 소스 실패는 로그만 남기고 전체 수집은 계속한다.
"""

from __future__ import annotations

import html
import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests

from . import config

log = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_WS_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[^\w\s]", re.UNICODE)


def _http_get(url: str) -> bytes:
    """테스트에서 monkeypatch 하기 쉽도록 분리한 HTTP GET."""
    resp = requests.get(
        url,
        headers={"User-Agent": config.USER_AGENT},
        timeout=config.FEED_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.content


def strip_html(text: str) -> str:
    return _WS_RE.sub(" ", html.unescape(_TAG_RE.sub(" ", text or ""))).strip()


def normalize_title(title: str) -> str:
    """중복 제거 키: 소문자화 + 구두점 제거 + 공백 정규화."""
    t = title.lower()
    # Google News 항목의 "제목 - 매체명" 꼬리표 제거
    t = re.sub(r"\s+-\s+[^-]{2,40}$", "", t)
    t = _NON_WORD_RE.sub(" ", t)
    return _WS_RE.sub(" ", t).strip()


def _entry_datetime(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        st = getattr(entry, attr, None) or entry.get(attr)
        if st:
            return datetime.fromtimestamp(time.mktime(st), tz=timezone.utc)
    return None


def _extract_fulltext(url: str) -> str:
    """기사 페이지에서 <p> 문단을 단순 추출한다. 실패하면 빈 문자열."""
    try:
        raw = _http_get(url).decode("utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        log.debug("본문 재추출 실패 %s: %s", url, e)
        return ""
    paras = [strip_html(p) for p in _P_RE.findall(raw)]
    # 광고/네비게이션성 초단문 문단 제거
    paras = [p for p in paras if len(p) >= 60]
    text = " ".join(paras)
    return text[: config.FULLTEXT_MAX_CHARS]


def _parse_feed(url: str):
    content = _http_get(url)
    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        raise ValueError(f"피드 파싱 실패: {parsed.get('bozo_exception')}")
    return parsed


def _entries_to_articles(parsed, source: dict, group: str, cutoff: datetime) -> list[dict]:
    articles = []
    for entry in parsed.entries:
        dt = _entry_datetime(entry)
        if dt is None or dt < cutoff:
            continue
        title = strip_html(entry.get("title", ""))
        link = entry.get("link", "")
        if not title or not link:
            continue
        body = strip_html(entry.get("summary", "") or entry.get("description", ""))
        articles.append(
            {
                "source": source["name"],
                "group": group,
                "title": title,
                "link": link,
                "published": dt.isoformat(),
                "body": body,
            }
        )
        if len(articles) >= config.MAX_PER_SOURCE:
            break
    return articles


def collect_source(source: dict, group: str, cutoff: datetime) -> list[dict]:
    """직접 RSS → 실패/0건이면 Google News site: 폴백."""
    urls: list[tuple[str, str]] = []
    if source.get("rss"):
        urls.append(("direct", source["rss"]))
    if source.get("domain"):
        urls.append(("google-news", config.GOOGLE_NEWS_SITE_RSS.format(domain=source["domain"])))

    for kind, url in urls:
        try:
            parsed = _parse_feed(url)
            articles = _entries_to_articles(parsed, source, group, cutoff)
            if articles:
                if kind == "google-news":
                    log.info("%s: Google News 폴백으로 %d건 수집", source["name"], len(articles))
                return articles
            log.warning("%s: %s 피드에서 최근 기사 0건", source["name"], kind)
        except Exception as e:  # noqa: BLE001
            log.warning("%s: %s 피드 실패 (%s) — 다음 방법 시도", source["name"], kind, e)
    log.error("%s: 모든 수집 방법 실패, 이 소스는 건너뜀", source["name"])
    return []


def _enrich_short_bodies(articles: list[dict]) -> None:
    for a in articles:
        if len(a["body"]) < config.MIN_BODY_CHARS:
            fulltext = _extract_fulltext(a["link"])
            if len(fulltext) > len(a["body"]):
                a["body"] = fulltext


def run(date: str | None = None) -> str:
    """수집 실행. raw.json 경로를 반환한다."""
    date = date or config.today_kst()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=config.LOOKBACK_HOURS)

    all_articles: list[dict] = []
    for group, sources in config.SOURCES.items():
        for source in sources:
            got = collect_source(source, group, cutoff)
            log.info("%s (%s): %d건", source["name"], group, len(got))
            all_articles.extend(got)

    # 제목 정규화 기준 전역 중복 제거 (먼저 수집된 기사 우선)
    seen: set[str] = set()
    deduped: list[dict] = []
    for a in all_articles:
        key = normalize_title(a["title"])
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(a)

    _enrich_short_bodies(deduped)

    for i, a in enumerate(deduped, 1):
        a["id"] = f"{date}-{i:03d}"

    out = {
        "date": date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(deduped),
        "articles": deduped,
    }
    path = config.date_dir(date) / "raw.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("수집 완료: %d건(중복 제거 후) → %s", len(deduped), path)
    return str(path)
