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


# Ajoutez ces nouvelles fonctions dans fonction.py

def select_infos_by_year(year):
    """
    Récupère les informations des employés présents pendant une année donnée.
    Un employé est considéré comme présent si :
    - Il est arrivé avant ou pendant l'année ET (il n'est pas parti OU il est parti après le début de l'année)

    Args:
        year (int): L'année pour laquelle filtrer les employés

    Returns:
        list: Liste des informations des employés présents pendant l'année
    """
    conn = get_db_connection()
    if conn is None:
        return "Échec de connexion à MySQL"

    cursor = conn.cursor()

    # Requête SQL pour filtrer par année
    # Un employé est présent pendant une année si :
    # 1. Sa date d'arrivée est <= 31/12/année
    # 2. ET (sa date de départ est NULL OU sa date de départ est >= 01/01/année)
    query = """
            SELECT * \
            FROM info
            WHERE (Date_d_arrivée_dans_l_unité IS NULL OR Date_d_arrivée_dans_l_unité <= %s)
              AND (Date_de_départ_de_l_unité IS NULL OR Date_de_départ_de_l_unité >= %s) \
            """

    # Dates de début et fin de l'année
    start_of_year = f"{year}-01-01"
    end_of_year = f"{year}-12-31"

    cursor.execute(query, (end_of_year, start_of_year))
    Infos = cursor.fetchall()
    cursor.close()
    conn.close()

    infos = []
    for info in Infos:
        info_list = list(info)

        # Formatage des dates (même code que select_all_infos)
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


def get_available_years():
    """
    Récupère toutes les années disponibles basées sur les dates d'arrivée et de départ.
    Limite les années à l'année actuelle maximum.

    Returns:
        list: Liste des années triées par ordre décroissant, limitées à l'année actuelle
    """
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = conn.cursor()

    # Récupérer les années min et max des dates d'arrivée et de départ
    query = """
            SELECT MIN(YEAR (Date_d_arrivée_dans_l_unité)) as min_arrival, \
                   MAX(YEAR (Date_d_arrivée_dans_l_unité)) as max_arrival, \
                   MAX(YEAR (Date_de_départ_de_l_unité))   as max_departure
            FROM info
            WHERE Date_d_arrivée_dans_l_unité IS NOT NULL \
            """

    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result or not result[0]:
        return []

    min_year = result[0]
    max_year = max(result[1] or 0, result[2] or 0)

    # Obtenir l'année actuelle
    current_year = datetime.datetime.now().year

    # Limiter max_year à l'année actuelle
    if max_year == 0 or max_year > current_year:
        max_year = current_year

    # Générer la liste des années
    years = list(range(min_year, max_year + 1))
    return sorted(years, reverse=True)  # Tri décroissant


# REMPLACEZ complètement votre fonction update_db_info existante par celle-ci :

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
        print(f"DEBUG: Début de update_db_info avec {len(changes)} modifications")

        # Pour chaque modification, utiliser les identifiants uniques (nom + prénom + date d'arrivée)
        for i, change in enumerate(changes):
            print(f"DEBUG: Traitement du changement {i}: {change}")

            # Récupérer les identifiants uniques
            nom = change.get('nom')
            prenom = change.get('prenom')
            date_arrivee = change.get('date_arrivee')  # Format YYYY-MM-DD ou None
            column_name = change.get('column')
            value = change.get('value')

            print(
                f"DEBUG: nom='{nom}', prenom='{prenom}', date_arrivee='{date_arrivee}', column='{column_name}', value='{value}'")

            if not nom or not prenom or not column_name:
                print(f"ERROR: Champs obligatoires manquants pour le changement {i}")
                cursor.close()
                return False

            # Mapping des noms de colonnes du frontend vers la nouvelle base de données
            column_mapping = {
                'Nom': 'Nom',
                'Prénom': 'Prénom',
                'Date_de_naissance': 'Date_de_naissance',
                'HF': 'HF',
                'Nationalité': 'Nationalité',
                'Ville_de_naissance': 'Ville_de_naissance',
                'Pays_de_naissance': 'Pays_de_naissance',
                'Numéro_de_téléphone': 'Numéro_de_téléphone',
                'Statut': 'Statut',
                'Responsable_ou_Encadrant': 'Responsable_ou_Encadrant',
                'Équipe': 'Équipe',
                'Nom_de_l_équipe_en_interne': 'Nom_de_l_équipe_en_interne',
                'Sections_disciplinaires': 'Sections_disciplinaires',
                'HDR': 'HDR',
                'Sujet_du_stage_de_la_visite_de_thèse': 'Sujet_du_stage_de_la_visite_de_thèse',
                'Établissement_d_origine': 'Établissement_d_origine',
                'Date_d_arrivée_dans_l_unité': 'Date_d_arrivée_dans_l_unité',
                'Date_de_départ_de_l_unité': 'Date_de_départ_de_l_unité',
                'Abandon': 'Abandon',
                'Date_Abandon': 'Date_Abandon',
                'Date_Soutenance': 'Date_Soutenance',
                'Date_de_sortie': 'Date_de_sortie',
                'Avis_ZRR_positif': 'Avis_ZRR_positif',
                'Avis_ZRR_négatif': 'Avis_ZRR_négatif',
                'Date_ZRR': 'Date_ZRR',
                'Caution': 'Caution',
                'Bureau': 'Bureau',
                'Charte_Informatique': 'Charte_Informatique',
                'Adresse_Postale_ou_dans_le_pays_d_origine': 'Adresse_Postale_ou_dans_le_pays_d_origine',
                'Adresse_mail': 'Adresse_mail',
                'Diplôme_préparé': 'Diplôme_préparé',
                'Nature_du_contrat': 'Nature_du_contrat',
                'Personne_à_prévenir_en_cas_d_urgence': 'Personne_à_prévenir_en_cas_d_urgence',
                'Adresse_Postale': 'Adresse_Postale',
                'Tél_et_mail': 'Tél_et_mail'
            }

            # Si le nom de colonne est dans notre mapping, utiliser le nom mappé
            # Sinon, utiliser le nom tel quel
            if column_name in column_mapping:
                db_column = column_mapping[column_name]
            else:
                db_column = column_name

            print(f"DEBUG: Mapping colonne '{column_name}' -> '{db_column}'")

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
                        print(f"DEBUG: Date convertie: {value}")
                    except ValueError:
                        # Si déjà au format DD/MM/YYYY, on le convertit
                        try:
                            parts = value.split('/')
                            if len(parts) == 3:
                                value = datetime.datetime(int(parts[2]), int(parts[1]), int(parts[0])).date()
                                print(f"DEBUG: Date convertie depuis DD/MM/YYYY: {value}")
                        except:
                            print(f"ERROR: Impossible de convertir la date: {value}")
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
                    if db_column == 'HF':
                        value = 'H' if value else 'F'
                    else:
                        value = 'Oui' if value else 'Non'
                elif isinstance(value, str):
                    if db_column == 'HF':
                        pass  # Garder la valeur telle quelle pour HF
                    elif value.lower() in ['true', '1', 'oui', 'yes', 'on']:
                        value = 'Oui'
                    elif value.lower() in ['false', '0', 'non', 'no', 'off']:
                        value = 'Non'

            # Construire la clause WHERE avec nom + prénom + date d'arrivée
            where_conditions = ["`Nom` = %s", "`Prénom` = %s"]
            where_params = [nom, prenom]

            if date_arrivee and date_arrivee != 'null' and date_arrivee != 'None':
                where_conditions.append("`Date_d_arrivée_dans_l_unité` = %s")
                where_params.append(date_arrivee)
                print(f"DEBUG: Utilisation de la date d'arrivée: {date_arrivee}")
            else:
                where_conditions.append("`Date_d_arrivée_dans_l_unité` IS NULL")
                print(f"DEBUG: Date d'arrivée NULL ou vide")

            where_clause = " AND ".join(where_conditions)

            # Vérifier d'abord si l'enregistrement existe
            check_query = f"SELECT COUNT(*) FROM info WHERE {where_clause}"
            cursor.execute(check_query, where_params)
            count = cursor.fetchone()[0]
            print(f"DEBUG: Nombre d'enregistrements trouvés: {count}")

            if count == 0:
                print(
                    f"ERROR: Aucun enregistrement trouvé avec les critères: nom='{nom}', prenom='{prenom}', date_arrivee='{date_arrivee}'")
                cursor.close()
                return False
            elif count > 1:
                print(f"WARNING: Plusieurs enregistrements trouvés ({count}), mise à jour de tous")

            # Mettre à jour la base de données
            query = f"UPDATE info SET `{db_column}` = %s WHERE {where_clause}"
            final_params = [value] + where_params

            print(f"DEBUG: Requête SQL: {query}")
            print(f"DEBUG: Paramètres: {final_params}")

            cursor.execute(query, final_params)
            affected_rows = cursor.rowcount
            print(f"DEBUG: Lignes affectées: {affected_rows}")

        conn.commit()
        cursor.close()
        print("DEBUG: Toutes les modifications ont été commitées avec succès")
        return True

    except Exception as e:
        print(f"ERROR: Erreur lors de la mise à jour de la base de données: {e}")
        import traceback
        traceback.print_exc()
        if 'cursor' in locals():
            cursor.close()
        conn.rollback()
        return False


def classify_member_by_status(statut, nature_contrat=None):
    """
    Classifie un membre selon son statut et la nature de son contrat.

    Args:
        statut (str): Le statut du membre
        nature_contrat (str): La nature du contrat du membre (optionnel)

    Returns:
        str: La catégorie ('permanents', 'temporaires', 'doctorants', 'stagiaires', 'autres')
    """
    if not statut:
        return 'autres'

    statut_upper = statut.upper().strip()

    # Classification basée sur vos données réelles

    # Membres permanents (statuts permanents)
    permanents_statuts = [
        'MCF', 'PR', 'EXIE', 'PR2', 'PR1', 'AJT', 'IR', 'PREMT', 'CH', 'IE'
    ]

    # Personnel temporaire
    temporaires_statuts = [
        'CDD IE', 'POST-DOCT', 'CH INVITÉ', 'ATER', 'PROF INVITÉ', 'CH ASSOCIÉ',
        'CHERCHEUR', 'VISITEUR', 'RESP. GEST. PROJET EUR.'
    ]

    # Doctorants
    doctorants_statuts = [
        'DOCTORANT', 'DOCTORANT EXT.'
    ]

    # Stagiaires
    stagiaires_statuts = [
        'STAGIAIRE', 'APPRENTI'
    ]

    # Vérification exacte des statuts
    if statut_upper in permanents_statuts:
        return 'permanents'
    elif statut_upper in temporaires_statuts:
        return 'temporaires'
    elif statut_upper in doctorants_statuts:
        return 'doctorants'
    elif statut_upper in stagiaires_statuts:
        return 'stagiaires'

    # Si on a la nature du contrat, on peut affiner
    if nature_contrat:
        nature_upper = nature_contrat.upper().strip()

        # Fonctionnaires = permanents
        if 'FONCTIONNAIRE' in nature_upper or 'ÉMÉRITE' in nature_upper:
            return 'permanents'

        # CDD et autres contrats temporaires
        if any(keyword in nature_upper for keyword in ['CDD', 'BRSE', 'CIFRE', 'SALARIÉ']):
            # Mais si c'est un doctorant avec bourse, c'est un doctorant
            if any(keyword in nature_upper for keyword in ['BRSE', 'CONTRAT DOC', 'ALLOCATION']):
                return 'doctorants'
            else:
                return 'temporaires'

    # Classification par mots-clés si pas de correspondance exacte
    if any(keyword in statut_upper for keyword in ['DOCT', 'PHD', 'THÈSE']):
        return 'doctorants'
    elif any(keyword in statut_upper for keyword in ['STAGE', 'ÉTUDIANT']):
        return 'stagiaires'
    elif any(keyword in statut_upper for keyword in ['POST', 'INVITÉ', 'VISIT', 'ATER']):
        return 'temporaires'
    elif any(keyword in statut_upper for keyword in ['MCF', 'PR', 'CH', 'IR', 'IE']):
        return 'permanents'

    return 'autres'


def classify_member_by_status(statut, nature_contrat=None):
    """
    Classifie un membre selon son statut et la nature de son contrat.

    Args:
        statut (str): Le statut du membre
        nature_contrat (str): La nature du contrat du membre (optionnel)

    Returns:
        str: La catégorie ('permanents', 'temporaires', 'doctorants', 'stagiaires', 'autres')
    """
    if not statut:
        return 'autres'

    statut_upper = statut.upper().strip()

    # Classification basée sur vos données réelles


    permanents_statuts = [
        'MCF', 'PR', 'EXIE', 'PR2', 'PR1', 'AJT', 'IR', 'PREMT', 'CH', 'IE'
    ]


    temporaires_statuts = [
        'CDD IE', 'POST-DOCT', 'CH INVITÉ', 'ATER', 'PROF INVITÉ', 'CH ASSOCIÉ',
        'CHERCHEUR', 'VISITEUR', 'RESP. GEST. PROJET EUR.'
    ]


    doctorants_statuts = [
        'DOCTORANT', 'DOCTORANT EXT.'
    ]


    stagiaires_statuts = [
        'STAGIAIRE', 'APPRENTI'
    ]


    if statut_upper in permanents_statuts:
        return 'permanents'
    elif statut_upper in temporaires_statuts:
        return 'temporaires'
    elif statut_upper in doctorants_statuts:
        return 'doctorants'
    elif statut_upper in stagiaires_statuts:
        return 'stagiaires'


    if nature_contrat:
        nature_upper = nature_contrat.upper().strip()


        if 'FONCTIONNAIRE' in nature_upper or 'ÉMÉRITE' in nature_upper:
            return 'permanents'


        if any(keyword in nature_upper for keyword in ['CDD', 'BRSE', 'CIFRE', 'SALARIÉ']):
            # Mais si c'est un doctorant avec bourse, c'est un doctorant
            if any(keyword in nature_upper for keyword in ['BRSE', 'CONTRAT DOC', 'ALLOCATION']):
                return 'doctorants'
            else:
                return 'temporaires'


    if any(keyword in statut_upper for keyword in ['DOCT', 'PHD', 'THÈSE']):
        return 'doctorants'
    elif any(keyword in statut_upper for keyword in ['STAGE', 'ÉTUDIANT']):
        return 'stagiaires'
    elif any(keyword in statut_upper for keyword in ['POST', 'INVITÉ', 'VISIT', 'ATER']):
        return 'temporaires'
    elif any(keyword in statut_upper for keyword in ['MCF', 'PR', 'CH', 'IR', 'IE']):
        return 'permanents'

    return 'autres'


def get_membres_by_category(year=None):
    """
    Récupère tous les membres organisés par catégories selon leur statut.
    Peut être filtré par année.

    Args:
        year (int, optional): Année pour filtrer les membres présents

    Returns:
        dict: Dictionnaire avec les catégories et leurs membres respectifs
    """
    conn = get_db_connection()
    if conn is None:
        return {}

    cursor = conn.cursor()

    if year:

        query = """
                SELECT * \
                FROM info
                WHERE (Date_d_arrivée_dans_l_unité IS NULL OR Date_d_arrivée_dans_l_unité <= %s)
                  AND \
                    (Date_de_départ_de_l_unité IS NULL OR Date_de_départ_de_l_unité >= %s OR YEAR (Date_de_départ_de_l_unité) = \
                    9999) \
                """
        start_of_year = f"{year}-01-01"
        end_of_year = f"{year}-12-31"

        print(f"DEBUG: Filtrage pour l'année {year}")
        print(f"DEBUG: Paramètres: end_of_year={end_of_year}, start_of_year={start_of_year}")

        cursor.execute(query, (end_of_year, start_of_year))
    else:
        cursor.execute('SELECT * FROM info')

    all_infos = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"DEBUG: Nombre total d'enregistrements trouvés: {len(all_infos)}")

    # Initialiser les catégories
    categories = {
        'permanents': [],
        'temporaires': [],
        'doctorants': [],
        'stagiaires': [],
        'autres': []
    }

    for i, info in enumerate(all_infos):
        info_list = list(info)

        # Conserver les dates originales pour le debug
        date_arrivee_originale = info_list[16]
        date_depart_originale = info_list[17]
        statut = info_list[8] if info_list[8] else ""

        # Formatage des dates APRÈS la sélection
        date_indices = [2, 16, 17, 19, 20, 21, 24]
        for idx in date_indices:
            if info_list[idx]:
                # Gérer les dates en 9999 (considérées comme "pas de date de fin")
                if idx in [17, 19, 20, 21] and info_list[idx].year == 9999:
                    info_list[idx] = ''  # Date de fin vide pour 9999
                else:
                    info_list[idx] = info_list[idx].strftime('%d/%m/%Y')

        nature_contrat = info_list[31] if info_list[31] else ""

        # Classification selon le statut et la nature du contrat
        category = classify_member_by_status(statut, nature_contrat)

        # Debug spécifique pour l'année demandée
        if year and i < 10:  # Debug les 10 premiers
            print(f"DEBUG #{i}: {info_list[1]} {info_list[0]} ({statut})")
            print(f"  Date arrivée originale: {date_arrivee_originale}")
            print(f"  Date départ originale: {date_depart_originale}")
            print(f"  Catégorie: {category}")
            print(f"  Date arrivée formatée: {info_list[16]}")
            print(f"  Date départ formatée: {info_list[17]}")

        categories[category].append(info_list)

    # Debug final
    if year:
        print(f"DEBUG: Résultats finaux pour {year}:")
        for cat, membres in categories.items():
            print(f"  {cat}: {len(membres)} membre(s)")
            if cat == 'stagiaires' and len(membres) > 0:
                print(f"    Premiers stagiaires:")
                for i, stagiaire in enumerate(membres[:3]):
                    print(
                        f"      {i + 1}. {stagiaire[1]} {stagiaire[0]} - Arrivée: {stagiaire[16]} - Départ: {stagiaire[17]}")

    return categories


def get_membre_fields(membre, category):
    """
    Extrait les champs pertinents d'un membre selon sa catégorie.

    Args:
        membre: Liste contenant toutes les informations du membre
        category: Catégorie du membre ('permanents', 'temporaires', 'doctorants', 'stagiaires')

    Returns:
        dict: Dictionnaire avec les champs pertinents pour la catégorie
    """

    base_info = {
        'nom': membre[0] or '',
        'prenom': membre[1] or '',
    }

    if category == 'permanents':
        return {
            **base_info,
            'statut': membre[8] or '',
            'equipe': membre[10] or '',
            'nom_equipe': membre[11] or '',
            'section_disciplinaire': membre[12] or '',
            'adresse_mail': membre[29] or '',
            'nature_contrat': membre[31] or ''
        }

    elif category == 'temporaires':
        return {
            **base_info,
            'statut': membre[8] or '',
            'equipe': membre[10] or '',
            'nom_equipe': membre[11] or '',
            'section_disciplinaire': membre[12] or '',
            'date_arrivee': membre[16] or '',
            'date_depart': membre[17] or '',
            'adresse_mail': membre[29] or '',
            'nature_contrat': membre[31] or ''
        }

    elif category == 'doctorants':
        return {
            **base_info,
            'caution': membre[25] or '',
            'bureau': membre[26] or '',
            'abandon': membre[18] or '',
            'date_abandon': membre[19] or '',
            'date_soutenance': membre[20] or '',
            'avis_zrr_positif': membre[22] or '',
            'avis_zrr_negatif': membre[23] or '',
            'etablissement_origine': membre[15] or '',
            'diplome_prepare': membre[30] or '',
            'date_arrivee': membre[16] or '',
            'date_depart': membre[17] or '',
            'adresse_mail': membre[29] or '',
            'statut': membre[8] or '',
            'nature_contrat': membre[31] or ''
        }

    elif category == 'stagiaires':
        return {
            **base_info,
            'abandon': membre[18] or '',
            'date_abandon': membre[19] or '',
            'avis_zrr_positif': membre[22] or '',
            'avis_zrr_negatif': membre[23] or '',
            'etablissement_origine': membre[15] or '',
            'diplome_prepare': membre[30] or '',
            'date_arrivee': membre[16] or '',
            'date_depart': membre[17] or '',
            'sujet_stage': membre[14] or '',
            'adresse_mail': membre[29] or '',
            'statut': membre[8] or '',
            'nature_contrat': membre[31] or ''
        }

    elif category == 'autres':
        return {
            **base_info,
            'statut': membre[8] or '',
            'equipe': membre[10] or '',
            'date_arrivee': membre[16] or '',
            'date_depart': membre[17] or '',
            'adresse_mail': membre[29] or '',
            'nature_contrat': membre[31] or ''
        }

    return base_info


def get_classification_stats():
    """
    Fonction utilitaire pour analyser la classification des statuts.
    Utile pour le debug et l'ajustement des règles de classification.

    Returns:
        dict: Statistiques de classification
    """
    conn = get_db_connection()
    if conn is None:
        return {}

    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT Statut, Nature_du_contrat FROM info WHERE Statut IS NOT NULL')
    combinations = cursor.fetchall()
    cursor.close()
    conn.close()

    stats = {
        'permanents': [],
        'temporaires': [],
        'doctorants': [],
        'stagiaires': [],
        'autres': []
    }

    for statut, nature in combinations:
        category = classify_member_by_status(statut, nature)
        stats[category].append({
            'statut': statut,
            'nature_contrat': nature or 'N/A'
        })

    return stats


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