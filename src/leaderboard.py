"""
leaderboard.py — Combines Match + Interest scores, computes final ranking.
"""

from typing import Any, Dict, List
import pandas as pd


MATCH_WEIGHT = 0.6
INTEREST_WEIGHT = 0.4


def compute_final_scores(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute weighted final score and sort by rank."""
    for c in candidates:
        match = c.get("match_score", 0)
        interest = c.get("interest_score", 0)
        c["final_score"] = round(MATCH_WEIGHT * match + INTEREST_WEIGHT * interest, 1)

    ranked = sorted(candidates, key=lambda x: x["final_score"], reverse=True)
    for i, c in enumerate(ranked):
        c["rank"] = i + 1
    return ranked


def to_dataframe(candidates: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert ranked candidates to a display-ready DataFrame."""
    rows = []
    for c in candidates:
        rows.append({
            "Rank": c.get("rank", "-"),
            "Name": c["name"],
            "Title": c["title"],
            "Exp (yrs)": c["experience_years"],
            "Match Score": c.get("match_score", 0),
            "Interest Score": c.get("interest_score", 0),
            "Final Score": c.get("final_score", 0),
            "Location": c.get("location", ""),
            "Notice": c.get("notice_period", ""),
        })
    return pd.DataFrame(rows)


def get_tier(score: float) -> str:
    """Return a tier label based on final score."""
    if score >= 80:
        return "🟢 Excellent"
    elif score >= 60:
        return "🟡 Good"
    elif score >= 40:
        return "🟠 Moderate"
    else:
        return "🔴 Weak"
