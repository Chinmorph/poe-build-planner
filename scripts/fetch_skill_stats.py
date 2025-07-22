# scripts/fetch_skill_stats.py
import sqlite3, pathlib, re

ROOT      = pathlib.Path(__file__).resolve().parents[1]
SK_DIR    = ROOT / "external" / "pob" / "src" / "Data" / "Skills"
DB        = ROOT / "data" / "poe.db"

FILES = [
    "act_str.lua","act_dex.lua","act_int.lua",
    "sup_str.lua","sup_dex.lua","sup_int.lua",
    "glove.lua","minion.lua","spectre.lua","other.lua",
]

HDR_RE = re.compile(r'\["(?P<name>[^"]+)"\]\s*=\s*{', re.S)
STAT_LIST_RE = re.compile(r'stats\s*=\s*{([^}]*)}', re.S)
LVL_START_RE = re.compile(r'\[\d+\]\s*=\s*{')
NUM_RE = re.compile(r'^[\s]*([-\d\.]+)')

def balance(text:str, idx:int) -> tuple[str,int]:
    """liefert den Block-inhalt (ohne äußere {}) und End-Index hinter „}“"""
    depth, i = 1, idx + 1
    while depth and i < len(text):
        if text[i] == "{": depth += 1
        elif text[i] == "}": depth -= 1
        i += 1
    return text[idx + 1:i - 1], i

def fetch_entries():
    for fn in FILES:
        body = (SK_DIR / fn).read_text(encoding="utf-8", errors="ignore")
        pos = 0
        while (m:=HDR_RE.search(body, pos)):
            name, pos = m.group("name"), m.end()
            # ── stats-Liste ───────────────────────────────
            s_m = STAT_LIST_RE.search(body, pos)
            if not s_m: continue
            stat_names = [
                s.strip().strip('"') for s in s_m.group(1).split(",") if s.strip()
            ]
            # ── levels-Block ─────────────────────────────
            lv_idx = body.find("levels", pos)
            if lv_idx == -1: continue
            brace = body.find("{", lv_idx)
            if brace == -1:  continue
            lv_block, block_end = balance(body, brace)

            # Einzelne Level-Einträge parsen
            lv_pos, row = 0, 1
            while (l_m:=LVL_START_RE.search(lv_block, lv_pos)):
                entry, lv_pos = balance(lv_block, l_m.end()-1)
                # numeric literals – der Reihe nach
                values=[]
                for part in entry.split(","):
                    part = part.strip()
                    if "=" in part:              # benannte Felder überspringen
                        continue
                    if (n:=NUM_RE.match(part)):
                        values.append(float(n.group(1)))
                for stat, val in zip(stat_names, values):
                    yield name, row, stat, val
                row += 1

# ---------- DB ---------- #
def main():
    # Mapping aus Tabelle gems: id → name
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("SELECT id, name FROM gems")
    id2name = dict(cur.fetchall())

    # Einzigartige Stat-Einträge sammeln und gleich in GUI-Namen umwandeln
    unique = {}
    for key, lvl, stat, val in fetch_entries():
        name_gui = id2name.get(key, key)          # auf GUI-Namen abbilden
        uniq_key = (name_gui, lvl, stat)
        if uniq_key not in unique:
            unique[uniq_key] = val

    cur.executescript("""
        DROP TABLE IF EXISTS gem_level_stats;
        CREATE TABLE gem_level_stats (
            name TEXT,
            lvl  INTEGER,
            stat TEXT,
            value REAL,
            PRIMARY KEY (name, lvl, stat)
        );
    """)
    cur.executemany(
        "INSERT INTO gem_level_stats VALUES (?,?,?,?)",
        [(n, l, s, v) for (n, l, s), v in unique.items()]
    )
    conn.commit()
    print(f"✅ {len(unique):,} Stat-Einträge gespeichert.")
    conn.close()

if __name__ == "__main__":
    main()