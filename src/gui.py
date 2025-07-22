# src/gui.py
import sys, sqlite3, pathlib
from PySide6.QtWidgets import (
    QApplication, QWidget, QListWidget, QTextEdit,
    QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem
)

DB_PATH = pathlib.Path(__file__).parent.parent / "data" / "poe.db"

class GemViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PoE Gem Viewer")
        self.conn = sqlite3.connect(DB_PATH)

        # Widgets
        self.listWidget = QListWidget()
        self.descBox    = QTextEdit(readOnly=True)
        self.levelTable = QTableWidget()
        self.statTable  = QTableWidget()

        # Level-Tabelle
        self.levelTable.setColumnCount(4)
        self.levelTable.setHorizontalHeaderLabels(["Lvl", "Req Lvl", "Mana", "Dmg Eff"])
        self.levelTable.cellClicked.connect(self.show_stats)

        # Layout
        right = QVBoxLayout()
        right.addWidget(self.descBox, 3)
        right.addWidget(self.levelTable, 2)
        right.addWidget(self.statTable, 3)

        main = QHBoxLayout(self)
        main.addWidget(self.listWidget, 30)
        main.addLayout(right, 70)

        # Daten laden
        self.load_gems()
        self.listWidget.currentTextChanged.connect(self.show_details)

    # ---------- DB-Hilfen ----------
    def load_gems(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM gems ORDER BY name COLLATE NOCASE")
        for (name,) in cur.fetchall():
            self.listWidget.addItem(name)

    def show_details(self, gem_name: str):
        self.current_gem = gem_name
        cur = self.conn.cursor()

        # Beschreibung
        cur.execute("SELECT description FROM gems WHERE name = ?", (gem_name,))
        desc = cur.fetchone()
        self.descBox.setPlainText(f"{gem_name}\n\n{desc[0] if desc else ''}")

        # Level-Tabelle
        cur.execute(
            "SELECT lvl, requiredLevel, manaCost, dmgEff "
            "FROM gem_levels WHERE name = ? ORDER BY lvl",
            (gem_name,))
        rows = cur.fetchall()
        self.levelTable.setRowCount(len(rows))
        for r, (lvl, req, mana, dmg) in enumerate(rows):
            for c, val in enumerate([lvl, req, mana, f"{dmg:.2f}"]):
                self.levelTable.setItem(r, c, QTableWidgetItem(str(val)))
        self.levelTable.resizeColumnsToContents()

        # Leere Stat-Tabelle
        self.statTable.setRowCount(0)
        self.statTable.setColumnCount(0)

    def show_stats(self, row: int, _col: int):
        lvl = int(self.levelTable.item(row, 0).text())
        cur = self.conn.cursor()

        # 1) nach Klartext-Name suchen
        # Level-Zeilen holen – erst nach Name, dann nach Gem-ID
        cur.execute(
            "SELECT lvl, requiredLevel, manaCost, dmgEff "
            "FROM gem_levels WHERE name = ? ORDER BY lvl",
            (gem_name := self.current_gem,)
        )
        rows = cur.fetchall()

        if not rows:
            cur.execute("SELECT id FROM gems WHERE name = ?", (gem_name,))
            r = cur.fetchone()
            if r:
                gem_id = r[0]
                cur.execute(
                    "SELECT lvl, requiredLevel, manaCost, dmgEff "
                    "FROM gem_levels WHERE name = ? ORDER BY lvl",
                    (gem_id,)
                )
                rows = cur.fetchall()

        # 2) falls leer: über Gem-ID gehen
        if not stats:
            cur.execute("SELECT id FROM gems WHERE name = ?", (self.current_gem,))
            r = cur.fetchone()
            if r:
                gem_id = r[0]
                cur.execute(
                    "SELECT stat, value FROM gem_level_stats "
                    "WHERE name = ? AND lvl = ? ORDER BY stat",
                    (gem_id, lvl)
                )
                stats = cur.fetchall()

        # Tabelle befüllen
        self.statTable.setColumnCount(2)
        self.statTable.setHorizontalHeaderLabels(["Stat", "Value"])
        self.statTable.setRowCount(len(stats))
        for r, (stat, val) in enumerate(stats):
            self.statTable.setItem(r, 0, QTableWidgetItem(stat))
            self.statTable.setItem(r, 1, QTableWidgetItem(f"{val:g}"))
        self.statTable.resizeColumnsToContents()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = GemViewer()
    viewer.resize(1000, 700)
    viewer.show()
    sys.exit(app.exec())