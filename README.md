# 💬 True-Buddy — Emotional Support Chatbot

[![CI/CD](https://github.com/me-Afzal/True-Buddy-Chatbot/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/me-Afzal/True-Buddy-Chatbot/actions/workflows/ci-cd.yml)


True-Buddy is a warm, empathetic **best-friend style chatbot** that listens, comforts, and uplifts you when you’re feeling down — or celebrates your happiness when you’re in a good mood.  
It uses **Google Gemini API (Gemini 2.0 Flash model)** for conversational responses and **Google Text-to-Speech (gTTS)** to read replies aloud.

---

## ✨ Features

- 💖 **Empathetic Conversations** — Listens without judgment, provides motivational quotes, and suggests uplifting movies when the user is down.  
- 🎙 **Text-to-Speech** — Reads responses aloud automatically.  
- 🤗 **Best Friend Personality** — Calls you "buddy" in a loving, supportive way.  
- 🎬 **Motivational Movie Suggestions** — Provided only when the user is feeling down.  
- 🎉 **Celebrates Your Joy** — Responds warmly when you share happy news, optionally with quotes.  
- 🖥 **Streamlit UI** — Clean, simple, and interactive chat interface.  
- 🔇 **Mute/Unmute Audio** — Control auto-played audio easily.

---

## 🛠 Tech Stack

- **Python 3.9+**
- **[Streamlit](https://streamlit.io/)** — Web UI  
- **[Google Gemini API](https://cloud.google.com/ai)** — Gemini 2.0 Flash model for conversational responses  
- **[gTTS](https://pypi.org/project/gTTS/)** — Google Text-to-Speech for audio playback  
- **Base64 Encoding** — For autoplay audio in the browser

---

### **📦 Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/me-Afzal/True-Buddy-Chatbot.git
   cd True-Buddy-Chatbot
   
2. **Create and activate a virtual environment (recommended)**  
   python \-m venv venv  
   \# On macOS/Linux  
   source venv/bin/activate  
   \# On Windows  
   \# venv\\Scripts\\activate

3. **Install dependencies**  
   pip install \-r requirements.txt

4. Set up environment variables  
   Create a file named .env in the root directory of your project (the same directory as app.py and requirements.txt). Add your Google Gemini API key to this file:  
   GEMINI\_API\_KEY=your\_google\_gemini\_api\_key

   *Replace your\_google\_gemini\_api\_key with your actual API key obtained from Google AI Studio.*  
5. **Run the Streamlit app**  
   streamlit run app.py

## 📑 Documentation

- [CI/CD Pipeline](docs/CI_CD.md)