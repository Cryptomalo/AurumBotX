import importlib.util
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.core.trading_engine_usdt_sqlalchemy import TradingEngineUSDT

FLASK_AVAILABLE = importlib.util.find_spec("flask") is not None

# Inizializza il trading engine (in un'applicazione reale, lo faresti in modo più strutturato)
engine = TradingEngineUSDT()


def _run_flask(port: int) -> None:
    from flask import Flask, jsonify, request

    app = Flask(__name__)

    @app.route('/api/status')
    def status():
        return jsonify({'status': 'online'})

    @app.route("/api/balance")
    def get_balance():
        balance = engine.get_balance()
        return jsonify(balance)

    @app.route('/api/emergency-stop', methods=['POST'])
    def emergency_stop():
        reason = request.json.get('reason', 'Manual stop from API')
        result = engine.emergency_stop(reason=reason)
        return jsonify(result)

    app.run(host='0.0.0.0', port=port)


class SimpleAPIHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status_code: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json({"status": "online", "mode": "simple"})
            return

        if self.path == "/api/balance":
            self._send_json(engine.get_balance())
            return

        self._send_json({"error": "not found"}, status_code=404)

    def do_POST(self):
        if self.path != "/api/emergency-stop":
            self._send_json({"error": "not found"}, status_code=404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        payload = json.loads(body.decode("utf-8") or "{}")
        reason = payload.get("reason", "Manual stop from API")
        result = engine.emergency_stop(reason=reason)
        self._send_json(result)


def _run_simple(port: int) -> None:
    server = HTTPServer(("0.0.0.0", port), SimpleAPIHandler)
    server.serve_forever()


if __name__ == '__main__':
    port = int(os.environ.get("API_SERVER_PORT", "5678"))
    if FLASK_AVAILABLE:
        _run_flask(port)
    else:
        _run_simple(port)
