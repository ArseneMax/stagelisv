import mysql.connector
from flask import Flask, render_template

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(host='localhost',user='root',password='root',database='lisv')

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM info')
    infos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('page1.html', infos=infos)

if __name__ == '__main__':
    app.run(debug=True)