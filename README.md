# InterviewIQ

An AI-powered interview coach built with **Python**, **Streamlit**, and **Gemini 3 Flash**. This bot analyzes specific Job Descriptions (JDs) and company contexts to provide tailored mock interview sessions with real-time feedback.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75C2?style=for-the-badge&logo=google-gemini&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

---

## Features

- Resume-aware dynamic question generation
- Difficulty: Easy / Medium / Hard / Auto (AI-calibrated)
- Personas: Friendly HR / Tough Technical / Stress Interview
- STAR method detector for behavioural questions
- Hint + Skip with score penalties
- Answer timer tracking
- Full radar chart + score/confidence dashboard


## Installation & Local Setup

To run this project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/smart-interview-bot.git](https://github.com/your-username/smart-interview-bot.git)
   cd smart-interview-bot
2. Install dependencies:
   ```bash
    pip install -r requirements.txt
   ```
3. Set up your API Key:
    - Get a free API key from Google AI Studio.
    - Create a .env file or replace the API_KEY variable in app.py.

4. Run the application:
    ```bash
    streamlit run app.py
    ```

## Deployment

This app is optimized for Streamlit Community Cloud.

1. Push your code to GitHub.
2. Connect your repository to Streamlit Cloud.
3. Add your GEMINI_API_KEY in the Advanced Settings > Secrets section of the Streamlit dashboard:
   ```Ini, TOML
    GEMINI_API_KEY = "your_api_key_here"
   ```

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


## License

Distributed under the MIT License. See `LICENSE` for more information.

Disclaimer: This bot is an AI assistant. While it provides realistic interview practice, users should always research company-specific interview processes via official channels.
