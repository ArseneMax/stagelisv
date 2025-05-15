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
    submit = SubmitField('Connexion')

class SignupForm(FlaskForm):
    username = StringField('Nom d’utilisateur', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField('S\'inscrire')

@web_ui.route('/')
@login_required
def index():
    return render_template('index.html', infos=select_all_infos())

@web_ui.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Récupérer tous les utilisateurs et chercher celui avec le bon login
        users = User.get_all_users()
        for user in users:
            if user[1] == username and user[2] == password:
                user_obj = User(user[0], user[1], user[2])
                login_user(user_obj)
                flash('Connexion réussie.')
                return redirect('/')

        flash('Nom d’utilisateur ou mot de passe incorrect.')

    return render_template('login.html', form=form)

@web_ui.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/login')


@web_ui.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Vérifier si username existe déjà
        users = User.get_all_users()
        for user in users:
            if user[1] == username:
                flash('Nom d’utilisateur déjà pris, merci d’en choisir un autre.')
                return render_template('signup.html', form=form)

        res = User.add_user(username, password)

        if res =='oui':
            return redirect('/login')
        else:
            return redirect('/signup')

    return render_template('signup.html', form=form)

