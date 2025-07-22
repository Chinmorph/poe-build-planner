# scripts/debug_count_levels.py
import pathlib, re

SKILL_DIR = pathlib.Path(__file__).resolve().parents[1] / "external" / "pob" / "src" / "Data" / "Skills"
FILES = [
    "act_str.lua","act_dex.lua","act_int.lua",
    "sup_str.lua","sup_dex.lua","sup_int.lua",
    "glove.lua","minion.lua","spectre.lua","other.lua",
]

LEVELS_RE = re.compile(r"\blevels\s*=\s*{")

def main():
    total_blocks = 0
    for f in FILES:
        p = SKILL_DIR / f
        if not p.exists():
            print(f"❌ Datei fehlt: {p}")
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        count = len(LEVELS_RE.findall(text))
        total_blocks += count
        print(f"{f:12} → {count} levels-Blöcke")
    print(f"\nGesamt: {total_blocks}")
    
if __name__ == "__main__":
    main()