import pathlib, sqlite3, requests

DB  = pathlib.Path("data/poe.db")
URL = "https://www.pathofexile.com/api/trade/data/skillgems?l=en"

def init_db(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS gems (
        id          TEXT PRIMARY KEY,
        name        TEXT,
        level_req   INTEGER,
        tags        TEXT,
        description TEXT
    )""")

def insert(conn, gems):
    for g in gems["result"]:
        conn.execute(
            "INSERT OR REPLACE INTO gems VALUES (?,?,?,?,?)",
            (
                g["id"],
                g["name"],
                g.get("levelRequirement", 1),
                ",".join(g.get("tags", [])),
                g.get("description", ""),
            ),
        )

def main():
    print("⏬  Lade Gem-Daten …")
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()               # bricht bei HTTP-Fehler ab
    data = resp.json()                    # jetzt erst in JSON wandeln
    DB.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB) as conn:
        init_db(conn)
        insert(conn, data)
        conn.commit()
    print(f"✅  {len(data['result'])} Gems in {DB} gespeichert.")

if __name__ == "__main__":
    main()