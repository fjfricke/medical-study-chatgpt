from dotenv import load_dotenv
import streamlit as st
import openai
import os
import json
import shutil
from markdown_pdf import MarkdownPdf, Section
import hashlib

SYSTEM_MESSAGE = "Du bist ein hilfreicher Assistent, der Patientenaufklärung zu einer Operation betreibt."
ASSISTANT_START_MESSAGE = "Ich kann dir bei Infos zu deiner OP helfen. Was für Fragen hast du?"

if os.getenv("FLY_APP_NAME"):  # Check if running on Fly.io
    base_path = "/data"  # Use the Fly.io mounted volume path
else:
    base_path = os.getcwd()

load_dotenv(dotenv_path=os.path.join(base_path, ".env"))
# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
PASSWORD_HASH = os.getenv("PASSWORD_HASH")

# Directory to save chat histories
CHAT_HISTORY_DIR = os.path.join(base_path, "chat_histories")
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

def save_chat_to_markdown(file_path, user_id, chat_history):
    with open(file_path, "w") as f:
        f.write(f"# Chat History for User ID: {user_id}\n\n")
        for entry in chat_history:
            role = entry['role']
            message = entry['content']
            f.write(f"## {role.capitalize()}\n{message}\n\n")

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

# Function to hash a password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Configure sidebar to be collapsed by default
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# Login functionality
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # Replace this with your actual authentication logic
        if username in ["admin", "study"] and hash_password(password) == PASSWORD_HASH:
            st.session_state.logged_in = True
            st.session_state.logged_in_as = username
            st.rerun()
        else:
            st.error("Invalid username or password")
else:
    # Rest of the app
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


    # Define the dialog function
    @st.dialog("Are you sure you want to reset?")
    def show_reset_dialog():
        st.write("This will clear the patient's session for the next patient. Stored content will not be deleted.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, reset"):
                st.session_state.user_id = ""
                st.session_state.chat_history = []
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.rerun()

    # Reset button to clear user_id and chat history
    with st.sidebar:
        if st.button("Reset"):
            show_reset_dialog()

    # Add a button to download the chat_histories folder
    if st.session_state.logged_in_as == "admin":
        with st.sidebar:
            if st.button("Prepare Download of Chat Histories"):
                # for each .md file in the chat_histories folder, convert it to a pdf and save it in the same folder
                for file in os.listdir(CHAT_HISTORY_DIR):
                    if file.endswith(".md"):
                        content = open(os.path.join(CHAT_HISTORY_DIR, file), "r").read()
                        pdf_file_path = os.path.join(CHAT_HISTORY_DIR, file.replace(".md", ".pdf"))
                        pdf = MarkdownPdf(toc_level=3)
                        pdf.add_section(Section(content))
                        pdf.save(pdf_file_path)
                zip_file_path = "chat_histories.zip"
                shutil.make_archive("chat_histories", "zip", CHAT_HISTORY_DIR)
                with open(zip_file_path, "rb") as f:
                    st.download_button(
                        label="Download Chat Histories as ZIP",
                        data=f,
                        file_name="chat_histories.zip",
                        mime="application/zip"
                    )

    # Define the dialog function
    @st.dialog("Are you sure you want to logout?")
    def show_logout_dialog():
        st.write("This will logout and clear the current patient session. Stored content will not be deleted.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, logout"):
                st.session_state.user_id = ""
                st.session_state.chat_history = []
                st.session_state.logged_in = False
                st.session_state.logged_in_as = ""
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.rerun()

    # Reset button to clear user_id and chat history
    with st.sidebar:
        if st.button("Logout"):
            show_logout_dialog()

    if st.session_state.logged_in_as == "admin":
        @st.dialog("Are you sure you want to wipe all data?")
        def show_wipe_dialog():
            st.write("This will wipe all data from the database. This action is irreversible.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, wipe"):
                    st.session_state.user_id = ""
                    st.session_state.chat_history = []
                    # remove all files in the chat_histories folder
                    for file in os.listdir(CHAT_HISTORY_DIR):
                        os.remove(os.path.join(CHAT_HISTORY_DIR, file))
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.rerun()
        with st.sidebar:
            if st.button("Wipe all data"):
                show_wipe_dialog()