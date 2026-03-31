from flask import Flask, redirect, url_for
from config import Config


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Jinja filter: {{ list | enumerate }} → [(0, item), (1, item), ...]
    app.jinja_env.filters["enumerate"] = enumerate

    from controllers.people import people_bp
    from controllers.social import social_bp
    from controllers.connections import connections_bp

    app.register_blueprint(people_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(connections_bp)

    @app.route("/")
    def index():
        return redirect(url_for("people.list_people"))

    return app
