"""Telegram 발송.

- sendMessage, parse_mode=HTML.
- 4096자 초과 시 섹션(## 헤딩) 단위로 분할 발송.
- TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID가 없으면 발송을 건너뛰고 report.md 경로만 출력.
"""

from __future__ import annotations

import html
import logging
import re
import time

import requests

from . import config

log = logging.getLogger(__name__)

TELEGRAM_LIMIT = 4096
_CHUNK_LIMIT = 3900  # HTML 태그 오버헤드 여유분

_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def md_to_telegram_html(md: str) -> str:
    """리포트 마크다운을 Telegram HTML로 변환한다(지원 태그만 사용)."""
    out_lines = []
    for line in md.splitlines():
        escaped = html.escape(line, quote=False)
        # 링크/볼드 변환 (이스케이프 후 패턴은 유지됨)
        escaped = _LINK_RE.sub(r'<a href="\2">\1</a>', escaped)
        escaped = _BOLD_RE.sub(r"<b>\1</b>", escaped)
        if escaped.startswith("# "):
            escaped = f"<b>{escaped[2:]}</b>"
        elif escaped.startswith("## "):
            escaped = f"<b>{escaped[3:]}</b>"
        elif escaped.startswith("### "):
            escaped = f"<b>{escaped[4:]}</b>"
        out_lines.append(escaped)
    return "\n".join(out_lines).strip()


def split_sections(md: str) -> list[str]:
    """## 헤딩 기준으로 섹션을 나누고, 한도 내에서 다시 묶는다."""
    sections: list[str] = []
    current: list[str] = []
    for line in md.splitlines():
        if line.startswith("## ") and current:
            sections.append("\n".join(current).strip())
            current = []
        current.append(line)
    if current:
        sections.append("\n".join(current).strip())

    # 섹션을 한도 내로 병합, 너무 긴 섹션은 줄 단위로 강제 분할
    chunks: list[str] = []
    buf = ""
    for sec in sections:
        candidate = f"{buf}\n\n{sec}" if buf else sec
        if len(candidate) <= _CHUNK_LIMIT:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        if len(sec) <= _CHUNK_LIMIT:
            buf = sec
        else:
            buf = ""
            piece = ""
            for line in sec.splitlines():
                cand = f"{piece}\n{line}" if piece else line
                if len(cand) > _CHUNK_LIMIT:
                    chunks.append(piece)
                    piece = line
                else:
                    piece = cand
            buf = piece
    if buf:
        chunks.append(buf)
    return chunks


def _send_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API 오류: {data}")


def run(date: str | None = None) -> str:
    date = date or config.today_kst()
    path = config.date_dir(date) / "report.md"
    if not path.exists():
        raise FileNotFoundError(f"{path} 없음 — 먼저 report를 실행하세요.")

    if not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        print(f"[send] TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID 미설정 — 발송 건너뜀")
        print(f"[send] 리포트 파일: {path}")
        return str(path)

    md = path.read_text(encoding="utf-8")
    chunks = split_sections(md)
    total = len(chunks)
    for i, chunk in enumerate(chunks, 1):
        text = md_to_telegram_html(chunk)
        if total > 1:
            text = f"({i}/{total})\n{text}"
        _send_message(text[:TELEGRAM_LIMIT])
        log.info("Telegram 발송 %d/%d (%d자)", i, total, len(text))
        if i < total:
            time.sleep(1)  # rate limit 여유
    log.info("Telegram 발송 완료: %d개 메시지", total)
    return str(path)
