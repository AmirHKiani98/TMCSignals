#!/usr/bin/env python3
"""
Helper launcher for the TMCGis project.

This script creates a virtual environment (if missing), installs python
dependencies from `requirements.txt`, tries to detect a compatible PyTorch
build for the local CUDA (if present), installs frontend packages (npm),
and launches backend and frontend processes concurrently.

It uses the venv's python executable directly for pip installs to avoid
relying on shell activation commands which are platform-specific.

Run from the repository root:
    python TMCSignal.py

"""
from __future__ import annotations
import os
import sys
import subprocess
import platform
import shutil
import time
import json
import re


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, ".venv")
REQUIREMENTS = os.path.join(SCRIPT_DIR, "requirements.txt")
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
FRONTEND_DIR = os.path.join(SCRIPT_DIR, "frontend")


def venv_python() -> str:
    """Return path to the venv python executable for current platform."""
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def ensure_venv() -> str:
    """Create a virtual environment if it doesn't exist and return python path."""
    if not os.path.isdir(VENV_DIR):
        print("Creating virtual environment at:", VENV_DIR)
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    py = venv_python()
    if not os.path.isfile(py):
        raise FileNotFoundError(f"Expected python in venv at {py} not found")
    return py


def pip_install(venv_py: str, requirements: str) -> None:
    """Install requirements.txt using the venv python's pip."""
    if not os.path.isfile(requirements):
        print("requirements.txt not found, skipping pip install")
        return
    cmd = [venv_py, "-m", "pip", "install", "-r", requirements]
    print("Installing Python requirements (this may take a while)...")
    subprocess.run(cmd, check=True)


def detect_cuda_version() -> tuple[bool, float | None]:
    """Try to detect CUDA version via nvidia-smi. Returns (found, version)."""
    try:
        res = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        out = res.stdout
        m = re.search(r"CUDA Version:\s*(\d+\.\d+)", out)
        if m:
            ver = float(m.group(1))
            return True, ver
    except Exception:
        pass
    return False, None


def fetch_pytorch_install_command() -> dict:
    """Scrape PyTorch previous versions page to collect install commands.

    Returns a mapping like { 'vX.Y.Z': { 'CUDA 11.8': 'pip install ...', 'CPU': 'pip install ...' } }
    This is best-effort and intended to help install a matching wheel.
    """
    import requests
    from bs4 import BeautifulSoup # type: ignore
    url = "https://pytorch.org/get-started/previous-versions/"
    print("Fetching PyTorch versions from", url)
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Failed to fetch PyTorch versions:", e)
        return {}
    soup = BeautifulSoup(r.text, "html.parser")
    data: dict = {}
    # Look for blocks that contain commands (heuristic)
    for h3 in soup.find_all("h3"):
        key = h3.get_text(strip=True)
        if not key:
            continue
        pre = None
        # find the next <pre> in siblings
        sib = h3.find_next_sibling()
        while sib is not None and pre is None:
            pre = sib.find("pre") if hasattr(sib, "find") else None
            sib = sib.find_next_sibling() if hasattr(sib, "find_next_sibling") else None
        if pre:
            text = pre.get_text().strip()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            entries: dict = {}
            # lines often come as alternating key/value pairs
            for i in range(0, len(lines), 2):
                k = lines[i].rstrip(':')
                v = lines[i+1] if i+1 < len(lines) else ''
                entries[k] = v
            data[key] = entries
    return data


def find_compatible_pytorch(pytorch_data: dict, cuda_found: bool, cuda_version: float | None):
    # Try to pick an exact match first, otherwise pick a CPU wheel or closest lower cuda
    keys = sorted(pytorch_data.keys(), reverse=True)
    # collect a CPU entry if present
    cpu_entry = None
    for k in keys:
        for ver, cmd in pytorch_data[k].items():
            if "CPU" in ver or "cpu" in ver.lower():
                cpu_entry = (ver, cmd)
                break
        if cpu_entry:
            break

    # If CUDA not present or not detected, prefer CPU entry
    if not cuda_found or cuda_version is None:
        return cpu_entry if cpu_entry else (None, None)

    # Try exact CUDA match first
    for k in keys:
        for ver, cmd in pytorch_data[k].items():
            m = re.search(r"CUDA\s*(\d+(?:\.\d+)?)", ver)
            if m:
                v = float(m.group(1))
                if abs(v - cuda_version) < 0.01:
                    return ver, cmd

    # Collect candidates <= cuda_version and pick the closest lower (max v)
    candidates_lower = []
    candidates_higher = []
    for k in keys:
        for ver, cmd in pytorch_data[k].items():
            m = re.search(r"CUDA\s*(\d+(?:\.\d+)?)", ver)
            if not m:
                continue
            v = float(m.group(1))
            if v <= cuda_version:
                candidates_lower.append((v, ver, cmd))
            else:
                candidates_higher.append((v, ver, cmd))

    if candidates_lower:
        candidates_lower.sort(key=lambda x: x[0], reverse=True)
        return candidates_lower[0][1], candidates_lower[0][2]

    # If no lower candidate, pick the smallest higher candidate
    if candidates_higher:
        candidates_higher.sort(key=lambda x: x[0])
        return candidates_higher[0][1], candidates_higher[0][2]

    # Fallback to CPU entry if present
    return cpu_entry if cpu_entry else (None, None)


def run_backend(venv_py: str) -> subprocess.Popen:
    """Start backend by running run_daphne.py using the venv python in BACKEND_DIR."""
    if not os.path.isdir(BACKEND_DIR):
        raise FileNotFoundError("backend directory not found")
    cmd = [venv_py, "run_daphne.py"]
    print("Starting backend with:", cmd, "cwd=", BACKEND_DIR)
    p = subprocess.Popen(cmd, cwd=BACKEND_DIR)
    return p


def run_frontend() -> subprocess.Popen | None:
    if not os.path.isdir(FRONTEND_DIR):
        print("Frontend folder not found, skipping frontend start")
        return None

    npm_exe = shutil.which("npm") or shutil.which("npm.cmd") or shutil.which("npx")
    if npm_exe:
        cmd = [npm_exe, "run", "dev"]
        print("Starting frontend with:", cmd, "cwd=", FRONTEND_DIR)
        p = subprocess.Popen(cmd, cwd=FRONTEND_DIR)
        return p

    # fallback to shell invocation which can resolve cmd shims on Windows
    print("npm not found via shutil.which(), attempting shell invocation 'npm run dev'...")
    try:
        p = subprocess.Popen("npm run dev", cwd=FRONTEND_DIR, shell=True)
        return p
    except FileNotFoundError:
        print("npm not available in PATH. Please install Node.js or run the frontend manually:")
        print(f"  cd {FRONTEND_DIR}")
        print("  npm install")
        print("  npm run dev")
        return None


def main():
    vpy = ensure_venv()

    # Install base requirements
    pip_install(vpy, REQUIREMENTS)
    site_packages_path = os.path.join(VENV_DIR, "Lib", "site-packages")  # Windows
    sys.path.insert(0, site_packages_path)
    # Now import requests/bs4 if missing

    # Detect CUDA and attempt to find compatible PyTorch install
    cuda_found, cuda_ver = detect_cuda_version()
    print(f"CUDA detected: {cuda_found}, version: {cuda_ver}")
    pytorch_data = fetch_pytorch_install_command()
    ver, install_cmd = find_compatible_pytorch(pytorch_data, cuda_found, cuda_ver)

    # Install frontend deps (if folder exists)
    if os.path.isdir(FRONTEND_DIR):
        print("Installing frontend npm packages in", FRONTEND_DIR)
        npm_exe = shutil.which("npm") or shutil.which("npm.cmd") or shutil.which("npx")
        try:
            if npm_exe:
                subprocess.run([npm_exe, "install"], cwd=FRONTEND_DIR, check=False)
            else:
                # fallback to shell invocation
                subprocess.run("npm install", cwd=FRONTEND_DIR, shell=True, check=False)
        except Exception as e:
            print("Failed to run npm install:", e)
            print("You can run the following manually:")
            print(f"  cd {FRONTEND_DIR}")
            print("  npm install")
            print("  npm run dev")
            return None

    # Start backend and frontend concurrently
    backend_proc = run_backend(vpy)
    frontend_proc = run_frontend()

    print("Launched backend (pid={})".format(backend_proc.pid if backend_proc else "-"))
    print("Launched frontend (pid={})".format(frontend_proc.pid if frontend_proc else "-"))

    try:
        # Wait for both processes; if frontend is None just wait on backend
        if frontend_proc:
            while True:
                ret_b = backend_proc.poll()
                ret_f = frontend_proc.poll()
                if ret_b is not None or ret_f is not None:
                    print("One of the processes exited: backend->", ret_b, "frontend->", ret_f)
                    break
                time.sleep(1)
        else:
            backend_proc.wait()
    except KeyboardInterrupt:
        print("Interrupted, terminating child processes...")
    finally:
        for p in (backend_proc, frontend_proc):
            if p and p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass


if __name__ == "__main__":
    main()
