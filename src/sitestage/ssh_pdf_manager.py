import paramiko
import os
import tempfile
from functools import lru_cache
from flask import send_file, abort, after_this_request
import re
import threading
import time

# Configuration SSH CORRIGÉE avec le bon chemin
SSH_CONFIG = {
    'hostname': '193.51.28.22',
    'username': 'maxearse',
    'password': 'Stage1712_192005',
    'port': 22,
    # Chemin correct trouvé via les tests
    'pdf_base_path': '/ADMINISTRATION/Administration/ARCHIVES/CONVENTION DE CONTRAT DE RECHERCHE',
    # Options supplémentaires pour la compatibilité
    'allow_agent': False,
    'look_for_keys': False,
    'gss_auth': False,
    'gss_kex': False,
}


class SSHPDFManager:
    """Gestionnaire pour accéder aux PDF via SSH"""

    def __init__(self):
        self.ssh_client = None
        self.sftp_client = None
        self._lock = threading.Lock()

    def connect(self):
        """Établit la connexion SSH/SFTP"""
        with self._lock:
            try:
                if self.ssh_client and self.ssh_client.get_transport() and self.ssh_client.get_transport().is_active():
                    return True

                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Connexion SSH
                self.ssh_client.connect(
                    hostname=SSH_CONFIG['hostname'],
                    username=SSH_CONFIG['username'],
                    password=SSH_CONFIG['password'],
                    port=SSH_CONFIG['port'],
                    timeout=15,
                    banner_timeout=30
                )

                # Ouvrir le canal SFTP
                self.sftp_client = self.ssh_client.open_sftp()
                print(f"Connexion SSH établie vers {SSH_CONFIG['hostname']}")
                return True

            except Exception as e:
                print(f"Erreur de connexion SSH: {e}")
                self.disconnect()
                return False

    def disconnect(self):
        """Ferme les connexions SSH/SFTP"""
        with self._lock:
            if self.sftp_client:
                try:
                    self.sftp_client.close()
                except:
                    pass
                self.sftp_client = None
            if self.ssh_client:
                try:
                    self.ssh_client.close()
                except:
                    pass
                self.ssh_client = None

    def find_base_path(self):
        """Utilise directement le chemin correct trouvé"""
        base_path = SSH_CONFIG['pdf_base_path']
        try:
            # Tester si le répertoire existe
            self.sftp_client.listdir(base_path)
            print(f"✅ Chemin utilisé: {base_path}")
            return base_path
        except Exception as e:
            print(f"❌ Erreur accès au chemin {base_path}: {e}")
            return None

    def list_year_directories(self):
        """Liste les répertoires d'années disponibles"""
        try:
            # D'abord, trouver le bon chemin de base
            base_path = self.find_base_path()
            if not base_path:
                print("❌ Aucun chemin de base trouvé")
                return []

            print(f"📁 Utilisation du chemin: {base_path}")
            items = self.sftp_client.listdir(base_path)
            year_dirs = []

            print(f"📋 Contenu du répertoire ({len(items)} éléments):")
            for item in items[:10]:  # Afficher les 10 premiers
                print(f"  - {item}")

            for item in items:
                item_path = f"{base_path}/{item}"
                try:
                    # Vérifier si c'est un répertoire
                    stat = self.sftp_client.stat(item_path)
                    if stat.st_mode & 0o040000:  # Répertoire
                        # Extraire l'année du nom du répertoire
                        year_matches = re.findall(r'(\d{4})', item)
                        if year_matches:
                            for year_str in year_matches:
                                year = int(year_str)
                                if 2000 <= year <= 2030:  # Années raisonnables
                                    year_dirs.append((year, item_path, item))
                                    break
                except Exception as e:
                    print(f"Erreur stat {item_path}: {e}")
                    continue

            # Trier par année (plus récent en premier)
            year_dirs.sort(reverse=True)
            print(f"📅 Répertoires d'années trouvés: {[f'{year} ({name})' for year, path, name in year_dirs]}")
            return year_dirs

        except Exception as e:
            print(f"Erreur listing répertoires d'années: {e}")
            return []

    def search_pdf_in_directory(self, dir_path, eotp):
        """Recherche un PDF dans un répertoire donné"""
        try:
            print(f"🔍 Recherche dans: {dir_path}")
            files = self.sftp_client.listdir(dir_path)
            eotp_clean = str(eotp).strip().upper()  # Convertir en majuscules

            print(f"📄 {len(files)} fichiers trouvés dans {dir_path}")
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            print(f"📄 {len(pdf_files)} fichiers PDF dans ce répertoire")

            # Afficher quelques exemples de noms
            if pdf_files:
                print("📋 Exemples de PDF:")
                for pdf in pdf_files[:5]:
                    print(f"  - {pdf}")

            # Différentes variantes de recherche - améliorer la correspondance
            search_patterns = [
                eotp_clean,
                eotp_clean.replace('-', ''),
                eotp_clean.replace('_', ''),
                eotp_clean.replace(' ', ''),
            ]

            # Recherche exacte d'abord
            for filename in pdf_files:
                filename_upper = filename.upper()
                filename_clean = filename_upper.replace('-', '').replace('_', '').replace(' ', '')

                print(f"🔍 Test fichier: {filename}")
                print(f"   EOTP recherché: {eotp_clean}")
                print(f"   Fichier normalisé: {filename_clean}")

                # Essayer différentes stratégies de correspondance
                for pattern in search_patterns:
                    if (pattern in filename_upper or
                            pattern in filename_clean or
                            filename_upper.startswith(pattern) or
                            filename_clean.startswith(pattern)):
                        full_path = f"{dir_path}/{filename}"
                        print(f"✅ PDF trouvé: {filename} dans {dir_path}")
                        print(f"   Correspondance avec motif: {pattern}")
                        return full_path, filename

            # Si aucune correspondance exacte, essayer une recherche plus flexible
            print(f"🔍 Recherche flexible pour {eotp_clean}...")
            for filename in pdf_files:
                # Extraire les parties numériques et alphabétiques
                import re
                file_parts = re.findall(r'[A-Z0-9]+', filename.upper())
                eotp_parts = re.findall(r'[A-Z0-9]+', eotp_clean)

                # Vérifier si toutes les parties de l'EOTP sont dans le nom du fichier
                if all(part in ' '.join(file_parts) for part in eotp_parts if len(part) > 1):
                    full_path = f"{dir_path}/{filename}"
                    print(f"✅ PDF trouvé (recherche flexible): {filename}")
                    return full_path, filename

            print(f"❌ Aucun PDF trouvé pour EOTP {eotp} dans {dir_path}")
            return None, None

        except Exception as e:
            print(f"Erreur recherche dans {dir_path}: {e}")
            return None, None

    def find_contract_pdf(self, eotp, year_hint=None):
        """
        Recherche un fichier PDF de contrat sur le serveur SSH
        """
        if not self.connect():
            print("❌ Impossible de se connecter via SSH")
            return None, None

        try:
            year_dirs = self.list_year_directories()
            if not year_dirs:
                print("❌ Aucun répertoire d'année trouvé")
                return None, None

            # Définir l'ordre de recherche
            if year_hint:
                # Chercher d'abord dans l'année suggérée
                priority_dirs = [(year, path, name) for year, path, name in year_dirs if year == year_hint]
                other_dirs = [(year, path, name) for year, path, name in year_dirs if year != year_hint]
                search_order = priority_dirs + other_dirs
            else:
                search_order = year_dirs

            print(f"🔍 Recherche PDF pour EOTP: {eotp}")
            if year_hint:
                print(f"📅 Année de priorité: {year_hint}")

            # Rechercher dans chaque répertoire
            for year, dir_path, dir_name in search_order:
                print(f"📁 Recherche dans: {dir_name} (année {year})")
                pdf_path, pdf_filename = self.search_pdf_in_directory(dir_path, eotp)
                if pdf_path:
                    return pdf_path, pdf_filename

            print(f"❌ Aucun PDF trouvé pour EOTP: {eotp}")
            return None, None

        except Exception as e:
            print(f"Erreur dans find_contract_pdf: {e}")
            return None, None

    def download_pdf_to_temp(self, remote_path, original_filename):
        """Télécharge un PDF dans un fichier temporaire"""
        if not self.connect():
            return None

        try:
            # Créer un fichier temporaire avec un nom approprié
            temp_dir = tempfile.gettempdir()
            safe_filename = "".join(c for c in original_filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
            temp_path = os.path.join(temp_dir, f"contract_pdf_{int(time.time())}_{safe_filename}")

            print(f"📥 Téléchargement de {remote_path} vers {temp_path}")

            # Télécharger le fichier
            self.sftp_client.get(remote_path, temp_path)

            print(f"✅ Téléchargement réussi: {temp_path}")
            return temp_path

        except Exception as e:
            print(f"❌ Erreur téléchargement PDF: {e}")
            return None

    def check_pdf_exists(self, eotp, year_hint=None):
        """Vérifie si un PDF existe pour un contrat"""
        pdf_path, _ = self.find_contract_pdf(eotp, year_hint)
        return pdf_path is not None


# Instance globale du gestionnaire
pdf_manager = SSHPDFManager()


# Fonctions pour l'intégration Flask
def serve_contract_pdf(eotp):
    """Sert le fichier PDF d'un contrat via SSH"""
    try:
        # Récupérer l'année du contrat pour optimiser la recherche
        from .fonction import get_db_connection  # Import local pour éviter les imports circulaires

        year_hint = None
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT YEAR(date_debut) FROM contrat WHERE eotp = %s", (eotp,))
                result = cursor.fetchone()
                if result and result[0]:
                    year_hint = result[0]
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Erreur récupération année: {e}")

        print(f"📄 Serving PDF pour EOTP: {eotp}, année: {year_hint}")

        # Rechercher le PDF
        remote_path, filename = pdf_manager.find_contract_pdf(eotp, year_hint)
        if not remote_path:
            print(f"❌ PDF non trouvé pour EOTP: {eotp}")
            abort(404, "PDF non trouvé pour ce contrat")

        # Télécharger dans un fichier temporaire
        temp_path = pdf_manager.download_pdf_to_temp(remote_path, filename)
        if not temp_path:
            print(f"❌ Erreur téléchargement pour EOTP: {eotp}")
            abort(500, "Erreur lors du téléchargement du PDF")

        # Nettoyer le fichier temporaire après l'envoi
        @after_this_request
        def remove_temp_file(response):
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    print(f"🗑️ Fichier temporaire supprimé: {temp_path}")
            except Exception as e:
                print(f"Erreur suppression fichier temporaire: {e}")
            return response

        # Envoyer le fichier
        return send_file(
            temp_path,
            as_attachment=False,
            mimetype='application/pdf',
            download_name=f'contrat_{eotp}.pdf'
        )

    except Exception as e:
        print(f"❌ Erreur serve_contract_pdf pour {eotp}: {e}")
        abort(500, "Erreur lors de l'accès au fichier")


def check_pdf_exists(eotp):
    """Vérifie si un PDF existe pour un contrat donné"""
    try:
        from .fonction import get_db_connection

        # Récupérer l'année pour optimiser
        year_hint = None
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT YEAR(date_debut) FROM contrat WHERE eotp = %s", (eotp,))
                result = cursor.fetchone()
                if result and result[0]:
                    year_hint = result[0]
                cursor.close()
                conn.close()
            except:
                pass

        print(f"🔍 Vérification PDF pour EOTP: {eotp} (année: {year_hint})")
        result = pdf_manager.check_pdf_exists(eotp, year_hint)
        print(f"{'✅' if result else '❌'} PDF {'trouvé' if result else 'non trouvé'} pour {eotp}")
        return result

    except Exception as e:
        print(f"❌ Erreur check_pdf_exists pour {eotp}: {e}")
        return False


@lru_cache(maxsize=200)
def get_pdf_url(eotp):
    """Retourne l'URL du PDF pour un contrat donné (avec cache)"""
    try:
        if check_pdf_exists(eotp):
            return f"/contrats/{eotp}/pdf"
        return None
    except:
        return None


def clear_pdf_cache():
    """Vide le cache des URLs PDF"""
    get_pdf_url.cache_clear()
    # Déconnecter pour forcer une nouvelle connexion
    pdf_manager.disconnect()


