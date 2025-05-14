from flask import Flask

def create_app():

    app = Flask(__name__)

    app.config.from_prefixed_env(prefix='ARCHILOG_FLASK')

    from .app import web_ui

    app.register_blueprint(web_ui)


    return app