# scripts/fetch_skill_descriptions.py
import sqlite3, requests, re, os, pathlib

BASE = "https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding/master/src/Data/Skills/"
FILES = [
    "act_str.lua","act_dex.lua","act_int.lua",
    "sup_str.lua","sup_dex.lua","sup_int.lua",
    "glove.lua","minion.lua","spectre.lua","other.lua",
]
DB = "data/poe.db"
DESC_RE = re.compile(
    r'name\s*=\s*"(?P<name>[^"]+)"[^}]*?description\s*=\s*"(?P<desc>[^"]+)"',
    re.S
)

def fetch(fname: str) -> str:
    r = requests.get(BASE + fname, timeout=30)
    r.raise_for_status()
    return r.text

def gather_descriptions() -> dict[str, str]:
    out = {}
    for f in FILES:
        text = fetch(f)
        for m in DESC_RE.finditer(text):
            out[m.group("name")] = m.group("desc")
    return out

def update_db(desc_map: dict[str, str]):
    if not pathlib.Path(DB).exists():
        raise FileNotFoundError("poe.db nicht gefunden – bitte erst fetch_gems.py laufen lassen.")
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        changes = 0
        for name, desc in desc_map.items():
            cur.execute(
                "UPDATE gems SET description = ? WHERE name = ? AND description = 'Keine Beschreibung gefunden.'",
                (desc, name),
            )
            changes += cur.rowcount
        conn.commit()
    print(f"✅ {changes} Beschreibungen aktualisiert.")

def main():
    print("Lade Skill-Dateien …")
    descs = gather_descriptions()
    update_db(descs)

if __name__ == "__main__":
    main()