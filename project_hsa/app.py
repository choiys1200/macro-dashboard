from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

import streamlit as st

from core.calculation.saju_engine import SajuInput, calculate_saju_profile
from core.intelligence.dream_analyst import DreamAnalyst
from core.intelligence.knowledge_manager import KnowledgeManager
from core.intelligence.saju_analyst import SajuAnalyst


st.set_page_config(page_title="Project HSA", layout="wide")
st.title("Project HSA (Human System Analytics)")
st.caption("사주(초기 기질) · MBTI(현재 OS) · 꿈(런타임 로그) 교차 분석")


@st.cache_resource
def get_knowledge_manager() -> KnowledgeManager:
    base_dir = Path(__file__).resolve().parent
    manager = KnowledgeManager(
        docs_path=base_dir / "data" / "docs",
        db_path=base_dir / "data" / "db",
    )
    manager.build_or_load_index()
    return manager


def _collect_mbti_scores(mbti: str) -> Dict[str, str]:
    normalized = mbti.strip().upper()
    if len(normalized) != 4:
        return {"error": "MBTI는 4글자 형식이어야 합니다. 예: INTJ"}
    return {
        "energy_direction": "내향" if normalized[0] == "I" else "외향",
        "information_style": "직관" if normalized[1] == "N" else "감각",
        "decision_style": "사고" if normalized[2] == "T" else "감정",
        "lifestyle_style": "판단" if normalized[3] == "J" else "인식",
    }


with st.sidebar:
    st.header("입력")
    birth_date = st.date_input("생년월일", value=datetime(1990, 1, 1))
    birth_hour = st.slider("출생 시각(24h)", min_value=0, max_value=23, value=8)
    mbti = st.text_input("MBTI", value="INTJ")
    dream_text = st.text_area("최근 꿈 기록", value="높은 곳에서 떨어질 것 같은 불안한 꿈을 반복해서 꿨다.")

analyze = st.button("분석 실행")

if analyze:
    manager = get_knowledge_manager()

    saju_input = SajuInput(
        year=birth_date.year,
        month=birth_date.month,
        day=birth_date.day,
        hour=birth_hour,
    )
    saju_profile = calculate_saju_profile(saju_input)
    mbti_profile = _collect_mbti_scores(mbti)

    st.subheader("Layer 1: 사주 기반 초기 기질")
    st.json(saju_profile)

    st.subheader("Layer 2: MBTI 현재 OS")
    st.json(mbti_profile)

    if "error" in mbti_profile:
        st.error(mbti_profile["error"])
    else:
        saju_analyst = SajuAnalyst(knowledge_manager=manager)
        dream_analyst = DreamAnalyst(knowledge_manager=manager)

        with st.spinner("사주 리포트 생성 중..."):
            saju_report = saju_analyst.generate_report(saju_profile, mbti_profile)
        with st.spinner("꿈 로그 분석 중..."):
            dream_report = dream_analyst.analyze_dream(dream_text, saju_profile, mbti_profile)

        st.subheader("Layer 1+2 통합 리포트")
        st.write(saju_report)

        st.subheader("Layer 3 런타임 로그 분석")
        st.write(dream_report)
