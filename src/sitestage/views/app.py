from MySQLdb import IntegrityError
from flask import render_template, Blueprint, flash, redirect
import logging
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from sitestage.fonction import *


web_ui= Blueprint('web_ui', __name__, url_prefix="/")


auth = HTTPBasicAuth()
users = {
    "admin": [generate_password_hash("admin"), ["admin", "user"]],
    "user": [generate_password_hash("user"), ["user"]]
}
@web_ui.route('/')
@auth.login_required
def index():

    return render_template('index.html', infos=select_all_infos())

#auth#
@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username)[0], password):
        return username
    return None

@auth.get_user_roles
def get_user_roles(username):
    return users.get(username)[1]

#error#
@web_ui.errorhandler(IntegrityError)
def handle_internal_error(error):
    flash("Erreur interne du serveur", "error")
    logging.exception(error)
    return redirect("/")


@web_ui.errorhandler(500)
def handle_internal_error(error):
    flash("Erreur interne du serveur", "error")
    logging.exception(error)
    return redirect("/")