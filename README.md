# 🎯 Nexus Scout

**AI-Powered Talent Scouting Agent** — Built for the Deccan Catalyst Hackathon

## What It Does

1. **Paste a Job Description** → The agent parses skills, experience, and role type
2. **AI Match Scoring** → Google Gemini evaluates each of 10 candidates against the JD (0-100 score + explanation)
3. **Conversation Simulation** → An AI recruiter chats with each candidate to assess their interest (0-100 score)
4. **Ranked Leaderboard** → Candidates are ranked by a weighted final score (60% Match + 40% Interest)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Key

Get a **free** Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

Option A — Create a `.env` file:
```bash
cp .env.example .env
# Edit .env and paste your key
```

Option B — Paste it directly in the app sidebar.

### 3. Run the App

```bash
streamlit run app.py
```

## Tech Stack

- **Frontend:** Streamlit with custom dark theme
- **LLM:** Google Gemini 2.0 Flash (free tier)
- **Language:** Python 3.10+

## Project Structure

```
├── app.py                  # Streamlit entry point
├── data/
│   └── candidates.json     # 10 synthetic candidate profiles
├── src/
│   ├── jd_parser.py        # JD text → structured requirements
│   ├── llm_engine.py       # Gemini API wrapper
│   ├── matcher.py          # Candidate ↔ JD match scoring
│   ├── conversation_sim.py # AI recruiter conversation simulation
│   └── leaderboard.py      # Score aggregation & ranking
├── .streamlit/
│   └── config.toml         # Dark theme configuration
├── requirements.txt
└── .env.example
```

## Scoring Formula

```
Final Score = (0.6 × Match Score) + (0.4 × Interest Score)
```

Weights are adjustable via the sidebar slider.

---

*Built with ❤️ for the Deccan Catalyst Hackathon*

