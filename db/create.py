import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import DB_NAME, DB_USER, DB_PASSWORD


def create_db():
    con = psycopg2.connect(dbname=DB_NAME,
                           user=DB_USER, host='',
                           password=DB_PASSWORD)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    with open('create.sql', 'r') as f:
        text = f.read()
    cur.execute(sql.SQL(text))
    cur.close()
    con.close()


if __name__ == '__main__':
    create_db()