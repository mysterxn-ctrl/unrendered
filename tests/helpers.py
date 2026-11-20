# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
"""Shared test helpers: import paths, an isolated state dir and an offline mock image API."""
import base64
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "unrendered"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

# 1x1 PNG
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC")


class MockAPI:
    """Speaks three common wire shapes: OpenAI-style sync JSON, multipart edits, and submit+poll async."""

    def __init__(self):
        self.requests = []
        self.jobs = {}
        api = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _json(self, obj, code=200):
                data = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                api.requests.append({"path": self.path, "headers": dict(self.headers), "body": body})
                if not (self.headers.get("Authorization") or self.headers.get("x-api-key")):
                    return self._json({"error": "unauthorized"}, 401)
                if self.path == "/v1/images/generations":
                    n = json.loads(body).get("n", 1)
                    return self._json({"data": [{"b64_json": base64.b64encode(PNG).decode(), "revised_prompt": "rp"}] * n})
                if self.path == "/v1/images/edits":
                    return self._json({"data": [{"b64_json": base64.b64encode(PNG).decode()}]})
                if self.path.startswith("/async/"):
                    api.jobs["j1"] = 0
                    return self._json({"request_id": "j1", "status": "queued"})
                return self._json({"error": "not found"}, 404)

            def do_GET(self):
                if self.path == "/v1/models":
                    return self._json({"data": [{"id": "gpt-image-2.6-sunburst"}, {"id": "gpt-image-2.6-flare"}]})
                if self.path == "/async/predictions/j1/result":
                    api.jobs["j1"] += 1
                    if api.jobs["j1"] < 2:
                        return self._json({"status": "processing"})
                    return self._json({"status": "completed", "outputs": [f"{api.base}/files/out.png"]})
                if self.path == "/files/out.png":
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(PNG)))
                    self.end_headers()
                    self.wfile.write(PNG)
                    return
                return self._json({"error": "not found"}, 404)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def temp_state():
    d = tempfile.mkdtemp(prefix="unrendered-test-")
    (Path(d) / "providers").mkdir()
    return Path(d)


def env_with(**kw):
    env = dict(os.environ)
    env.update({k: str(v) for k, v in kw.items()})
    return env
