import os
import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import base64
from io import StringIO

# -------------------------------
#       SETUP & CONFIG
# -------------------------------

# Load environment variables
load_dotenv(".env")
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

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
    /* Make the main container fit the entire screen, allow scrolling on small screens. */
    .stApp {
        background: linear-gradient(135deg, #E3F2FD 0%, #FFF9C4 100%) !important;
        font-family: "Helvetica Neue", Arial, sans-serif;
        color: #333;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box;
        min-height: 100vh !important; /* Use min-height instead of fixed height */
        overflow: auto !important;    /* Allow page scrolling if needed */
        display: flex;
        flex-direction: column;
    }

    /* Title and welcome message with minimal margins */
    .title {
        font-size: 1.2rem;
        text-align: center;
        margin: 0 !important;
        padding: 4px 0 !important;
    }
    .welcome {
        font-size: 0.9rem;
        text-align: center;
        margin: 0 !important;
        padding: 2px 0 !important;
    }

    /* Fixed-size conversation box so it doesn't stretch endlessly.
       Use overflow-y: auto to allow scrolling inside the box. */
    .conversation-box {
        border: 1px solid #ddd;
        background-color: #fafafa;
        border-radius: 6px;
        padding: 0.5rem;
        margin: 0.5rem;
        height: 30vh !important;   /* Default height on larger screens */
        overflow-y: auto;          /* Scroll within the box if messages exceed this height */
        flex: none;
    }

    /* Increase conversation box height on smaller screens (e.g., phones) */
    @media (max-width: 600px) {
        .conversation-box {
            height: 40vh !important;
        }
    }

    /* Properly wrap long text in messages */
    .user-message, .bot-message {
        word-wrap: break-word;
        padding: 6px 8px;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }

    /* Style for user messages */
    .user-message {
        background-color: #e8f4ff;
        border: 1px solid #c9e8ff;
        color: #0d47a1;
    }

    /* Style for bot messages */
    .bot-message {
        background-color: #f0fff4;
        border: 1px solid #c2f2d0;
        color: #1b5e20;
    }

    /* Download link style (Purple button) */
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

    /* Clear Chat button styling (Red) */
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
    
    /* Send button styling inside forms (Blue) */
    .stButton button {
        background-color: #1976D2 !important;
        color: #ffffff !important;
        font-weight: 600;
        border: none;
        border-radius: 4px;
        box-shadow: none;
        padding: 0.4rem 0.8rem;
        width: 100%;
        text-align: center;
        margin-top: 6px;
        font-size: 0.85rem;
    }
    .stButton button:hover {
        background-color: #115293 !important;
        color: #ffffff !important;
    }

    /* Slightly larger input text and spacing for better accessibility */
    .stTextInput label {
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
        color: #444444;
    }
    .stTextInput div[data-baseweb="input"] {
        background-color: #ffffff !important;
        color: #333333 !important;
        min-height: 38px !important;
        border: 1px solid #ccc !important;
        border-radius: 4px !important;
    }

    /* Action buttons container - minimal vertical space */
    .action-buttons {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin: 4px 0.5rem 0.5rem 0.5rem;
    }

    /* Style the scrollbar for the conversation box if content overflows */
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
        response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:uolo-ai:uolobot-2:Ao6BTB9X",
            messages=st.session_state.conversation_history,
            temperature=1,
            max_completion_tokens=200,
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
st.markdown('<div class="welcome">Welcome! I am UoloBot, I am here to help.</div>', unsafe_allow_html=True)

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
