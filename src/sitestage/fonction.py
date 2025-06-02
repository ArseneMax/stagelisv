import pymysql
from flask_login import UserMixin
from flask import  flash
import datetime

def get_db_connection():
    try:
        print("Tentative de connexion à MySQL...")
        conn = pymysql.connect(
            host='193.51.28.22',
            user='vba_user',
            password='!mariadbLisv78140%',
            database='testmember',
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

        # Formatage des dates selon les nouveaux champs
        # Date_naissance (index 2)
        if info_list[2]:
            info_list[2] = info_list[2].strftime('%d/%m/%Y')

        # Date_arrivee_unite (index 13)
        if info_list[13]:
            info_list[13] = info_list[13].strftime('%d/%m/%Y')

        # Date_depart_unite (index 14)
        if info_list[14]:
            info_list[14] = info_list[14].strftime('%d/%m/%Y')

        # Date_abandon (index 16)
        if info_list[16]:
            info_list[16] = info_list[16].strftime('%d/%m/%Y')

        infos.append(info_list)
    return infos





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

            # Mapping des noms de colonnes du frontend vers la base de données
            column_mapping = {
                'Nom': 'Nom',
                'Prénom': 'Prenom',
                'Date de naissance': 'Date_naissance',
                'Sexe': 'Sexe',
                'Nationalité': 'Nationalite',
                'Ville de naissance': 'Ville_naissance',
                'Pays de naissance': 'Pays_naissance',
                'Numéro de téléphone': 'Numero_telephone',
                'Statut': 'Statut',
                'Responsable encadrant': 'Responsable_encadrant',
                'Équipe': 'Equipe',
                'Sujet stage/visite/thèse': 'Sujet_stage_visite_these',
                'Établissement d\'origine': 'Etablissement_origine',
                'Date d\'arrivée unité': 'Date_arrivee_unite',
                'Date de départ unité': 'Date_depart_unite',
                'Abandon': 'Abandon',
                'Date abandon': 'Date_abandon',
                'Avis ZRR positif': 'Avis_ZRR_positif',
                'Avis ZRR négatif': 'Avis_ZRR_negatif',
                'Caution': 'Caution',
                'Bureau': 'Bureau',
                'Charte informatique': 'Charte_informatique',
                'Adresse postale origine': 'Adresse_postale_origine',
                'Adresse mail': 'Adresse_mail',
                'Diplôme préparé': 'Diplome_prepare',
                'Nature du contrat': 'Nature_contrat',
                'Personne à prévenir urgence': 'Personne_a_prevenir_urgence',
                'Adresse postale urgence': 'Adresse_postale_urgence',
                'Tél/mail urgence': 'Tel_mail_urgence'
            }

            # Si le nom de colonne est dans notre mapping, utiliser le nom mappé
            # Sinon, utiliser le nom tel quel (au cas où il correspondrait déjà)
            if column_name in column_mapping:
                db_column = column_mapping[column_name]
            else:
                db_column = column_name

            value = change['value']

            # Récupérer l'ID unique de la ligne (en supposant que la combinaison nom+prénom est unique)
            cursor.execute('SELECT Nom, Prenom FROM info LIMIT %s, 1', (row_id,))
            row_info = cursor.fetchone()

            if not row_info:
                return False

            nom, prenom = row_info

            # Traitement spécial pour les dates
            if db_column in ['Date_naissance', 'Date_arrivee_unite', 'Date_depart_unite', 'Date_abandon']:
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

            # Traitement spécial pour les booléens
            elif db_column in ['Abandon', 'Caution', 'Charte_informatique']:
                if isinstance(value, bool):
                    value = value
                elif isinstance(value, str):
                    value = value.lower() in ['true', '1', 'oui', 'yes', 'on']
                else:
                    value = bool(value)

            # Traitement spécial pour les champs Avis ZRR (VARCHAR(3))
            elif db_column in ['Avis_ZRR_positif', 'Avis_ZRR_negatif']:
                if isinstance(value, bool):
                    value = 'Oui' if value else 'Non'
                elif value in ['true', 'True', '1']:
                    value = 'Oui'
                elif value in ['false', 'False', '0']:
                    value = 'Non'

            # Mettre à jour la base de données - Utiliser des backticks pour les noms de colonnes
            query = f"UPDATE info SET `{db_column}` = %s WHERE Nom = %s AND Prenom = %s"
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