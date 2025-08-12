import streamlit as st
import os
from gtts import gTTS
import tempfile
import base64
from together import Together

# ---- Together API ----
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
client = Together(api_key=TOGETHER_API_KEY)

# ---- System Prompt ----
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
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
}

# ---- API Call ----
def call_model(messages):
    response = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        messages=messages,
        max_tokens=200  # Limit length for concise responses
    )
    return response.choices[0].message.content

# ---- Streamlit UI ----
st.set_page_config(page_title="True-Buddy", page_icon="💬")

# Title + description
st.markdown(
    """
    <h1 style="text-align:center; color:#FFFFFF; font-family:Segoe UI;">
        💬 True-Buddy
    </h1>
    <p style="text-align:center; font-size:16px; color:gray; margin-top:-10px; font-family:Segoe UI;">
        An emotional support friend chatbot that listens, cares, and uplifts your spirit.
    </p>
    """,
    unsafe_allow_html=True
)

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

user_input = st.chat_input("Buddy, How are you feeling today?")

if user_input:
    # Add user message
    st.session_state["chat_history"].append({"role": "user", "content": user_input})

    # Keep only last few turns
    trimmed_history = st.session_state["chat_history"][-2:]

    # Show "thinking" loader while model generates reply
    with st.spinner("🤖 Your True-Buddy is thinking..."):
        messages_for_api = [SYSTEM_PROMPT] + trimmed_history
        bot_reply = call_model(messages_for_api)

    # Store bot reply
    st.session_state["chat_history"].append({"role": "assistant", "content": bot_reply})

    # Convert reply to speech
    tts = gTTS(bot_reply)
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_audio_file.name)

    # Store audio for autoplay
    with open(temp_audio_file.name, "rb") as f:
        audio_base64 = base64.b64encode(f.read()).decode()
    st.session_state["last_audio_base64"] = audio_base64

# ---- Display Chat ----
for message in st.session_state["chat_history"]:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(message["content"])

# ---- Autoplay Latest Audio (no buttons) ----
if "last_audio_base64" in st.session_state:
    # Initialize mute state in session_state
    if "muted" not in st.session_state:
        st.session_state["muted"] = False

    # Button to toggle mute/unmute
    if st.button("Mute" if not st.session_state["muted"] else "Unmute"):
        st.session_state["muted"] = not st.session_state["muted"]

    # Render audio with muted attribute based on state
    muted_attr = "muted" if st.session_state["muted"] else ""
    audio_html = f"""
    <audio autoplay {muted_attr} controls>
        <source src="data:audio/mp3;base64,{st.session_state['last_audio_base64']}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
