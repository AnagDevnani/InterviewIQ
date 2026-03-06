# InterPrep: Smart Interview Preperation Bot
## Possible Topic Options
> selected topic: AI/GenAI

1. Resume Analyzer using GenAI
2. Chatbot for College FAQ
3. AI Code Review Assistant
4. Fake News Detection
5. AI-based Email Summarizer
6. Smart Interview Preperation Bot
7. AI Bug Detection Tool
8. AI Meeting Notes Generator

## Tech Stack
- Python
- OpenAI / HuggingFace
- LangChain
- Streamlit

## Work Flow:
. Setup & API Keys

    Get a Gemini API Key: Go to Google AI Studio. Generate a free API key for the "Gemini 3 Flash" model.

    GitHub Repository: Create a new public repository on GitHub (e.g., interview-bot).

2. The Logic Design (The "Prompting" Strategy)

To make your bot "smart," you will use two distinct prompt phases:

    Phase 1 (Topic Generation): Send the Job Description (JD) and Company name to the AI. Ask it to return a list of 5–7 key interview categories (e.g., System Design, Behavioral, React Fundamentals).

    Phase 2 (Questioning): Once a user selects a topic, the AI generates a specific question. After the user answers, the AI provides feedback and moves to the next question.

3. Coding the Application

Create a file named app.py. Your code structure should look like this:
Python

import streamlit as st
import google.generativeai as genai

# Configuration
# in your Python code, read from env or secrets
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # ensure dotenv has been loaded earlier.  Alternatively use st.secrets in Streamlit.
model = genai.GenerativeModel('gemini-3-flash-preview')

st.title("🤖 Smart Interview Prep Bot")

# Step 1: Input Section
with st.container():
    jd = st.text_area("Paste the Job Description:")
    company = st.text_input("Target Company Name:")
    
    if st.button("Analyze Role"):
        # AI logic to generate topics based on jd and company
        prompt = f"Based on this JD: {jd} at {company}, list 5 interview topics."
        response = model.generate_content(prompt)
        st.session_state.topics = response.text
        st.write("### Recommended Topics:")
        st.write(st.session_state.topics)

# Step 2: Interview Loop
if 'topics' in st.session_state:
    selected_topic = st.selectbox("Choose a topic to practice:", ["Technical", "Behavioral", "Culture Fit"])
    if st.button("Start Interview"):
        # AI logic to ask a question
        q_prompt = f"Ask a difficult interview question for {selected_topic}."
        question = model.generate_content(q_prompt)
        st.subheader(question.text)
        user_answer = st.text_input("Your Answer:")

4. Deployment

    requirements.txt: Create this file in your repo and add:
    Plaintext

    streamlit
    google-generativeai

    Connect to Streamlit Cloud:

        Go to share.streamlit.io.

        Connect your GitHub account and select your interview-bot repo.

        Crucial: Add your API Key in the "Advanced Settings" → "Secrets" section of Streamlit so it isn't hardcoded in your public GitHub files.

💡 Pro-Tips for the "Smart" Aspect

    Memory: Use st.session_state to store the chat history so the bot remembers what questions it already asked.

    Scoring: Ask the AI to provide a "Confidence Score" (1–10) after every user answer to help the user track progress.

    STAR Method: Instruct the AI to specifically look for "Situation, Task, Action, Result" in behavioral answers and point out if one is missing.



-------------------------------------------------------------------------------------------------------------------------------------


# 🎯 InterviewIQ — AI Mock Interview Coach

An AI-powered mock interview bot built with Streamlit + Gemini API.

## Quick Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

Add your Gemini API key to `.streamlit/secrets.toml` or paste it in the sidebar.

## Project Structure
```
interview-bot/
├── app.py                  # Main app — all 5 steps
├── config.py               # Constants + all prompt templates  
├── requirements.txt
├── .streamlit/secrets.toml # API key (gitignored)
└── modules/
    ├── parser.py           # PDF + DOCX parsing
    ├── gemini_client.py    # Gemini API wrapper
    ├── session.py          # Session state helpers
    └── charts.py           # Plotly dashboard charts
```

## Features
- Resume-aware dynamic question generation
- Difficulty: Easy / Medium / Hard / Auto (AI-calibrated)
- Personas: Friendly HR / Tough Technical / Stress Interview
- STAR method detector for behavioural questions
- Hint + Skip with score penalties
- Answer timer tracking
- Full radar chart + score/confidence dashboard