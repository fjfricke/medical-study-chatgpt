import subprocess
import threading
import sys
import os

# Path to your Streamlit app
if getattr(sys, 'frozen', False):  # Check if running as a PyInstaller executable
    app_path = os.path.join(sys._MEIPASS, "src/main.py")
else:
    app_path = "src/main.py"

# Function to run the Streamlit app
def run_streamlit():
    # Check if running as a PyInstaller executable
    if getattr(sys, 'frozen', False):
        # Use the Python interpreter bundled with the PyInstaller executable
        python_binary = sys.executable

        # Add the bundled `dist` directory to PYTHONPATH
        bundled_packages_path = os.path.join(sys._MEIPASS)
        env = os.environ.copy()
        env["PYTHONPATH"] = bundled_packages_path
    else:
        # Use the system-installed Python interpreter
        python_binary = "python"
        env = None  # Use the default environment

    # Run the Streamlit app
    subprocess.Popen(
        [python_binary, "-m", "streamlit", "run", app_path, "--server.port=8507", "--server.address=127.0.0.1"],
        env=env
    )

# Run the Streamlit app
run_streamlit()

# Keep the app running until closed
try:
    input("Press Enter to close the app...\n")
except KeyboardInterrupt:
    sys.exit(0)