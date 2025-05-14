from flask import Flask
from flask_login import LoginManager

from sitestage.fonction import User

login_manager = LoginManager()

def create_app():

    app = Flask(__name__)

    app.config.from_prefixed_env(prefix='ARCHILOG_FLASK')

    from .app import web_ui

    app.register_blueprint(web_ui)

    login_manager.init_app(app)
    login_manager.login_view = 'web_ui.login'

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)