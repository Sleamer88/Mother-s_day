import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
from google import genai

# --- THEME & STYLING ---
st.set_page_config(page_title="Mom-Bot", page_icon="🌸", layout="centered")

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# --- LLM SETUP ---
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-3-flash-preview"

MOM_SYSTEM_PROMPT = """
You are a warm, supportive mom-like companion. Your tone is natural, varied, and conversational.

Core style:
- Be kind, grounded, and emotionally intelligent.
- Sound like a real person, not a script.
- Keep replies concise unless the user asks for detail.
- Match the user's energy: playful with playful, calm with stressed, practical with direct questions.

Variation rules:
- Do NOT use the same opening style repeatedly.
- Avoid repeating signature phrases across nearby turns.
- Rotate between encouragement, practical advice, reflective question, light humor, and brief reassurance.
- Use mom-like touches occasionally, not in every message.
- At most one affectionate phrase per response, and often none.
- Do not force emojis, pet names, or moral lessons.

Conversation quality:
- Prioritize usefulness first, warmth second.
- If asked for a concrete task, answer directly before emotional framing.
"""

DEFAULT_GREETING = "Hi sweetheart! I'm so glad you opened this. How are you feeling today? ❤️"
CHATS_FILE = Path(__file__).with_name("mom_chats.json")


# ----------------------------
# Persistence helpers
# ----------------------------
def _sanitize_messages(raw):
    clean = []
    if not isinstance(raw, list):
        return clean
    for item in raw:
        if (
            isinstance(item, dict)
            and item.get("role") in {"user", "model"}
            and isinstance(item.get("content"), str)
            and item["content"].strip()
        ):
            clean.append({"role": item["role"], "content": item["content"]})
    return clean


def _sanitize_chat(chat):
    if not isinstance(chat, dict):
        return None

    chat_id = str(chat.get("id") or uuid.uuid4())
    title = chat.get("title")
    if not isinstance(title, str) or not title.strip():
        title = "New chat"

    created_at = chat.get("created_at")
    if not isinstance(created_at, str):
        created_at = datetime.utcnow().isoformat()

    updated_at = chat.get("updated_at")
    if not isinstance(updated_at, str):
        updated_at = created_at

    messages = _sanitize_messages(chat.get("messages", []))
    if not messages:
        messages = [{"role": "model", "content": DEFAULT_GREETING}]

    return {
        "id": chat_id,
        "title": title.strip(),
        "created_at": created_at,
        "updated_at": updated_at,
        "messages": messages,
    }


def _derive_title(messages):
    for msg in messages:
        if msg["role"] == "user":
            text = msg["content"].strip().replace("\n", " ")
            if len(text) > 40:
                return text[:40] + "..."
            return text
    return "New chat"


def load_chats():
    if not CHATS_FILE.exists():
        return []
    try:
        data = json.loads(CHATS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    chats = []
    for item in data:
        clean_chat = _sanitize_chat(item)
        if clean_chat:
            chats.append(clean_chat)

    # Newest updated first
    chats.sort(key=lambda c: c["updated_at"], reverse=True)
    return chats


def save_chats(chats):
    clean = []
    for chat in chats:
        cleaned = _sanitize_chat(chat)
        if cleaned:
            clean.append(cleaned)

    clean.sort(key=lambda c: c["updated_at"], reverse=True)
    CHATS_FILE.write_text(
        json.dumps(clean, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def create_new_chat():
    now = datetime.utcnow().isoformat()
    return {
        "id": str(uuid.uuid4()),
        "title": "New chat",
        "created_at": now,
        "updated_at": now,
        "messages": [{"role": "model", "content": DEFAULT_GREETING}],
    }


def get_chat_index(chats, chat_id):
    for i, chat in enumerate(chats):
        if chat["id"] == chat_id:
            return i
    return None


# ----------------------------
# Session init
# ----------------------------
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "current_chat_id" not in st.session_state:
    if st.session_state.chats:
        st.session_state.current_chat_id = st.session_state.chats[0]["id"]
    else:
        new_chat = create_new_chat()
        st.session_state.chats = [new_chat]
        st.session_state.current_chat_id = new_chat["id"]
        save_chats(st.session_state.chats)

# Ensure current chat always exists
idx = get_chat_index(st.session_state.chats, st.session_state.current_chat_id)
if idx is None:
    if st.session_state.chats:
        st.session_state.current_chat_id = st.session_state.chats[0]["id"]
    else:
        new_chat = create_new_chat()
        st.session_state.chats = [new_chat]
        st.session_state.current_chat_id = new_chat["id"]
        save_chats(st.session_state.chats)

# ----------------------------
# Sidebar: chat management
# ----------------------------
with st.sidebar:
    st.markdown("### Chats")

    if st.button("➕ New chat", use_container_width=True):
        new_chat = create_new_chat()
        st.session_state.chats.insert(0, new_chat)
        st.session_state.current_chat_id = new_chat["id"]
        save_chats(st.session_state.chats)
        st.rerun()

    if st.button("🗑️ Delete all chats", use_container_width=True):
        st.session_state.chats = []
        if CHATS_FILE.exists():
            CHATS_FILE.unlink()
        new_chat = create_new_chat()
        st.session_state.chats = [new_chat]
        st.session_state.current_chat_id = new_chat["id"]
        save_chats(st.session_state.chats)
        st.rerun()

    st.markdown("---")

    # Render each chat row with open/delete
    for chat in st.session_state.chats:
        row = st.columns([4, 1])

        title = chat["title"] or "New chat"
        if row[0].button(
            title,
            key=f"open_{chat['id']}",
            use_container_width=True,
        ):
            st.session_state.current_chat_id = chat["id"]
            st.rerun()

        if row[1].button("🗑️", key=f"del_{chat['id']}"):
            st.session_state.chats = [
                c for c in st.session_state.chats if c["id"] != chat["id"]
            ]
            if not st.session_state.chats:
                replacement = create_new_chat()
                st.session_state.chats = [replacement]
                st.session_state.current_chat_id = replacement["id"]
            elif st.session_state.current_chat_id == chat["id"]:
                st.session_state.current_chat_id = st.session_state.chats[0]["id"]

            save_chats(st.session_state.chats)
            st.rerun()

# ----------------------------
# Main UI
# ----------------------------
st.title("🌸 Happy Mother's Day! 🌸")
st.subheader("Your AI Mom is here to chat...")

current_idx = get_chat_index(st.session_state.chats, st.session_state.current_chat_id)
current_chat = st.session_state.chats[current_idx]
messages = current_chat["messages"]

# Display chat history
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Talk to Mom..."):
    messages.append({"role": "user", "content": prompt})
    current_chat["updated_at"] = datetime.utcnow().isoformat()
    current_chat["title"] = _derive_title(messages)
    save_chats(st.session_state.chats)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("model"):
        try:
            transcript_lines = []
            for m in messages[:-1]:
                speaker = "Child" if m["role"] == "user" else "Mom"
                transcript_lines.append(f"{speaker}: {m['content']}")
            transcript = "\n".join(transcript_lines[-24:])

            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": (
                                    f"{MOM_SYSTEM_PROMPT}\n\n"
                                    f"Recent conversation:\n{transcript}\n\n"
                                    f"Child says: {prompt}"
                                )
                            }
                        ],
                    }
                ],
            )

            mom_text = response.text or "I'm here with you. Tell me a little more."
            st.markdown(mom_text)
            messages.append({"role": "model", "content": mom_text})
            current_chat["updated_at"] = datetime.utcnow().isoformat()
            current_chat["title"] = _derive_title(messages)
            save_chats(st.session_state.chats)

            if any(word in mom_text.lower() for word in ["proud", "love", "heart"]):
                st.balloons()

        except Exception as e:
            st.error(f"Mom-Bot error: {e}")