from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

from ..fonction import User

login_manager = LoginManager()

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config.from_prefixed_env(prefix='LISV_FLASK')
    app.config.update(
        SECRET_KEY='temp'
    )
    print('SECRET_KEY:', app.config.get('SECRET_KEY'))  # Ajout utile pour debug

    from .app import web_ui
    app.register_blueprint(web_ui)

    login_manager.init_app(app)
    login_manager.login_view = 'web_ui.login'

    return app



@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)