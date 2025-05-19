from flask import render_template, Blueprint, flash, redirect, jsonify, request, url_for
from ..fonction import *
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from ..decorators import *
from flask_login import login_user, login_required, logout_user

web_ui = Blueprint('web_ui', __name__, url_prefix="/")


class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField("Connexion")


class SignupForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField("S'inscrire")


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
                return redirect('/')

        flash("Nom d'utilisateur ou mot de passe incorrect.")

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
                flash("Nom d'utilisateur déjà pris, merci d'en choisir un autre.")
                return render_template('signup.html', form=form)

        res = User.add_user(username, password)

        if res == 'oui':
            return redirect('/login')
        else:
            return redirect('/signup')

    return render_template('signup.html', form=form)


@web_ui.route('/update_info', methods=['POST'])
@login_required
@admin_required
def update_info():
    data = request.json
    changes = data.get('changes', [])

    if not changes:
        return jsonify({'success': False, 'error': 'Aucune modification fournie'})

    conn = get_db_connection()
    if conn is None:
        return jsonify({'success': False, 'error': 'Erreur de connexion à la base de données'})

    success = update_db_info(conn, changes)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Erreur lors de la mise à jour des données'})


@web_ui.route('/admin/users', methods=['GET'])
@login_required
@admin_required
def admin_users():
    users = User.get_all_users()
    return render_template('admin_users.html', users=users, current_user_id=current_user.id)


@web_ui.route('/admin/change_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    new_role = request.form.get('role')

    # Vérifier si l'utilisateur essaie de se retirer son propre rôle d'admin
    if int(user_id) == int(current_user.id) and new_role != 'admin':
        flash('Vous ne pouvez pas vous retirer votre propre rôle d\'administrateur.')
        return redirect(url_for('web_ui.admin_users'))

    if new_role not in ['user', 'admin']:
        flash('Rôle non valide.')
        return redirect(url_for('web_ui.admin_users'))

    success = User.set_role(user_id, new_role)
    if success:
        flash(f'Rôle modifié avec succès.')
    else:
        flash('Erreur lors de la modification du rôle.')

    return redirect(url_for('web_ui.admin_users'))


@web_ui.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    # Empêcher la suppression de son propre compte
    if int(user_id) == int(current_user.id):
        flash('Vous ne pouvez pas supprimer votre propre compte.')
        return redirect(url_for('web_ui.admin_users'))

    success = User.delete_user(user_id)
    if success:
        flash('Utilisateur supprimé avec succès.')
    else:
        flash('Erreur lors de la suppression de l\'utilisateur.')

    return redirect(url_for('web_ui.admin_users'))