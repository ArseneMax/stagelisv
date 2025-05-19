import MySQLdb
import pymysql


def get_db_connection():
    try:
        print("Tentative de connexion à MySQL...")
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='root',
            database='lisv',
            port=3306,
            charset='utf8mb4'
        )
        print("Connexion MySQL réussie!")
        return conn
    except Exception as e:
        print(f"Erreur de connexion: {str(e)}")
        return None


def create_admin(username, password):
    conn = get_db_connection()
    if conn is None:
        print('Erreur de connexion à la base.')
        return False

    cursor = conn.cursor()

    # Vérifier si l'utilisateur existe déjà
    cursor.execute('SELECT * FROM user WHERE login = %s', (username,))
    existing_user = cursor.fetchone()

    try:
        if existing_user:
            user_id = existing_user[0]
            # Mettre à jour l'utilisateur existant pour en faire un admin
            cursor.execute('UPDATE user SET role = %s WHERE id = %s', ('admin', user_id))
            print(f"L'utilisateur {username} a été promu administrateur.")
        else:
            # Créer un nouvel utilisateur admin
            cursor.execute('INSERT INTO user (login, password, role) VALUES (%s, %s, %s)',
                           (username, password, 'admin'))
            print(f"Un nouvel administrateur {username} a été créé.")

        conn.commit()
        return True
    except Exception as e:
        print(f"Erreur lors de la création de l'administrateur: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    success = create_admin(username, password)
    if success:
        print("Opération réussie.")
    else:
        print("Échec de l'opération.")
        sys.exit(1)