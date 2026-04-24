import json
from typing import Any, Dict, List
from src.llm_engine import call_gemini, parse_json_response

class ScoutAgent:
    def __init__(self, client):
        self.client = client
        self.system_instruction = (
            "You are an elite AI Scout Agent. Your job is to evaluate a batch of candidates "
            "against a job description simultaneously. Be strict but fair. "
            "A match_score of 80+ is excellent, 50-79 is moderate. "
            "Also estimate an interest_score (0-100) based on their profile, skills, and hidden satisfaction/salary expectations. "
            "Return valid JSON only."
        )

    def evaluate_batch(self, jd_text: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Format the candidates compactly to fit in context
        compact_candidates = []
        for c in candidates:
            compact_candidates.append({
                "id": c["id"],
                "name": c["name"],
                "title": c["title"],
                "experience_years": c["experience_years"],
                "skills": c.get("skills", []),
                "satisfaction": c.get("current_job_satisfaction", "Unknown"),
                "salary_expectation": c.get("salary_expectation", "Unknown"),
                "summary": c.get("summary", ""),
            })

        prompt = f"""
        Evaluate the following candidates against the Job Description.

        ## Job Description
        {jd_text}

        ## Candidates Batch
        {json.dumps(compact_candidates, indent=2)}

        ## Instructions
        Return a single JSON object with a 'results' key containing an array.
        For each candidate, provide:
        - "id": candidate id
        - "match_score": <int 0-100>
        - "interest_score": <int 0-100>
        - "explanation": "<exactly 2 sentences explaining both scores>"

        Return ONLY JSON. Do not include markdown code block syntax if it breaks parsing.
        """
        
        raw_response = call_gemini(self.client, prompt, system_instruction=self.system_instruction)
        try:
            parsed = parse_json_response(raw_response)
            results_list = parsed.get("results", [])
            
            # Merge back
            enriched = []
            results_map = {r["id"]: r for r in results_list if "id" in r}
            for c in candidates:
                res = results_map.get(c["id"], {})
                c_copy = c.copy()
                c_copy["match_score"] = res.get("match_score", 0)
                c_copy["interest_score"] = res.get("interest_score", 0)
                c_copy["explanation"] = res.get("explanation", "Failed to evaluate.")
                
                # Compute final score exactly like leaderboard used to do
                c_copy["final_score"] = int((c_copy["match_score"] * 0.6) + (c_copy["interest_score"] * 0.4))
                enriched.append(c_copy)
            return enriched
        except Exception as e:
            raise RuntimeError(f"ScoutAgent failed to process batch: {e}\nRaw output: {raw_response[:500]}")


class NegotiatorAgent:
    def __init__(self, client):
        self.client = client
        self.system_instruction = (
            "You are a Negotiator Agent. Your job is to draft highly personalized, "
            "persuasive outreach messages to top candidates."
        )

    def draft_outreach_batch(self, jd_text: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        compact_candidates = []
        for c in candidates:
            compact_candidates.append({
                "id": c["id"],
                "name": c["name"],
                "title": c["title"],
                "skills": c.get("skills", []),
                "satisfaction": c.get("current_job_satisfaction", "Unknown")
            })

        prompt = f"""
        You are reaching out to the Top {len(candidates)} candidates for the following job.
        
        ## Job Description
        {jd_text[:1000]}
        
        ## Top Candidates
        {json.dumps(compact_candidates, indent=2)}
        
        ## Instructions
        For each candidate, write a highly persuasive 3-sentence outreach message.
        Tailor the hook based on their specific skills and hidden satisfaction level.
        Return ONLY a JSON object with a 'results' key containing an array.
        Each item should have:
        - "id": candidate id
        - "outreach_message": "..."
        """
        raw_response = call_gemini(self.client, prompt, system_instruction=self.system_instruction)
        
        parsed = parse_json_response(raw_response)
        results_list = parsed.get("results", [])
        
        enriched = []
        results_map = {r["id"]: r for r in results_list if "id" in r}
        for c in candidates:
            c_copy = c.copy()
            c_copy["outreach_message"] = results_map.get(c["id"], {}).get("outreach_message", "Could not generate message.")
            enriched.append(c_copy)
        return enriched
