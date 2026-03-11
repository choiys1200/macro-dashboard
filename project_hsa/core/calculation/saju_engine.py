from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, TypedDict

from korean_lunar_calendar import KoreanLunarCalendar


STEMS: List[str] = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
BRANCHES: List[str] = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

STEM_TO_ELEMENT: Dict[str, str] = {
    "갑": "목",
    "을": "목",
    "병": "화",
    "정": "화",
    "무": "토",
    "기": "토",
    "경": "금",
    "신": "금",
    "임": "수",
    "계": "수",
}
BRANCH_TO_ELEMENT: Dict[str, str] = {
    "인": "목",
    "묘": "목",
    "사": "화",
    "오": "화",
    "진": "토",
    "술": "토",
    "축": "토",
    "미": "토",
    "신": "금",
    "유": "금",
    "해": "수",
    "자": "수",
}
HOUR_BRANCHES: List[tuple[int, int, str]] = [
    (23, 24, "자"),
    (0, 1, "자"),
    (1, 3, "축"),
    (3, 5, "인"),
    (5, 7, "묘"),
    (7, 9, "진"),
    (9, 11, "사"),
    (11, 13, "오"),
    (13, 15, "미"),
    (15, 17, "신"),
    (17, 19, "유"),
    (19, 21, "술"),
    (21, 23, "해"),
]


@dataclass(frozen=True)
class SajuInput:
    year: int
    month: int
    day: int
    hour: int


class SajuProfile(TypedDict):
    solar_datetime: str
    lunar_date: str
    gapja: Dict[str, str]
    five_elements_score: Dict[str, int]


def _get_hour_branch(hour: int) -> str:
    for start, end, branch in HOUR_BRANCHES:
        if start <= hour < end:
            return branch
    return "자"


def _derive_hour_stem(day_stem: str, hour_branch: str) -> str:
    day_idx = STEMS.index(day_stem)
    branch_idx = BRANCHES.index(hour_branch)
    stem_idx = (day_idx * 2 + branch_idx) % 10
    return STEMS[stem_idx]


def calculate_saju_profile(payload: SajuInput) -> SajuProfile:
    """Convert Gregorian birth datetime to saju profile with five-element scores."""
    calendar = KoreanLunarCalendar()
    calendar.setSolarDate(payload.year, payload.month, payload.day)

    year_gapja = calendar.getGapJaString().split(" ")[0]
    month_gapja = calendar.getGapJaString().split(" ")[1]
    day_gapja = calendar.getGapJaString().split(" ")[2]

    hour_branch = _get_hour_branch(payload.hour)
    hour_stem = _derive_hour_stem(day_gapja[0], hour_branch)
    hour_gapja = f"{hour_stem}{hour_branch}"

    symbols = [
        year_gapja[0],
        year_gapja[1],
        month_gapja[0],
        month_gapja[1],
        day_gapja[0],
        day_gapja[1],
        hour_stem,
        hour_branch,
    ]

    scores: Dict[str, int] = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for symbol in symbols:
        if symbol in STEM_TO_ELEMENT:
            scores[STEM_TO_ELEMENT[symbol]] += 1
        elif symbol in BRANCH_TO_ELEMENT:
            scores[BRANCH_TO_ELEMENT[symbol]] += 1

    return {
        "solar_datetime": datetime(payload.year, payload.month, payload.day, payload.hour).isoformat(),
        "lunar_date": f"{calendar.lunarYear:04d}-{calendar.lunarMonth:02d}-{calendar.lunarDay:02d}",
        "gapja": {
            "year": year_gapja,
            "month": month_gapja,
            "day": day_gapja,
            "hour": hour_gapja,
        },
        "five_elements_score": scores,
    }
