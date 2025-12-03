#!/bin/bash

# Start backend in a new terminal
start cmd.exe //k "python -m venv .venv & .venv\\Scripts\\activate & pip install -r requirements.txt & cd backend & python run_daphne.py"

# Start frontend in a new terminal
start cmd.exe //k "cd frontend & npm run dev"
