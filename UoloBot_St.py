import os
import time
import streamlit as st
import openai  # Instead of from openai import OpenAI
from dotenv import load_dotenv
import base64
from io import StringIO

# -------------------------------
#       SETUP & CONFIG
# -------------------------------

# Load environment variables from .env (optional for local dev)
load_dotenv()

# Try getting the key from st.secrets first; if empty, fallback to os.getenv
api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OpenAI API key not found. Please set OPENAI_API_KEY in your Streamlit secrets "
        "or in a local .env file."
    )

# Set the OpenAI API key globally
openai.api_key = api_key

# (Optional) If you want a separate client reference, you can do:
client = openai

# Max conversation messages to keep (for user & assistant each)
MAX_HISTORY_LENGTH = 10

# Streamlit page config
st.set_page_config(
    page_title="UoloBot_2",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject a meta tag to improve mobile responsiveness
st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """,
    unsafe_allow_html=True
)

# -------------------------------
#   CUSTOM STYLING FOR UI
# -------------------------------
st.markdown(
    """
    <style>
    /* Custom CSS omitted for brevity; keep your existing styles here. */
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
#       HELPER FUNCTIONS
# -------------------------------
def truncate_history_if_needed():
    """
    Ensures the conversation history does not exceed the max allowed length.
    Removes older messages while keeping the system prompt.
    """
    if len(st.session_state.conversation_history) > (2 * MAX_HISTORY_LENGTH + 1):
        excess_count = len(st.session_state.conversation_history) - (2 * MAX_HISTORY_LENGTH + 1)
        st.session_state.conversation_history = (
            st.session_state.conversation_history[:1]
            + st.session_state.conversation_history[1 + excess_count:]
        )

def chatbot_response(user_input):
    """
    Sends the user's message to the OpenAI API and retrieves the bot's response.
    Adds both the user's message and the bot's reply to the conversation history.
    """
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    truncate_history_if_needed()

    try:
        response = openai.ChatCompletion.create(
            # Or client.ChatCompletion.create if you want to use 'client'
            model="ft:gpt-4o-mini-2024-07-18:uolo-ai:uolobot-2:Ao6BTB9X",
            messages=st.session_state.conversation_history,
            temperature=1,
            max_tokens=200,  #  rename 'max_completion_tokens' to 'max_tokens' for correct usage
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        assistant_reply = response.choices[0].message.content
        st.session_state.conversation_history.append({"role": "assistant", "content": assistant_reply})
        return assistant_reply
    except Exception:
        return (
            "I’m sorry, but I’m having trouble answering right now. "
            "Please try again or contact support."
        )

def clear_chat():
    """
    Clears the conversation history, preserving only the system message.
    """
    st.session_state.conversation_history = st.session_state.conversation_history[:1]

def get_download_link():
    """
    Returns an HTML link that allows users to download the current chat history as a .txt file.
    """
    chat_text = []
    for msg in st.session_state.conversation_history:
        if msg["role"] == "user":
            chat_text.append(f"You: {msg['content']}")
        elif msg["role"] == "assistant":
            chat_text.append(f"UoloBot_2: {msg['content']}\n")

    buffer = StringIO("\n".join(chat_text))
    buffer.seek(0)

    b64 = base64.b64encode(buffer.read().encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="chat_history.txt" class="download-link">Download Chat</a>'
    return href

# -------------------------------
#   INITIALIZE SESSION STATE
# -------------------------------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = [
        {
            "role": "system",
            "content": (
                "You are UoloBot, Uolo’s dedicated help desk assistant. "
                "Maintain a friendly tone and ask clarifying questions to narrow down the best answers "
                "based on the training data. Remain true to your fine-tuned training data. "
                "Only answer questions about the platform or study; politely refuse if unrelated."
            )
        }
    ]

# -------------------------------
#         APP LAYOUT
# -------------------------------

# Title and Welcome Message (no space above)
st.markdown('<div class="title">UoloBot_2</div>', unsafe_allow_html=True)
st.markdown('<div class="welcome">Welcome! I am UoloBot, here to help.</div>', unsafe_allow_html=True)

# Container to display chat
def render_chat():
    chat_html = "<div class='conversation-box'>"
    for msg in st.session_state.conversation_history:
        if msg["role"] == "system":
            # Skip or handle system messages differently if desired
            continue
        elif msg["role"] == "user":
            chat_html += f"<div class='user-message'>You: {msg['content']}</div>"
        elif msg["role"] == "assistant":
            chat_html += f"<div class='bot-message'>UoloBot_2: {msg['content']}</div>"
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

# Callback for handling user input
def handle_message():
    user_text = st.session_state["user_input_key"]
    if user_text.strip():
        with st.spinner("UoloBot_2 is typing..."):
            time.sleep(1.0)  # Optional simulated delay
            chatbot_response(user_text.strip())
    # Clear the text input
    st.session_state["user_input_key"] = ""

# Render chat box (fixed size)
render_chat()

# User input form + Send button
with st.form("user_input_form", clear_on_submit=True):
    st.text_input(
        "",
        key="user_input_key",
        placeholder="Enter your message here..."
    )
    st.form_submit_button("Send", on_click=handle_message)

# Container for additional buttons (Clear Chat, Download Chat)
st.markdown("<div class='action-buttons'>", unsafe_allow_html=True)
if st.button("Clear Chat"):
    clear_chat()
download_link = get_download_link()
st.markdown(download_link, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
