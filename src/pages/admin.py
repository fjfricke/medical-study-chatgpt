import os
import json
import streamlit as st

if os.getenv("FLY_APP_NAME"):  # Check if running on Fly.io
    base_path = "/data"  # Use the Fly.io mounted volume path
else:
    base_path = os.getcwd()

# Path to settings file
SETTINGS_FILE = os.path.join(base_path, "settings.json")
CHAT_HISTORY_DIR = os.path.join(base_path, "chat_histories")

# Load settings
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        # Create the file with default settings
        default_settings = {
            "system_message": "",
            "assistant_start_message": ""
        }
        return default_settings
    else:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

# Save settings
def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

# Get existing patient IDs
def get_existing_patients():
    if not os.path.exists(CHAT_HISTORY_DIR):
        return []
    files = os.listdir(CHAT_HISTORY_DIR)
    patient_ids = set()
    for file in files:
        if file.endswith(".md") or file.endswith(".json") or file.endswith(".pdf"):
            patient_id = file.split(".")[0]  # Extract patient ID from filename
            patient_ids.add(patient_id)
    return sorted(patient_ids)

# Admin Panel UI
st.title("Admin Panel")

settings = load_settings()

if st.session_state.get("logged_in_as") == "admin":

    # Input fields for system and assistant messages
    st.subheader("System- und Assistant-Nachrichten anpassen")
    system_message = st.text_area("System Message", value=settings["system_message"])
    assistant_start_message = st.text_area("Assistant Start Message", value=settings["assistant_start_message"])

    if st.button("Speichern"):
        settings["system_message"] = system_message
        settings["assistant_start_message"] = assistant_start_message
        save_settings(settings)
        st.success("Einstellungen wurden gespeichert!")

    # Display existing patients
    st.subheader("Vorhandene Patienten")
    patient_ids = get_existing_patients()
    if patient_ids:
        st.write("Folgende Patienten-IDs existieren bereits:")
        for patient_id in patient_ids:
            st.write(f"- {patient_id}")
    else:
        st.write("Es sind keine Patienten vorhanden.")

    # Add functionality to delete all data
    st.subheader("Alle Daten löschen")
    if st.session_state.logged_in_as == "admin":
        @st.dialog("Bist du sicher, dass du alle Daten löschen möchtest?")
        def show_wipe_dialog():
            st.write("Dies wird alle Daten aus der Datenbank mitsamt allen Chat-Historien löschen. Diese Aktion ist unwiderruflich.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Ja, löschen"):
                    st.session_state.user_id = ""
                    st.session_state.chat_history = []
                    # remove all files in the chat_histories folder
                    for file in os.listdir(CHAT_HISTORY_DIR):
                        os.remove(os.path.join(CHAT_HISTORY_DIR, file))
                    st.rerun()
            with col2:
                if st.button("Abbrechen"):
                    st.rerun()
        if st.button("Alle Daten löschen"):
            show_wipe_dialog()

else:
    st.error("Du hast keine Berechtigung, diese Seite zu sehen.")
