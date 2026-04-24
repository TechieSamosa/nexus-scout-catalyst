import json
import random

specifics = [
    {
        "id": "C001", "name": "Sanvi Kulkarni", "title": "Data Scientist", "experience_years": 3,
        "location": "Bhopal, India", "education": "B.Tech Computer Science, VIT Bhopal",
        "skills": ["Python", "Pandas", "Machine Learning", "SQL", "Tableau", "Scikit-Learn"],
        "summary": "Data Scientist with a strong background in predictive modeling.",
        "current_job_satisfaction": "Neutral", "salary_expectation": "15 LPA",
        "notice_period": "30 days", "preferred_work_mode": "Hybrid"
    },
    {
        "id": "C002", "name": "Kushi Desai", "title": "Bio Engineering Student", "experience_years": 0,
        "location": "Bhopal, India", "education": "B.Tech Bio Engineering, VIT Bhopal (Class of 2026)",
        "skills": ["Bioinformatics", "Python", "Data Analysis", "Research"],
        "summary": "Enthusiastic Bio Engineering student seeking internship opportunities.",
        "current_job_satisfaction": "Very dissatisfied (looking for first job)", "salary_expectation": "Stipend",
        "notice_period": "Immediate", "preferred_work_mode": "Remote"
    },
    {
        "id": "C003", "name": "Ananya Bhat", "title": "Data Science Specialist", "experience_years": 1,
        "location": "Vellore, India", "education": "Integrated M.Tech CSE (Spec in Data Science), VIT Vellore",
        "skills": ["Python", "Deep Learning", "NLP", "TensorFlow", "SQL"],
        "summary": "Recent graduate with specialized knowledge in Data Science and NLP.",
        "current_job_satisfaction": "Looking for growth", "salary_expectation": "18 LPA",
        "notice_period": "15 days", "preferred_work_mode": "Hybrid"
    },
    {
        "id": "C004", "name": "Greeshma Akkichetti", "title": "Software Engineer", "experience_years": 2,
        "location": "Hyderabad, India", "education": "B.Tech Computer Science",
        "skills": ["Java", "Spring Boot", "AWS", "Microservices", "REST APIs"],
        "summary": "Backend developer with experience in building scalable microservices.",
        "current_job_satisfaction": "Neutral", "salary_expectation": "16 LPA",
        "notice_period": "60 days", "preferred_work_mode": "On-site"
    },
    {
        "id": "C005", "name": "Aditya Khamitkar", "title": "Junior Data Scientist", "experience_years": 2,
        "location": "Pune, India", "education": "B.Tech AI & Data Science",
        "skills": ["Python", "PyTorch", "GANs", "Deep Learning", "Computer Vision"],
        "summary": "Passionate about deep learning, with strong expertise in GANs and image generation.",
        "current_job_satisfaction": "Wants more challenging AI projects", "salary_expectation": "14 LPA",
        "notice_period": "30 days", "preferred_work_mode": "Remote"
    },
    {
        "id": "C006", "name": "Aditya Khamitkar", "title": "ML Engineer", "experience_years": 4,
        "location": "Pune, India", "education": "M.Tech Computer Science",
        "skills": ["Python", "MLOps", "AWS", "Kubernetes", "Docker", "SageMaker"],
        "summary": "Machine Learning Engineer focusing on deploying models to production using MLOps best practices.",
        "current_job_satisfaction": "Satisfied but open to big tech roles", "salary_expectation": "28 LPA",
        "notice_period": "60 days", "preferred_work_mode": "Hybrid"
    },
    {
        "id": "C007", "name": "Aditya Khamitkar", "title": "Statistician", "experience_years": 5,
        "location": "Pune, India", "education": "M.Sc Statistics",
        "skills": ["R", "SAS", "Statistical Modeling", "A/B Testing", "Python", "Data Analysis"],
        "summary": "Statistician with extensive experience in experimental design and hypothesis testing.",
        "current_job_satisfaction": "Dissatisfied with company culture", "salary_expectation": "20 LPA",
        "notice_period": "30 days", "preferred_work_mode": "On-site"
    }
]

first_names = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Neha", "Rohan", "Pooja", "Karan", "Riya", "Aarav", "Ishita", "Arjun", "Kavya", "Aryan"]
last_names = ["Sharma", "Verma", "Gupta", "Singh", "Patel", "Reddy", "Nair", "Joshi", "Deshmukh", "Iyer", "Chauhan", "Bose"]
titles = ["Frontend Developer", "Backend Engineer", "Full Stack Developer", "DevOps Engineer", "Cloud Architect", "Product Manager", "UX Designer", "QA Engineer", "Staff Software Engineer", "Data Engineer"]
satisfactions = ["Highly satisfied", "Moderately satisfied", "Neutral", "Slightly dissatisfied", "Highly dissatisfied - looking to switch immediately", "Bored and seeking growth"]

for i in range(8, 31):
    candidate = {
        "id": f"C{i:03d}",
        "name": f"{random.choice(first_names)} {random.choice(last_names)}",
        "title": random.choice(titles),
        "experience_years": random.randint(1, 15),
        "location": random.choice(["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune"]) + ", India",
        "education": "B.Tech Computer Science",
        "skills": random.sample(["React", "Node.js", "Python", "AWS", "Docker", "Kubernetes", "Java", "Spring", "Go", "SQL", "NoSQL", "Figma", "GCP"], k=5),
        "summary": "Experienced professional looking for the next big challenge.",
        "current_job_satisfaction": random.choice(satisfactions),
        "salary_expectation": f"{random.randint(10, 60)} LPA",
        "notice_period": random.choice(["Immediate", "15 days", "30 days", "60 days", "90 days"]),
        "preferred_work_mode": random.choice(["Remote", "Hybrid", "On-site"])
    }
    specifics.append(candidate)

with open(r"c:\Users\HP\Desktop\deccan-catalyst-scout\data\candidates.json", "w") as f:
    json.dump(specifics, f, indent=2)

print("Generated 30 candidates successfully.")
