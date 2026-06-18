import os
import sys

# --- TERMINAL PATH VIRTUALIZATION ---
IS_ANDROID = os.path.exists("/data/data/com.termux")
if IS_ANDROID:
    print("[!] Android detected. Virtualizing paths...")
    # Map C:\AI to Termux Home
    BASE_DIR = os.path.expanduser("~/council_v3")
else:
    BASE_DIR = "C:\\AI"

# Override internal path logic before loading the bridge
os.environ["COUNCIL_HEADLESS"] = "1"

# Force imports to work even if requirements.txt failed heavy libs
try:
    import council_v3_bridge
except ImportError as e:
    print(f"[!] Error loading bridge: {e}")
    print("[!] Ensure you ran: pip install flask flask-cors flask-sock requests python-dotenv")
    sys.exit(1)

if __name__ == "__main__":
    print("[+] Launching Headless Council Bridge for Android...")
    # Port 5002 for the App to find us
    # Bind to 0.0.0.0 to allow connection from the Android WebView
    council_v3_bridge.app.run(host='0.0.0.0', port=5002, debug=False)
