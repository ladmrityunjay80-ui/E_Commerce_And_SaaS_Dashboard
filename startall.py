#!/usr/bin/env python3
"""
Start script to run both backend and frontend servers simultaneously.
This script starts the FastAPI backend and Vite frontend development servers.
"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def print_banner():
    """Print a banner for the startup script."""
    print("=" * 60)
    print("  SaaS Admin Dashboard - Development Server")
    print("=" * 60)
    print()


def check_node():
    """Check if Node.js is installed."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Node.js found: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    print("✗ Node.js not found. Please install Node.js to run the frontend.")
    return False


def check_python():
    """Check if Python is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Python found: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    print("✗ Python not found.")
    return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    # Check Python
    if not check_python():
        return False
    
    # Check Node.js
    if not check_node():
        return False
    
    # Check if backend requirements are installed
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import fastapi, uvicorn, sqlalchemy"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ Backend dependencies installed")
        else:
            print("⚠ Backend dependencies may not be fully installed")
            print("  Run: cd backend && pip install -r requirements.txt")
    except subprocess.TimeoutExpired:
        print("⚠ Could not verify backend dependencies")
    
    # Check if frontend node_modules exists
    if (FRONTEND_DIR / "node_modules").exists():
        print("✓ Frontend dependencies installed")
    else:
        print("⚠ Frontend dependencies not installed")
        print("  Run: cd frontend && npm install")
    
    print()
    return True


def start_backend():
    """Start the FastAPI backend server."""
    print("Starting FastAPI backend server...")
    print(f"  Directory: {BACKEND_DIR}")
    print(f"  URL: http://localhost:8000")
    print(f"  API Docs: http://localhost:8000/docs")
    print()
    
    # Change to backend directory
    os.chdir(BACKEND_DIR)
    
    # Start uvicorn server
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    return backend_process


def start_frontend():
    """Start the Vite frontend development server."""
    print("Starting Vite frontend development server...")
    print(f"  Directory: {FRONTEND_DIR}")
    print(f"  URL: http://localhost:3000")
    print()
    
    # Change to frontend directory
    os.chdir(FRONTEND_DIR)
    
    # Start npm dev server
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    return frontend_process


def monitor_processes(backend_process, frontend_process):
    """Monitor the running processes and handle shutdown."""
    processes = {
        "Backend": backend_process,
        "Frontend": frontend_process
    }
    
    print("=" * 60)
    print("  Both servers are running!")
    print("=" * 60)
    print()
    print("Backend:  http://localhost:8000")
    print("Frontend: http://localhost:3000")
    print("API Docs: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop all servers")
    print()
    
    try:
        # Monitor processes
        while True:
            # Check if any process has died
            for name, process in processes.items():
                if process.poll() is not None:
                    print(f"⚠ {name} process has stopped unexpectedly")
                    return False
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        for name, process in processes.items():
            if process.poll() is None:
                print(f"Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"Force killing {name}...")
                    process.kill()
        
        print("All servers stopped.")
        return True


def main():
    """Main function to start both servers."""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("Please install the required dependencies and try again.")
        sys.exit(1)
    
    # Start backend
    try:
        backend_process = start_backend()
        time.sleep(2)  # Give backend time to start
    except Exception as e:
        print(f"Failed to start backend: {e}")
        sys.exit(1)
    
    # Start frontend
    try:
        frontend_process = start_frontend()
        time.sleep(2)  # Give frontend time to start
    except Exception as e:
        print(f"Failed to start frontend: {e}")
        backend_process.terminate()
        sys.exit(1)
    
    # Monitor processes
    monitor_processes(backend_process, frontend_process)


if __name__ == "__main__":
    main()
