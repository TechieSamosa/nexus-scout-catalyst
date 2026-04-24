import json
import os
from typing import Any, Dict, List, TypedDict
from pydantic import BaseModel, Field

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# --- Pydantic Models for Structured Output ---

class CandidateScore(BaseModel):
    id: str = Field(description="The unique ID of the candidate")
    match_score: int = Field(description="Match score out of 100")
    interest_score: int = Field(description="Interest score out of 100")
    explanation: str = Field(description="Exactly 2 sentences explaining both scores")

class ScoutBatchResult(BaseModel):
    results: List[CandidateScore]

class OutreachMessage(BaseModel):
    id: str = Field(description="The unique ID of the candidate")
    outreach_message: str = Field(description="The 3-sentence customized outreach message")

class NegotiatorBatchResult(BaseModel):
    results: List[OutreachMessage]

# --- Graph State ---

class GraphState(TypedDict):
    candidates_list: List[Dict[str, Any]]
    jd_text: str
    match_weight: float
    interest_weight: float
    processed_candidates: List[Dict[str, Any]]
    final_scores: List[Dict[str, Any]]

# --- Nodes ---

def scout_node(state: GraphState):
    """
    Chunks candidates into groups of 5 and processes them via ChatGroq.
    """
    candidates = state["candidates_list"]
    jd_text = state["jd_text"]
    match_w = state.get("match_weight", 0.6)
    interest_w = state.get("interest_weight", 0.4)
    
    # Initialize ChatGroq with versatile model as requested
    llm = ChatGroq(model="llama3-70b-8192", temperature=0.2)
    structured_llm = llm.with_structured_output(ScoutBatchResult)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an elite AI Scout Agent. Evaluate the batch of candidates against the job description simultaneously. Be strict but fair. A match_score of 80+ is excellent, 50-79 is moderate. Also estimate an interest_score (0-100) based on their profile, skills, and hidden satisfaction/salary expectations."),
        ("human", "## Job Description\n{jd_text}\n\n## Candidates Batch\n{candidates_batch}")
    ])
    
    chain = prompt | structured_llm
    
    chunk_size = 5
    enriched_candidates = []
    
    # Chunking logic
    for i in range(0, len(candidates), chunk_size):
        chunk = candidates[i:i+chunk_size]
        compact_chunk = []
        for c in chunk:
            compact_chunk.append({
                "id": c["id"],
                "name": c["name"],
                "title": c["title"],
                "experience_years": c["experience_years"],
                "skills": c.get("skills", []),
                "satisfaction": c.get("current_job_satisfaction", "Unknown"),
                "salary_expectation": c.get("salary_expectation", "Unknown"),
                "summary": c.get("summary", ""),
            })
            
        try:
            result = chain.invoke({
                "jd_text": jd_text,
                "candidates_batch": json.dumps(compact_chunk, indent=2)
            })
            
            results_map = {r.id: r for r in result.results}
            for c in chunk:
                c_copy = c.copy()
                res = results_map.get(c["id"])
                if res:
                    c_copy["match_score"] = res.match_score
                    c_copy["interest_score"] = res.interest_score
                    c_copy["explanation"] = res.explanation
                else:
                    c_copy["match_score"] = 0
                    c_copy["interest_score"] = 0
                    c_copy["explanation"] = "Failed to evaluate."
                
                c_copy["final_score"] = round((c_copy["match_score"] * match_w) + (c_copy["interest_score"] * interest_w), 1)
                enriched_candidates.append(c_copy)
                
        except Exception as e:
            print(f"Error processing chunk: {e}")
            for c in chunk:
                c_copy = c.copy()
                c_copy["match_score"] = 0
                c_copy["interest_score"] = 0
                c_copy["explanation"] = f"Failed: {e}"
                c_copy["final_score"] = 0
                enriched_candidates.append(c_copy)
                
    # Sort candidates
    enriched_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    for idx, c in enumerate(enriched_candidates):
         c["rank"] = idx + 1
         
    return {"processed_candidates": enriched_candidates}

def negotiator_node(state: GraphState):
    """
    Takes top 3 candidates from state and generates custom outreach emails.
    """
    processed = state.get("processed_candidates", [])
    jd_text = state["jd_text"]
    
    top_3 = processed[:3]
    
    if not top_3:
        return {"final_scores": processed}
        
    llm = ChatGroq(model="llama3-70b-8192", temperature=0.7)
    structured_llm = llm.with_structured_output(NegotiatorBatchResult)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Negotiator Agent. Your job is to draft highly personalized, persuasive outreach messages to top candidates. Write a highly persuasive 3-sentence outreach message for each candidate. Tailor the hook based on their specific skills and hidden satisfaction level."),
        ("human", "## Job Description\n{jd_text}\n\n## Top Candidates\n{candidates_batch}")
    ])
    
    chain = prompt | structured_llm
    
    compact_candidates = []
    for c in top_3:
        compact_candidates.append({
            "id": c["id"],
            "name": c["name"],
            "title": c["title"],
            "skills": c.get("skills", []),
            "satisfaction": c.get("current_job_satisfaction", "Unknown")
        })
        
    try:
        result = chain.invoke({
            "jd_text": jd_text[:1000],
            "candidates_batch": json.dumps(compact_candidates, indent=2)
        })
        
        results_map = {r.id: r for r in result.results}
        
        for i, c in enumerate(top_3):
            res = results_map.get(c["id"])
            if res:
                top_3[i]["outreach_message"] = res.outreach_message
            else:
                top_3[i]["outreach_message"] = "Could not generate message."
                
    except Exception as e:
         print(f"Error generating outreach: {e}")
         for i, c in enumerate(top_3):
             top_3[i]["outreach_message"] = f"Could not generate message: {e}"
             
    # Reassemble final_scores
    final_list = top_3 + processed[3:]
    return {"final_scores": final_list}

def build_workflow():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("scout", scout_node)
    workflow.add_node("negotiator", negotiator_node)
    
    workflow.set_entry_point("scout")
    workflow.add_edge("scout", "negotiator")
    workflow.add_edge("negotiator", END)
    
    return workflow.compile()

