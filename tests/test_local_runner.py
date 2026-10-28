import importlib.util
import socket
import subprocess
import sys
import time
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location("local_runner", ROOT / "scripts/run_local.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_occupied_port_is_reported_without_stopping_foreign_server(runner):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0)); listener.listen()
        port = listener.getsockname()[1]
        with pytest.raises(runner.LocalProblem, match=str(port)):
            runner.require_free_ports([port])
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            pass


def test_failed_child_stops_sibling_and_reports_failure(runner, tmp_path):
    children = []
    def spawn(command, **kwargs):
        process = subprocess.Popen(command, **kwargs)
        children.append(process)
        return process
    with (tmp_path / "children.log").open("w") as log:
        with pytest.raises(runner.LocalProblem):
            runner.supervise([
                [sys.executable, "-c", "import time; time.sleep(60)"],
                [sys.executable, "-c", "raise SystemExit(7)"],
            ], [log, log], lambda: False, spawn=spawn, interval=0.02, startup_timeout=3)
    assert len(children) == 2 and all(child.poll() is not None for child in children)


def test_startup_failure_or_timeout_does_not_leave_orphan(runner, tmp_path):
    children = []
    def spawn(command, **kwargs):
        if children:
            raise OSError("synthetic startup failure")
        process = subprocess.Popen(command, **kwargs); children.append(process)
        return process
    with (tmp_path / "children.log").open("w") as log:
        with pytest.raises(runner.LocalProblem):
            runner.supervise([[sys.executable, "-c", "import time; time.sleep(60)"]] * 2,
                             [log, log], lambda: False, spawn=spawn, interval=0.02, startup_timeout=.2)
    assert children and children[0].poll() is not None


@pytest.mark.parametrize("failure", [None, "cors", "frontend", "javascript", "backend"])
def test_readiness_checks_application_frontend_assets_and_cors(runner, monkeypatch, failure):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            self.send_response(200)
            if failure != "cors":
                self.send_header("Access-Control-Allow-Origin", runner.FRONTEND)
            self.end_headers()
            if self.path == "/api/health":
                body = json.dumps({"status": "ok"}).encode()
            elif self.path == "/openapi.json":
                paths = {} if failure == "backend" else {path: {} for path in ("/api/students/import", "/api/geocode/retry", "/api/groups/generate", "/api/groups/export")}
                body = json.dumps({"paths": paths}).encode()
            elif self.path == "/":
                body = b"another application" if failure == "frontend" else (ROOT / "frontend/index.html").read_bytes()
            else:
                body = b"another script" if failure == "javascript" else (ROOT / "frontend/js/api.js").read_bytes()
            self.wfile.write(body)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    url = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setattr(runner, "FRONTEND", url)
    monkeypatch.setattr(runner, "BACKEND", url)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        if failure:
            with pytest.raises(runner.LocalProblem):
                runner.check_services()
        else:
            assert runner.check_services()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)


def test_unready_startup_timeout_cleans_children(runner, tmp_path):
    children = []
    def spawn(command, **kwargs):
        process = subprocess.Popen(command, **kwargs); children.append(process)
        return process
    with (tmp_path / "children.log").open("w") as log:
        with pytest.raises(runner.LocalProblem, match="timed out"):
            runner.supervise([[sys.executable, "-c", "import time; time.sleep(60)"]] * 2,
                             [log, log], lambda: False, spawn=spawn, interval=.02, startup_timeout=.1)
    assert len(children) == 2 and all(child.poll() is not None for child in children)
