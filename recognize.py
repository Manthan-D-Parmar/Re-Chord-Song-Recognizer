import os
import sounddevice as sd
import soundfile as sf

from db import init_db, get_top_similar_songs
from fingerprint import fingerprint

#CONSTANTS
T_RECORD = 5
SR = 22050
TEMP_FOLDER = "temp"
TEMP_PATH = os.path.join(TEMP_FOLDER,'recorded.wav')
MATCH_LIM = 5
RECOMMEND_LIM = 5

def find_best_match(conn,hashes):
    cur = conn.cursor()
    matches = {}

    for hash,test_offset in hashes:
        cur.execute('SELECT song_id, offset FROM fingerprints WHERE hash = ?',(hash,))
        ans = cur.fetchall()

        for song_id,song_offset in ans:
            diff = round(song_offset - test_offset,2)
            key = (song_id,diff)
            if key in matches:
                matches[key]+=1
            else:
                matches[key] = 1

    if not matches:
        return None,0
    
    best_key = max(matches,key = matches.get)
    best_song_id,_ = best_key
    best_score = matches[best_key]

    if best_score >= MATCH_LIM:
        return best_song_id, best_score
    else:
        return None,0


def recognize(conn,audio_path):
    hashes = fingerprint(audio_path)
    song_id, score = find_best_match(conn,hashes)

    if song_id is None:
        return None,0,None,""
    
    cur = conn.cursor()
    cur.execute('SELECT title,url FROM songs WHERE song_id = ?',(song_id,))
    row = cur.fetchone()
    title = row[0] if row else None
    url = row[1] if row else None
    similar_songs = get_top_similar_songs(conn,song_id,limit = RECOMMEND_LIM)

    return title,score,similar_songs,url
