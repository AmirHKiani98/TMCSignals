#!/bin/bash

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start backend in a new terminal
start cmd.exe //k "call \"$SCRIPT_DIR\\.venv\\Scripts\\activate\" && cd /d \"$SCRIPT_DIR\\backend\" && python run_daphne.py"

# Start frontend in a new terminal
start cmd.exe //k "cd /d \"$SCRIPT_DIR\\frontend\" && npm run dev"
