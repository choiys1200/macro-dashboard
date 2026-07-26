@echo off
rem 데일리 브리핑 전체 파이프라인 실행 (collect -> summarize -> report -> send)
cd /d "%~dp0"
if not exist logs mkdir logs

set PYTHON=.venv\Scripts\python.exe
if not exist %PYTHON% set PYTHON=python

%PYTHON% -m news_brief.main all >> logs\run_%date:~0,4%%date:~5,2%%date:~8,2%.log 2>&1
