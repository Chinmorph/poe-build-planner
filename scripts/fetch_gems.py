"""
Lädt die aktuelle Gems.lua aus dem Path-of-Building-Community-Repo,
wandelt die Lua-Tabelle mit slpp in Python um und schreibt eine
sehr einfache Gems-Tabelle in data/poe.db (SQLite).
"""

import pathlib, sqlite3, requests, re
from slpp import SLPP as slpp

URL = "https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding/dev/src/Data/Gems.lua"
DB  = pathlib.Path("data/poe.db")

def fetch_lua(url: str) -> str:
    print("⏬  Lade Gems.lua …")
    resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return resp.text

def lua_to_dict(lua_code: str) -> dict:
    """
    Nimmt alles ab 'return {' bis zum Dateiende
    und wandelt es mit slpp in ein Python-Dict.
    """
    start = lua_code.find("return {")
    if start == -1:
        raise ValueError("Keine 'return {'-Stelle gefunden")
    table_text = lua_code[start + len("return "):]   # beginnt mit '{'
    return slpp().decode(table_text)

def save_to_sqlite(gems: dict):
    DB.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS gems (
            key   TEXT PRIMARY KEY,
            name  TEXT,
            tag   TEXT
        )""")
        conn.executemany(
            "INSERT OR REPLACE INTO gems VALUES (?,?,?)",
            (
                (k, v.get("name", k), ",".join(v.get("tags", [])))
                for k, v in gems.items()
            ),
        )
        conn.commit()
    print(f"✅  {len(gems):,} Gems in {DB} gespeichert.")

def main():
    lua_text = fetch_lua(URL)
    gems_dict = lua_to_dict(lua_text)
    save_to_sqlite(gems_dict)

if __name__ == "__main__":
    main()