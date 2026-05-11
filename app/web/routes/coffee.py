"""Coffee blueprint — serves the scenario view and SSE event stream."""

import json
import queue
import threading
import time
from flask import Blueprint, Response, render_template, stream_with_context

coffee_bp = Blueprint(
    "coffee",
    __name__,
    static_folder="../static",
    static_url_path="/static",
    template_folder="../templates",
)

# ---------------------------------------------------------------------------
# SSE event bus (thread-safe queue per client)
# ---------------------------------------------------------------------------

_subscribers: list[queue.SimpleQueue] = []
_subscribers_lock = threading.Lock()


def emit_event(data: dict) -> None:
    """Publish a state-change event to all connected SSE clients.

    Called from the LCD main loop (or stage handlers) via the sse_emit callback.
    """
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
    """Yield SSE-formatted lines from the per-client queue."""
    q: queue.SimpleQueue = queue.SimpleQueue()
    with _subscribers_lock:
        _subscribers.append(q)
    try:
        # Send an initial ping so the browser knows the stream is alive
        yield "data: {\"event\":\"connected\"}\n\n"
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

@coffee_bp.route("/")
def coffee_index():
    return render_template("scenarios/coffee.html")


@coffee_bp.route("/events")
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
