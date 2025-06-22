from db import init_db, clear_db

if __name__ == "__main__":
    conn = init_db()
    clear_db(conn)
    print("Database cleared successfully.")
    conn.close()