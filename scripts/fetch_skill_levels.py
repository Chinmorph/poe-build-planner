# scripts/fetch_skill_levels.py
import sqlite3, re, pathlib, itertools

P_ROOT    = pathlib.Path(__file__).resolve().parents[1]
SKILL_DIR = P_ROOT / "external" / "pob" / "src" / "Data" / "Skills"
DB_PATH   = P_ROOT / "data" / "poe.db"

FILES = [
    "act_str.lua","act_dex.lua","act_int.lua",
    "sup_str.lua","sup_dex.lua","sup_int.lua",
    "glove.lua","minion.lua","spectre.lua","other.lua",
]

HDR_RE = re.compile(r'\["(?P<name>[^"]+)"\]\s*=\s*{', re.S)
LVL_START_RE = re.compile(r'\[\d+\]\s*=\s*{')

FIELD_INT  = re.compile(r'\b(levelRequirement|manaCost)\s*=\s*(\d+)')
FIELD_FLOAT= re.compile(r'\bdamageEffectiveness\s*=\s*([-\d\.]+)')

def scan_levels(block: str) -> list[dict]:
    """Zerlegt den 'levels = { … }'-Block in einzelne Einträge und holt Kernfelder."""
    entries = []
    idx = 0
    while True:
        m = LVL_START_RE.search(block, idx)
        if not m:
            break
        i = m.end()  # Position nach der öffnenden '{'
        depth = 1
        while depth and i < len(block):
            if block[i] == "{":
                depth += 1
            elif block[i] == "}":
                depth -= 1
            i += 1
        entry = block[m.end():i-1]  # Inhalt ohne äußere {}
        idx = i                     # Weitersuchen ab hier

        # Kern-Stats herausfischen
        fields_int   = {k:int(v) for k,v in FIELD_INT.findall(entry)}
        dmg_eff_m    = FIELD_FLOAT.search(entry)
        dmg_eff      = float(dmg_eff_m.group(1)) if dmg_eff_m else 1.0

        entries.append({
            "requiredLevel": fields_int.get("levelRequirement", 0),
            "manaCost":      fields_int.get("manaCost", 0),
            "dmgEff":        dmg_eff,
        })
    return entries

def gather_all():
    for fname in FILES:
        text = (SKILL_DIR / fname).read_text(encoding="utf-8", errors="ignore")
        pos = 0
        while True:
            h = HDR_RE.search(text, pos)
            if not h:
                break
            name = h.group("name")
            # Finde 'levels = {' ab h.end()
            levels_idx = text.find("levels", h.end())
            if levels_idx == -1:
                pos = h.end()
                continue
            brace_start = text.find("{", levels_idx)
            if brace_start == -1:
                pos = h.end()
                continue
            # Klammern balancieren, um Ende des Blocks zu finden
            depth, j = 1, brace_start + 1
            while depth and j < len(text):
                if text[j] == "{": depth += 1
                elif text[j] == "}": depth -= 1
                j += 1
            lvl_block = text[brace_start + 1 : j - 1]
            levels = scan_levels(lvl_block)
            if levels:
                yield name, levels
            pos = j  # weitersuchen nach diesem Skill-Block

def update_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS gem_levels")
        cur.execute("""
            CREATE TABLE gem_levels (
                name TEXT,
                lvl  INTEGER,
                requiredLevel INTEGER,
                manaCost INTEGER,
                dmgEff REAL,
                PRIMARY KEY (name, lvl)
            )
        """)
        rows = []
        for name, lvls in gather_all():
            for idx, d in enumerate(lvls, start=1):
                rows.append((name, idx, d["requiredLevel"], d["manaCost"], d["dmgEff"]))
        cur.executemany("INSERT INTO gem_levels VALUES (?,?,?,?,?)", rows)
        conn.commit()
    print(f"✅ {len(rows):,} Level-Einträge gespeichert.")

if __name__ == "__main__":
    update_db()