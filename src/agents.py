import os
import json
from typing import Any, Dict, List, TypedDict
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

# --- State Definition ---
class GraphState(TypedDict):
    candidates_list: List[Dict[str, Any]]
    jd_text: str
    match_weight: float
    interest_weight: float
    final_scores: List[Dict[str, Any]]

# --- Pydantic Models for Structured Output ---
class CandidateEvaluation(BaseModel):
    id: str = Field(description="The ID of the candidate")
    match_score: int = Field(description="Score from 0-100 indicating JD match")
    interest_score: int = Field(description="Score from 0-100 indicating candidate interest")
    explanation: str = Field(description="Exactly 2 sentences explaining the scores")

class BatchEvaluation(BaseModel):
    results: List[CandidateEvaluation] = Field(description="List of candidate evaluations")

class CandidateOutreach(BaseModel):
    id: str = Field(description="The ID of the candidate")
    outreach_message: str = Field(description="3-sentence outreach message")

class BatchOutreach(BaseModel):
    results: List[CandidateOutreach] = Field(description="List of outreach messages")

# --- Node Functions ---
def scout_node(state: GraphState):
    """Evaluates candidates in batches against the JD."""
    # Initialize Llama-3 70B via Groq
    llm = ChatGroq(model_name="llama3-70b-8192", temperature=0)
    structured_llm = llm.with_structured_output(BatchEvaluation)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an elite AI Scout Agent. Your job is to evaluate a batch of candidates against a job description simultaneously. Be strict but fair. A match_score of 80+ is excellent, 50-79 is moderate. Also estimate an interest_score (0-100) based on their profile, skills, and hidden satisfaction/salary expectations."),
        ("user", "## Job Description\n{jd_text}\n\n## Candidates Batch\n{candidates_batch}")
    ])
    
    chain = prompt | structured_llm
    
    candidates = state["candidates_list"]
    match_w = state["match_weight"]
    interest_w = state["interest_weight"]
    
    enriched_candidates = []
    chunk_size = 15  # Process in chunks of 15 to ensure reliable structured output
    
    for i in range(0, len(candidates), chunk_size):
        chunk = candidates[i:i + chunk_size]
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
                "jd_text": state["jd_text"],
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
            raise RuntimeError(f"ScoutAgent failed to process batch: {e}")
            
    # Sort and rank
    enriched_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    for rank, c in enumerate(enriched_candidates, 1):
        c["rank"] = rank
        
    return {"final_scores": enriched_candidates}

def negotiator_node(state: GraphState):
    """Drafts personalized outreach messages for the top candidates."""
    llm = ChatGroq(model_name="llama3-70b-8192", temperature=0.7)
    structured_llm = llm.with_structured_output(BatchOutreach)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Negotiator Agent. Your job is to draft highly personalized, persuasive outreach messages to top candidates."),
        ("user", "You are reaching out to the Top candidates for the following job.\n\n## Job Description\n{jd_text}\n\n## Top Candidates\n{candidates_batch}\n\nFor each candidate, write a highly persuasive 3-sentence outreach message. Tailor the hook based on their specific skills and hidden satisfaction level.")
    ])
    
    chain = prompt | structured_llm
    
    final_scores = state["final_scores"]
    top_3 = final_scores[:3]
    
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
            "jd_text": state["jd_text"][:1000],
            "candidates_batch": json.dumps(compact_candidates, indent=2)
        })
        
        results_map = {r.id: r for r in result.results}
        
        for c in top_3:
            res = results_map.get(c["id"])
            c["outreach_message"] = res.outreach_message if res else "Could not generate message."
    except Exception as e:
        print(f"Negotiator failed: {e}")
        
    return {"final_scores": final_scores}

# --- Graph Builder ---
def build_workflow():
    """Build and compile the LangGraph agentic workflow."""
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("scout", scout_node)
    workflow.add_node("negotiator", negotiator_node)
    
    # Define edges
    workflow.add_edge(START, "scout")
    workflow.add_edge("scout", "negotiator")
    workflow.add_edge("negotiator", END)
    
    return workflow.compile()
