"""ZeroRange web companion — Flask application factory."""

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    from app.web.routes.coffee import coffee_bp
    app.register_blueprint(coffee_bp, url_prefix="/scenarios/coffee")

    from app.web.routes.garage import garage_bp
    app.register_blueprint(garage_bp, url_prefix="/scenarios/garage")

    from app.web.routes.index import index_bp
    app.register_blueprint(index_bp, url_prefix="/")

    return app
