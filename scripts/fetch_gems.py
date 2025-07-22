# scripts/fetch_gems.py
import sqlite3, requests, re, os
from slpp import slpp as lua

URL = "https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding/master/src/Data/Gems.lua"
DB  = "data/poe.db"

def download() -> str:
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    return r.text

def parse(lua_src: str) -> dict:
    idx = lua_src.find("return")
    if idx == -1:
        raise ValueError("'return' keyword not found in Gems.lua")
    raw = lua_src[idx + 6 :].strip()
    return lua.decode(raw)          # → Python-Dict

def save(gems: dict):
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS gems")
        cur.execute("""
            CREATE TABLE gems (
                id          TEXT PRIMARY KEY,
                name        TEXT,
                description TEXT
            )
        """)
        cur.executemany(
            "INSERT INTO gems VALUES (?,?,?)",
            (
                (
                    gem_id,
                    g.get("name", ""),
                    g.get("description", "") or "Keine Beschreibung gefunden."
                )
                for gem_id, g in gems.items()
            )
        )
        conn.commit()

def main():
    raw   = download()
    gems  = parse(raw)
    save(gems)
    print(f"✅ {len(gems)} Gems importiert (mit Beschreibung).")

if __name__ == "__main__":
    main()