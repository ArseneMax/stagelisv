import MySQLdb


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
    return infos