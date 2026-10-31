"""
AI Learning Roadmap Generator
-----------------------------
A beginner-friendly Streamlit app that uses Google Gemini (Google AI Studio)
to create a personalized learning roadmap for any field.
"""

import os
import re
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import errors as genai_errors

# ----------------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Learning Roadmap Generator",
    page_icon="🧭",
    layout="wide",
)

# Gemini model names change over time. The app tries them in this order and
# automatically moves to the next one if a model is not found (404) or overloaded.
# gemini-2.5-* models are no longer available to new API keys.
DEFAULT_MODEL = "gemini-3.8-flash"
FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
]

CUSTOM_CSS = """
<style>
.hero {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #06b6d4 100%);
    padding: 2rem 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 1.5rem;
}
.hero h1 { color: white; margin: 0; font-size: 2.2rem; }
.hero p  { color: #e0e7ff; margin: 0.4rem 0 0 0; font-size: 1.05rem; }
.info-card {
    background: rgba(124, 58, 237, 0.08);
    border-left: 5px solid #7c3aed;
    padding: 0.8rem 1.1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
}
div.stButton > button:first-child {
    background: linear-gradient(90deg, #4f46e5, #7c3aed);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
}
div.stButton > button:first-child:hover { opacity: 0.9; color: white; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------
def get_api_key():
    """Read the API key from Streamlit secrets (preferred) or an env variable."""
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key:
            return str(key).strip()
    except (KeyError, FileNotFoundError):
        pass  # No secrets file or key missing: try the environment next.
    return os.environ.get("GEMINI_API_KEY", "").strip() or None


def get_model_name():
    """Allow changing the model from secrets without editing the code."""
    try:
        return str(st.secrets.get("GEMINI_MODEL", DEFAULT_MODEL))
    except Exception:
        return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)


def validate_inputs(field, goal, hours):
    """Return a list of problems with the user's input (empty list = valid)."""
    problems = []
    field = field.strip()
    goal = goal.strip()

    if not field:
        problems.append("Please enter a learning field.")
    elif len(field) < 2 or len(field) > 100:
        problems.append("Learning field must be between 2 and 100 characters.")
    elif not re.search(r"[A-Za-z]", field):
        problems.append("Learning field should contain some letters (e.g. 'Data Science').")

    if not goal:
        problems.append("Please describe your learning goal.")
    elif len(goal) < 10:
        problems.append("Please describe your goal in at least 10 characters.")
    elif len(goal) > 1000:
        problems.append("Learning goal is too long (maximum 1000 characters).")

    if hours <= 0:
        problems.append("Daily study time must be greater than 0.")

    return problems


def build_prompt(field, level, duration, hours, goal):
    """Create the instructions we send to Gemini."""
    return f"""
You are an expert career coach and curriculum designer.
Create a detailed, personalized learning roadmap using the information below.

- Learning field: {field}
- Current skill level: {level}
- Total duration: {duration}
- Daily study time: {hours} hours per day
- Learning goal: {goal}

Rules:
- The roadmap MUST fit the skill level ({level}) and the duration ({duration}).
- The schedule must be realistic for {hours} hours of study per day.
- Use Markdown. Start each main section with a level-2 heading (## ).
- Use EXACTLY these 11 sections, in this order:

## 1. Introduction to {field}
## 2. Required Skills and Prerequisites
## 3. Step-by-Step Learning Plan
(Split into clear stages, e.g. "### Stage 1: ...", with goals for each stage.)
## 4. Weekly / Monthly Schedule
(Use a Markdown table or a clear list that covers the whole {duration}.)
## 5. Important Topics to Study
## 6. Recommended Tools and Technologies
## 7. Practical Projects for Practice
## 8. Free Learning Resources
## 9. Recommended YouTube Channels and Documentation
## 10. Final Project Ideas
## 11. Career Opportunities

- Only recommend real, well-known resources, and do not invent links.
- Keep the language simple, motivating, and well organized.
"""


def friendly_api_error(e, model_name):
    """Turn a Gemini API error into a clear message for the user."""
    code = getattr(e, "code", None)
    if code in (400, 401, 403):
        return (
            f"Gemini rejected the request (error {code}). Your API key may be "
            "invalid, restricted, or missing access. Create a new key in Google AI Studio."
        )
    if code == 429:
        return "Rate limit or free quota reached. Please wait a minute and try again."
    return f"Gemini API error ({code}): {getattr(e, 'message', str(e))}"


def generate_roadmap(api_key, primary_model, prompt):
    """
    Call Gemini and return (text, error_message, model_used).
    If a model is not found or is overloaded, the next model in the list is tried.
    """
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return None, f"Could not create the Gemini client: {e}", None

    models_to_try = [primary_model] + [m for m in FALLBACK_MODELS if m != primary_model]
    last_error = "No model could be used."

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            text = (response.text or "").strip()
            if not text:
                return None, (
                    "Gemini returned an empty response. This can happen when the "
                    "request is blocked by safety filters. Try rephrasing your field or goal."
                ), model_name
            return text, None, model_name

        except genai_errors.ClientError as e:
            if getattr(e, "code", None) == 404:
                last_error = f"Model '{model_name}' is not available for your key."
                continue  # Try the next model.
            return None, friendly_api_error(e, model_name), model_name

        except genai_errors.ServerError as e:
            last_error = (
                f"Gemini servers are busy right now ({getattr(e, 'code', '')}). "
                "Please try again in a few moments."
            )
            continue  # Try the next model.

        except genai_errors.APIError as e:
            return None, friendly_api_error(e, model_name), model_name

        except Exception as e:  # Connection problems and anything unexpected.
            message = str(e)
            if any(w in message.lower() for w in ("connect", "timeout", "timed out", "network", "dns")):
                return None, f"Could not connect to the Gemini API. Check your internet connection. ({message})", model_name
            return None, f"Unexpected error: {message}", model_name

    return None, (
        f"{last_error} Tried: {', '.join(models_to_try)}. "
        "Open the sidebar and click 'Check API key and models' to see which models your key can use, "
        "then set GEMINI_MODEL in your secrets."
    ), None


def list_available_models(api_key):
    """Return (names, error). Used by the sidebar 'Check API key' button."""
    try:
        client = genai.Client(api_key=api_key)
        names = []
        for m in client.models.list():
            name = (getattr(m, "name", "") or "").replace("models/", "")
            actions = getattr(m, "supported_actions", None) or []
            if name.startswith("gemini") and ("generateContent" in actions or not actions):
                names.append(name)
        return sorted(set(names)), None
    except genai_errors.APIError as e:
        return None, friendly_api_error(e, "")
    except Exception as e:
        return None, f"Could not reach Gemini: {e}"


def split_sections(markdown_text):
    """Split the roadmap into (intro_text, [(title, body), ...]) using '## ' headings."""
    parts = re.split(r"^##\s+(?!#)", markdown_text, flags=re.MULTILINE)
    intro = parts[0].strip()
    sections = []
    for part in parts[1:]:
        lines = part.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections.append((title, body))
    return intro, sections


def build_download_text(info, roadmap):
    """Create the text file that users can download."""
    header = (
        "AI LEARNING ROADMAP\n"
        "===================\n"
        f"Field:    {info['field']}\n"
        f"Level:    {info['level']}\n"
        f"Duration: {info['duration']}\n"
        f"Daily:    {info['hours']} hours/day\n"
        f"Goal:     {info['goal']}\n"
        f"Created:  {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        "===================\n\n"
    )
    return header + roadmap


# ----------------------------------------------------------------------------
# Sidebar navigation
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧭 Roadmap AI")
    st.caption("Your personal learning planner")
    page = st.radio("Navigation", ["🚀 Generate Roadmap", "ℹ️ About"], label_visibility="collapsed")
    st.divider()
    if st.button("🔍 Check API key and models"):
        _key = get_api_key()
        if not _key:
            st.error("No API key found.")
        else:
            with st.spinner("Checking..."):
                _names, _err = list_available_models(_key)
            if _err:
                st.error(_err)
            elif not _names:
                st.warning("Key works, but no Gemini models were listed.")
            else:
                st.success(f"Key works. {len(_names)} models available.")
                st.code("\n".join(_names))
    st.caption("Powered by Google Gemini and Streamlit")


# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown(
    """
<div class="hero">
    <h1>🧭 AI Learning Roadmap Generator</h1>
    <p>Get a personalized, step-by-step learning plan for any field or skill.</p>
</div>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# About page
# ----------------------------------------------------------------------------
if page == "ℹ️ About":
    st.subheader("About this app")
    st.write(
        "This app uses Google Gemini to build a learning roadmap that matches your "
        "field, skill level, available time, and goals."
    )
    st.markdown(
        """
**How to use it**
1. Open **Generate Roadmap** in the sidebar.
2. Fill in your field, level, duration, daily study time, and goal.
3. Click **Generate Roadmap** and wait a few seconds.
4. Explore each stage and download your roadmap.

**Tip:** The more specific your goal, the better your roadmap will be.
"""
    )
    st.stop()


# ----------------------------------------------------------------------------
# Main page: input form
# ----------------------------------------------------------------------------
api_key = get_api_key()
if not api_key:
    st.error(
        "🔑 **Gemini API key not found.**\n\n"
        "Add `GEMINI_API_KEY` to `.streamlit/secrets.toml` (local) or to the app "
        "**Secrets** settings (Streamlit Cloud). See the README for step-by-step instructions."
    )

st.markdown(
    '<div class="info-card">Fill in the details below and click <b>Generate Roadmap</b>.</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    field = st.text_input(
        "📚 Learning Field",
        placeholder="e.g. Data Science, Web Development, Cybersecurity",
    )
    level = st.selectbox("🎯 Skill Level", ["Beginner", "Intermediate", "Advanced"])
with col2:
    duration = st.selectbox("⏳ Learning Duration", ["1 Month", "3 Months", "6 Months", "1 Year"])
    hours = st.slider("🕒 Daily Study Time (hours)", min_value=0.5, max_value=12.0, value=2.0, step=0.5)

goal = st.text_area(
    "🏆 Learning Goal",
    placeholder="e.g. I want to become a junior data analyst and get my first job.",
    height=120,
)

generate = st.button("✨ Generate Roadmap", use_container_width=True)


# ----------------------------------------------------------------------------
# Generate the roadmap
# ----------------------------------------------------------------------------
if generate:
    problems = validate_inputs(field, goal, hours)

    if not api_key:
        st.error("Cannot generate a roadmap without an API key.")
    elif problems:
        for p in problems:
            st.warning(p)
    else:
        prompt = build_prompt(field.strip(), level, duration, hours, goal.strip())
        with st.spinner("🤖 Gemini is building your personalized roadmap..."):
            roadmap, error, model_used = generate_roadmap(api_key, get_model_name(), prompt)

        if error:
            st.error(error)
        else:
            # Save in session_state so the roadmap stays after clicking Download.
            st.session_state["roadmap"] = roadmap
            st.session_state["info"] = {
                "field": field.strip(),
                "level": level,
                "duration": duration,
                "hours": hours,
                "goal": goal.strip(),
            }
            st.session_state["model_used"] = model_used


# ----------------------------------------------------------------------------
# Show the roadmap
# ----------------------------------------------------------------------------
if "roadmap" in st.session_state:
    roadmap = st.session_state["roadmap"]
    info = st.session_state["info"]

    st.divider()
    st.subheader(f"📍 Your Roadmap: {info['field']}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Level", info["level"])
    m2.metric("Duration", info["duration"])
    m3.metric("Daily Study", f"{info['hours']} h")

    st.caption(f"Generated with {st.session_state.get('model_used', 'Gemini')}")

    intro, sections = split_sections(roadmap)
    if intro:
        st.markdown(intro)

    if sections:
        for i, (title, body) in enumerate(sections):
            with st.expander(title, expanded=(i == 0)):
                st.markdown(body)
    else:
        # If the AI ignored our format, still show everything.
        st.markdown(roadmap)

    st.divider()
    d1, d2 = st.columns(2)
    safe_name = re.sub(r"[^A-Za-z0-9]+", "_", info["field"]).strip("_") or "roadmap"
    with d1:
        st.download_button(
            "⬇️ Download as TXT",
            data=build_download_text(info, roadmap),
            file_name=f"{safe_name}_roadmap.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "⬇️ Download as Markdown",
            data=build_download_text(info, roadmap),
            file_name=f"{safe_name}_roadmap.md",
            mime="text/markdown",
            use_container_width=True,
        )
