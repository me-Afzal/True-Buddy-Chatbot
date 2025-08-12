import streamlit as st
import os
from gtts import gTTS
import tempfile
import base64
import requests

# ---- Gemini API config ----
API_KEY = st.secrets["GOOGLE_API_KEY"]  
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY,
}

# ---- System Prompt (same as before) ----
SYSTEM_PROMPT = (
    "You are TrueBuddy — an empathetic, supportive best friend who listens without judgment and speaks "
    "with kindness, warmth, and encouragement. Your goal is to make the user (whom you lovingly call 'buddy') "
    "feel safe, valued, and understood in every conversation.\n\n"
    "Write all responses as a single short paragraph of about five sentences.\n"
    "Always include at least one motivational quote and one or two uplifting movie names in your reply.\n\n"
    "1️⃣ If the user feels sad, heartbroken, discouraged, lonely, or hopeless:\n"
    "- Comfort them with gentle, caring words.\n"
    "- Acknowledge their pain and remind them of their inner strength.\n"
    "- Share at least one motivational quote.\n"
    "- Suggest 1–2 uplifting or motivational movies in a friendly, conversational way.\n\n"
    "2️⃣ If the user expresses suicidal thoughts or wanting to harm themselves:\n"
    "- Respond with deep compassion, urgency, and empathy.\n"
    "- Reassure them: 'I’m here with you, buddy. Even if no one else stands with you, I do.'\n"
    "- Encourage them to focus on reasons to live and their value in the world.\n"
    "- Include at least one powerful quote about life and hope.\n"
    "- Suggest 1–2 uplifting movies.\n"
    "- Avoid medical advice, but encourage contacting a trusted friend, family member, "
    "or a suicide prevention helpline.\n\n"
    "3️⃣ If the user is happy or excited:\n"
    "- Celebrate their joy genuinely.\n"
    "- Say 'I’m proud of your happiness, buddy' in a heartfelt, natural way.\n"
    "- Keep it warm, friendly, and still follow the five-sentence limit.\n\n"
    "Always use a conversational, best-friend style, keep referring to the user as 'buddy' in a loving way, "
    "and make them feel emotionally safe, valued, and understood."
)

# ---- New API call function for Gemini ----
def call_model(messages):
    # Build prompt text by combining system prompt + last messages into one text string
    prompt_text = SYSTEM_PROMPT + "\n\n"
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        prefix = "User:" if role == "user" else "Assistant:"
        prompt_text += f"{prefix} {content}\n"
    
    # Build Gemini API payload with combined prompt text
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt_text
                    }
                ]
            }
        ]
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    
    # Extract generated assistant text
    try:
        assistant_reply = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        assistant_reply = "Sorry, I can't help you right now. Something is wrong with my Backend"
    return assistant_reply

# ---- Streamlit UI ----
st.set_page_config(page_title="True-Buddy", page_icon="💬")

st.markdown(
    """
    <h1 style="text-align:center; color:#FFFFFF; font-family:Segoe UI;">
        💬 True-Buddy
    </h1>
    <p style="text-align:center; font-size:16px; color:gray; margin-top:-10px; font-family:Segoe UI;">
        An emotional support friend chatbot that listens, cares, and uplifts your spirit.
    </p>
    """,
    unsafe_allow_html=True,
)

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

user_input = st.chat_input("Buddy, How are you feeling today?")

if user_input:
    st.session_state["chat_history"].append({"role": "user", "content": user_input})

    # Limit chat history to last 4 messages for context
    trimmed_history = st.session_state["chat_history"][-2:]

    with st.spinner("🤖 Your True-Buddy is thinking..."):
        bot_reply = call_model(trimmed_history)

    st.session_state["chat_history"].append({"role": "assistant", "content": bot_reply})

    # Convert reply to speech
    tts = gTTS(bot_reply)
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_audio_file.name)

    with open(temp_audio_file.name, "rb") as f:
        audio_base64 = base64.b64encode(f.read()).decode()
    st.session_state["last_audio_base64"] = audio_base64

# Display chat messages
for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Audio playback with mute/unmute button
if "last_audio_base64" in st.session_state:
    if "muted" not in st.session_state:
        st.session_state["muted"] = False

    if st.button("Mute" if not st.session_state["muted"] else "Unmute"):
        st.session_state["muted"] = not st.session_state["muted"]

    muted_attr = "muted" if st.session_state["muted"] else ""
    audio_html = f"""
    <audio autoplay {muted_attr} controls>
        <source src="data:audio/mp3;base64,{st.session_state['last_audio_base64']}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
