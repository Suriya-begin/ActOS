import subprocess
import sys
import time
import os

log_file = "e:/ActOS/backend/uvicorn_output.log"
print(f"Starting uvicorn... Logging to {log_file}")

# Clean old log
if os.path.exists(log_file):
    try:
        os.remove(log_file)
    except:
        pass

env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"

# Start uvicorn process
with open(log_file, "w", encoding="utf-8") as f:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=f,
        stderr=subprocess.STDOUT,
        env=env,
        cwd="e:/ActOS/backend"
    )

print(f"Uvicorn process started with PID {proc.pid}")

# Wait for startup
for i in range(15):
    time.sleep(1)
    if os.path.exists(log_file):
        with open(log_file, "r") as lf:
            content = lf.read()
            if "Application startup complete" in content or "Uvicorn running on" in content:
                print("Uvicorn started successfully!")
                break
            if "AddrInUse" in content or "error" in content.lower() or "exception" in content.lower():
                print("Uvicorn encountered an error during startup:")
                print(content)
                break
else:
    print("Startup monitoring timeout. Current log content:")
    if os.path.exists(log_file):
        with open(log_file, "r") as lf:
            print(lf.read())
