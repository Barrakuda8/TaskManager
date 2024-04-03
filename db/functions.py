import asyncio
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import DB_NAME, DB_USER, DB_PASSWORD


async def start_db():
    global con, cur

    con = psycopg2.connect(dbname=DB_NAME,
                           user=DB_USER, host='',
                           password=DB_PASSWORD)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()


async def get_supports():
    cur.execute(sql.SQL(f"SELECT id, username FROM supports;"))
    data = cur.fetchall()
    return data


async def get_support(username):
    cur.execute(sql.SQL(f"SELECT id FROM supports WHERE username = '{username}';"))
    data = cur.fetchone()
    return data


async def get_support_username(support):
    cur.execute(sql.SQL(f"SELECT username FROM supports WHERE id = {support};"))
    data = cur.fetchone()
    return data


async def add_support(id_, username):
    cur.execute(sql.SQL(f"INSERT INTO supports (id, username) "
                        f"VALUES ({id_}, '{username}');"))
    con.commit()


async def change_support_username(support, username):
    cur.execute(sql.SQL(f"UPDATE supports SET username = '{username}' WHERE id = {support};"))
    con.commit()


async def remove_support(support):
    cur.execute(sql.SQL(f"DELETE FROM supports WHERE id = {support};"))
    con.commit()


async def create_request(buyer_id, support, text, chat):
    cur.execute(sql.SQL(f"INSERT INTO requests (buyer_id, support, text, chat) "
                        f"VALUES ('{buyer_id}', '{support}', '{text}', {chat}) RETURNING id, created_at;"))
    data = cur.fetchone()
    con.commit()
    return data


async def get_request(request):
    cur.execute(sql.SQL(f"SELECT buyer_id, status, created_at, completed_at, text FROM requests WHERE id = {request};"))
    data = cur.fetchone()
    data = {
        'buyer_id': data[0],
        'status': data[1],
        'created_at': data[2],
        'completed_at': data[3],
        'text': data[4]
    }
    return data


async def change_status(request, status):
    if status == 'completed':
        cur.execute(sql.SQL(f"UPDATE requests SET completed_at = (timezone('Europe/Moscow', now())) WHERE id = {request};"))
    cur.execute(sql.SQL(f"UPDATE requests SET status = '{status}' WHERE id = {request} "
                        f"RETURNING buyer_id, status, created_at, completed_at, text, chat;"))
    con.commit()
    data = cur.fetchone()
    data = {
        'buyer_id': data[0],
        'status': data[1],
        'created_at': data[2],
        'completed_at': data[3],
        'text': data[4],
        'chat': data[5]
    }
    return data


async def get_admins():
    cur.execute(sql.SQL(f"SELECT id, name FROM admins;"))
    data = cur.fetchall()
    return data


async def check_admin(admin):
    cur.execute(sql.SQL(f"SELECT id FROM admins WHERE id = {admin};"))
    data = cur.fetchone()
    return data is not None


async def add_admin(id_, name):
    cur.execute(sql.SQL(f"INSERT INTO admins (id, name) "
                        f"VALUES ({id_}, '{name}');"))
    con.commit()


async def change_admin_name(admin, name):
    cur.execute(sql.SQL(f"UPDATE admins SET name = '{name}' WHERE id = {admin};"))
    con.commit()


async def remove_admin(admin):
    cur.execute(sql.SQL(f"DELETE FROM admins WHERE id = {admin};"))
    con.commit()


async def get_admin_name(admin):
    cur.execute(sql.SQL(f"SELECT name FROM admins WHERE id = {admin};"))
    data = cur.fetchone()
    return data

