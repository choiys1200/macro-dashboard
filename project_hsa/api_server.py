from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from core.calculation.saju_engine import SajuInput, calculate_saju_profile
from core.intelligence.dream_analyst import DreamAnalyst
from core.intelligence.knowledge_manager import KnowledgeManager
from core.intelligence.saju_analyst import SajuAnalyst


class AnalyzeRequest(BaseModel):
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    mbti: str = Field(..., min_length=4, max_length=4)
    dream_text: str


app = FastAPI(title="Project HSA API", version="0.1.0")
BASE_DIR = Path(__file__).resolve().parent
knowledge_manager = KnowledgeManager(BASE_DIR / "data" / "docs", BASE_DIR / "data" / "db")
knowledge_manager.build_or_load_index()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest) -> Dict[str, object]:
    saju_input = SajuInput(
        year=payload.year,
        month=payload.month,
        day=payload.day,
        hour=payload.hour,
    )
    saju_profile = calculate_saju_profile(saju_input)
    mbti_profile = {"mbti": payload.mbti.upper()}

    saju_analyst = SajuAnalyst(knowledge_manager)
    dream_analyst = DreamAnalyst(knowledge_manager)

    return {
        "saju_profile": saju_profile,
        "saju_report": saju_analyst.generate_report(saju_profile, mbti_profile),
        "dream_report": dream_analyst.analyze_dream(payload.dream_text, saju_profile, mbti_profile),
    }
