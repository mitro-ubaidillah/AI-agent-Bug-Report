import subprocess
import sys
import time
import signal
from pathlib import Path
import threading

# ANSI Colors for beautiful prefix logs
COLORS = {
    "TICKET": "\033[94m[Ticket App 8000]\033[0m",
    "TRANSFER": "\033[92m[Transfer App 8001]\033[0m",
    "FRD": "\033[93m[FRD App 8002]\033[0m",
    "MIDDLEWARE": "\033[95m[Middleware App 8003]\033[0m",
    "SYSTEM": "\033[96m[System Orchestrator]\033[0m",
}

processes = []
threads = []
running = True


def log_stream(proc, prefix):
    """Read logs from a process and print with a colored prefix."""
    while running:
        line = proc.stdout.readline()
        if not line:
            break
        # Print with colors
        sys.stdout.write(f"{prefix} {line}")
        sys.stdout.flush()


def shutdown_servers(signum=None, frame=None):
    """Gracefully terminate all running subprocesses."""
    global running
    if not running:
        return
    running = False
    print(f"\n{COLORS['SYSTEM']} Shutting down all servers gracefully...")
    for name, proc in processes:
        print(f"{COLORS['SYSTEM']} Terminating {name}...")
        proc.terminate()
    
    # Wait for processes to exit
    for name, proc in processes:
        try:
            proc.wait(timeout=3)
            print(f"{COLORS['SYSTEM']} {name} stopped.")
        except subprocess.TimeoutExpired:
            print(f"{COLORS['SYSTEM']} Force killing {name}...")
            proc.kill()
            proc.wait()
    
    print(f"{COLORS['SYSTEM']} All servers shut down. Goodbye!")
    sys.exit(0)


def main():
    # Register shutdown signals
    signal.signal(signal.SIGINT, shutdown_servers)
    signal.signal(signal.SIGTERM, shutdown_servers)

    base_dir = Path(__file__).parent.resolve()
    apps = [
        ("Ticket App", base_dir / "apps" / "ticket_app", 8000, COLORS["TICKET"]),
        ("Transfer App", base_dir / "apps" / "transfer_app", 8001, COLORS["TRANSFER"]),
        ("FRD App", base_dir / "apps" / "frd_app", 8002, COLORS["FRD"]),
        ("Middleware App", base_dir / "apps" / "middleware_app", 8003, COLORS["MIDDLEWARE"]),
    ]

    print(f"{COLORS['SYSTEM']} Starting all microservice servers...")

    for name, cwd_path, port, prefix in apps:
        if not cwd_path.exists():
            print(f"{COLORS['SYSTEM']} Error: Directory {cwd_path} does not exist!")
            shutdown_servers()

        print(f"{COLORS['SYSTEM']} Starting {name} on port {port} in {cwd_path.name}...")
        # Run uvicorn as a module using the current python executable
        cmd = [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port), "--host", "127.0.0.1"]
        
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        processes.append((name, proc))

        # Start thread to read stdout
        t = threading.Thread(target=log_stream, args=(proc, prefix), daemon=True)
        t.start()
        threads.append(t)
        
        # Give a small delay to prevent ports overlapping on startup race conditions
        time.sleep(0.5)

    print(f"{COLORS['SYSTEM']} All 4 servers are up and running!")
    print(f"{COLORS['SYSTEM']} - Ticket App: http://127.0.0.1:8000")
    print(f"{COLORS['SYSTEM']} - Transfer App: http://127.0.0.1:8001")
    print(f"{COLORS['SYSTEM']} - FRD App: http://127.0.0.1:8002")
    print(f"{COLORS['SYSTEM']} - Middleware App: http://127.0.0.1:8003")
    print(f"{COLORS['SYSTEM']} Press Ctrl+C to shut down all servers.")

    # Keep the orchestrator main thread alive
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            shutdown_servers()


if __name__ == "__main__":
    main()
