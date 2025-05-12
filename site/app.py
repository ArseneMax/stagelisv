from flask import Flask, render_template
import MySQLdb

app = Flask(__name__)


def get_db_connection():
    try:
        print(" Tentative de connexion à MySQL...")
        conn = MySQLdb.connect(
            host='127.0.0.1',
            user='root',
            password='root',
            database='lisv',
            port=3306,
            auth_plugin='mysql_native_password'
        )
        print(" Connexion MySQL réussie!")
        return conn
    except Exception as e:
        print(" erreur de con:")
        return None


@app.route('/')
def index():
    conn = get_db_connection()
    if conn is None:
        return " Échec de connexion à MySQL"
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM info')
    infos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html', infos=infos)

if __name__ == '__main__':
    app.run(debug=True)