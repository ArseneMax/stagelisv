from flask import Flask, render_template
from datetime import datetime
import MySQLdb
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
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

auth = HTTPBasicAuth()
users = {
    "admin": [generate_password_hash("admin"), ["admin", "user"]],
    "user": [generate_password_hash("user"), ["user"]]
}
@app.route('/')
@auth.login_required
def index():
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

    return render_template('index.html', infos=infos)

#auth#
@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username)[0], password):
        return username
    return None

@auth.get_user_roles
def get_user_roles(username):
    return users.get(username)[1]


if __name__ == '__main__':
    app.run(debug=True)