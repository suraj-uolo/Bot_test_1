import os
import time
import streamlit as st
import openai
from dotenv import load_dotenv
import base64
from io import StringIO

load_dotenv()

api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in Streamlit secrets or a local .env file.")

openai.api_key = api_key
client = openai
MAX_HISTORY_LENGTH = 10

st.set_page_config(page_title="UoloBot_2", layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #F1F8E9 0%, #FFFFFF 100%) !important;
        font-family: "Helvetica Neue", Arial, sans-serif;
        color: #333;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box;
        height: auto !important;
        display: flex;
        flex-direction: column;
    }
    html, body, [class*="css"] {
        font-size: 1rem;
    }
    .title {
        font-size: 1.3rem;
        text-align: center;
        margin: 0 !important;
        padding: 6px 0 !important;
        font-weight: bold;
    }
    .welcome {
        font-size: 1rem;
        text-align: center;
        margin: 0 !important;
        padding: 2px 0 10px 0 !important;
        color: #555;
    }

    /* ------------- Fixed-size conversation box ------------- */
    .conversation-box {
        border: 1px solid #ddd;
        background-color: #fafafa;
        border-radius: 6px;
        padding: 0.5rem;
        margin: 0.5rem;
        /* Set a fixed (or max) height; adjust to your preference. */
        height: 350px; 
        max-height: 350px;
        /* Make sure it can scroll */
        overflow-y: auto;  
        /* Prevent it from expanding further */
        flex-grow: 0;  
    }
    /* For smaller screens, you can reduce the height further */
    @media (max-width: 600px) {
        .conversation-box {
            height: 250px;
            max-height: 250px;
        }
    }

    .user-message, .bot-message {
        word-wrap: break-word;
        padding: 8px 10px;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 0.95rem;
    }
    .user-message {
        background-color: #e8f4ff;
        border: 1px solid #c9e8ff;
        color: #0d47a1;
    }
    .bot-message {
        background-color: #f0fff4;
        border: 1px solid #c2f2d0;
        color: #1b5e20;
    }
    a.download-link {
        color: #ffffff !important;
        background-color: #6A1B9A;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        text-decoration: none;
        font-size: 0.85rem;
        text-align: center;
        display: block;
    }
    a.download-link:hover {
        background-color: #4A148C;
        text-decoration: none;
    }
    .css-1q8dd3e, .css-h2pz5l {
        background-color: #D32F2F !important;
        color: #ffffff !important;
        border-radius: 4px;
        border: none;
        font-weight: 600;
        box-shadow: none;
        padding: 0.4rem 0.8rem;
        width: 100%;
        text-align: center;
        margin-top: 6px;
    }
    .css-1q8dd3e:hover, .css-h2pz5l:hover {
        background-color: #B71C1C !important;
        color: #f2f2f2 !important;
    }
    .stButton button {
        background-color: #1976D2 !important;
        color: #f9f9f9 !important;
        font-weight: 600;
        border: none;
        border-radius: 4px;
        box-shadow: none;
        padding: 0.4rem 0.8rem;
        width: 100%;
        text-align: center;
        margin-top: 6px;
        font-size: 0.9rem;
    }
    .stButton button:hover {
        background-color: #115293 !important;
        color: #ffffff !important;
    }
    .stTextInput label {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
        color: #444444;
    }
    .stTextInput div[data-baseweb="input"] {
        background-color: #ffffff !important;
        color: #333333 !important;
        min-height: 42px !important;
        border: 1px solid #ccc !important;
        border-radius: 4px !important;
    }
    .action-buttons {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin: 4px 0.5rem 1rem 0.5rem;
    }
    .conversation-box::-webkit-scrollbar {
        width: 6px;
    }
    .conversation-box::-webkit-scrollbar-thumb {
        background-color: rgba(0,0,0,0.2);
        border-radius: 3px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def truncate_history_if_needed():
    if len(st.session_state.conversation_history) > (2 * MAX_HISTORY_LENGTH + 1):
        excess_count = len(st.session_state.conversation_history) - (2 * MAX_HISTORY_LENGTH + 1)
        st.session_state.conversation_history = (
            st.session_state.conversation_history[:1]
            + st.session_state.conversation_history[1 + excess_count:]
        )

def chatbot_response(user_input):
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    truncate_history_if_needed()

    try:
        response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:uolo-ai:uolobot-2:Ao6BTB9X",
            messages=st.session_state.conversation_history,
            temperature=1,
            max_tokens=200,
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
    st.session_state.conversation_history = st.session_state.conversation_history[:1]

def get_download_link():
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

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = [
        {
            "role": "system",
            "content": (
                "You are UoloBot, Uolo’s dedicated help desk assistant. "
                "Always maintain a friendly, helpful tone. "
                "If a question is not addressed by your training data, politely instruct the user to contact the Uolo support team via WhatsApp nUmber: 9599822544  "
                "Do not offer to contact support on their behalf. "
                "Always remain true to your fine-tuned training data. "
                "Only answer questions related to the Uolo Edtech Platforms and educational doubts; politely refuse if unrelated."
            )
        }
    ]
st.markdown('<div class="title">UoloBot_2</div>', unsafe_allow_html=True)
st.markdown('<div class="welcome">Welcome! I am UoloBot, here to assist you.</div>', unsafe_allow_html=True)

def render_chat():
    chat_html = "<div class='conversation-box'>"
    for msg in st.session_state.conversation_history:
        if msg["role"] == "system":
            continue
        elif msg["role"] == "user":
            chat_html += f"<div class='user-message'>You: {msg['content']}</div>"
        elif msg["role"] == "assistant":
            chat_html += f"<div class='bot-message'>UoloBot_2: {msg['content']}</div>"
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

    # Auto-scroll to the bottom after rendering
    scroll_script = """
    <script>
    var conversationBox = document.querySelector('.conversation-box');
    if (conversationBox){
        conversationBox.scrollTop = conversationBox.scrollHeight;
    }
    </script>
    """
    st.markdown(scroll_script, unsafe_allow_html=True)

def handle_message():
    user_text = st.session_state["user_input_key"]
    if user_text.strip():
        with st.spinner("UoloBot_2 is typing..."):
            time.sleep(1.0)
            chatbot_response(user_text.strip())
    st.session_state["user_input_key"] = ""

render_chat()

with st.form("user_input_form", clear_on_submit=True):
    st.text_input("", key="user_input_key", placeholder="Enter your message here...")
    st.form_submit_button("Send", on_click=handle_message)

st.markdown("<div class='action-buttons'>", unsafe_allow_html=True)
if st.button("Clear Chat"):
    clear_chat()

download_link = get_download_link()
st.markdown(download_link, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

