# news-brief-bot

해외 보수 성향 언론의 최근 24시간 뉴스를 수집·요약하고, BBC·Reuters를 크로스체크
소스로 포함한 한국어 데일리 브리핑을 생성해 Telegram으로 발송하는 Python 서비스입니다.

## 파이프라인

```
collect  → data/YYYY-MM-DD/raw.json        (RSS 수집 + 24시간 필터 + 중복 제거)
summarize→ data/YYYY-MM-DD/summaries.json  (gpt-4o-mini, 기사당 한국어 3문장 요약)
report   → data/YYYY-MM-DD/report.md       (gpt-4o, 고정 포맷 브리핑 1회 호출)
send     → Telegram sendMessage            (HTML, 4096자 초과 시 섹션 분할)
```

각 단계는 이전 단계의 JSON 파일만 읽으므로 독립 재실행이 가능합니다.
날짜 폴더는 KST 기준입니다.

## 뉴스 소스

- **보수 매체**: Fox News, Breitbart, NY Post, Washington Examiner,
  Daily Wire, National Review, Daily Caller, Washington Times
- **크로스체크**: BBC World, Reuters (공개 RSS가 없어 Google News RSS의
  `site:reuters.com` 검색으로 우회)

직접 RSS가 실패하거나 최근 기사가 0건이면 해당 소스 도메인의 Google News
검색 RSS로 자동 폴백합니다. 소스 목록·URL은 `news_brief/config.py`에서 관리합니다.

## 설치

```bat
cd C:\Project\news-brief-bot
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
rem .env를 열어 OPENAI_API_KEY (필수), TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID (선택) 입력
```

Telegram 값이 없으면 send 단계는 발송을 건너뛰고 `report.md` 경로만 출력합니다.

## 실행

```bat
.venv\Scripts\python -m news_brief.main all
rem 또는 단계별:
.venv\Scripts\python -m news_brief.main collect
.venv\Scripts\python -m news_brief.main summarize
.venv\Scripts\python -m news_brief.main report
.venv\Scripts\python -m news_brief.main send
rem 특정 날짜 재실행:
.venv\Scripts\python -m news_brief.main report --date 2026-07-26
```

API 키 없이 파이프라인만 점검하려면 `.env`에 `NEWS_BRIEF_MOCK_LLM=1`을 넣고
실행하세요(LLM 호출이 mock 응답으로 대체됩니다).

## 스케줄링 (Windows 작업 스케줄러)

매일 06:40 KST에 실행하도록 등록 (관리자 권한 불필요, 아래 명령을 직접 실행):

```bat
schtasks /Create /TN "NewsBriefBot" /TR "C:\Project\news-brief-bot\run_daily.bat" /SC DAILY /ST 06:40 /F
```

확인/삭제:

```bat
schtasks /Query /TN "NewsBriefBot"
schtasks /Delete /TN "NewsBriefBot" /F
```

실행 로그는 `logs\run_YYYYMMDD.log`에 쌓입니다.

## 비용 통제

`news_brief/config.py`에서 관리:

| 항목 | 기본값 |
|---|---|
| 소스당 기사 상한 `MAX_PER_SOURCE` | 8 |
| 요약 모델 / max_tokens | gpt-4o-mini / 350 |
| 리포트 모델 / max_tokens | gpt-4o / 4000 |
| 요약 입력 본문 상한 `FULLTEXT_MAX_CHARS` | 2,500자 |

모델 교체는 `config.py`의 모델명과 `news_brief/llm.py`(provider 래퍼)만 수정하면 됩니다.
