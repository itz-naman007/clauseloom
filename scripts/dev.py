"""Start the API and Vite together; Ctrl-C stops both."""

import os
import subprocess
import sys

os.environ.setdefault("LLM_BASE_URL", "http://127.0.0.1:11434")
api = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        "backend",
        "--host",
        "127.0.0.1",
        "--port",
        "8080",
        "--no-access-log",
    ]
)
ui = subprocess.Popen(["npm.cmd" if os.name == "nt" else "npm", "run", "dev"], cwd="frontend")
try:
    api.wait()
except KeyboardInterrupt:
    pass
finally:
    ui.terminate()
    api.terminate()
