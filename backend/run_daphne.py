import subprocess
from watchgod import run_process

def run():
    # Start Daphne as a subprocess and wait for it to finish
    proc = subprocess.Popen(['daphne', 'processor.asgi:application', '--port', '8811'])
    try:
        proc.wait()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_process('.', run)