"""Garage blueprint — serves the scenario view and SSE event stream."""

import json
import queue
import threading
import time
from flask import Blueprint, Response, render_template, request, stream_with_context

garage_bp = Blueprint(
    "garage",
    __name__,
    static_folder="../static",
    static_url_path="/static",
    template_folder="../templates",
)

# ---------------------------------------------------------------------------
# SSE event bus
# ---------------------------------------------------------------------------

_subscribers: list = []
_subscribers_lock = threading.Lock()


def emit_event(data: dict) -> None:
    """Publish a state-change event to all connected SSE clients."""
    payload = json.dumps(data)
    with _subscribers_lock:
        dead = []
        for q in _subscribers:
            try:
                q.put_nowait(payload)
            except Exception:
                dead.append(q)
        for q in dead:
            _subscribers.remove(q)


def _sse_generator():
    q: queue.SimpleQueue = queue.SimpleQueue()
    with _subscribers_lock:
        _subscribers.append(q)
    try:
        yield 'data: {"event":"connected"}\n\n'
        while True:
            try:
                payload = q.get(timeout=25)
                yield f"data: {payload}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"
    finally:
        with _subscribers_lock:
            try:
                _subscribers.remove(q)
            except ValueError:
                pass


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@garage_bp.route("/")
def garage_index():
    return render_template("scenarios/garage.html")


@garage_bp.route("/debug/send-press", methods=["POST"])
def debug_send_press():
    """[DEBUG] Trigger a synthetic press_emitted event (TX only, no score change)."""
    emit_event({"event": "press_emitted", "counter": 0, "debug": True})
    return "", 204


@garage_bp.route("/events")
def events():
    """Server-Sent Events endpoint for live stage transitions."""
    return Response(
        stream_with_context(_sse_generator()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
