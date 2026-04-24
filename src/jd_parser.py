"""
jd_parser.py — Extracts structured requirements from raw Job Description text.
"""

import re
from typing import Dict, List, Any

SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#",
    "react", "angular", "vue", "next.js", "node.js", "express", "django", "flask", "fastapi",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
    "jenkins", "ci/cd", "github actions",
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "spark", "airflow",
    "langchain", "llamaindex", "openai", "hugging face", "rag", "llm", "genai",
    "prompt engineering", "vector database",
    "rest api", "graphql", "microservices",
    "agile", "scrum", "jira", "product management",
    "figma", "ui/ux", "penetration testing", "cybersecurity", "siem", "owasp",
    "flutter", "dart", "kotlin", "swift", "react native",
    "power bi", "tableau", "a/b testing", "analytics",
    "git", "linux", "bash", "devops", "mlops",
]

EXPERIENCE_PATTERNS = [
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
    r"(?:experience|exp)\s*(?:of\s+)?(\d+)\+?\s*(?:years?|yrs?)",
    r"(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)",
]

ROLE_TYPE_KEYWORDS = {
    "backend": ["backend", "server-side", "api development"],
    "frontend": ["frontend", "front-end", "user interface"],
    "fullstack": ["full stack", "fullstack", "full-stack"],
    "data_science": ["data science", "machine learning", "ml engineer"],
    "devops": ["devops", "sre", "infrastructure", "cloud engineer"],
    "mobile": ["mobile", "android", "ios", "flutter"],
    "product": ["product manager", "product owner"],
    "security": ["security", "cybersecurity", "penetration testing"],
    "data_analyst": ["data analyst", "business analyst", "analytics"],
    "genai": ["genai", "generative ai", "llm", "large language model"],
}


def extract_skills(jd_text: str) -> List[str]:
    jd_lower = jd_text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        if len(skill) <= 3:
            if re.search(rf"\b{re.escape(skill)}\b", jd_lower):
                found.append(skill)
        else:
            if skill in jd_lower:
                found.append(skill)
    return list(set(found))


def extract_experience(jd_text: str) -> Dict[str, Any]:
    jd_lower = jd_text.lower()
    for pattern in EXPERIENCE_PATTERNS:
        match = re.search(pattern, jd_lower)
        if match:
            groups = match.groups()
            if len(groups) == 2 and groups[1] is not None:
                return {"min_years": int(groups[0]), "max_years": int(groups[1])}
            return {"min_years": int(groups[0]), "max_years": None}
    return {"min_years": None, "max_years": None}


def detect_role_type(jd_text: str) -> List[str]:
    jd_lower = jd_text.lower()
    detected = []
    for role_type, keywords in ROLE_TYPE_KEYWORDS.items():
        if any(k in jd_lower for k in keywords):
            detected.append(role_type)
    return detected or ["general"]


def parse_jd(jd_text: str) -> Dict[str, Any]:
    """Main parser: returns skills, experience, role_types, raw_text."""
    return {
        "skills": extract_skills(jd_text),
        "experience": extract_experience(jd_text),
        "role_types": detect_role_type(jd_text),
        "raw_text": jd_text.strip(),
    }
