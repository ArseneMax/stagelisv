import pymysql
from flask_login import UserMixin


def get_db_connection():
    try:
        print("Tentative de connexion à MySQL...")
        conn = pymysql.connect(
            host='193.51.28.22',
            user='vba_user',
            password='!mariadbLisv78140%',
            database='member',
            port=3307,
            charset='utf8mb4'
        )
        print("Connexion MySQL réussie!")
        return conn
    except Exception as e:
        print(f"Erreur de connexion: {str(e)}")
        return None

def select_all_infos():
    conn = get_db_connection()
    if conn is None:
        return " Échec de connexion à MySQL"
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM info')
    Infos = cursor.fetchall()
    cursor.close()
    conn.close()

    infos = []
    for info in Infos:
        info_list = list(info)

        if info_list[2]:
            info_list[2] = info_list[2].strftime('%d/%m/%Y')

        if info_list[8]:
            info_list[8] = info_list[8].strftime('%d/%m/%Y')

        if info_list[9]:
            info_list[9] = info_list[9].strftime('%d/%m/%Y')

        if info_list[10]:
            info_list[10] = info_list[10].strftime('%d/%m/%Y')

        if info_list[16]:
            info_list[16] = info_list[16].strftime('%d/%m/%Y')

        infos.append(info_list)
    return infos


from flask import jsonify, request, flash
import datetime


def update_db_info(conn, changes):
    """
    Met à jour les informations dans la base de données.

    Args:
        conn: Connexion à la base de données
        changes: Liste des modifications à appliquer

    Returns:
        True si la mise à jour est réussie, False sinon
    """
    try:
        cursor = conn.cursor()

        # Pour chaque modification, récupérer l'ID de la ligne et mettre à jour la colonne correspondante
        for change in changes:
            row_id = int(change['rowId'])
            column_name = change['column']

            # Convertir les noms de colonnes du format frontend au format de la base de données
            # Remplacer les espaces par des underscores si nécessaire
            column_mapping = {
                'Date de naissance': 'Date_de_naissance',
                'Date demande ZRR': 'Date_demande_ZRR',
                'Date d\'arrivée estimée': 'Date_arrivee_estimee',
                'Date d\'arrivée réelle': 'Date_arrivee_reelle',
                'Date de sortie': 'Date_de_sortie',
                'Nationalité': 'Nationalité',
                'Statut': 'Statut',
                'Nature du contrat': 'Nature_du_contrat',
                'Contrat au sein du laboratoire': 'Contrat_au_sein_du_laboratoire',
                'Établissement d\'origine': 'Établissement_d_origine',
                'Adresse mail': 'Adresse_mail',
                'Avis ZRR positif': 'Avis_ZRR_positif',
                'Avis ZRR negatif': 'Avis_ZRR_negatif',
                'Caution': 'Caution',
                'Bureau': 'Bureau',
                'Charte informatique': 'Charte_informatique',
                'Adresse MAC': 'Adresse_MAC',
                'Prêt matériel': 'Prêt_matériel',
                'Fiche renseignement archive': 'Fiche_renseignement_archive',
                'Fiche ZRR Archivé': 'Fiche_ZRR_Archivé',
                'Fiche ZRR Avis reservé': 'Fiche_ZRR_Avis_reservé'
            }

            # Si le nom de colonne est dans notre mapping, utiliser le nom mappé
            # Sinon, remplacer simplement les espaces par des underscores
            if column_name in column_mapping:
                db_column = column_mapping[column_name]
            else:
                db_column = column_name.replace(' ', '_')

            value = change['value']

            # Récupérer l'ID unique de la ligne (en supposant que la combinaison nom+prénom est unique)
            cursor.execute('SELECT Nom, Prénom FROM info LIMIT %s, 1', (row_id,))
            row_info = cursor.fetchone()

            if not row_info:
                return False

            nom, prenom = row_info

            # Traitement spécial pour les dates
            if db_column in ['Date_de_naissance', 'Date_demande_ZRR', 'Date_arrivee_estimee',
                             'Date_arrivee_reelle', 'Date_de_sortie']:
                if value:
                    # Convertir le format de date YYYY-MM-DD en objet datetime
                    try:
                        value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        # Si déjà au format DD/MM/YYYY, on le convertit
                        try:
                            parts = value.split('/')
                            if len(parts) == 3:
                                value = datetime.datetime(int(parts[2]), int(parts[1]), int(parts[0])).date()
                        except:
                            value = None
                else:
                    value = None

            # Mettre à jour la base de données - Utiliser des backticks pour les noms de colonnes
            query = f"UPDATE info SET `{db_column}` = %s WHERE Nom = %s AND Prénom = %s"
            cursor.execute(query, (value, nom, prenom))

        conn.commit()
        cursor.close()
        return True

    except Exception as e:
        print(f"Erreur lors de la mise à jour de la base de données: {e}")
        conn.rollback()
        return False


class User(UserMixin):
    def __init__(self, id, username, password, role='user'):
        self.id = id
        self.username = username
        self.password = password
        self.role = role  # Ajout de l'attribut role

    @staticmethod
    def get_all_users():
        conn = get_db_connection()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user')
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return users

    @staticmethod
    def get_user(user_id):
        users = User.get_all_users()
        for user in users:
            if str(user[0]) == str(user_id):  # user[0] = id
                return User(user[0], user[1], user[2],
                            user[3] if len(user) > 3 else 'user')  # id, login, password, role
        return None

    def get_id(self):
        return str(self.id)

    def is_admin(self):
        return self.role == 'admin'

    @staticmethod
    def add_user(username, password, role='user'):
        conn = get_db_connection()
        if conn is None:
            print('Erreur de connexion à la base.')
            return 'non'

        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO user (login, password, role) VALUES (%s, %s, %s)', (username, password, role))
            conn.commit()
            flash('Inscription réussie, vous pouvez maintenant vous connecter.')
            return 'oui'
        except Exception as e:
            flash('Erreur lors de l\'inscription.')
            print(e)
            return 'non'
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def set_role(user_id, new_role):
        conn = get_db_connection()
        if conn is None:
            print('Erreur de connexion à la base.')
            return False

        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE user SET role = %s WHERE id = %s', (new_role, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Erreur lors de la mise à jour du rôle: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete_user(user_id):
        conn = get_db_connection()
        if conn is None:
            print('Erreur de connexion à la base.')
            return False

        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM user WHERE id = %s', (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression de l'utilisateur: {e}")
            return False
        finally:
            cursor.close()
            conn.close()