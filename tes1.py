"""
TalentScout Hiring Assistant (Gemini Edition)
--------------------------------------------
- Streamlit UI for candidate screening
- Generates 3–5 technical questions per tech using Gemini or local fallback
- Handles follow-up chat gracefully
"""

import streamlit as st
import json, os, re
from datetime import datetime
from typing import List, Dict

# Optional Gemini setup
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

# ---------- Constants ----------
END_KEYWORDS = {"exit", "quit", "bye", "goodbye", "end", "stop"}
SIMULATED_DB_PATH = "simulated_candidates.json"

# ---------- Utilities ----------
def sanitize_text(s: str) -> str:
    return s.strip()

def split_tech_stack(raw: str) -> List[str]:
    items = re.split(r"[,\n/|]+|\band\b", raw, flags=re.IGNORECASE)
    return [sanitize_text(i) for i in items if sanitize_text(i)]

def anonymize_candidate(candidate: Dict) -> Dict:
    anonym = candidate.copy()
    anonym["email"] = "***redacted***"
    anonym["phone"] = "***redacted***"
    return anonym

def save_simulated(candidate: Dict):
    anonym = anonymize_candidate(candidate)
    record = {"timestamp": datetime.utcnow().isoformat() + "Z", "candidate": anonym}
    data = []
    if os.path.exists(SIMULATED_DB_PATH):
        try:
            with open(SIMULATED_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
    data.append(record)
    with open(SIMULATED_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------- Fallback question templates ----------
FALLBACK_TEMPLATES = {
    "python": [
        "Explain the difference between list and tuple in Python.",
        "How does Python’s garbage collection work?",
        "Write a simple function to remove duplicates from a list.",
        "Explain how to profile and optimize Python code."
    ],
    "django": [
        "Explain Django’s request/response lifecycle.",
        "How do you define a many-to-many relationship in Django models?",
        "What are signals and when would you use them?",
        "How do you handle performance in Django ORM?"
    ],
    "react": [
        "How does the virtual DOM in React improve performance?",
        "What’s the difference between state and props?",
        "Explain useEffect and useMemo hooks.",
        "How do you optimize large React applications?"
    ],
    "sql": [
        "What’s the difference between clustered and non-clustered indexes?",
        "How would you remove duplicates from a SQL table?",
        "Explain transactions and isolation levels.",
        "How do you use EXPLAIN ANALYZE to optimize queries?"
    ],
    "aws": [
        "What’s the difference between EC2, Lambda, and Fargate?",
        "Explain IAM and how to enforce least privilege.",
        "How do you design a fault-tolerant system on AWS?"
    ]
}

def fallback_generate_for_tech(tech: str, n: int = 4) -> List[str]:
    for key, qs in FALLBACK_TEMPLATES.items():
        if key in tech.lower():
            return qs[:n]
    generic = [
        f"What are the main components of {tech}?",
        f"How do you handle performance optimization in {tech}?",
        f"What’s a common pitfall when using {tech}?",
        f"Describe how you’d debug an issue in a {tech} project."
    ]
    return generic[:n]

def deterministic_generate_questions(tech_list: List[str], n_per_tech=4) -> Dict[str, List[str]]:
    return {tech: fallback_generate_for_tech(tech, n_per_tech) for tech in tech_list}

# ---------- Gemini question generator ----------
def gemini_generate_questions(tech_list: List[str], position: str, years: str, notes: str, n_per_tech=4) -> Dict[str, List[str]]:
    api_key = ""
    if not GEMINI_AVAILABLE:
        raise RuntimeError("Gemini library not installed.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro-latest")

    prompt = f"""
    You are TalentScout's hiring assistant.
    Candidate details:
    - Desired Position: {position}
    - Experience: {years} years
    - Notes: {notes}
    Candidate tech stack: {', '.join(tech_list)}

    Generate {n_per_tech} technical interview questions per technology, tailored to the desired position.
    Keep each question short and clear. Return output as JSON like:
    {{
        "tech_questions": {{
            "Python": ["Question1", "Question2", ...],
            "React": [...]
        }}
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        start, end = text.find("{"), text.rfind("}")
        data = json.loads(text[start:end + 1])
        return data.get("tech_questions", {})
    except Exception as e:
        raise RuntimeError(f"Gemini generation failed: {e}")

# ---------- Follow-up handler ----------
def handle_followup(text: str) -> str:
    text_l = text.lower()
    if "regenerate" in text_l:
        techs = split_tech_stack(st.session_state.candidate_info.get("tech_stack_raw", ""))
        questions = deterministic_generate_questions(techs)
        st.session_state.last_questions = questions
        lines = ["Here are new questions:"]
        for t, qs in questions.items():
            lines.append(f"{t}:")
            for i, q in enumerate(qs, 1):
                lines.append(f"  {i}. {q}")
        return "\n".join(lines)
    if "show my info" in text_l:
        info = st.session_state.candidate_info
        masked = info.copy()
        masked["email"] = "***"
        masked["phone"] = "***"
        return json.dumps(masked, indent=2)
    if any(k in text_l for k in END_KEYWORDS):
        return "Thanks for chatting. We'll be in touch soon!"
    return "I can regenerate questions, show your info, or end the chat. Try 'regenerate' or 'exit'."

# ---------- Streamlit UI ----------
st.set_page_config(page_title="TalentScout Hiring Assistant (Gemini)", layout="centered")

st.title("TalentScout — Hiring Assistant")
st.write("I'll gather your details and generate technical screening questions. Type 'exit' to end.")

if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = {}

with st.form("candidate_form"):
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    phone = st.text_input("Phone Number")
    years = st.text_input("Years of Experience")
    position = st.text_input("Desired Position(s)")
    location = st.text_input("Current Location")
    tech_stack_raw = st.text_input("Tech Stack (comma separated)")
    use_gemini = st.checkbox("Use Gemini API for question generation", value=True)
    submitted = st.form_submit_button("Submit and Generate Questions")

if submitted:
    info = {
        "name": name, "email": email, "phone": phone, "years": years,
        "position": position, "location": location,
        "tech_stack_raw": tech_stack_raw, "notes": notes if 'notes' in locals() else ""
    }
    st.session_state.candidate_info = info
    techs = split_tech_stack(tech_stack_raw)

    st.success(f"Candidate saved. Detected tech stack: {', '.join(techs)}")

    try:
        if use_gemini:
            st.info("Generating questions using Gemini...")
            questions = gemini_generate_questions(techs, position, years, info["notes"])
        else:
            questions = deterministic_generate_questions(techs)
    except Exception as e:
        st.error(str(e))
        questions = deterministic_generate_questions(techs)

    st.session_state.last_questions = questions
    save_simulated(info)

    st.markdown("### Generated Questions")
    for tech, qs in questions.items():
        st.markdown(f"**{tech}**")
        for i, q in enumerate(qs, 1):
            st.write(f"{i}. {q}")

# ---------- Chat area ----------
st.markdown("---")
st.subheader("Chat with Assistant")

with st.form("chat_form"):
    user_input = st.text_input("You:", key="chat_input")
    submitted_chat = st.form_submit_button("Send")

if submitted_chat:
    if not user_input.strip():
        st.warning("Type something first.")
    else:
        response = handle_followup(user_input)
        st.session_state.conversation.append(("You", user_input))
        st.session_state.conversation.append(("Assistant", response))

# ---------- Show chat ----------
st.markdown("---")
for sender, msg in st.session_state.conversation[-10:]:
    st.markdown(f"**{sender}:** {msg}")

st.markdown("---")
st.caption("Note: This demo anonymizes stored data and is not for real candidate information.")