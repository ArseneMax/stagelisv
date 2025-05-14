import flask
from flask import render_template, Blueprint, flash, redirect
from sitestage.fonction import *
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

from flask_login import LoginManager, login_user, login_required, logout_user

web_ui= Blueprint('web_ui', __name__, url_prefix="/")

class LoginForm(FlaskForm):
    username = StringField('Nom d’utilisateur', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=3, max=50)])


@web_ui.route('/')
@login_required
def index():
    return render_template('index.html', infos=select_all_infos())

@web_ui.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()
    if form.validate_on_submit():

        login_user(user)

        flask.flash('Logged in successfully.')



        return redirect('/')
    return flask.render_template('login.html', form=form)

@web_ui.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/login')

@web_ui.route('/signup')
def signup():
    return 'Signup'

