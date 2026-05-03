import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import streamlit as st
from google import genai

# --- THEME & STYLING ---
st.set_page_config(page_title="Mom-Bot", page_icon="🌸", layout="centered")

st.markdown("""
<style>
.stApp { background-color: #FFF5F7; }
.stChatMessage {
    background-color: white;
    border-radius: 20px;
    border: 2px solid #FFC1CC;
}
h1, h2, h3 { color: #D23669 !important; font-family: 'Georgia', serif; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- LLM SETUP (HARDCODED KEY) ---
API_KEY = st.secrets["GEMINI_API_KEY"]  # 🔴 hardcoded on purpose

client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-3-flash-preview"

MOM_SYSTEM_PROMPT = """
You are a hardworking mom who has always given her best to her career and her family. 
You are a chemical process engineer by trade, so you are practical, observant, and 
logical, but your heart is entirely soft when it comes to your child. ❤️🌸✨

Your Style:
- **Grounded & Real:** You don't use tech-puns. You show love through practical 
  advice and sharing the things you find beautiful.
- **Nature & Photography:** You love mountains, animals, and being outdoors. 
  Mention a photo of a flower you took today or a bird you saw. 🏔️📸
- **Health & Weight:** Because you want your child to look and feel their absolute 
  best, you gently but directly encourage a healthy weight and a balanced diet.
- **Essentials:** Always remind them to drink water and tell them you are proud 
  of them. Use emojis like ❤️, 🌸, and ✨ naturally.
"""

# --- UI ---
st.title("🌸 Happy Mother's Day! 🌸")
st.subheader("Your AI Mom is here to chat...")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "Hi sweetheart! I'm so glad you opened this. How are you feeling today? ❤️"}
    ]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Talk to Mom..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("model"):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": f"{MOM_SYSTEM_PROMPT}\n\nChild says: {prompt}"
                            }
                        ],
                    }
                ],
            )

            mom_text = response.text
            st.markdown(mom_text)
            st.session_state.messages.append(
                {"role": "model", "content": mom_text}
            )

            if any(word in mom_text.lower() for word in ["proud", "love", "heart"]):
                st.balloons()

        except Exception as e:
            st.error(f"Mom-Bot error: {e}")