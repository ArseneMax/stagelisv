import pymysql
from flask_login import UserMixin
from flask import flash
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

        # Formatage des dates selon la nouvelle structure
        # Date_de_naissance (index 2)
        if info_list[2]:
            info_list[2] = info_list[2].strftime('%d/%m/%Y')

        # Date_d_arrivée_dans_l_unité (index 16)
        if info_list[16]:
            info_list[16] = info_list[16].strftime('%d/%m/%Y')

        # Date_de_départ_de_l_unité (index 17)
        if info_list[17]:
            info_list[17] = info_list[17].strftime('%d/%m/%Y')

        # Date_Abandon (index 19)
        if info_list[19]:
            info_list[19] = info_list[19].strftime('%d/%m/%Y')

        # Date_Soutenance (index 20)
        if info_list[20]:
            info_list[20] = info_list[20].strftime('%d/%m/%Y')

        # Date_de_sortie (index 21)
        if info_list[21]:
            info_list[21] = info_list[21].strftime('%d/%m/%Y')

        # Date_ZRR (index 24)
        if info_list[24]:
            info_list[24] = info_list[24].strftime('%d/%m/%Y')

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

            # Mapping des noms de colonnes du frontend vers la nouvelle base de données
            column_mapping = {
                'Nom': 'Nom',
                'Prénom': 'Prénom',
                'Date de naissance': 'Date_de_naissance',
                'H/F': 'HF',  # Changé de 'H/F' vers 'HF'
                'Sexe': 'HF',  # Mapping de l'ancien nom vers le nouveau
                'Nationalité': 'Nationalité',
                'Ville de naissance': 'Ville_de_naissance',
                'Pays de naissance': 'Pays_de_naissance',
                'Numéro de téléphone': 'Numéro_de_téléphone',
                'Statut': 'Statut',
                'Responsable encadrant': 'Responsable_ou_Encadrant',
                'Équipe': 'Équipe',
                'Nom de l\'équipe en interne': 'Nom_de_l_équipe_en_interne',  # Changé les apostrophes
                'Sections disciplinaires': 'Sections_disciplinaires',
                'HDR': 'HDR',
                'Sujet stage/visite/thèse': 'Sujet_du_stage_de_la_visite_de_thèse',
                'Établissement d\'origine': 'Établissement_d_origine',  # Changé les apostrophes
                'Date d\'arrivée unité': 'Date_d_arrivée_dans_l_unité',  # Changé les apostrophes
                'Date de départ unité': 'Date_de_départ_de_l_unité',
                'Abandon': 'Abandon',
                'Date abandon': 'Date_Abandon',
                'Date soutenance': 'Date_Soutenance',
                'Date de sortie': 'Date_de_sortie',
                'Avis ZRR positif': 'Avis_ZRR_positif',
                'Avis ZRR négatif': 'Avis_ZRR_négatif',
                'Date ZRR': 'Date_ZRR',
                'Caution': 'Caution',
                'Bureau': 'Bureau',
                'Charte informatique': 'Charte_Informatique',
                'Adresse postale origine': 'Adresse_Postale_ou_dans_le_pays_d_origine',  # Changé les apostrophes
                'Adresse mail': 'Adresse_mail',
                'Diplôme préparé': 'Diplôme_préparé',
                'Nature du contrat': 'Nature_du_contrat',
                'Personne à prévenir urgence': 'Personne_à_prévenir_en_cas_d_urgence',  # Changé les apostrophes
                'Adresse postale urgence': 'Adresse_Postale',
                'Tél/mail urgence': 'Tél_et_mail'
            }

            # Si le nom de colonne est dans notre mapping, utiliser le nom mappé
            # Sinon, utiliser le nom tel quel (au cas où il correspondrait déjà)
            if column_name in column_mapping:
                db_column = column_mapping[column_name]
            else:
                db_column = column_name

            value = change['value']

            # Récupérer l'ID unique de la ligne (en supposant que la combinaison nom+prénom est unique)
            cursor.execute('SELECT `Nom`, `Prénom` FROM info LIMIT %s, 1', (row_id,))
            row_info = cursor.fetchone()

            if not row_info:
                return False

            nom, prenom = row_info

            # Traitement spécial pour les dates
            date_columns = [
                'Date_de_naissance', 'Date_d_arrivée_dans_l_unité',
                'Date_de_départ_de_l_unité', 'Date_Abandon',
                'Date_Soutenance', 'Date_de_sortie', 'Date_ZRR'
            ]

            if db_column in date_columns:
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

            # Traitement spécial pour les champs VARCHAR avec valeurs booléennes
            boolean_varchar_columns = [
                'HF', 'HDR', 'Abandon', 'Avis_ZRR_positif',
                'Avis_ZRR_négatif', 'Charte_Informatique'
            ]

            if db_column in boolean_varchar_columns:
                if isinstance(value, bool):
                    # Pour HF, on peut adapter selon vos besoins
                    if db_column == 'HF':
                        value = 'H' if value else 'F'  # ou une autre logique
                    else:
                        value = 'Oui' if value else 'Non'
                elif isinstance(value, str):
                    if db_column == 'HF':
                        # Garder la valeur telle quelle pour HF
                        pass
                    elif value.lower() in ['true', '1', 'oui', 'yes', 'on']:
                        value = 'Oui'
                    elif value.lower() in ['false', '0', 'non', 'no', 'off']:
                        value = 'Non'

            # Mettre à jour la base de données - Utiliser des backticks pour les noms de colonnes
            query = f"UPDATE info SET `{db_column}` = %s WHERE `Nom` = %s AND `Prénom` = %s"
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