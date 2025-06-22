import os

from db import init_db,add_song,store_fingerprints,add_tag,add_song_tag,get_song_id_by_title,get_song_tags,store_song_similarity

from fingerprint import fingerprint

#CONSTANTS
SONGS_DIR = os.path.join(os.path.dirname(__file__),'data')
TAGS_FILE = '_songs_tags.txt'
URLS_FILE = '_songs_url.txt'
TOP_N = 5

def parse_songs_tags(tags_path):
    songs = []
    with open(tags_path,'r',encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    i = 0
    while i < len(lines): 
        line = lines[i]
        if '|' in line:
            title = line.split('|',1)[1]
            tags = lines[i+1].split() # tag1,tag2,...
            songs.append((title,tags))
            i+=2 # skip title + tags
        else: # if no | skip
            i+=1

    return songs


def import_songs_and_tags(conn,songs):
    song_ids = {}
    
    for title, tags in songs:
        song_id = get_song_id_by_title(conn,title)
        if song_id is None:
            song_id = add_song(conn,title)
        song_ids[title] = song_id

        for tag in tags:
            tag_id = add_tag(conn,tag)
            add_song_tag(conn,song_id,tag_id)


    return song_ids


def compute_and_store_similarities(conn,song_ids):
    titles = list(song_ids.keys())

    for t1 in titles:
        id1 = song_ids[t1]
        tags1 = set(get_song_tags(conn,id1))
        similar = []

        for t2 in titles:
            if t1 == t2:
                continue

            id2 = song_ids[t2]
            tags2 = set(get_song_tags(conn,id2))
            shared = len(tags1 & tags2)
            if shared > 0:
                similar.append((id2,shared))

        similar.sort(key = lambda x : (-x[1],x[0]))

        for id2, count in similar[:TOP_N]:
            store_song_similarity(conn,id1,id2,count)


def process_songs():
    conn = init_db()
    
    for fname in os.listdir(SONGS_DIR):
        if not fname.lower().endswith('.mp3'):
            continue

        title = os.path.splitext(fname)[0]
        path = os.path.join(SONGS_DIR,fname)

        print("Processing: ",title)
        song_id = add_song(conn,title)
        print(" ID : ", song_id)

        hashes = fingerprint(path)
        print("Generated ",len(hashes)," hashes")
        store_fingerprints(conn,song_id,hashes)

    tags_path = os.path.join(SONGS_DIR,TAGS_FILE)
    songs_and_tags = parse_songs_tags(tags_path)

    urls_path = os.path.join(SONGS_DIR,URLS_FILE)
    
    url_map = {}
    if os.path.exists(urls_path):
        with open(urls_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            for i in range(0, len(lines), 2):
                if i+1 < len(lines):
                    raw_title = lines[i]
                    if '|' in raw_title:
                        title = raw_title.split('|', 1)[1].strip()
                    else:
                        title = raw_title.strip()
                    url = lines[i+1]
                    url_map[title] = url

    

    song_ids = import_songs_and_tags(conn,songs_and_tags)
    compute_and_store_similarities(conn,song_ids)
    # Update each song with its URL
    for fname in os.listdir(SONGS_DIR):
        if not fname.lower().endswith('.mp3'):
            continue
        title = os.path.splitext(fname)[0]
        if title in url_map:
            conn.execute("UPDATE songs SET url = ? WHERE title = ?", (url_map[title], title))
    conn.commit()
    print("All songs, tags and similarities are imported.")
    conn.close()


if __name__ == "__main__":
    process_songs()