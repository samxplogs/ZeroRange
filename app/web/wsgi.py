#!/usr/bin/env python3
"""WSGI entry point for ZeroRange web companion."""

from app.web import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False, threaded=True)
