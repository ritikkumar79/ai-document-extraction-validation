import subprocess, sys
subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--reload"])
