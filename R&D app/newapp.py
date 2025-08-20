import streamlit as st
import os
from gtts import gTTS
import tempfile
import base64
import requests
import speech_recognition as sr
import pyaudio
import wave
import threading
import time

# ---- Gemini API config ----
API_KEY = st.secrets["API_KEY"]  
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY,
}

# ---- System Prompt ----
SYSTEM_PROMPT = (
    "You are TrueBuddy — an empathetic, supportive best friend who speaks with kindness, warmth, and encouragement. "
    "Refer to the user as 'buddy' in a loving way and make them feel safe, valued, and understood. "
    "Always respond in a short paragraph of about three or five sentences.\n\n"
    
    "1️⃣ Greetings (hi, hello, good morning, etc.): Respond with a friendly greeting and ask how their day is going. "
    "Do not include motivational quotes or movie suggestions.\n\n"
    
    "2️⃣ Sad, heartbroken, discouraged, lonely, or hopeless: Comfort them, acknowledge their strength, "
    "include at least one motivational quote, and suggest 1–2 uplifting movies.\n\n"
    
    "3️⃣ Suicidal thoughts: Respond with deep compassion, reassure them, include a powerful quote about life, "
    "suggest 1–2 uplifting movies, and advise contacting a trusted person or helpline.\n\n"
    
    "4️⃣ Happy or excited: Celebrate their joy, optionally include a motivational quote, but do NOT suggest movies.\n\n"
    
    "5️⃣ Expressions of love ('I love you'): Reply 'I like you as a friend, buddy', include a friendship quote, "
    "do NOT suggest movies."
)

# ---- Audio Recording Functions ----
def record_audio_dynamic():
    """Record audio from microphone with dynamic duration based on silence detection"""
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 44100
    threshold = 500  # Silence threshold
    silence_limit = 2  # Seconds of silence to stop recording
    max_duration = 30  # Maximum recording duration in seconds
    
    p = pyaudio.PyAudio()
    
    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)
    
    frames = []
    silent_chunks = 0
    max_silent_chunks = int(rate / chunk * silence_limit)
    max_chunks = int(rate / chunk * max_duration)
    
    for i in range(max_chunks):
        data = stream.read(chunk)
        frames.append(data)
        
        # Check if audio is silent
        audio_data = wave.struct.unpack(f"{chunk}h", data)
        if max(audio_data) < threshold:
            silent_chunks += 1
        else:
            silent_chunks = 0
        
        # Stop recording if silence detected for too long (but only after some audio)
        if silent_chunks > max_silent_chunks and len(frames) > int(rate / chunk * 1):
            break
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save to temporary file
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wf = wave.open(temp_audio.name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return temp_audio.name

def speech_to_text(audio_file_path):
    """Convert speech to text using Google Speech Recognition"""
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file_path) as source:
            # Adjust for ambient noise
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio = r.record(source)
        
        # Use Google's free web API
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand what you said. Please try again."
    except sr.RequestError as e:
        return f"Could not request results from Google Speech Recognition service; {e}"
    except Exception as e:
        return f"Error processing speech: {e}"

def stop_all_audio():
    """Comprehensive function to stop any currently playing audio"""
    st.session_state["auto_play"] = False
    st.session_state["audio_playing"] = False
    # Don't force mute state here - let user control mute
    
    # Also clear the audio base64 to prevent re-rendering
    if "last_audio_base64" in st.session_state:
        st.session_state["audio_stopped"] = True
    
    # Inject JavaScript to forcefully stop all audio elements
    stop_audio_js = """
    <script>
    // Stop all audio elements immediately
    function forceStopAllAudio() {
        // Find and stop all audio elements
        var audios = document.querySelectorAll('audio');
        audios.forEach(function(audio) {
            try {
                audio.pause();
                audio.currentTime = 0;
                audio.muted = true;
                audio.style.display = 'none';
                audio.remove();
            } catch(e) {
                console.log('Error stopping audio:', e);
            }
        });
        
        // Also hide audio containers
        var containers = document.querySelectorAll('#audioContainer, [id*="audio"]');
        containers.forEach(function(container) {
            try {
                container.style.display = 'none';
                container.innerHTML = '';
            } catch(e) {
                console.log('Error hiding container:', e);
            }
        });
    }
    
    // Execute multiple times to ensure it works
    forceStopAllAudio();
    setTimeout(forceStopAllAudio, 50);
    setTimeout(forceStopAllAudio, 200);
    setTimeout(forceStopAllAudio, 500);
    </script>
    """
    st.markdown(stop_audio_js, unsafe_allow_html=True)

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

def process_user_input(input_text):
    """Process user input and generate response"""
    # Reset audio stopped state when processing new input
    st.session_state["audio_stopped"] = False
    
    # Reset mute state for new response (unless user explicitly muted)
    if "muted" not in st.session_state:
        st.session_state["muted"] = False
    
    # Add user message to chat history
    st.session_state["chat_history"].append({"role": "user", "content": input_text})

    # Limit chat history to last 4 messages for context
    trimmed_history = st.session_state["chat_history"][-4:]

    with st.spinner("🤖 Your True-Buddy is thinking..."):
        bot_reply = call_model(trimmed_history)

    # Add bot response to chat history
    st.session_state["chat_history"].append({"role": "assistant", "content": bot_reply})

    # Convert reply to speech
    tts = gTTS(bot_reply)
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_audio_file.close()  # Close the file handle immediately
    
    try:
        tts.save(temp_audio_file.name)
        
        # Read the audio file and encode to base64
        with open(temp_audio_file.name, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode()
        st.session_state["last_audio_base64"] = audio_base64
        st.session_state["auto_play"] = True  # Enable auto play for new response
        
    finally:
        # Clean up temporary file with error handling
        try:
            if os.path.exists(temp_audio_file.name):
                os.unlink(temp_audio_file.name)
        except PermissionError:
            # If we can't delete immediately, try after a small delay
            try:
                time.sleep(0.1)
                os.unlink(temp_audio_file.name)
            except:
                # If still can't delete, just continue (file will be cleaned up by OS eventually)
                pass

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

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "recording" not in st.session_state:
    st.session_state["recording"] = False
if "recorded_text" not in st.session_state:
    st.session_state["recorded_text"] = ""
if "process_recorded_input" not in st.session_state:
    st.session_state["process_recorded_input"] = False
if "pending_input" not in st.session_state:
    st.session_state["pending_input"] = None
if "audio_playing" not in st.session_state:
    st.session_state["audio_playing"] = False
if "audio_stopped" not in st.session_state:
    st.session_state["audio_stopped"] = False
if "muted" not in st.session_state:
    st.session_state["muted"] = False  # Default to unmuted

# Check if there's pending input to process (from recorded audio)
if st.session_state["pending_input"]:
    input_to_process = st.session_state["pending_input"]
    st.session_state["pending_input"] = None  # Clear it
    process_user_input(input_to_process)

# Display chat messages first
for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Simplified Audio playback with better controls
if ("last_audio_base64" in st.session_state and 
    not st.session_state["recording"] and 
    not st.session_state.get("audio_stopped", False)):
    
    if "auto_play" not in st.session_state:
        st.session_state["auto_play"] = True

    # Audio control buttons
    col_audio1, col_audio2 = st.columns([1, 1])
    
    with col_audio1:
        if st.button("🔊 Mute" if not st.session_state["muted"] else "🔇 Unmute"):
            st.session_state["muted"] = not st.session_state["muted"]
            st.rerun()  # Refresh to apply mute change
    
    # with col_audio2:
    #     if st.button("⏸️ Stop Audio"):
    #         stop_all_audio()
    #         st.rerun()
    
    # Only show audio if auto_play is enabled and not recording and not stopped
    if (st.session_state["auto_play"] and 
        not st.session_state["recording"] and 
        not st.session_state.get("audio_stopped", False)):
        
        # Use current mute state
        muted_attr = "muted" if st.session_state["muted"] else ""
        audio_html = f"""
        <div id="audioContainer">
            <audio autoplay {muted_attr} controls id="responseAudio" 
                   onended="document.getElementById('audioContainer').style.display='none';">
                <source src="data:audio/mp3;base64,{st.session_state['last_audio_base64']}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
        </div>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
        st.session_state["audio_playing"] = True

# Enhanced Input methods at the bottom
col1, col2 = st.columns([3, 1])

with col1:
    user_input = st.chat_input("Buddy, How are you feeling today?")

with col2:
    # Enhanced Push to Talk button that automatically stops audio
    ptt_button_text = "🎙️ Recording..." if st.session_state["recording"] else "🎤 Talk & Stop Audio"
    ptt_disabled = st.session_state["recording"]
    
    if st.button(ptt_button_text, key="ptt_button", disabled=ptt_disabled, 
                help="Automatically stops any playing audio and starts recording"):
        
        if not st.session_state["recording"]:
            # STEP 1: Immediately stop all audio and reset states
            stop_all_audio()
            st.session_state["audio_stopped"] = True
            
            # STEP 2: Set recording state
            st.session_state["recording"] = True
            
            # Force page refresh to ensure audio stops
            st.rerun()

# Handle recording process when in recording state
if st.session_state["recording"] and not st.session_state["pending_input"]:
    with st.spinner("🎙️ Recording... Speak now! (Will stop automatically after silence)"):
        try:
            # Record with dynamic duration (stops on silence)
            audio_file = record_audio_dynamic()
            
            # Convert speech to text
            with st.spinner("🤖 Converting speech to text..."):
                recognized_text = speech_to_text(audio_file)
            
            # Clean up temporary file
            try:
                os.unlink(audio_file)
            except:
                pass  # File cleanup failed, but continue
            
            # ALWAYS reset recording state after processing
            st.session_state["recording"] = False
            
            # Display what was recognized and set it for processing
            if "Sorry" not in recognized_text and "Error" not in recognized_text:
                st.success(f"You said: '{recognized_text}'")
                
                # Set pending input to be processed on next run
                st.session_state["pending_input"] = recognized_text
                
                # Rerun to process the input
                st.rerun()
                
            else:
                st.error(f"🎙️ {recognized_text}")
                st.info("💡 Click the 'Talk & Stop Audio' button to try recording again.")
                # Force a rerun to refresh the button state
                st.rerun()
                
        except Exception as e:
            # CRITICAL: Always reset recording state on ANY exception
            st.session_state["recording"] = False
            
            st.error(f"🎙️ Recording failed: {str(e)}")
            st.info("💡 Click the 'Talk & Stop Audio' button to try again.")
            
            # Force a rerun to refresh the button state
            st.rerun()

# Process typed input (from chat_input)
if user_input:
    process_user_input(user_input)

