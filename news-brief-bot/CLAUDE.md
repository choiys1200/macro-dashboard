# news-brief-bot

## 목적

매일 오전 7시(KST) 기준 최근 24시간의 해외 보수 성향 언론 뉴스를 수집·요약하고,
BBC·Reuters를 크로스체크 소스로 포함한 한국어 브리핑 리포트를 생성해 Telegram으로
발송하는 파일 기반 Python 서비스. DB·임베딩·클러스터링 없음.

## 구조

```
news_brief/
  config.py     # 소스 리스트(conservative/crosscheck 두 그룹), 모델명, 상한값, .env 로드
  llm.py        # LLM provider 래퍼 (chat() 하나로 통일, MOCK_LLM 지원)
  collect.py    # RSS 수집 → data/YYYY-MM-DD/raw.json
  summarize.py  # 기사별 요약(gpt-4o-mini) → summaries.json
  report.py     # 최종 리포트(gpt-4o, 1회 호출) → report.md
  send.py       # Telegram 발송 (HTML, 4096자 분할)
  main.py       # CLI: python -m news_brief.main collect|summarize|report|send|all
data/           # 날짜별(KST) 중간 산출물 — git 미추적
run_daily.bat   # 스케줄러가 실행하는 진입점 (logs\에 로그 기록)
```

## 핵심 설계 결정

- **각 단계는 독립 재실행 가능**: 이전 단계의 JSON만 읽는다. `--date`로 과거 날짜 재처리.
- **summarize는 재개(resume) 가능**: summaries.json에 이미 있는 기사 id는 건너뛰고,
  기사 1건 처리할 때마다 중간 저장한다.
- **RSS 폴백**: 직접 피드 실패/0건 시 `GOOGLE_NEWS_SITE_RSS`(site:도메인 검색)로 폴백.
  Reuters는 공개 RSS가 없어 처음부터 Google News 우회(`rss: None`).
- **본문 재추출**: RSS 본문이 `MIN_BODY_CHARS`(300자) 미만이면 기사 페이지의 `<p>`를
  정규식으로 추출해 `FULLTEXT_MAX_CHARS`(2500자)까지 사용. 실패해도 진행.
- **중복 제거**: 제목 정규화(소문자화·구두점 제거·Google News의 " - 매체명" 꼬리표 제거)
  키로 전역 dedup.
- **개별 소스 실패는 로그만** 남기고 전체 수집은 계속한다.
- **LLM 호출은 llm.chat() 하나로만**: 모델/프로바이더 교체 시 config.py + llm.py만 수정.
- **비용 상한은 전부 config.py에**: MAX_PER_SOURCE=8, SUMMARY_MAX_TOKENS=350,
  REPORT_MAX_TOKENS=4000, FULLTEXT_MAX_CHARS=2500.
- **secrets는 .env로만**: OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
  Telegram 값이 없으면 send는 건너뛰고 report.md 경로만 출력(폴백).
- **MOCK 모드**: `NEWS_BRIEF_MOCK_LLM=1`이면 llm.chat()이 결정적 mock 응답 반환 —
  API 키/네트워크 없이 파이프라인 배선 점검용.

## 실행법

```
python -m news_brief.main all            # 전체
python -m news_brief.main collect        # 단계별
python -m news_brief.main report --date 2026-07-26
```

오프라인 스모크 테스트: `python tests/offline_smoke.py`
(픽스처 RSS + mock LLM으로 4단계 전체를 네트워크 없이 검증)

## 스케줄링

Windows 작업 스케줄러에 매일 06:40 KST로 run_daily.bat 등록 — 명령은 README.md 참고.

## 리포트 포맷 (report.py의 SYSTEM_PROMPT가 강제)

오늘 한눈에 보기(5줄) / 주요 뉴스 Top 5(무슨 일·확인된 사실·주의할 점·출처) /
보수 매체 단독 뉴스 2~3건 / 한국 독자 포인트(시장·투자, 반도체·AI, 외교안보) /
추가로 볼 뉴스 3건. 존댓말, 사실과 주장·해석 구분, 보수/크로스체크 소스 구분 활용.
