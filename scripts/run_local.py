"""Run both local services together; stop owned children on failure or Ctrl+C."""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = "http://127.0.0.1:5500"
BACKEND = "http://127.0.0.1:8001"


class LocalProblem(Exception):
    pass


def require_free_ports(ports):
    for port in ports:
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                raise LocalProblem(f"Port {port} is already in use. No existing process was stopped. Run --check or close the other server yourself.")


def check_services():
    """Readiness, including CORS and the frontend source; never calls a provider."""
    request = Request(f"{BACKEND}/api/health", headers={"Origin": FRONTEND})
    with urlopen(request, timeout=2) as response:
        if json.load(response) != {"status": "ok"}:
            raise LocalProblem("Backend health response is not ready.")
        if response.headers.get("Access-Control-Allow-Origin") != FRONTEND:
            raise LocalProblem("Backend CORS does not allow http://127.0.0.1:5500. Check CORS_ORIGINS in backend/.env.")
    with urlopen(f"{BACKEND}/openapi.json", timeout=2) as response:
        paths = json.load(response).get("paths", {})
        if not all(path in paths for path in ("/api/students/import", "/api/geocode/retry", "/api/groups/generate", "/api/groups/export")):
            raise LocalProblem("Backend is not the expected WebGIS application.")
    with urlopen(FRONTEND, timeout=2) as response:
        if response.read() != (ROOT / "frontend/index.html").read_bytes():
            raise LocalProblem("Port 5500 is not serving this project's frontend.")
    with urlopen(f"{FRONTEND}/js/api.js", timeout=2) as response:
        if response.read() != (ROOT / "frontend/js/api.js").read_bytes():
            raise LocalProblem("Frontend JavaScript is missing or from another project.")
    return True


def supervise(commands, logs, readiness, *, spawn=subprocess.Popen, interval=.5, startup_timeout=90):
    children = []
    try:
        for command, log in zip(commands, logs):
            children.append(spawn(command, cwd=ROOT, stdout=log, stderr=log))
        print(f"Starting both services (up to {startup_timeout:g}s). Logs: .local-tests/local-server/", flush=True)
        deadline = time.monotonic() + startup_timeout
        ready = False
        last_error = "Services are not ready."
        while True:
            for index, child in enumerate(children):
                if child.poll() is not None:
                    raise LocalProblem(f"Service {index + 1} exited (code {child.returncode}). Check .local-tests/local-server logs.")
            if not ready:
                try:
                    ready = bool(readiness())
                except Exception as exc:
                    # Only local status/configuration errors; no provider URLs or API keys.
                    last_error = str(exc) if isinstance(exc, LocalProblem) else "Local HTTP connection is not ready."
                if ready:
                    print(f"READY: {FRONTEND} | API: {BACKEND}/docs", flush=True)
                    print("Keep this runner open. Press Ctrl+C to stop both services.", flush=True)
                elif time.monotonic() >= deadline:
                    raise LocalProblem(f"Startup timed out. {last_error}")
            time.sleep(interval)
    except OSError:
        raise LocalProblem("Cannot start local Python services. Check the virtual environment and dependencies.") from None
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only frontend/backend/CORS check")
    args = parser.parse_args()
    try:
        if args.check:
            try:
                check_services()
            except LocalProblem:
                raise
            except Exception:
                raise LocalProblem("WebGIS is not reachable at ports 8001/5500. Run start-webgis.cmd and check its logs.") from None
            print(f"READY: {FRONTEND} | backend/CORS/frontend assets OK")
            return 0
        require_free_ports([8001, 5500])
        output = ROOT / ".local-tests/local-server"
        output.mkdir(parents=True, exist_ok=True)
        commands = [
            [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8001"],
            [sys.executable, "-m", "http.server", "5500", "--bind", "127.0.0.1", "--directory", "frontend"],
        ]
        with (output / "backend.log").open("a", encoding="utf8") as backend_log, (output / "frontend.log").open("a", encoding="utf8") as frontend_log:
            supervise(commands, [backend_log, frontend_log], check_services)
    except KeyboardInterrupt:
        print("Stopped both local services.")
        return 0
    except LocalProblem as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
