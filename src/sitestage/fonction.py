from functools import lru_cache

import pymysql
import requests
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

        # Grouper les modifications par personne pour éviter les conflits
        changes_by_person = {}
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

            # Créer une clé unique pour cette personne basée sur les identifiants ORIGINAUX
            # Ces identifiants ne changent jamais pendant le traitement
            person_key = f"{nom}|{prenom}|{date_arrivee or 'NULL'}"

            if person_key not in changes_by_person:
                changes_by_person[person_key] = {
                    'nom_original': nom,  # Nom original pour identifier l'enregistrement
                    'prenom_original': prenom,  # Prénom original pour identifier l'enregistrement
                    'date_arrivee_original': date_arrivee,
                    'changes': []
                }

            changes_by_person[person_key]['changes'].append({
                'column': column_name,
                'value': value
            })

        print(f"DEBUG: Modifications regroupées pour {len(changes_by_person)} personne(s)")

        # Traiter chaque personne séparément
        for person_key, person_data in changes_by_person.items():
            nom_original = person_data['nom_original']
            prenom_original = person_data['prenom_original']
            date_arrivee_originale = person_data['date_arrivee_original']
            person_changes = person_data['changes']

            print(f"DEBUG: Traitement de {nom_original} {prenom_original} avec {len(person_changes)} modification(s)")

            # IMPORTANT : Trier les modifications pour traiter Date_d_arrivée_dans_l_unité en premier
            # puis Nom et Prénom, puis le reste
            def sort_priority(change):
                column = change['column']
                if column == 'Date_d_arrivée_dans_l_unité':
                    return 0
                elif column == 'Nom':
                    return 1
                elif column == 'Prénom':
                    return 2
                else:
                    return 3

            person_changes.sort(key=sort_priority)

            # Variables pour garder trace des identifiants courants
            nom_courant = nom_original
            prenom_courant = prenom_original
            date_arrivee_courante = date_arrivee_originale

            # Appliquer toutes les modifications pour cette personne une par une
            for i, change_data in enumerate(person_changes):
                column_name = change_data['column']
                value = change_data['value']

                print(f"DEBUG: Modification {i + 1}/{len(person_changes)} - Colonne: {column_name}")

                # Construire la clause WHERE en utilisant les identifiants COURANTS
                where_conditions = ["`Nom` = %s", "`Prénom` = %s"]
                where_params = [nom_courant, prenom_courant]

                if date_arrivee_courante and date_arrivee_courante != 'null' and date_arrivee_courante != 'None':
                    where_conditions.append("`Date_d_arrivée_dans_l_unité` = %s")
                    where_params.append(date_arrivee_courante)
                    print(f"DEBUG: Utilisation de la date d'arrivée courante: {date_arrivee_courante}")
                else:
                    where_conditions.append("`Date_d_arrivée_dans_l_unité` IS NULL")
                    print(f"DEBUG: Date d'arrivée courante NULL ou vide")

                where_clause = " AND ".join(where_conditions)

                # Vérifier si l'enregistrement existe avec les identifiants courants
                check_query = f"SELECT COUNT(*) FROM info WHERE {where_clause}"
                cursor.execute(check_query, where_params)
                count = cursor.fetchone()[0]
                print(
                    f"DEBUG: Nombre d'enregistrements trouvés pour {nom_courant} {prenom_courant} avec date courante: {count}")

                if count == 0:
                    print(
                        f"ERROR: Aucun enregistrement trouvé pour {nom_courant} {prenom_courant} avec date_arrivee='{date_arrivee_courante}'")
                    cursor.close()
                    return False
                elif count > 1:
                    print(
                        f"WARNING: Plusieurs enregistrements trouvés pour {nom_courant} {prenom_courant} ({count}), mise à jour de tous")

                # Mapping des noms de colonnes
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

                if column_name in column_mapping:
                    db_column = column_mapping[column_name]
                else:
                    db_column = column_name

                print(f"DEBUG: Mapping colonne '{column_name}' -> '{db_column}' pour {nom_courant} {prenom_courant}")

                # Traitement spécial pour les dates
                date_columns = [
                    'Date_de_naissance', 'Date_d_arrivée_dans_l_unité',
                    'Date_de_départ_de_l_unité', 'Date_Abandon',
                    'Date_Soutenance', 'Date_de_sortie', 'Date_ZRR'
                ]

                if db_column in date_columns:
                    if value:
                        try:
                            value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
                            print(f"DEBUG: Date convertie: {value}")
                        except ValueError:
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
                            pass
                        elif value.lower() in ['true', '1', 'oui', 'yes', 'on']:
                            value = 'Oui'
                        elif value.lower() in ['false', '0', 'non', 'no', 'off']:
                            value = 'Non'

                # Mettre à jour cette colonne pour cette personne
                query = f"UPDATE info SET `{db_column}` = %s WHERE {where_clause}"
                final_params = [value] + where_params

                print(f"DEBUG: Requête SQL pour {db_column}: {query}")
                print(f"DEBUG: Paramètres: {final_params}")

                cursor.execute(query, final_params)
                affected_rows = cursor.rowcount
                print(f"DEBUG: Lignes affectées pour {db_column}: {affected_rows}")

                if affected_rows == 0:
                    print(f"WARNING: Aucune ligne affectée pour {nom_courant} {prenom_courant} - {db_column}")
                else:
                    print(f"SUCCESS: Mise à jour réussie pour {nom_courant} {prenom_courant} - {db_column}")

                # IMPORTANT : Mettre à jour les variables courantes après chaque modification
                if db_column == 'Date_d_arrivée_dans_l_unité' and value is not None:
                    date_arrivee_courante = value.strftime('%Y-%m-%d')
                    print(f"DEBUG: Date d'arrivée courante mise à jour vers: {date_arrivee_courante}")
                elif db_column == 'Nom' and value is not None:
                    nom_courant = value
                    print(f"DEBUG: Nom courant mis à jour vers: {nom_courant}")
                elif db_column == 'Prénom' and value is not None:
                    prenom_courant = value
                    print(f"DEBUG: Prénom courant mis à jour vers: {prenom_courant}")

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


@lru_cache(maxsize=50)
def get_hal_publications(year=None, author=None, doc_type=None, limit=100, start=0):
    """
    Récupère les publications HAL du LISV avec cache

    Args:
        year (int): Année de publication
        author (str): Nom d'auteur à rechercher
        doc_type (str): Type de document (ART, COMM, THESE, etc.)
        limit (int): Nombre de résultats max
        start (int): Index de départ pour pagination

    Returns:
        dict: Données des publications avec métadonnées
    """
    url = "https://api.archives-ouvertes.fr/search/"

    # Construction de la requête de base
    filters = []

    # Filtre par laboratoire - essayer plusieurs variantes du nom
    lab_filters = [
        'labStructName_s:"Laboratoire d\'Ingénierie des Systèmes de Versailles"',
        'labStructName_s:"LISV"',
        'labStructAcronym_s:"LISV"',
        'labStructName_s:"Laboratoire d\'Ingenierie des Systemes de Versailles"'  # Sans accents
    ]
    filters.append(f"({' OR '.join(lab_filters)})")

    # Filtre par année
    if year:
        filters.append(f'publicationDate_s:[{year}-01-01T00:00:00Z TO {year}-12-31T23:59:59Z]')

    # Filtre par type de document
    if doc_type and doc_type != 'ALL':
        filters.append(f'docType_s:"{doc_type}"')

    # Construction de la requête principale - SOLUTION BASÉE SUR LE DEBUG
    query = '*:*'
    if author:
        author_clean = author.strip()

        # Séparer les mots du nom
        author_words = [word.strip() for word in author_clean.split() if word.strip()]

        if len(author_words) == 1:
            # Un seul mot : recherche simple
            query = f'authFullName_s:*{author_words[0]}*'
        else:
            # Plusieurs mots : utiliser la stratégie AND qui fonctionne
            # Chaque mot doit être présent dans authFullName_s
            word_conditions = []
            for word in author_words:
                if len(word) > 1:  # Ignorer les mots d'une lettre
                    word_conditions.append(f'authFullName_s:*{word}*')

            if word_conditions:
                query = ' AND '.join(word_conditions)
            else:
                # Fallback si tous les mots sont trop courts
                query = f'authFullName_s:*{author_clean}*'

    params = {
        'q': query,
        'fq': filters,
        'wt': 'json',
        'fl': 'title_s,authFullName_s,authLastName_s,authFirstName_s,publicationDate_s,doiId_s,uri_s,docType_s,abstract_s,keyword_s,journalTitle_s,conferenceTitle_s,fileMain_s,labStructName_s,halId_s,citationFull_s',
        'rows': limit,
        'start': start,
        'sort': 'publicationDate_s desc'
    }

    try:
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            num_found = data.get('response', {}).get('numFound', 0)

            return {
                'docs': data.get('response', {}).get('docs', []),
                'numFound': num_found,
                'start': data.get('response', {}).get('start', 0)
            }
        else:
            print(f"DEBUG HAL: Erreur HTTP {response.status_code}")
            print(f"DEBUG HAL: Réponse: {response.text[:500]}")

    except requests.RequestException as e:
        print(f"Erreur API HAL: {e}")

    return {'docs': [], 'numFound': 0, 'start': 0}


def get_hal_statistics():
    """Récupère des statistiques sur les publications HAL du LISV"""
    try:
        # Correction de l'erreur datetime
        import datetime as dt
        current_year = dt.datetime.now().year

        # Publications par année (5 dernières années)
        years_stats = {}

        for year in range(current_year - 4, current_year + 1):
            result = get_hal_publications(year=year, limit=1)
            years_stats[year] = result['numFound']

        # Publications par type de document
        doc_types = ['ART', 'COMM', 'THESE', 'HDR', 'REPORT', 'COUV']
        types_stats = {}

        for doc_type in doc_types:
            result = get_hal_publications(doc_type=doc_type, limit=1)
            types_stats[doc_type] = result['numFound']

        # Total général
        total_result = get_hal_publications(limit=1)

        return {
            'years': years_stats,
            'types': types_stats,
            'total': total_result['numFound']
        }

    except Exception as e:
        print(f"Erreur lors du calcul des statistiques HAL: {e}")
        return {'years': {}, 'types': {}, 'total': 0}


def format_publication_data(pub):
    """Formate les données d'une publication pour l'affichage"""

    # Fonction utilitaire pour gérer les champs qui peuvent être string ou liste
    def get_field_value(field_data):
        if isinstance(field_data, list) and field_data:
            return field_data[0]
        elif isinstance(field_data, str):
            return field_data
        return ''

    # Formatage de la date
    pub_date = get_field_value(pub.get('publicationDate_s', ''))
    formatted_date = ''
    if pub_date:
        try:
            from datetime import datetime as dt
            date_obj = dt.strptime(pub_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d/%m/%Y')
        except ValueError:
            try:
                date_obj = dt.strptime(pub_date[:10], '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d/%m/%Y')
            except ValueError:
                formatted_date = pub_date

    # Type de document avec libellé
    doc_type = get_field_value(pub.get('docType_s', ''))
    doc_type_labels = {
        'ART': 'Article de revue',
        'COMM': 'Communication',
        'THESE': 'Thèse',
        'HDR': 'HDR',
        'REPORT': 'Rapport',
        'COUV': 'Ouvrage',
        'UNDEFINED': 'Non défini'
    }
    doc_type_label = doc_type_labels.get(doc_type, doc_type)

    # Abstract tronqué pour l'affichage
    abstract = get_field_value(pub.get('abstract_s', ''))
    abstract_short = abstract[:300] + '...' if len(abstract) > 300 else abstract

    # CORRECTION: Traitement correct des champs HAL (string ou liste)
    hal_id_raw = get_field_value(pub.get('halId_s', ''))
    uri_raw = get_field_value(pub.get('uri_s', ''))

    clean_uri = ''
    final_hal_id = ''

    # Stratégie 1: Utiliser l'URI directement si elle est complète et valide
    if uri_raw and uri_raw.startswith('http') and ('hal.science' in uri_raw or 'theses.hal.science' in uri_raw):
        clean_uri = uri_raw
        # Extraire l'ID de l'URI pour le hal_id
        if '/tel-' in uri_raw:
            final_hal_id = uri_raw.split('/tel-')[-1].split('v')[0].split('?')[0].split('#')[0]
            final_hal_id = f"tel-{final_hal_id}"
        elif '/hal-' in uri_raw:
            final_hal_id = uri_raw.split('/hal-')[-1].split('v')[0].split('?')[0].split('#')[0]
            final_hal_id = f"hal-{final_hal_id}"
        elif uri_raw.endswith('/'):
            final_hal_id = uri_raw.rstrip('/').split('/')[-1].split('v')[0]
        else:
            final_hal_id = uri_raw.split('/')[-1].split('v')[0].split('?')[0].split('#')[0]

    # Stratégie 2: Utiliser halId_s si pas d'URI valide
    elif hal_id_raw and len(hal_id_raw) > 5:  # Minimum 6 caractères pour un ID HAL valide
        final_hal_id = hal_id_raw.strip()

        # Construire l'URI selon le type d'ID
        if final_hal_id.startswith('tel-'):
            clean_uri = f"https://theses.hal.science/{final_hal_id}"
        elif final_hal_id.startswith('hal-'):
            clean_uri = f"https://hal.science/{final_hal_id}"
        else:
            # ID sans préfixe, ajouter hal- par défaut
            final_hal_id = f"hal-{final_hal_id}"
            clean_uri = f"https://hal.science/{final_hal_id}"

    # Validation finale
    if final_hal_id and len(final_hal_id) < 8:  # Un ID HAL valide fait au moins 8 caractères
        clean_uri = ''
        final_hal_id = ''

    # Nettoyage du DOI
    raw_doi = get_field_value(pub.get('doiId_s', ''))
    clean_doi = ''
    if raw_doi and '.' in raw_doi and len(raw_doi) > 5 and raw_doi not in ['1', '0', 'null', 'NULL']:
        clean_doi = raw_doi

    # Récupération de l'URL du fichier principal si disponible
    file_url = ''
    has_file = bool(pub.get('fileMain_s'))
    if has_file:
        file_main = get_field_value(pub.get('fileMain_s', ''))
        if file_main:
            # Construire l'URL complète du fichier
            if file_main.startswith('http'):
                file_url = file_main
            elif final_hal_id:
                # Construire l'URL basée sur l'ID HAL
                if final_hal_id.startswith('tel-'):
                    file_url = f"https://theses.hal.science/{final_hal_id}/document"
                else:
                    file_url = f"https://hal.science/{final_hal_id}/document"

    # Récupération des autres champs avec la fonction utilitaire
    title = get_field_value(pub.get('title_s', '')) or 'Titre non disponible'

    # Pour les champs qui sont vraiment des listes
    authors = pub.get('authFullName_s', [])
    if not isinstance(authors, list):
        authors = [authors] if authors else []

    keywords = pub.get('keyword_s', [])
    if not isinstance(keywords, list):
        keywords = [keywords] if keywords else []

    journal = get_field_value(pub.get('journalTitle_s', ''))
    conference = get_field_value(pub.get('conferenceTitle_s', ''))
    citation = get_field_value(pub.get('citationFull_s', ''))

    return {
        'title': title,
        'authors': authors,
        'publication_date': pub_date,
        'publication_date_formatted': formatted_date,
        'doc_type': doc_type,
        'doc_type_label': doc_type_label,
        'doi': clean_doi,
        'uri': clean_uri,
        'abstract': abstract,
        'abstract_short': abstract_short,
        'keywords': keywords,
        'journal': journal,
        'conference': conference,
        'hal_id': final_hal_id,
        'has_file': has_file,
        'file_url': file_url,
        'citation': citation,
        'year': pub_date[:4] if pub_date and len(pub_date) >= 4 else ''
    }


def get_hal_doc_types():
    """Retourne les types de documents HAL avec leurs libellés"""
    return {
        'ALL': 'Tous les types',
        'ART': 'Articles de revues',
        'COMM': 'Communications',
        'THESE': 'Thèses',
        'HDR': 'HDR',
        'REPORT': 'Rapports',
        'COUV': 'Ouvrages',
        'UNDEFINED': 'Non défini'
    }


def clear_hal_cache():
    """Vide le cache des publications HAL"""
    get_hal_publications.cache_clear()
    print("Cache HAL vidé")


def test_hal_connection():
    """Teste la connexion à l'API HAL"""
    try:
        result = get_hal_publications(limit=1)
        if result['numFound'] > 0:
            print(f" Connexion HAL OK - {result['numFound']} publications trouvées au total")
            return True
        else:
            print("⚠️ Connexion HAL OK mais aucune publication trouvée")
            return True
    except Exception as e:
        print(f" Erreur de connexion HAL: {e}")
        return False