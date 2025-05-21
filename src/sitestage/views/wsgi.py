import sys
import os

# Ajouter le chemin du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import correct de l'application Flask
from sitestage.views import create_app

# Création de l'application
application = create_app()

# Pour WebStation sur Synology, 'application' est la variable standard attendue
# Pour les tests locaux, on peut lancer directement ce fichier
if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5050)