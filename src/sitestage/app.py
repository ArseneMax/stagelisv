import os
from dotenv import load_dotenv
from flask import Flask, render_template, Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
import datetime

from .fonction import User, get_db_connection, update_db_info, select_all_infos, get_available_years, select_infos_by_year, get_membres_by_category, get_membre_fields, get_hal_statistics, get_hal_publications, get_hal_doc_types, format_publication_data, select_all_contrats, select_contrats_by_year, get_available_years_contrats
from .decorators import admin_required
from .ssh_pdf_manager import serve_contract_pdf, check_pdf_exists

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
def index():
    """Route principale - affiche les membres par catégories (anciennes 'categories')"""
    # Si aucune année n'est spécifiée, utiliser l'année courante
    year = request.args.get('year', type=int)
    current_year = datetime.datetime.now().year

    if year is None:
        year = current_year

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
                           selected_year=year,
                           current_year=current_year)


@web_ui.route('/tableau')
@login_required
@admin_required
def tableau():
    """Route pour afficher le tableau complet (ancien index) - nécessite une connexion"""
    year = request.args.get('year', type=int)
    available_years = get_available_years()

    if year:
        infos = select_infos_by_year(year)
    else:
        infos = select_all_infos()

    return render_template('index.html',
                           infos=infos,
                           available_years=available_years,
                           selected_year=year)


@web_ui.route('/categories')
def categories():
    """Route de redirection vers la page principale pour compatibilité"""
    return redirect(url_for('web_ui.index'))


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
                # Rediriger vers la page demandée ou vers la page principale
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect('/')
        flash("Nom d'utilisateur ou mot de passe incorrect.")
    return render_template('login.html', form=form)


@web_ui.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')


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
@admin_required
def update_info():
    """Route pour mettre à jour les informations - nécessite d'être admin"""
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
@admin_required
def admin_users():
    users = User.get_all_users()
    return render_template('admin_users.html', users=users, current_user_id=current_user.id)


@web_ui.route('/admin/change_role/<int:user_id>', methods=['POST'])
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
@admin_required
def delete_user(user_id):
    if int(user_id) == int(current_user.id):
        flash('Vous ne pouvez pas supprimer votre propre compte.')
        return redirect(url_for('web_ui.admin_users'))
    success = User.delete_user(user_id)
    flash('Utilisateur supprimé avec succès.' if success else 'Erreur lors de la suppression de l\'utilisateur.')
    return redirect(url_for('web_ui.admin_users'))


@web_ui.route('/publications')
def publications():
    """Route pour afficher les publications HAL du laboratoire"""
    # Récupération des paramètres de filtre
    year = request.args.get('year', type=int)
    author = request.args.get('author', '').strip()
    doc_type = request.args.get('doc_type', '').strip()
    page = request.args.get('page', 1, type=int)

    # Pagination
    per_page = 20
    start = (page - 1) * per_page

    # Récupération des publications
    try:
        publications_data = get_hal_publications(
            year=year,
            author=author if author else None,
            doc_type=doc_type if doc_type else None,
            limit=per_page,
            start=start
        )

        # Formatage des données pour l'affichage
        formatted_publications = []
        for pub in publications_data['docs']:
            formatted_publications.append(format_publication_data(pub))

        # Calcul de la pagination
        total_publications = publications_data['numFound']
        total_pages = (total_publications + per_page - 1) // per_page

        # Récupération des statistiques
        stats = get_hal_statistics()

        # Types de documents disponibles pour le filtre
        doc_types_labels = get_hal_doc_types()

        return render_template('publications.html',
                               publications=formatted_publications,
                               total_publications=total_publications,
                               current_page=page,
                               total_pages=total_pages,
                               per_page=per_page,
                               selected_year=year,
                               selected_author=author,
                               selected_doc_type=doc_type,
                               doc_types_labels=doc_types_labels,
                               statistics=stats,
                               available_years=get_available_years())

    except Exception as e:
        print(f"Erreur dans la route publications: {e}")
        flash(f"Erreur lors de la récupération des publications: {str(e)}", "error")
        return render_template('publications.html',
                               publications=[],
                               total_publications=0,
                               doc_types_labels=get_hal_doc_types(),
                               error="Erreur de connexion à l'API HAL")


@web_ui.route('/contrats')
def contrats():
    """Route pour afficher le tableau des contrats - accès libre"""
    year = request.args.get('year', type=int)
    responsable = request.args.get('responsable', '').strip()

    available_years = get_available_years_contrats()

    if year:
        contrats = select_contrats_by_year(year)
    else:
        contrats = select_all_contrats()

    # Filtrage par responsable si spécifié
    if responsable:
        contrats = [c for c in contrats if c[3] and responsable.lower() in c[3].lower()]

    return render_template('contrats.html',
                           contrats=contrats,
                           available_years=available_years,
                           selected_year=year)


@web_ui.route('/contrats/<eotp>/pdf')
def get_contract_pdf(eotp):
    """Route pour servir le PDF d'un contrat via SSH"""
    return serve_contract_pdf(eotp)


@web_ui.route('/contrats/<eotp>/check-pdf')
def check_contract_pdf(eotp):
    """Route AJAX pour vérifier si un PDF existe"""
    try:
        exists = check_pdf_exists(eotp)
        return jsonify({
            'exists': exists,
            'url': f'/contrats/{eotp}/pdf' if exists else None
        })
    except Exception as e:
        print(f"Erreur check PDF pour {eotp}: {e}")
        return jsonify({'exists': False, 'error': str(e)})


@web_ui.route('/api/pdf-status')
def pdf_status_batch():
    """Route pour vérifier le statut PDF de plusieurs contrats"""
    eotps = request.args.getlist('eotp')
    results = {}

    print(f"Vérification PDF en lot pour: {eotps}")

    for eotp in eotps:
        if eotp:  # Ignorer les EOTP vides
            try:
                exists = check_pdf_exists(eotp)
                results[eotp] = {
                    'exists': exists,
                    'url': f'/contrats/{eotp}/pdf' if exists else None
                }
            except Exception as e:
                print(f"Erreur vérification PDF pour {eotp}: {e}")
                results[eotp] = {'exists': False, 'error': str(e)}

    return jsonify(results)


app.register_blueprint(web_ui)