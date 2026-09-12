#!/usr/bin/env python
"""
Freelenso Local Service Runner (Without Docker)
Usage:
    python run_local.py web             # Run Django monolith on port 8000
    python run_local.py user            # Run User Service on port 8001
    python run_local.py project         # Run Project Service on port 8002
    python run_local.py payment         # Run Payment Service on port 8003
    python run_local.py notification    # Run Notification Service on port 8004
    python run_local.py all             # Run Django and all microservices concurrently
"""

import os
import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent

# Locate venv python if available
VENV_PYTHON = ROOT_DIR / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

SERVICES = {
    "web": {
        "name": "Django Monolith Web App",
        "port": 8000,
        "cwd": ROOT_DIR,
        "cmd": [PYTHON_EXE, "manage.py", "runserver", "0.0.0.0:8000"],
        "url": "http://127.0.0.1:8000/"
    },
    "user": {
        "name": "User Service",
        "port": 8001,
        "cwd": ROOT_DIR / "services" / "user-service",
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001", "--reload"],
        "url": "http://127.0.0.1:8001/docs"
    },
    "project": {
        "name": "Project Service",
        "port": 8002,
        "cwd": ROOT_DIR / "services" / "project-service",
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8002", "--reload"],
        "url": "http://127.0.0.1:8002/docs"
    },
    "payment": {
        "name": "Payment Service",
        "port": 8003,
        "cwd": ROOT_DIR / "services" / "payment-service",
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8003", "--reload"],
        "url": "http://127.0.0.1:8003/docs"
    },
    "notification": {
        "name": "Notification Service",
        "port": 8004,
        "cwd": ROOT_DIR / "services" / "notification-service",
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8004", "--reload"],
        "url": "http://127.0.0.1:8004/docs"
    },
}

def run_single(service_key: str):
    if service_key not in SERVICES:
        print(f"Unknown service: {service_key}")
        print(f"Available: {', '.join(SERVICES.keys())} or 'all'")
        sys.exit(1)
    
    svc = SERVICES[service_key]
    print(f"\n[*] Starting {svc['name']} on {svc['url']} ...\n")
    try:
        subprocess.run(svc["cmd"], cwd=svc["cwd"])
    except KeyboardInterrupt:
        print(f"\nStopped {svc['name']}.")

def run_all():
    processes = []
    print("\n" + "="*60)
    print("[*] Starting Freelenso Services Concurrently:")
    for key, svc in SERVICES.items():
        print(f"  * {svc['name']:<25} -> {svc['url']}")
    print("="*60 + "\n")
    print("Press Ctrl+C to stop all services.\n")
    
    try:
        for key, svc in SERVICES.items():
            p = subprocess.Popen(svc["cmd"], cwd=svc["cwd"])
            processes.append((svc["name"], p))
        
        for name, p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n[*] Stopping all services...")
        for name, p in processes:
            p.terminate()
        for name, p in processes:
            p.wait()
        print("[+] All services stopped.")

if __name__ == "__main__":
    target = sys.argv[1].lower() if len(sys.argv) > 1 else "web"
    if target == "all":
        run_all()
    else:
        run_single(target)
