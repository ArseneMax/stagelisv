import os
from dotenv import load_dotenv
from flask import Flask, render_template, Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

from .fonction import User, get_db_connection, update_db_info, select_all_infos, get_available_years, select_infos_by_year, get_membres_by_category,get_membre_fields
from .decorators import admin_required

# Chargement des variables d'environnement
load_dotenv()

# Création de l'application
app = Flask(__name__)
app.config.from_prefixed_env(prefix='LISV_FLASK')
app.config.update(SECRET_KEY='temp')
print('SECRET_KEY:', app.config.get('SECRET_KEY'))  # Debug

# Configuration du système de connexion
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'web_ui.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)

# Blueprint pour l'interface web
web_ui = Blueprint('web_ui', __name__, url_prefix="/")


# Formulaires
class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField("Connexion")

class SignupForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField("S'inscrire")

# Routes
@web_ui.route('/')
@login_required
def index():
    return render_template('index.html', infos=select_all_infos())


@web_ui.route('/filter-by-year', methods=['GET', 'POST'])
@login_required
def filter_by_year_page():
    if request.method == 'POST':
        year = request.form.get('year', type=int)
        if year:
            return redirect(url_for('web_ui.year_view', year=year))

    available_years = get_available_years()
    return render_template('filter_year.html', available_years=available_years)



@web_ui.route('/year/<int:year>')
@login_required
def year_view(year):
    infos = select_infos_by_year(year)
    available_years = get_available_years()
    return render_template('year_view.html',
                           infos=infos,
                           year=year,
                           available_years=available_years)


@web_ui.route('/categories')
@login_required
def categories():
    """Route pour afficher les membres par catégories, avec filtrage optionnel par année"""
    year = request.args.get('year', type=int)
    available_years = get_available_years()

    categories_data = get_membres_by_category(year)

    # Organiser les données pour l'affichage
    organized_data = {}
    for category, membres in categories_data.items():
        organized_data[category] = []
        for membre in membres:
            member_data = get_membre_fields(membre, category)
            organized_data[category].append(member_data)

    return render_template('categories.html',
                           categories=organized_data,
                           available_years=available_years,
                           selected_year=year)



@web_ui.route('/categories-by-year', methods=['GET', 'POST'])
@login_required
def categories_by_year_page():
    if request.method == 'POST':
        year = request.form.get('year', type=int)
        if year:
            return redirect(url_for('web_ui.categories', year=year))

    available_years = get_available_years()
    return render_template('categories_filter_year.html', available_years=available_years)


@web_ui.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
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
    return jsonify({'success': success})

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
    if int(user_id) == int(current_user.id) and new_role != 'admin':
        flash('Vous ne pouvez pas vous retirer votre propre rôle d\'administrateur.')
        return redirect(url_for('web_ui.admin_users'))
    if new_role not in ['user', 'admin']:
        flash('Rôle non valide.')
        return redirect(url_for('web_ui.admin_users'))
    success = User.set_role(user_id, new_role)
    flash('Rôle modifié avec succès.' if success else 'Erreur lors de la modification du rôle.')
    return redirect(url_for('web_ui.admin_users'))

@web_ui.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if int(user_id) == int(current_user.id):
        flash('Vous ne pouvez pas supprimer votre propre compte.')
        return redirect(url_for('web_ui.admin_users'))
    success = User.delete_user(user_id)
    flash('Utilisateur supprimé avec succès.' if success else 'Erreur lors de la suppression de l\'utilisateur.')
    return redirect(url_for('web_ui.admin_users'))

app.register_blueprint(web_ui)