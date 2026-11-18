# start_all.py — backend + ngrok tunnel, token inline
import subprocess
import sys
import time
import os

# ── Paste your real token here ──
NGROK_AUTHTOKEN = "32YLc6Wskxk6X2N7d1P1DdneMas_7zxms4oHSLcnXhAMfzoD3"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

NGROK = os.path.join(SCRIPT_DIR, "ngrok.exe")
BACKEND = os.path.join(SCRIPT_DIR, "irrigation_backend.py")

if not os.path.isfile(NGROK):
    raise FileNotFoundError(f"ngrok.exe not found at: {NGROK}")
if not os.path.isfile(BACKEND):
    raise FileNotFoundError(f"irrigation_backend.py not found at: {BACKEND}")

# 1. configure token
subprocess.run([NGROK, "config", "add-authtoken", NGROK_AUTHTOKEN], check=True)

# 2. start backend (plain HTTP — SSL disabled)
backend = subprocess.Popen(
    [sys.executable, BACKEND],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

time.sleep(3)

# 3. start ngrok tunnel
ngrok = subprocess.Popen(
    [NGROK, "http", "127.0.0.1:8000"],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

print("\n✅ Backend and ngrok are starting in separate windows.")
print("   Look at the ngrok window for your public https://... URL.")
print("   Press Ctrl+C here to shut both down.\n")

try:
    backend.wait()
except KeyboardInterrupt:
    print("\nStopping...")
    ngrok.terminate()
    backend.terminate()