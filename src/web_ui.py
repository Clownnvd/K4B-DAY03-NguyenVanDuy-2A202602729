"""Local demo UI: FiProve-inspired shell around the required Lab 3 comparison."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agent_provider import get_provider
from app import run_baseline_chatbot, run_react_agent


HTML = (Path(__file__).with_name("ui_template.html")
        .read_text(encoding="utf-8").encode("utf-8"))


def make_handler(provider):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self._reply(200, HTML, "text/html; charset=utf-8")
            elif self.path == "/health":
                self._json(200, {"status": "ok", "model": provider.model_name,
                                 "live_api": provider.is_live})
            else:
                self._json(404, {"error": "Not found"})

        def do_POST(self):
            if self.path != "/api/compare":
                self._json(404, {"error": "Not found"})
                return
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 10000:
                self._json(400, {"error": "Invalid request size"})
                return
            try:
                payload = json.loads(self.rfile.read(size))
                query = payload.get("question", "").strip()
                if not 1 <= len(query) <= 500:
                    raise ValueError("Câu hỏi phải dài 1–500 ký tự.")
                baseline = run_baseline_chatbot(query, provider)
                agent = run_react_agent(query, provider)
                self._json(200, {"baseline": baseline, "agent": agent})
            except (ValueError, json.JSONDecodeError) as exc:
                self._json(400, {"error": str(exc)})
            except Exception as exc:
                self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

        def _json(self, status, data):
            self._reply(status, json.dumps(data, ensure_ascii=False).encode("utf-8"),
                        "application/json; charset=utf-8")

        def _reply(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    provider = get_provider(mock=args.mock)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(provider))
    print(f"Demo UI: http://127.0.0.1:{args.port} | {provider.model_name} "
          f"| live_api={provider.is_live}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
