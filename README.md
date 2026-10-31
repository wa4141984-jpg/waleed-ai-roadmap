# 🧭 AI Learning Roadmap Generator

A beginner-friendly web app that creates a **personalized learning roadmap** for any field or skill using Google Gemini AI.

## ✨ Features

- Enter any learning field (Data Science, Python, Cybersecurity, ...)
- Choose skill level, duration (1 month to 1 year), and daily study hours
- Describe your own learning goal
- AI-generated roadmap with 11 sections: introduction, prerequisites, step-by-step plan, schedule, topics, tools, projects, free resources, YouTube channels, final projects, and careers
- Expandable sections, sidebar navigation, loading spinner
- Download your roadmap as TXT or Markdown
- Error handling for missing API key, bad input, connection problems, API errors, and empty responses
- Automatic fallback to another Gemini model if one is unavailable
- Sidebar button to check your API key and list the models it can use

## 🛠 Technologies Used

- Python 3.10+
- Streamlit (user interface)
- Google Gemini API via Google AI Studio (`google-genai` SDK)
- GitHub (code storage)
- Streamlit Community Cloud (deployment)

## 📁 Project Structure

```
your-project/
├── app.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── secrets.toml     <- you create this (NEVER upload it to GitHub)
```

## 🔑 Step 1: Get a Google AI Studio API Key

1. Go to https://aistudio.google.com/
2. Sign in with your Google account.
3. Click **Get API key** then **Create API key**.
4. Copy the key and keep it private.

## 💻 Step 2: Run Locally

```bash
# 1. Create a folder and put the 3 files inside it
cd your-project

# 2. (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install libraries
pip install -r requirements.txt
```

Create the file `.streamlit/secrets.toml` (make the `.streamlit` folder first):

```toml
GEMINI_API_KEY = "paste-your-key-here"
```

Run the app:

```bash
streamlit run app.py
```

It opens at http://localhost:8501.

### Optional: Run in Google Colab

```python
!pip install -q streamlit google-genai
# Upload app.py to Colab, then:
import os
os.environ["GEMINI_API_KEY"] = "paste-your-key-here"   # do not share this notebook with the key inside!
!npm install -q localtunnel
!streamlit run app.py &>/content/logs.txt &
!curl https://loca.lt/mytunnelpassword      # this prints the tunnel password
!npx localtunnel --port 8501
```

Open the link that is printed and enter the tunnel password shown above.

## 🐙 Step 3: Upload to GitHub

1. Create a free account at https://github.com
2. Click **New repository**, name it `ai-roadmap-generator`, and keep it **Public** (required for the free Streamlit plan unless you connect a private repo).
3. Create a file called `.gitignore` with this content so your key is never uploaded:

   ```
   .streamlit/secrets.toml
   venv/
   __pycache__/
   ```
4. Upload with Git:

   ```bash
   git init
   git add app.py requirements.txt README.md .gitignore
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/ai-roadmap-generator.git
   git push -u origin main
   ```

   (Or use **Add file → Upload files** on the GitHub website, but never upload `secrets.toml`.)

## 🚀 Step 4: Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **Create app** and choose your repository, branch `main`, and main file `app.py`.
3. Click **Advanced settings** and paste this in **Secrets**:

   ```toml
   GEMINI_API_KEY = "paste-your-key-here"
   ```
4. Click **Deploy**. After a minute, your app has a public link.

To change the secret later: app menu → **Settings → Secrets**.

## ⚙️ Gemini Model Names (Important)

Google retires models regularly. `gemini-2.5-flash` and the other 2.5 models are now limited to accounts that already used them, so new API keys get a **404 "model not found"** error.

This app uses **`gemini-3.8-flash`** by default and automatically falls back to `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, and `gemini-flash-latest` if one is not available for your key.

To choose a model yourself, add this to your secrets (no code change needed):

```toml
GEMINI_MODEL = "gemini-3.8-flash"
```

Not sure which models your key can use? Run the app and click **🔍 Check API key and models** in the sidebar. It lists the models available to your key. You can also see the official list at https://ai.google.dev/gemini-api/docs/models

## 🧯 Troubleshooting

| Problem | Fix |
|---|---|
| "API key not found" | Check the secret is named exactly `GEMINI_API_KEY` |
| Error 400/403 | Key is invalid or restricted, create a new one |
| Error 404 / "model not found" | Click **Check API key and models** in the sidebar, then set `GEMINI_MODEL` to one it lists. Also run `pip install -U google-genai` |
| Error 429 | Free quota reached, wait and retry |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Old SDK problems | Run `pip install -U streamlit google-genai` |

## 🔒 Security

Never write your API key inside `app.py` or commit `secrets.toml`. If a key leaks, delete it in Google AI Studio and create a new one.

## 📄 License

Free to use for learning purposes.
