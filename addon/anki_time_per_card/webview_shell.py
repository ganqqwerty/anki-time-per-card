"""HTML assembly for the Svelte Anki WebView."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def render_webview_content(
    *,
    initial_state_name: str,
    initial_state: dict[str, Any],
    bundle_js: Path,
    bundle_css: Path,
    scope: str,
) -> tuple[str, str]:
    """Render body/head fragments for ``AnkiWebView.stdHtml``."""

    initial_state_json = escape_embedded_json(initial_state)
    css = _bundle_text_or_placeholder(bundle_css, scope=scope, kind="CSS")
    js = _bundle_text_or_placeholder(bundle_js, scope=scope, kind="JavaScript")
    head = f"""<meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>{css}</style>"""
    body = f"""
  <div id="app"></div>
  <script>window.{initial_state_name} = {initial_state_json};</script>
  <script>{frontend_error_reporter(scope)}</script>
  <script>{js}</script>"""
    return body, head


def escape_embedded_json(value: dict[str, Any] | str) -> str:
    raw = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))
    return raw.replace("</script>", "<\\/script>")


def frontend_error_reporter(scope: str) -> str:
    scope_json = json.dumps(scope)
    return f"""
window.__timePerCardBridge = window.__timePerCardBridge || function(command, payload) {{
  if (typeof pycmd === "function") {{
    pycmd("bridge:" + JSON.stringify({{ command: command, payload: payload }}));
  }}
}};
window.addEventListener("error", function(event) {{
  window.__timePerCardBridge("frontend.log", {{
    scope: {scope_json},
    level: "error",
    message: (event.message || "unknown") + " @ " + (event.filename || "?") + ":" + (event.lineno || "?"),
    stack: event.error && event.error.stack ? String(event.error.stack) : ""
  }});
}});
window.addEventListener("unhandledrejection", function(event) {{
  var reason = event.reason || "unknown";
  window.__timePerCardBridge("frontend.log", {{
    scope: {scope_json},
    level: "error",
    message: "Unhandled rejection: " + String(reason && reason.message ? reason.message : reason),
    stack: reason && reason.stack ? String(reason.stack) : ""
  }});
}});
"""


def _bundle_text_or_placeholder(path: Path, *, scope: str, kind: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")

    message = f"{scope} WebView {kind} bundle is missing: {path.name}"
    logger.error(message)
    if kind == "CSS":
        return ""
    return f"document.getElementById('app').textContent = {json.dumps(message)};"
