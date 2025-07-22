# scripts/fetch_skills.py
import os, sqlite3, requests, re
from slpp import slpp as lua

BASE_URL = "https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding/master/src/Data/Skills/"
SKILL_FILES = [
    "act_str.lua","act_dex.lua","act_int.lua",
    "sup_str.lua","sup_dex.lua","sup_int.lua",
    "glove.lua","minion.lua","spectre.lua","other.lua",
]
DB_PATH = "data/poe.db"

def download_lua(fname:str)->str:
    resp = requests.get(BASE_URL+fname, timeout=30)
    resp.raise_for_status()
    return resp.text

def lua_to_dict(code:str)->dict:
    # Entferne 'return' am Anfang der Datei
    code = re.sub(r"^[\s\r\n]*return\s+", "", code, 1, flags=re.S)
    return lua.decode(code)

def write_db(entries:list[dict]):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS skills")
        c.execute("""
            CREATE TABLE skills(
                id TEXT PRIMARY KEY,
                name TEXT,
                gemTags TEXT,
                description TEXT
            )
        """)
        for e in entries:
            c.execute(
                "INSERT INTO skills VALUES (?,?,?,?)",
                (
                    e.get("id",""),
                    e.get("name",""),
                    ",".join(e.get("gemTags",[])),
                    e.get("description","")
                )
            )
        conn.commit()

def main():
    all_entries = []
    for f in SKILL_FILES:
        lua_code = download_lua(f)
        tbl = lua_to_dict(lua_code)

        # unterschiedliche Rückgabetypen handhaben
        if isinstance(tbl, dict):
            entries = list(tbl.values())
        elif isinstance(tbl, list):
            entries = tbl
        else:
            print(f"⚠️  {f}: unerwarteter Typ {type(tbl)} – übersprungen")
            entries = []

        all_entries.extend(entries)
        print(f"{f} → {len(entries)} Einträge importiert")

if __name__ == "__main__":
    main()