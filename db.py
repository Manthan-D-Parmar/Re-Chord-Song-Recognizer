import os
import sqlite3

# Path to .db file
def get_db_path():
    folder = os.path.join(os.path.dirname(__file__),'database')
    os.makedirs(folder,exist_ok=True)
    
    return os.path.join(folder,'fingerprints.db')


# Initialize DB
def init_db():
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute(''' 
                CREATE TABLE IF NOT EXISTS songs (
                    song_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE NOT NULL,
                    url TEXT
                    )
                ''')
    

    cur.execute('''
                CREATE TABLE IF NOT EXISTS fingerprints (
                    hash TEXT NOT NULL,
                    song_id INTEGER NOT NULL,
                    offset INTEGER NOT NULL,
                    FOREIGN KEY (song_id) REFERENCES songs (song_id)
                    )
                ''')
    cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_hash ON fingerprints(hash)
                ''')
    cur.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT UNIQUE NOT NULL
                    )
                ''')
    cur.execute('''
                CREATE TABLE IF NOT EXISTS song_tags (
                    song_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (song_id,tag_id),
                    FOREIGN KEY (song_id) REFERENCES songs (song_id),
                    FOREIGN KEY (tag_id) REFERENCES tags (tag_id)
                    )
                 ''')
    cur.execute('''
                CREATE TABLE IF NOT EXISTS song_similarities (
                    song_id1 INTEGER NOT NULL,
                    song_id2 INTEGER NOT NULL,
                    shared_tags INTEGER NOT NULL,
                    PRIMARY KEY (song_id1, song_id2),
                    FOREIGN KEY (song_id1) REFERENCES songs (song_id),
                    FOREIGN KEY (song_id2) REFERENCES songs (song_id)
                    )
                 ''')
    conn.commit()

    return conn


# Clear DB
def clear_db(conn):
    cur = conn.cursor()
    cur.execute('DELETE FROM fingerprints')
    cur.execute('DELETE FROM songs')
    cur.execute('DELETE FROM tags')
    cur.execute('DELETE FROM song_tags')
    cur.execute('DELETE FROM song_similarities')
    cur.execute("DELETE FROM sqlite_sequence WHERE name='songs';")
    conn.commit()


# Add song (Return ID)
def add_song(conn,title): 
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO songs (title) VALUES (?)',(title,))
    conn.commit()

    return cur.lastrowid


# Store hashes of song
def store_fingerprints(conn,song_id,hash_list):
    cur = conn.cursor()
    cur.executemany('''
                    INSERT INTO fingerprints (hash,song_id,offset) VALUES (?,?,?)
                    ''',[(h,song_id,offset) for h,offset in hash_list])
    conn.commit()


# Find song matching hash
def query_hashes(conn,hashes): 
    cur = conn.cursor()
    temp = ','.join('?' for _ in hashes) # temp = (?,?,...,?) 
    query = f'''
            SELECT s.song_id, s.title, f.offset
            FROM songs AS s
            JOIN fingerprints AS f ON s.song_id = f.song_id
            WHERE f.hash IN ({temp}) 
            ''' 
    cur.execute(query,tuple(hashes))

    return cur.fetchall()


# Add tag (Return ID)
def add_tag(conn,name):
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO tags (tag_name) VALUES (?)',(name,))
    conn.commit()
    cur.execute('SELECT tag_id FROM tags WHERE tag_name = ?',(name,))
    return cur.fetchone()[0]


# Link song and tag
def add_song_tag(conn,song_id,tag_id):
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO song_tags (song_id,tag_id) VALUES (?,?)',(song_id,tag_id))
    conn.commit()


# Get ID for song title
def get_song_id_by_title(conn,title):
    cur = conn.cursor()
    cur.execute('SELECT song_id FROM songs WHERE title = ?',(title,))
    row = cur.fetchone()

    return row[0] if row else None


# Get all tags for song
def get_song_tags(conn,song_id):
    cur = conn.cursor()
    cur.execute('''
                SELECT t.tag_name
                FROM tags AS t 
                JOIN song_tags AS st ON t.tag_id = st.tag_id
                WHERE st.song_id = ?
                ''',(song_id,))
    
    return [r[0] for r in cur.fetchall()]


# Store similarity score between two songs
def store_song_similarity(conn,id1,id2,score):
    cur = conn.cursor()
    cur.execute('''
                INSERT OR REPLACE INTO song_similarities (song_id1, song_id2, shared_tags) VALUES (?,?,?)
                ''',(id1,id2,score))
    conn.commit()


# Get similar songs by tag count
def get_top_similar_songs(conn, song_id, limit = 5):
    cur = conn.cursor()
    cur.execute('''
                SELECT s.song_id, s.title, ss.shared_tags,s.url
                FROM song_similarities AS ss
                JOIN songs AS s ON ss.song_id2 = s.song_id
                WHERE ss.song_id1 = ?
                ORDER BY ss.shared_tags DESC, s.title ASC
                LIMIT ?
                ''',(song_id,limit))

    return cur.fetchall()


if __name__ == "__main__":
    conn = init_db()
    print("Database ready.")
    conn.close()