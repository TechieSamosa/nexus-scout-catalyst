"""
matcher.py — Compares candidates against a parsed JD using Gemini for scoring.
"""

import json
import time
from typing import Any, Callable, Dict, List, Optional
from src.llm_engine import call_gemini, parse_json_response


SYSTEM_INSTRUCTION = """You are an expert technical recruiter with 15 years of experience.
You evaluate candidate-job fit with precision. Be strict but fair.
A score of 80+ means excellent fit. 50-79 is moderate. Below 50 is weak.
Always return valid JSON."""

MATCH_PROMPT_TEMPLATE = """Evaluate how well this candidate matches the job description.

## Job Description
{jd_text}

## Candidate Profile
- Name: {name}
- Title: {title}
- Experience: {experience_years} years
- Skills: {skills}
- Education: {education}
- Summary: {summary}
- Past Roles: {past_roles}
- Certifications: {certifications}

## Instructions
Return ONLY a JSON object with exactly these fields:
{{
  "match_score": <integer 0-100>,
  "explanation": "<exactly 2 sentences explaining the match>"
}}"""


def format_candidate_for_prompt(candidate: Dict[str, Any]) -> Dict[str, str]:
    """Format candidate data for prompt insertion."""
    past_roles_str = ""
    for role in candidate.get("past_roles", []):
        highlights = "; ".join(role.get("highlights", []))
        past_roles_str += f"  - {role['role']} at {role['company']} ({role['duration']}): {highlights}\n"

    return {
        "name": candidate["name"],
        "title": candidate["title"],
        "experience_years": str(candidate["experience_years"]),
        "skills": ", ".join(candidate.get("skills", [])),
        "education": candidate.get("education", "N/A"),
        "summary": candidate.get("summary", ""),
        "past_roles": past_roles_str.strip(),
        "certifications": ", ".join(candidate.get("certifications", [])),
    }


def score_candidate(client, candidate: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
    """Score a single candidate against the JD. Returns match_score and explanation."""
    formatted = format_candidate_for_prompt(candidate)
    prompt = MATCH_PROMPT_TEMPLATE.format(jd_text=jd_text, **formatted)

    try:
        raw = call_gemini(client, prompt, system_instruction=SYSTEM_INSTRUCTION)
        result = parse_json_response(raw)
        return {
            "match_score": max(0, min(100, int(result.get("match_score", 0)))),
            "explanation": str(result.get("explanation", "No explanation provided.")),
        }
    except Exception as e:
        return {
            "match_score": 0,
            "explanation": f"Scoring failed: {str(e)}",
        }


def score_all_candidates(
    client, candidates: List[Dict[str, Any]], jd_text: str,
    progress_callback=None, rate_limit_callback: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """Score all candidates. Returns list of candidates with match_score and explanation added."""
    results = []
    total = len(candidates)
    for i, candidate in enumerate(candidates):
        score_data = score_candidate(client, candidate, jd_text)
        enriched = {**candidate, **score_data}
        results.append(enriched)
        if progress_callback:
            progress_callback(i + 1, total, candidate["name"])
        # Rate-limit pause between API calls (skip after last candidate)
        if i < total - 1:
            if rate_limit_callback:
                rate_limit_callback(i + 1, total, candidate["name"])
            time.sleep(4)
    return results
