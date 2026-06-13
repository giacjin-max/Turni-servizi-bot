import sqlite3

DB_NAME = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        date TEXT,
        user TEXT,
        status TEXT,
        PRIMARY KEY (date, user)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS expected (
        date TEXT,
        user TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_response(date, user, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT OR REPLACE INTO responses VALUES (?, ?, ?)
    """, (date, user, status))

    conn.commit()
    conn.close()


def get_responses(date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT user, status FROM responses WHERE date=?", (date,))
    rows = c.fetchall()

    conn.close()
    return dict(rows)


def get_expected(date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT user FROM expected WHERE date=?", (date,))
    rows = c.fetchall()

    conn.close()
    return set([r[0] for r in rows])


def save_expected(date, users):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    for u in users:
        c.execute("INSERT OR IGNORE INTO expected VALUES (?, ?)", (date, u))

    conn.commit()
    conn.close()
