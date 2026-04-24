"""
conversation_sim.py — Simulates AI Recruiter <-> Candidate conversation to assess interest.
"""

import time
from typing import Any, Callable, Dict, List, Optional
from src.llm_engine import call_gemini, parse_json_response


SYSTEM_INSTRUCTION = """You are simulating a realistic recruiting conversation.
You must generate a natural dialogue between a recruiter and a candidate.
The candidate's responses should realistically reflect their satisfaction level.
Always return valid JSON."""

CONVERSATION_PROMPT = """Simulate a brief recruiting conversation between an AI Recruiter and a candidate.

## Role Being Pitched
{jd_summary}

## Candidate Profile
- Name: {name}
- Current Role: {title}
- Experience: {experience_years} years
- Key Skills: {skills}
- Current Satisfaction: {satisfaction}
- Salary Expectation: {salary}
- Notice Period: {notice}
- Preferred Work Mode: {work_mode}

## Instructions
1. The recruiter pitches the role and asks about interest.
2. The candidate responds based on their satisfaction level and profile.
3. Generate exactly 4-6 exchange turns (each turn = one recruiter + one candidate message).
4. Then assess the candidate's overall interest.

Return ONLY a JSON object:
{{
  "conversation": [
    {{"role": "recruiter", "message": "..."}},
    {{"role": "candidate", "message": "..."}}
  ],
  "interest_score": <integer 0-100>,
  "interest_summary": "<1 sentence summary of candidate's interest level>"
}}"""


def simulate_conversation(
    client, candidate: Dict[str, Any], jd_text: str
) -> Dict[str, Any]:
    """Simulate a recruiter-candidate conversation and return interest assessment."""
    # Build a short JD summary (first 300 chars)
    jd_summary = jd_text[:500].strip()

    prompt = CONVERSATION_PROMPT.format(
        jd_summary=jd_summary,
        name=candidate["name"],
        title=candidate["title"],
        experience_years=candidate["experience_years"],
        skills=", ".join(candidate.get("skills", [])[:6]),
        satisfaction=candidate.get("current_job_satisfaction", "Unknown"),
        salary=candidate.get("salary_expectation", "Not specified"),
        notice=candidate.get("notice_period", "Not specified"),
        work_mode=candidate.get("preferred_work_mode", "Flexible"),
    )

    try:
        raw = call_gemini(client, prompt, system_instruction=SYSTEM_INSTRUCTION)
        result = parse_json_response(raw)
        return {
            "conversation": result.get("conversation", []),
            "interest_score": max(0, min(100, int(result.get("interest_score", 50)))),
            "interest_summary": str(result.get("interest_summary", "No summary.")),
        }
    except Exception as e:
        return {
            "conversation": [],
            "interest_score": 50,
            "interest_summary": f"Conversation simulation failed: {str(e)}",
        }


def simulate_all_conversations(
    client,
    candidates: List[Dict[str, Any]],
    jd_text: str,
    progress_callback=None,
    rate_limit_callback: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """Run conversation simulation for all candidates."""
    results = []
    total = len(candidates)
    for i, candidate in enumerate(candidates):
        conv_data = simulate_conversation(client, candidate, jd_text)
        enriched = {**candidate, **conv_data}
        results.append(enriched)
        if progress_callback:
            progress_callback(i + 1, total, candidate["name"])
        # Rate-limit pause between API calls (skip after last candidate)
        if i < total - 1:
            if rate_limit_callback:
                rate_limit_callback(i + 1, total, candidate["name"])
            time.sleep(6)
    return results
