# biz_ownership.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys

DB_PATH = "phoenix.db"

class OwnershipManager:
    def __init__(self, root, biz_id):
        self.root = root
        self.biz_id = biz_id
        self.root.title(f"Ownership History - Business ID {biz_id}")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

        self.setup_ui()
        self.load_ownerships()

    def setup_ui(self):
        self.tree = ttk.Treeview(self.root, columns=("person_id", "Name", "Type", "Start", "End", "Notes"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10)

        ttk.Button(btn_frame, text="Add Owner", command=self.add_owner).pack(side="left")
        ttk.Button(btn_frame, text="Edit", command=self.edit_owner).pack(side="left")
        ttk.Button(btn_frame, text="Delete", command=self.delete_owner).pack(side="left")

    def load_ownerships(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("""
            SELECT o.person_id, 
                   p.first_name || ' ' || IFNULL(p.middle_name || ' ', '') || p.last_name AS full_name,
                   o.ownership_type, o.start_date, o.end_date, o.notes
            FROM BizOwnership o
            JOIN People p ON o.person_id = p.id
            WHERE o.biz_id = ?
            ORDER BY o.start_date
        """, (self.biz_id,))
        for row in self.cursor.fetchall():
            self.tree.insert('', 'end', values=row)

    def add_owner(self):
        self.open_editor()

    def edit_owner(self):
        selected = self.tree.selection()
        if not selected:
            return
        person_id = self.tree.item(selected[0])['values'][0]
        self.open_editor(person_id)

    def delete_owner(self):
        selected = self.tree.selection()
        if not selected:
            return
        person_id = self.tree.item(selected[0])['values'][0]
        confirm = messagebox.askyesno("Delete", "Delete selected ownership record?")
        if confirm:
            self.cursor.execute("DELETE FROM BizOwnership WHERE biz_id = ? AND person_id = ?", (self.biz_id, person_id))
            self.conn.commit()
            self.load_ownerships()

    def open_editor(self, person_id=None):
        win = tk.Toplevel(self.root)
        win.title("Edit Owner" if person_id else "Add Owner")

        ttk.Label(win, text="Person ID:").grid(row=0, column=0, padx=5, pady=5)
        entry_person = ttk.Entry(win, width=10)
        entry_person.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(win, text="Ownership Type:").grid(row=1, column=0, padx=5, pady=5)
        entry_type = ttk.Entry(win, width=30)
        entry_type.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(win, text="Start Date:").grid(row=2, column=0, padx=5, pady=5)
        entry_start = ttk.Entry(win, width=20)
        entry_start.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(win, text="End Date:").grid(row=3, column=0, padx=5, pady=5)
        entry_end = ttk.Entry(win, width=20)
        entry_end.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(win, text="Notes:").grid(row=4, column=0, padx=5, pady=5)
        entry_notes = ttk.Entry(win, width=40)
        entry_notes.grid(row=4, column=1, padx=5, pady=5)

        if person_id:
            self.cursor.execute("SELECT * FROM BizOwnership WHERE biz_id = ? AND person_id = ?", (self.biz_id, person_id))
            row = self.cursor.fetchone()
            if row:
                entry_person.insert(0, row[1])
                entry_type.insert(0, row[2])
                entry_start.insert(0, row[3])
                entry_end.insert(0, row[4])
                entry_notes.insert(0, row[5])

        def save():
            person = entry_person.get().strip()
            type_ = entry_type.get().strip()
            start = entry_start.get().strip()
            end = entry_end.get().strip()
            notes = entry_notes.get().strip()
            if not person:
                messagebox.showerror("Error", "Person ID required.")
                return

            if person_id:  # Editing
                self.cursor.execute("""
                    UPDATE BizOwnership
                    SET ownership_type=?, start_date=?, end_date=?, notes=?
                    WHERE biz_id=? AND person_id=?
                """, (type_, start, end, notes, self.biz_id, person))
            else:  # Adding
                self.cursor.execute("""
                    INSERT INTO BizOwnership (biz_id, person_id, ownership_type, start_date, end_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (self.biz_id, person, type_, start, end, notes))
            self.conn.commit()
            win.destroy()
            self.load_ownerships()

        ttk.Button(win, text="Save", command=save).grid(row=5, column=0, columnspan=2, pady=10)


def main():
    if len(sys.argv) < 2:
        print("Usage: python biz_ownership.py <biz_id>")
        return

    biz_id = int(sys.argv[1])
    root = tk.Tk()
    app = OwnershipManager(root, biz_id)
    root.geometry("800x400")
    root.mainloop()

if __name__ == "__main__":
    main()