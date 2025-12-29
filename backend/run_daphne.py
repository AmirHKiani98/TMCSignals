import subprocess
import sys
from watchgod import run_process

def run():
    # Start Daphne as a subprocess and wait for it to finish
    # Use the current Python executable to run daphne as a module so we don't
    # rely on an activated shell or PATH having the 'daphne' console script.
    proc = subprocess.Popen([sys.executable, '-m', 'daphne', 'processor.asgi:application', '--port', '8811'])
    try:
        proc.wait()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_process('.', run)