"""Root index blueprint — lists all available scenarios."""

from flask import Blueprint, render_template_string

index_bp = Blueprint("index", __name__)

_INDEX_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ZeroRange</title>
<style>
  :root{--bg:#0e0e0e;--fg:#f4f1ec;--accent:#ff6a00}
  body{background:var(--bg);color:var(--fg);font-family:monospace;padding:2rem;margin:0}
  h1{color:var(--accent);letter-spacing:.1em}
  .scenarios{display:flex;flex-wrap:wrap;gap:1.5rem;margin-top:2rem}
  .card{border:1px solid var(--accent);border-radius:6px;padding:1.5rem;width:200px;
        text-decoration:none;color:var(--fg);transition:background .2s}
  .card:hover{background:#1a1a1a}
  .card svg{display:block;margin:0 auto 1rem}
  .card h2{font-size:1rem;text-align:center;margin:0}
</style>
</head>
<body>
<h1>ZeroRange</h1>
<p>Select a training scenario:</p>
<div class="scenarios">
  <a class="card" href="/scenarios/coffee/">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
      <use href="/scenarios/coffee/static/scenarios/coffee/logo.svg#icon"/>
    </svg>
    <h2>Coffee</h2>
  </a>
  <a class="card" href="/scenarios/garage/">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
      <use href="/scenarios/garage/static/scenarios/garage/logo.svg#icon"/>
    </svg>
    <h2>Garage</h2>
  </a>
</div>
</body>
</html>"""


@index_bp.route("/")
def index():
    return render_template_string(_INDEX_TMPL)
