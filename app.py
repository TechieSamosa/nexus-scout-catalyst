"""
Nexus Scout — AI Talent Scouting Agent
Main Streamlit application.
"""

import json
import os
import random
import time
import streamlit as st
from dotenv import load_dotenv

import requests
import plotly.express as px
from streamlit_lottie import st_lottie
from src.jd_parser import parse_jd
from src.agents import build_workflow
from src.leaderboard import to_dataframe, get_tier

# ---------------------------------------------------------------------------
# Page config & theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Nexus Scout",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for premium look
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide default streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main container */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Hero header */
.hero-header {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-header h1 {
    color: #ffffff;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.5px;
}
.hero-header p {
    color: #a5b4fc;
    font-size: 1.05rem;
    margin: 0;
    font-weight: 400;
}

/* Metric cards */
.metric-card {
    background: rgba(30, 27, 75, 0.4);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 20px rgba(0, 242, 254, 0.4), inset 0 0 10px rgba(0, 242, 254, 0.2);
    border-color: rgba(0, 242, 254, 0.6);
}
.metric-value {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00f2fe, #4facfe);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.metric-label {
    color: #94a3b8;
    font-size: 0.85rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 0.3rem;
}

/* Candidate card */
.candidate-card {
    background: rgba(30, 41, 59, 0.4);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
}
.candidate-card:hover {
    border-color: rgba(0, 242, 254, 0.4);
    box-shadow: 0 0 25px rgba(0, 242, 254, 0.25);
}
.candidate-name {
    font-size: 1.3rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0 0 0.2rem 0;
}
.candidate-title {
    color: #818cf8;
    font-size: 0.95rem;
    font-weight: 500;
    margin: 0 0 0.8rem 0;
}
.score-badge {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
    margin-right: 0.5rem;
}
.score-excellent { background: rgba(34,197,94,0.15); color: #4ade80; }
.score-good { background: rgba(234,179,8,0.15); color: #facc15; }
.score-moderate { background: rgba(249,115,22,0.15); color: #fb923c; }
.score-weak { background: rgba(239,68,68,0.15); color: #f87171; }

/* Chat bubble */
.chat-bubble {
    padding: 0.7rem 1rem;
    border-radius: 12px;
    margin-bottom: 0.6rem;
    max-width: 85%;
    font-size: 0.9rem;
    line-height: 1.5;
}
.chat-recruiter {
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: #c7d2fe;
    margin-right: auto;
}
.chat-candidate {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.2);
    color: #a7f3d0;
    margin-left: auto;
}
.chat-role-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.2rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29 0%, #1e1b4b 100%);
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li {
    color: #cbd5e1;
}

/* Table styling */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Load environment
# ---------------------------------------------------------------------------
load_dotenv()

JD_POOL = [
    """Senior Backend Engineer — FinTech Startup (Hyderabad)

We are looking for a Senior Backend Engineer to join our core payments team. You will design and build scalable microservices that process millions of transactions daily.

Requirements:
- 4+ years of experience in backend development
- Strong proficiency in Python, Django or Flask
- Experience with PostgreSQL, Redis, and message queues
- Hands-on experience with Docker, Kubernetes, and AWS
- Familiarity with CI/CD pipelines and DevOps practices
- Experience building and consuming REST APIs at scale
- Strong understanding of distributed systems and microservices architecture

Nice to have:
- Experience in fintech or payments domain
- Knowledge of event-driven architecture (Kafka, RabbitMQ)
- AWS certifications

We offer competitive compensation (₹30-45 LPA), hybrid work from our Hyderabad office, and equity in a Series-B funded startup.""",

    """Data Scientist — HealthTech Company (Bangalore)

Join our data science team building predictive models that improve patient outcomes across 200+ hospitals.

Requirements:
- 3+ years of experience in data science or machine learning
- Strong proficiency in Python, Pandas, NumPy, and Scikit-learn
- Experience with deep learning frameworks (TensorFlow or PyTorch)
- Solid understanding of statistics, probability, and hypothesis testing
- Experience with SQL and large-scale data pipelines
- Ability to communicate insights to non-technical stakeholders

Nice to have:
- Experience in healthcare or biotech domain
- Knowledge of NLP and computer vision techniques
- Publications in peer-reviewed ML conferences

Compensation: ₹25-40 LPA with health benefits and remote flexibility.""",

    """ML Engineer — Autonomous Vehicles Division (Pune)

We are hiring an ML Engineer to develop and deploy perception models for our self-driving vehicle platform.

Requirements:
- 3+ years building production ML systems
- Expertise in Python, PyTorch, and ONNX
- Experience with computer vision (object detection, segmentation)
- Proficiency in model optimization and edge deployment (TensorRT, CUDA)
- Familiarity with MLOps tools (MLflow, Kubeflow, or Weights & Biases)
- Strong C++ skills for performance-critical components

Nice to have:
- Experience with LiDAR or sensor fusion
- Contributions to open-source ML projects
- MS/PhD in Computer Science or related field

Compensation: ₹35-55 LPA + stock options + relocation support.""",

    """DevOps / SRE Engineer — E-Commerce Platform (Mumbai)

We need a DevOps Engineer to maintain and scale infrastructure supporting 50M+ monthly active users.

Requirements:
- 4+ years of experience in DevOps or Site Reliability Engineering
- Expert-level knowledge of AWS (EC2, ECS, Lambda, RDS, S3)
- Strong experience with Terraform, Ansible, or Pulumi for IaC
- Proficiency in Docker, Kubernetes, and Helm charts
- Experience setting up CI/CD pipelines (GitHub Actions, Jenkins, ArgoCD)
- Monitoring and observability (Prometheus, Grafana, Datadog)

Nice to have:
- Experience with service mesh (Istio, Linkerd)
- Chaos engineering practices
- AWS Solutions Architect certification

Compensation: ₹28-42 LPA, fully remote with quarterly offsites.""",

    """Frontend Engineer — EdTech Startup (Remote, India)

Build beautiful, accessible, and performant learning experiences used by 2M+ students.

Requirements:
- 3+ years of professional frontend development
- Expert-level React.js and TypeScript
- Experience with Next.js and server-side rendering
- Strong CSS skills (Tailwind CSS, CSS Modules, or Styled Components)
- Experience with state management (Redux, Zustand, or Jotai)
- Knowledge of web accessibility standards (WCAG 2.1)

Nice to have:
- Experience with animation libraries (Framer Motion, GSAP)
- Familiarity with design systems and Storybook
- Experience with WebRTC or real-time collaboration features

Compensation: ₹20-35 LPA, 100% remote, flexible hours.""",

    """Cloud Architect — Banking & Financial Services (Chennai)

Design and implement cloud-native architectures for one of India's largest private banks.

Requirements:
- 6+ years of experience in cloud architecture and design
- Deep expertise in AWS or Azure (multi-account strategy, landing zones)
- Experience designing microservices and event-driven architectures
- Strong knowledge of security best practices (IAM, encryption, compliance)
- Experience with containerization and orchestration at scale
- Hands-on with Infrastructure as Code (Terraform, CloudFormation)

Nice to have:
- Experience in BFSI or regulated industries
- AWS Solutions Architect Professional or Azure Solutions Architect Expert
- Knowledge of FinOps and cloud cost optimization

Compensation: ₹45-65 LPA + performance bonus.""",

    """Full Stack Developer — SaaS Product (Hyderabad)

Join our product team building a next-generation project management SaaS platform.

Requirements:
- 3+ years of full stack development experience
- Proficiency in React.js or Vue.js for frontend
- Backend experience with Node.js (Express/Fastify) or Python (FastAPI/Django)
- Strong experience with PostgreSQL and Redis
- Understanding of RESTful API design and GraphQL
- Familiarity with Git workflows and code review practices

Nice to have:
- Experience with WebSocket-based real-time features
- Knowledge of multi-tenancy patterns
- Prior experience in B2B SaaS products

Compensation: ₹22-38 LPA, hybrid work, generous ESOP pool.""",

    """Cybersecurity Engineer — Defence & Aerospace (Hyderabad)

Strengthen the security posture of mission-critical systems used across defence operations.

Requirements:
- 4+ years in cybersecurity or information security
- Experience with vulnerability assessment and penetration testing
- Strong knowledge of network security, firewalls, and IDS/IPS
- Proficiency in Python or Go for security tooling and automation
- Familiarity with SIEM platforms (Splunk, ELK, or QRadar)
- Understanding of compliance frameworks (ISO 27001, NIST, SOC 2)

Nice to have:
- OSCP, CEH, or CISSP certification
- Experience with cloud security (AWS Security Hub, GuardDuty)
- Background in threat intelligence or incident response

Compensation: ₹30-50 LPA + government project allowances.""",

    """Mobile App Developer — Consumer FinTech (Bangalore)

Build and ship delightful mobile experiences for our personal finance super-app with 5M+ users.

Requirements:
- 3+ years of mobile development experience
- Proficiency in React Native or Flutter (cross-platform)
- Experience with native modules (Swift/Kotlin) for platform-specific features
- Strong understanding of mobile UI/UX patterns and performance optimization
- Experience integrating payment SDKs, biometrics, and push notifications
- Familiarity with CI/CD for mobile (Fastlane, Bitrise, or Codemagic)

Nice to have:
- Experience with offline-first architecture
- Knowledge of app store optimization (ASO)
- Prior experience in fintech or payments domain

Compensation: ₹25-40 LPA, hybrid Bangalore, wellness benefits.""",

    """Data Engineer — Logistics & Supply Chain (Pune)

Design and maintain data pipelines powering real-time analytics for a fleet of 10,000+ delivery vehicles.

Requirements:
- 3+ years of data engineering experience
- Strong proficiency in Python and SQL
- Experience with Apache Spark, Kafka, and Airflow
- Hands-on with cloud data warehouses (BigQuery, Redshift, or Snowflake)
- Knowledge of data modeling, ETL/ELT patterns, and data quality frameworks
- Experience with Docker and Kubernetes for pipeline deployment

Nice to have:
- Experience with real-time streaming (Flink, Kafka Streams)
- Knowledge of dbt for data transformation
- Familiarity with logistics or supply chain domain

Compensation: ₹24-38 LPA, hybrid Pune, learning budget of ₹1L/year.""",
]


def load_candidates():
    """Load candidates from JSON file."""
    data_path = os.path.join(os.path.dirname(__file__), "data", "candidates.json")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


def get_score_class(score):
    """Return CSS class based on score value."""
    if score >= 80:
        return "score-excellent"
    elif score >= 60:
        return "score-good"
    elif score >= 40:
        return "score-moderate"
    return "score-weak"


def render_hero():
    """Render the hero header."""
    st.markdown("""
    <div class="hero-header">
        <h1>🎯 Nexus Scout</h1>
        <p>AI-Powered Talent Scouting Agent — Paste a JD, discover your best candidates</p>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(results):
    """Render summary metric cards."""
    avg_match = sum(c.get("match_score", 0) for c in results) / len(results)
    avg_interest = sum(c.get("interest_score", 0) for c in results) / len(results)
    avg_final = sum(c.get("final_score", 0) for c in results) / len(results)
    top = results[0]["name"] if results else "—"

    cols = st.columns(4)
    metrics = [
        (f"{avg_match:.0f}", "Avg Match Score"),
        (f"{avg_interest:.0f}", "Avg Interest Score"),
        (f"{avg_final:.0f}", "Avg Final Score"),
        (f"🏆 {top}", "Top Candidate"),
    ]
    for col, (val, label) in zip(cols, metrics):
        col.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{val}</p>
            <p class="metric-label">{label}</p>
        </div>
        """, unsafe_allow_html=True)


def render_candidate_card(candidate, expanded=False):
    """Render a single candidate card with expandable details."""
    ms = candidate.get("match_score", 0)
    iscore = candidate.get("interest_score", 0)
    fs = candidate.get("final_score", 0)
    rank = candidate.get("rank", "?")
    tier = get_tier(fs)

    ms_class = get_score_class(ms)
    is_class = get_score_class(iscore)
    fs_class = get_score_class(fs)

    with st.expander(
        f"#{rank}  {candidate['name']}  —  {candidate['title']}  |  Final: {fs}  {tier}",
        expanded=expanded,
    ):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{ms}</p>
                <p class="metric-label">Match Score</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{iscore}</p>
                <p class="metric-label">Interest Score</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{fs}</p>
                <p class="metric-label">Final Score</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        col_exp, col_radar = st.columns([1.5, 1])
        
        with col_exp:
            st.markdown(f"**📝 Match Explanation:** {candidate.get('explanation', 'N/A')}")
            
        with col_radar:
            # Generate Radar Chart
            categories = ['JD Alignment', 'Technical Depth', 'Experience Match', 'Role Fit', 'Domain Knowledge']
            # Map score to axes with slight variance
            score = ms
            r_values = [
                min(100, score + random.randint(-5, 5)),
                min(100, score + random.randint(-10, 10)),
                min(100, score + random.randint(-5, 5)),
                min(100, score + random.randint(-8, 8)),
                min(100, score + random.randint(-15, 15)),
            ]
            
            import pandas as pd
            df_radar = pd.DataFrame(dict(r=r_values, theta=categories))
            fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True)
            fig.update_traces(fill='toself', fillcolor='rgba(0, 242, 254, 0.4)', line_color='#00f2fe')
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, gridcolor='rgba(255,255,255,0.1)'),
                    angularaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#cbd5e1'))
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=20, b=20),
                height=250
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")

        # Candidate details
        det_col1, det_col2 = st.columns(2)
        with det_col1:
            st.markdown(f"**📍 Location:** {candidate.get('location', 'N/A')}")
            st.markdown(f"**🎓 Education:** {candidate.get('education', 'N/A')}")
            st.markdown(f"**⏰ Notice Period:** {candidate.get('notice_period', 'N/A')}")
        with det_col2:
            st.markdown(f"**💰 Salary:** {candidate.get('salary_expectation', 'N/A')}")
            st.markdown(f"**🏢 Work Mode:** {candidate.get('preferred_work_mode', 'N/A')}")
            st.markdown(f"**📅 Experience:** {candidate.get('experience_years', 'N/A')} years")

        # Skills
        skills = candidate.get("skills", [])
        if skills:
            skill_tags = " ".join(
                [f"`{s}`" for s in skills]
            )
            st.markdown(f"**🛠️ Skills:** {skill_tags}")

        # Outreach Message
        outreach = candidate.get("outreach_message")
        if outreach:
            st.markdown("---")
            st.markdown("**✍️ Negotiator Agent Outreach Draft:**")
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 1rem; border-radius: 4px;">
                <i>"{outreach}"</i>
            </div>
            """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")


    st.markdown("### 📊 Scoring Weights")
    match_weight = st.slider("Match Score Weight", 0.0, 1.0, 0.6, 0.05)
    interest_weight = round(1.0 - match_weight, 2)
    st.caption(f"Interest Weight: **{interest_weight}**")

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    **Nexus Scout** uses Llama-3 (Groq) via LangGraph
    to intelligently match candidates to job descriptions
    and simulate recruiter conversations to assess interest.

    Built for the **Deccan Catalyst Hackathon** 🚀
    """)


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
render_hero()

# JD Input
st.markdown("### 📋 Job Description")
col_jd1, col_jd2 = st.columns([4, 1])
with col_jd2:
    gen_random = st.button("🎲 Generate Random JD", use_container_width=True)

if gen_random:
    st.session_state["jd_text"] = random.choice(JD_POOL)

jd_text = st.text_area(
    "Paste the Job Description below",
    value=st.session_state.get("jd_text", ""),
    height=220,
    placeholder="Paste a detailed job description here...",
    label_visibility="collapsed",
)
st.session_state["jd_text"] = jd_text

# Parse preview
if jd_text.strip():
    parsed = parse_jd(jd_text)
    with st.expander("🔍 Parsed JD Preview", expanded=False):
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            st.markdown(f"**Role Types:** {', '.join(parsed['role_types'])}")
        with p_col2:
            exp = parsed["experience"]
            exp_str = f"{exp['min_years']}+ years" if exp["min_years"] else "Not specified"
            st.markdown(f"**Experience:** {exp_str}")
        with p_col3:
            st.markdown(f"**Skills Found:** {len(parsed['skills'])}")
        if parsed["skills"]:
            st.markdown(" ".join([f"`{s}`" for s in sorted(parsed["skills"])]))

st.markdown("---")

# Scout button
scout_btn = st.button(
    "🚀 Scout Candidates",
    use_container_width=True,
    type="primary",
    disabled=not jd_text.strip(),
)

# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------
if scout_btn:
    api_key = ""
    try:
        api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
        
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY", "")

    if not api_key:
        st.error("⚠️ API key not found. Please set GROQ_API_KEY in Streamlit secrets or environment variables.")
        st.stop()
    else:
        # Set it in the environment so Langchain can pick it up
        os.environ["GROQ_API_KEY"] = api_key

    if not jd_text.strip():
        st.error("⚠️ Please paste a Job Description.")
        st.stop()

    # Load candidates
    candidates = load_candidates()

    # Create Lottie container
    lottie_container = st.empty()
    with lottie_container.container():
        st.markdown("<h3 style='text-align: center; color: #00f2fe;'>Initializing LangGraph Agentic Workflow...</h3>", unsafe_allow_html=True)
        # Radar animation
        lottie_url = "https://lottie.host/80dc0e6e-2144-4b53-b30f-b054238714eb/E2kP0Jt774.json"
        lottie_json = load_lottieurl(lottie_url)
        if not lottie_json:
            # Fallback URL
            lottie_url = "https://assets9.lottiefiles.com/packages/lf20_x62chj8y.json"
            lottie_json = load_lottieurl(lottie_url)
            
        if lottie_json:
            st_lottie(lottie_json, height=300, key="scanning")
        else:
            st.info("Scanning candidates in batch mode...")

    # Status updates
    app = build_workflow()
    
    with st.status('Agent Graph Executing...', expanded=True) as status:
        try:
            status.write("Initializing LangGraph Workflow...")
            status.write("Scout Node analyzing batches of candidates...")
            
            # Stream execution
            events = app.stream({
                "candidates_list": candidates,
                "jd_text": jd_text,
                "match_weight": match_weight,
                "interest_weight": interest_weight
            })
            
            final_state = {}
            for event in events:
                node_name = list(event.keys())[0]
                final_state = event[node_name]
                
                if node_name == "scout":
                    status.write("Scout Node complete. Filtering Top 3...")
                elif node_name == "negotiator":
                    status.write("Negotiator Node drafting custom outreach...")
            
            ranked = final_state.get("final_scores", [])
            status.update(label="Agentic Workflow complete!", state="complete", expanded=False)
            
        except Exception as e:
            lottie_container.empty()
            status.update(label=f"Agentic Workflow failed: {e}", state="error", expanded=True)
            st.stop()
            
    lottie_container.empty()
    st.session_state["results"] = ranked

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]

    st.markdown("---")
    st.markdown("### 📊 Results Dashboard")

    # Metrics row
    render_metrics(results)
    st.markdown("")

    # Leaderboard table
    st.markdown("### 🏆 Candidate Leaderboard")
    df = to_dataframe(results)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("🏅 Rank", width="small"),
            "Match Score": st.column_config.ProgressColumn(
                "Match Score", min_value=0, max_value=100, format="%d"
            ),
            "Interest Score": st.column_config.ProgressColumn(
                "Interest Score", min_value=0, max_value=100, format="%d"
            ),
            "Final Score": st.column_config.ProgressColumn(
                "Final Score", min_value=0, max_value=100, format="%d"
            ),
        },
    )

    # Candidate detail cards
    st.markdown("---")
    st.markdown("### 👥 Candidate Details")
    st.caption("Click on any candidate to expand their full profile, scores, and conversation.")
    for i, candidate in enumerate(results):
        render_candidate_card(candidate, expanded=(i == 0))
