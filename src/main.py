from dotenv import load_dotenv
import streamlit as st
import openai
import os
import json
import shutil
import sys

SYSTEM_MESSAGE = "Du bist ein hilfreicher Assistent, der Patientenaufklärung zu einer Operation betreibt."
ASSISTANT_START_MESSAGE = "Ich kann dir bei Infos zu deiner OP helfen. Was für Fragen hast du?"

if getattr(sys, 'frozen', False):  # Check if running as a PyInstaller executable
    base_path = sys._MEIPASS
else:
    base_path = os.getcwd()

load_dotenv(dotenv_path=os.path.join(base_path, ".env"))
# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Directory to save chat histories
CHAT_HISTORY_DIR = os.path.join(base_path, "chat_histories")
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

def save_chat_to_markdown(file_path, user_id, chat_history):
    with open(file_path, "w") as f:
        f.write(f"# Chat History for User ID: {user_id}\n\n")
        for entry in chat_history:
            role = entry['role']
            message = entry['content']
            f.write(f"**{role.capitalize()}**: {message}\n\n")

def save_to_json(file_path, user_id, chat_history):
    data = {
        "patient_id": user_id,
        "chat_history": chat_history
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def generate_stream(messages):
    try:
        response = openai.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4"),
            messages=messages,
            stream=True
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except openai.APIError as e:
        st.error(f"API Error: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# Configure sidebar to be collapsed by default
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# Page Header
st.title("Patientenaufklärungsstudie mittels ChatGPT")


# Setting the patient id
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if not st.session_state.user_id:
    user_input_id = st.text_input("Gib deine anonymisierte Patienten-ID ein, um den Chat zu starten..")
    if user_input_id:
        st.session_state.user_id = user_input_id
        st.rerun()  # Force a rerun after setting user_id
user_id = st.session_state.user_id

# Running the chat window
if user_id:
    chat_file_path = os.path.join(CHAT_HISTORY_DIR, f"{user_id}.md")
    json_file_path = os.path.join(CHAT_HISTORY_DIR, f"{user_id}.json")

    if "chat_history" not in st.session_state or st.session_state.chat_history == []:
        st.session_state.chat_history = [
            {
                "role": "system",
                "content": SYSTEM_MESSAGE
            },
            {
                "role": "assistant",
                "content": ASSISTANT_START_MESSAGE
            }
        ]

    # Display chat history using st.chat_message
    for chat in st.session_state.chat_history:
        if chat["role"] != "system":  # Skip system messages
            with st.chat_message(chat["role"]):
                st.markdown(chat["content"])

    # User input message
    user_message = st.chat_input("Schreibe deine Anfrage hier...")
    if user_message:
        # Append user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_message})

        # Display the user message immediately
        with st.chat_message("user"):
            st.markdown(user_message)

        # Generate GPT streaming response
        messages = st.session_state.chat_history
        full_response = ""
        with st.spinner("ChatGPT antwortet..."):
            response_stream = generate_stream(messages)
            if response_stream:
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    for token in response_stream:
                        full_response += token
                        response_placeholder.markdown(full_response, unsafe_allow_html=True)

        # Save GPT response
        if full_response:
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

            # Save chat history to markdown file
            save_chat_to_markdown(chat_file_path, user_id, st.session_state.chat_history)

            # Save chat history to JSON file
            save_to_json(json_file_path, user_id, st.session_state.chat_history)

# Reset button to clear user_id and chat history
with st.sidebar:
    if st.button("Reset"):
        st.session_state.user_id = ""
        st.session_state.chat_history = []
        st.rerun()

# Add a button to download the chat_histories folder
with st.sidebar:
    if st.button("Download Chat Histories"):
        zip_file_path = "chat_histories.zip"
        shutil.make_archive("chat_histories", "zip", CHAT_HISTORY_DIR)
        with open(zip_file_path, "rb") as f:
            st.download_button(
                label="Download Chat Histories as ZIP",
                data=f,
                file_name="chat_histories.zip",
                mime="application/zip"
            )