"""Interactive Web Demo for SlothSwitch.

Runs a zero-dependency local HTTP server providing a modern UI to test
the SlothSwitch routing pipeline interactively in real time.
"""

from __future__ import annotations

import json
import logging
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from slothswitch.api import create_router
from slothswitch.schemas import RoutingRequest

logger = logging.getLogger("slothswitch.demo")
PORT = 8080

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SlothSwitch — Interactive AI Routing Demo</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(18, 24, 38, 0.7);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #6366f1;
      --primary-glow: rgba(99, 102, 241, 0.25);
      --accent: #06b6d4;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --fast-path: #10b981;
      --small-llm: #3b82f6;
      --large-llm: #a855f7;
      --clarify: #f59e0b;
      --fallback: #ef4444;
      --human-review: #ec4899;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, var(--bg) 60%);
      color: var(--text-main);
      min-height: 100vh;
      padding: 2rem 1rem;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .container {
      width: 100%;
      max-width: 960px;
    }

    header {
      text-align: center;
      margin-bottom: 2.5rem;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      color: #a5b4fc;
      margin-bottom: 1rem;
    }
    h1 {
      font-size: 2.75rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      margin-bottom: 0.75rem;
      background: linear-gradient(135deg, #ffffff 40%, #a5b4fc 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    p.subtitle {
      color: var(--text-muted);
      font-size: 1.1rem;
      max-width: 600px;
      margin: 0 auto;
    }

    .card {
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 1.75rem;
      box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
      margin-bottom: 1.5rem;
    }

    .samples-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }
    .sample-btn {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      font-size: 0.78rem;
      font-weight: 500;
      padding: 0.4rem 0.75rem;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .sample-btn:hover {
      background: rgba(99, 102, 241, 0.15);
      color: #fff;
      border-color: rgba(99, 102, 241, 0.4);
    }

    textarea {
      width: 100%;
      height: 110px;
      background: rgba(10, 15, 26, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 10px;
      padding: 1rem;
      color: #fff;
      font-family: inherit;
      font-size: 0.95rem;
      resize: vertical;
      outline: none;
      transition: border-color 0.2s;
    }
    textarea:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--primary-glow);
    }

    .action-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 1rem;
    }
    .btn-route {
      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      color: #fff;
      border: none;
      font-weight: 600;
      font-size: 0.95rem;
      padding: 0.75rem 1.75rem;
      border-radius: 10px;
      cursor: pointer;
      box-shadow: 0 4px 14px 0 var(--primary-glow);
      transition: transform 0.1s, opacity 0.2s;
    }
    .btn-route:hover { opacity: 0.95; transform: translateY(-1px); }
    .btn-route:active { transform: translateY(0); }

    .result-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.25rem;
      margin-top: 1rem;
    }
    @media (max-width: 768px) {
      .result-grid { grid-template-columns: 1fr; }
    }

    .metric-box {
      background: rgba(10, 15, 26, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
    }
    .metric-title {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 0.5rem;
    }
    .route-pill {
      display: inline-block;
      font-weight: 700;
      font-size: 1.1rem;
      padding: 0.25rem 0.75rem;
      border-radius: 8px;
      color: #fff;
    }

    .bg-FAST_PATH { background: var(--fast-path); }
    .bg-SMALL_LLM { background: var(--small-llm); }
    .bg-LARGE_LLM { background: var(--large-llm); }
    .bg-CLARIFY { background: var(--clarify); }
    .bg-FALLBACK { background: var(--fallback); }
    .bg-HUMAN_REVIEW { background: var(--human-review); }

    pre {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      background: rgba(0, 0, 0, 0.3);
      padding: 1rem;
      border-radius: 8px;
      overflow-x: auto;
      color: #e2e8f0;
      line-height: 1.5;
    }

    .hidden { display: none; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">SlothSwitch v0.1.0 • Intelligent AI Router</div>
      <h1>Stop spending big-model compute on small decisions.</h1>
      <p class="subtitle">Inspect requests, select optimal processing tiers, enforce deterministic safety gates, and measure savings.</p>
    </header>

    <div class="card">
      <div class="samples-bar">
        <span style="font-size: 0.8rem; color: var(--text-muted); align-self: center;">Try sample:</span>
        <button class="sample-btn" onclick="setQuery('Where can I download my latest invoice?')">Simple FAQ (Fast Path)</button>
        <button class="sample-btn" onclick="setQuery('How do I update my profile notification settings?')">Routine Inquiry (Small LLM)</button>
        <button class="sample-btn" onclick="setQuery('We are seeing distributed deadlocks between Kafka consumers and our PostgreSQL outbox table during rebalancing. Here is our traceback: ```\nError: deadlock detected\n```')">Complex Architecture (Large LLM)</button>
        <button class="sample-btn" onclick="setQuery('Help')">Unclear / Fragment (Clarify)</button>
        <button class="sample-btn" onclick="setQuery('Under GDPR Article 17, delete all my personal data and confirm with an audit record.')">Compliance / Legal (Human Review)</button>
      </div>

      <textarea id="queryInput" placeholder="Enter a customer support request, technical inquiry, or message..."></textarea>

      <div class="action-row">
        <label style="font-size: 0.85rem; color: var(--text-muted); display: flex; align-items: center; gap: 0.4rem; cursor: pointer;">
          <input type="checkbox" id="baselineToggle"> Compare against Fixed Large LLM Baseline
        </label>
        <button class="btn-route" onclick="submitRouting()">Route Request</button>
      </div>
    </div>

    <div id="resultsCard" class="card hidden">
      <h3 style="font-size: 1.1rem; margin-bottom: 1rem;">Routing Outcome</h3>
      <div class="result-grid">
        <div class="metric-box">
          <div class="metric-title">Selected Processing Path</div>
          <div id="routePill" class="route-pill bg-FAST_PATH">FAST_PATH</div>
          <div id="routeReasoning" style="margin-top: 0.75rem; font-size: 0.85rem; color: var(--text-muted);"></div>
        </div>

        <div class="metric-box">
          <div class="metric-title">Policy & Telemetry</div>
          <div style="font-size: 0.9rem; line-height: 1.8;">
            <div><strong>Policy Gate:</strong> <span id="policyGateStatus" style="color: var(--fast-path);">ACCEPTED</span></div>
            <div><strong>Confidence:</strong> <span id="confidenceVal">0.92</span></div>
            <div><strong>Routing Overhead:</strong> <span id="latencyVal">0.3 ms</span></div>
            <div><strong>Estimated Cost:</strong> <span id="costVal">$0.00000 USD</span></div>
          </div>
        </div>
      </div>

      <div class="metric-box" style="margin-top: 1.25rem;">
        <div class="metric-title">Dispatched Task Execution</div>
        <div id="taskOutput" style="font-size: 0.95rem; line-height: 1.6; color: #f1f5f9;"></div>
      </div>

      <div class="metric-box" style="margin-top: 1.25rem;">
        <div class="metric-title">Raw Telemetry Record (JSON)</div>
        <pre><code id="jsonRecord"></code></pre>
      </div>
    </div>
  </div>

  <script>
    function setQuery(text) {
      document.getElementById('queryInput').value = text;
    }

    async function submitRouting() {
      const content = document.getElementById('queryInput').value.trim();
      if (!content) return alert('Please enter a request to route.');

      const baseline = document.getElementById('baselineToggle').checked;

      try {
        const res = await fetch('/api/route', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content, baseline })
        });
        const data = await res.json();
        renderResult(data);
      } catch (err) {
        alert('Routing request failed: ' + err);
      }
    }

    function renderResult(data) {
      const dec = data.route_decision;
      const res = data.task_result;

      document.getElementById('resultsCard').classList.remove('hidden');

      const pill = document.getElementById('routePill');
      pill.textContent = dec.chosen_route;
      pill.className = 'route-pill bg-' + dec.chosen_route;

      document.getElementById('routeReasoning').textContent = dec.reasoning || 'Rule match';
      
      const gate = document.getElementById('policyGateStatus');
      if (dec.accepted) {
        gate.textContent = 'AUTHORIZED';
        gate.style.color = 'var(--fast-path)';
      } else {
        gate.textContent = 'DIVERTED (' + (dec.fallback_reason || 'Policy rule') + ')';
        gate.style.color = 'var(--fallback)';
      }

      document.getElementById('confidenceVal').textContent = dec.confidence ? dec.confidence.toFixed(2) : 'N/A';
      document.getElementById('latencyVal').textContent = (dec.latency_ms || 0.1).toFixed(2) + ' ms';
      document.getElementById('costVal').textContent = '$' + ((res && res.estimated_cost_usd) || 0).toFixed(5) + ' USD';
      document.getElementById('taskOutput').textContent = (res && res.output) || 'No output produced';
      document.getElementById('jsonRecord').textContent = JSON.stringify(data, null, 2);
    }
  </script>
</body>
</html>
"""


class DemoRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for the web demo."""

    router = None
    baseline_router = None

    @classmethod
    def setup_routers(cls) -> None:
        if cls.router is None:
            cls.router = create_router("config/routing.yaml")
        if cls.baseline_router is None:
            cls.baseline_router = create_router("config/routing.yaml", baseline_mode=True)

    def do_GET(self) -> None:
        """Serve the main demo single-page application."""
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        """Handle JSON routing requests."""
        if self.path == "/api/route":
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            content = payload.get("content", "")
            use_baseline = payload.get("baseline", False)

            active_router = self.baseline_router if use_baseline else self.router
            req = RoutingRequest(
                request_id=str(uuid.uuid4()),
                content=content,
            )
            record = active_router.process(req)

            resp_payload = {
                "request_id": record.request_id,
                "route_decision": record.route_decision.model_dump(),
                "task_result": record.task_result.model_dump() if record.task_result else None,
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress spammy HTTP server logging in stdout
        pass


def run_demo(port: int = PORT) -> None:
    """Run the interactive web demo server."""
    DemoRequestHandler.setup_routers()
    server = HTTPServer(("127.0.0.1", port), DemoRequestHandler)
    print(f"\n=======================================================")
    print(f"  SlothSwitch Web Demo Server Running!")
    print(f"  Open in your browser: http://localhost:{port}")
    print(f"=======================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping demo server...")
        server.server_close()


if __name__ == "__main__":
    run_demo()
