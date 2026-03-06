import streamlit as st
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Interview Pro", page_icon="🤖")

# --- API SETUP ---
# In production, use st.secrets["GEMINI_API_KEY"]
# For local testing, replace 'YOUR_API_KEY' with your actual key
API_KEY = "YOUR_API_KEY"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- SESSION STATE INITIALIZATION ---
if "step" not in st.session_state:
    st.session_state.step = "input"  # Steps: input, selection, interview
if "topics" not in st.session_state:
    st.session_state.topics = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- APP UI ---
st.title("🤖 Smart Interview Prep Bot")
st.markdown("Prepare for your dream job with AI-driven mock interviews.")

# --- STEP 1: JOB INPUT ---
if st.session_state.step == "input":
    with st.form("job_details"):
        company = st.text_input("Company Name", placeholder="e.g. Google, local startup, etc.")
        jd = st.text_area("Job Description", placeholder="Paste the JD here...", height=200)
        submitted = st.form_submit_button("Generate Interview Plan")

        if submitted and jd:
            with st.spinner("Analyzing role and generating topics..."):
                prompt = f"Based on this JD for {company}: '{jd}', list 5 distinct interview topic categories (e.g. Technical, Behavioral, Problem Solving). Return ONLY the list separated by commas."
                response = model.generate_content(prompt)
                st.session_state.topics = [t.strip() for t in response.text.split(",")]
                st.session_state.company = company
                st.session_state.step = "selection"
                st.rerun()

# --- STEP 2: TOPIC SELECTION ---
elif st.session_state.step == "selection":
    st.success(f"Analysis complete for **{st.session_state.company}**!")
    st.subheader("Select a topic to start practicing:")
    
    for topic in st.session_state.topics:
        if st.button(f"Practice {topic}"):
            st.session_state.current_topic = topic
            st.session_state.step = "interview"
            st.rerun()
    
    if st.button("← Back"):
        st.session_state.step = "input"
        st.rerun()

# --- STEP 3: INTERVIEW INTERFACE ---
elif st.session_state.step == "interview":
    st.info(f"Currently practicing: **{st.session_state.current_topic}**")
    
    # Display Chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Initial Question Generation
    if len(st.session_state.chat_history) == 0:
        initial_prompt = f"You are a recruiter at {st.session_state.company}. Ask one challenging interview question regarding {st.session_state.current_topic}."
        bot_q = model.generate_content(initial_prompt).text
        st.session_state.chat_history.append({"role": "assistant", "content": bot_q})
        st.rerun()

    # User Answer Input
    if user_input := st.chat_input("Type your answer here..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner("Evaluating..."):
            eval_prompt = f"""
            The user is interviewing for {st.session_state.company}. 
            Topic: {st.session_state.current_topic}.
            Question: {st.session_state.chat_history[-2]['content']}
            User Answer: {user_input}
            
            Provide brief feedback, then ask the NEXT relevant interview question.
            """
            bot_response = model.generate_content(eval_prompt).text
            st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
            st.rerun()

    if st.button("Exit Interview"):
        st.session_state.step = "selection"
        st.session_state.chat_history = []
        st.rerun()
