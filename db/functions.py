import asyncio
from datetime import datetime, timedelta
import pytz
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
    cur.execute(sql.SQL(f"SELECT username FROM supports;"))
    data = cur.fetchall()
    return data


async def get_team_supports(team):
    cur.execute(sql.SQL(f"SELECT username FROM supports WHERE team = '{team}';"))
    data = cur.fetchall()
    return data


async def get_support(support):
    cur.execute(sql.SQL(f"SELECT id, team, lead_id, english FROM supports WHERE username = '{support}';"))
    data = cur.fetchone()
    if data is not None:
        data = {
            'id': data[0],
            'team': data[1],
            'lead_id': f'🟢 {data[2]}' if data[2] is not None else '🔴',
            'english': '🟢' if data[3] else '🔴'
        }
    return data


async def get_request_english(request):
    cur.execute(sql.SQL(f"SELECT supports.english FROM supports JOIN requests ON supports.username = requests.support "
                        f"WHERE requests.id = {request};"))
    data = cur.fetchone()
    return data[0]


async def get_support_id(support):
    cur.execute(sql.SQL(f"SELECT id FROM supports WHERE username = '{support}';"))
    data = cur.fetchone()
    return data


async def get_lead(lead_id):
    cur.execute(sql.SQL(f"SELECT username FROM supports WHERE lead_id = {lead_id};"))
    data = cur.fetchone()
    return data


async def add_support(id_, username, team, lead_id=None):
    cur.execute(sql.SQL(f"INSERT INTO supports (id, username, team, lead_id) "
                        f"VALUES ({id_}, '{username}', '{team}', {'NULL' if lead_id is None else lead_id});"))
    con.commit()


async def change_support_username(support, username):
    cur.execute(sql.SQL(f"UPDATE requests SET support = '{username}' WHERE support = '{support}';"))
    cur.execute(sql.SQL(f"UPDATE supports SET username = '{username}' WHERE username = '{support}';"))
    con.commit()


async def change_support_lead(support, lead=None):
    lead_id = f"'{lead}'" if lead is not None else 'NULL'
    cur.execute(sql.SQL(f"UPDATE supports SET lead_id = {lead_id} WHERE username = '{support}';"))
    con.commit()


async def change_support_team(support, team):
    cur.execute(sql.SQL(f"UPDATE supports SET team = '{team}' WHERE username = '{support}';"))
    con.commit()


async def change_support_id(support, id_):
    cur.execute(sql.SQL(f"UPDATE supports SET id = {id_} WHERE username = '{support}';"))
    con.commit()


async def change_english(support):
    cur.execute(sql.SQL(f"SELECT english FROM supports WHERE username = '{support}';"))
    data = cur.fetchone()
    cur.execute(sql.SQL(f"UPDATE supports SET english = {'FALSE' if data[0] else 'TRUE'} WHERE username = '{support}';"))
    con.commit()


async def get_support_schedule(support):
    cur.execute(sql.SQL(f"SELECT day_start, day_end, days_off FROM supports WHERE username = '{support}';"))
    data = cur.fetchone()
    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
    data = {
        'day_start': data[0].strftime('%H:%M') if data[0] is not None else '-',
        'day_end': data[1].strftime('%H:%M') if data[1] is not None else '-',
        'days_off': ', '.join([days[day] for day in data[2]]) if data[2] is not None else '-'
    }
    return data


async def change_support_day_start(support, time):
    day_start = f"'{time}'" if time is not None else 'NULL'
    cur.execute(sql.SQL(f"UPDATE supports SET day_start = {day_start} WHERE username = '{support}';"))
    con.commit()


async def change_support_day_end(support, time):
    day_end = f"'{time}'" if time is not None else 'NULL'
    cur.execute(sql.SQL(f"UPDATE supports SET day_end = {day_end} WHERE username = '{support}';"))
    con.commit()


async def change_support_days_off(support, days):
    days_off = "'{" + ','.join(days) + "}'" if days is not None else 'NULL'
    cur.execute(sql.SQL(f"UPDATE supports SET days_off = {days_off} WHERE username = '{support}';"))
    con.commit()


async def get_supports_end_notifications(time):
    today = datetime.now(pytz.timezone('Europe/Moscow')).weekday()
    cur.execute(sql.SQL(f"SELECT username, day_end, id, english FROM supports "
                        f"WHERE day_end IS NOT NULL AND (days_off IS NULL OR NOT ({today} = ANY (days_off)));"))
    result = []
    supports = cur.fetchall()
    for support in supports:
        time_to = datetime.now(pytz.timezone('Europe/Moscow'))
        time_from = datetime.now(pytz.timezone('Europe/Moscow')).replace(hour=support[1].hour, minute=support[1].minute)
        if time_to - time_from <= timedelta(minutes=time):
            cur.execute(sql.SQL(f"SELECT id, buyer_id, status, created_at, started_at, text "
                                f"FROM requests WHERE support = '{support[0]}' AND status IN ('created','started');"))
        requests = cur.fetchall()
        if len(requests) > 0:
            result.append([support[0], support[2], support[3], requests])
    return result


async def get_supports_start_notifications(time):
    today = datetime.now(pytz.timezone('Europe/Moscow')).weekday()
    cur.execute(sql.SQL(f"SELECT username, day_start, id, english FROM supports "
                        f"WHERE day_start IS NOT NULL AND (days_off IS NULL OR NOT ({today} = ANY (days_off)));"))
    result = []
    supports = cur.fetchall()
    for support in supports:
        time_to = datetime.now(pytz.timezone('Europe/Moscow'))
        time_from = datetime.now(pytz.timezone('Europe/Moscow')).replace(hour=support[1].hour, minute=support[1].minute)
        if time_to - time_from <= timedelta(minutes=time):
            cur.execute(sql.SQL(f"UPDATE requests SET status = 'started' WHERE status = 'delayed' "
                                f"AND support = '{support[0]}';"))
            con.commit()
            cur.execute(sql.SQL(f"SELECT id, buyer_id, status, created_at, started_at, text "
                                f"FROM requests WHERE support = '{support[0]}' AND status IN ('created','started');"))
        requests = cur.fetchall()
        if len(requests) > 0:
            result.append([support[0], support[2], support[3], requests])
    return result


async def remove_support(support):
    cur.execute(sql.SQL(f"DELETE FROM supports WHERE username = '{support}';"))
    con.commit()


async def create_request(buyer_id, support, text, chat):
    cur.execute(sql.SQL(f"INSERT INTO requests (buyer_id, support, text, chat) "
                        f"VALUES ('{buyer_id}', '{support}', '{text}', {chat}) RETURNING id, created_at;"))
    data = cur.fetchone()
    con.commit()
    return data


async def get_request(request):
    cur.execute(sql.SQL(f"SELECT buyer_id, status, created_at, started_at, completed_at, text, support"
                        f" FROM requests WHERE id = {request};"))
    data = cur.fetchone()
    data = {
        'buyer_id': data[0],
        'status': data[1],
        'created_at': data[2],
        'started_at': data[3],
        'completed_at': data[4],
        'text': data[5],
        'support': data[6]
    }
    return data


async def get_requests_stats(period):
    cur.execute(sql.SQL(f"SELECT id, buyer_id, support, text, chat, status, created_at, started_at, completed_at"
                        f" FROM requests WHERE created_at >= '{period}';"))
    data = cur.fetchall()
    return data


async def get_request_team(request):
    cur.execute(sql.SQL(f"SELECT supports.team FROM requests JOIN supports "
                        f"ON requests.support = supports.username WHERE requests.id = {request};"))
    data = cur.fetchone()
    return data[0]


async def change_request_support(request, support):
    cur.execute(sql.SQL(f"UPDATE requests SET support = '{support}' WHERE id = {request};"))
    con.commit()


async def change_status(request, status):
    if status == 'completed':
        cur.execute(sql.SQL(f"UPDATE requests SET completed_at = (timezone('Europe/Moscow', now())) WHERE id = {request};"))
    if status == 'started':
        cur.execute(sql.SQL(f"UPDATE requests SET started_at = (timezone('Europe/Moscow', now())) WHERE id = {request} "
                            f"AND started_at IS NULL;"))
    cur.execute(sql.SQL(f"UPDATE requests SET status = '{status}' WHERE id = {request} "
                        f"RETURNING buyer_id, status, created_at, started_at, completed_at, text, chat, support;"))
    con.commit()
    data = cur.fetchone()
    data = {
        'buyer_id': data[0],
        'status': data[1],
        'created_at': data[2],
        'started_at': data[3],
        'completed_at': data[4],
        'text': data[5],
        'chat': data[6],
        'support': data[7]
    }
    return data


async def get_requests(team, status):
    cur.execute(sql.SQL(f"SELECT requests.id, requests.buyer_id, requests.support FROM requests "
                        f"JOIN supports ON requests.support = supports.username "
                        f"WHERE supports.team = '{team}' AND requests.status = '{status}' ORDER BY id;"))
    data = cur.fetchall()
    data = [[result[0], f'{result[0]} : {result[1]} : {result[2]}'] for result in data]
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
    return data if data is None else data[0]


async def get_teams():
    cur.execute(sql.SQL(f"SELECT name FROM teams;"))
    data = cur.fetchall()
    return data


async def get_team(team):
    cur.execute(sql.SQL(f"SELECT name FROM teams WHERE name = '{team}';"))
    team_data = cur.fetchone()
    cur.execute(sql.SQL(f"SELECT username FROM supports WHERE team = '{team}';"))
    supports_data = cur.fetchall()
    cur.execute(sql.SQL(f"SELECT username FROM supports WHERE team = '{team}' AND lead_id IS NOT NULL;"))
    leads_data = cur.fetchall()
    cur.execute(sql.SQL(f"SELECT requests.id FROM requests JOIN supports ON requests.support = supports.username "
                        f"WHERE supports.team = '{team}';"))
    requests_data = cur.fetchall()
    if team_data is not None:
        data = {
            'supports': len(supports_data),
            'leads': ', '.join([lead[0] for lead in leads_data]) if len(leads_data) > 0 else '-',
            'requests': len(requests_data)
        }
    else:
        data = None
    return data


async def create_team(name):
    cur.execute(sql.SQL(f"INSERT INTO teams (name) "
                        f"VALUES ('{name}');"))
    con.commit()


async def change_team_name(team, name):
    cur.execute(sql.SQL(f"UPDATE supports SET team = '{name}' WHERE team = '{team}';"))
    con.commit()
    cur.execute(sql.SQL(f"UPDATE teams SET name = '{name}' WHERE name = '{team}';"))
    con.commit()


async def get_team_notification(team):
    cur.execute(sql.SQL(f"SELECT notification_time, notification_text FROM teams WHERE name = '{team}';"))
    data = cur.fetchone()
    data = {
        'time': f'{data[0]} мин' if data[0] is not None else '-',
        'text': data[1] if data[1] is not None else '-'
    }
    return data


async def change_team_notification_time(team, time):
    text = time if time is not None else "NULL"
    cur.execute(sql.SQL(f"UPDATE teams SET notification_time = {time} WHERE name = '{team}';"))
    con.commit()


async def change_team_notification_text(team, text):
    text = f"'{text}'" if text is not None else "NULL"
    cur.execute(sql.SQL(f"UPDATE teams SET notification_text = {text} WHERE name = '{team}';"))
    con.commit()


async def get_requests_notifications(time):
    cur.execute(sql.SQL(f"SELECT name, notification_time, notification_text FROM teams "
                        f"WHERE notification_time IS NOT NULL AND notification_text IS NOT NULL;"))
    result = []
    teams = cur.fetchall()
    for team in teams:
        cur.execute(sql.SQL(f"SELECT s.id, r.id, r.buyer_id, r.created_at, r.text, r.support "
                            f"FROM requests as r JOIN supports as s ON r.support = s.username "
                            f"WHERE r.status = 'created' AND s.team = '{team[0]}'"
                            f"AND r.created_at + INTERVAL '{team[1]} minutes' > "
                            f"(timezone('Europe/Moscow', now())) - INTERVAL '{time} minutes'"))
        requests = cur.fetchall()
        result.append([team[2], requests])
    return result


async def delete_team(team):
    cur.execute(sql.SQL(f"DELETE FROM teams WHERE name = '{team}';"))
    con.commit()


async def get_completed_chat():
    cur.execute(sql.SQL(f"SELECT id FROM completed_chat;"))
    data = cur.fetchone()
    return data if data is None else data[0]


async def set_completed_chat(chat):
    current = await get_completed_chat()
    if current is None:
        cur.execute(sql.SQL(f"INSERT INTO completed_chat (id) VALUES ({chat});"))
    else:
        cur.execute(sql.SQL(f"UPDATE completed_chat SET id = {chat} WHERE id = {current};"))
    con.commit()


async def check_request_support(request, support):
    cur.execute(sql.SQL(f"SELECT requests.id FROM requests JOIN supports "
                        f"ON requests.support = supports.username "
                        f"WHERE requests.id = {request} AND supports.id = {support};"))
    data = cur.fetchone()
    return data is not None
