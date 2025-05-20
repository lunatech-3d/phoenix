# business.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import webbrowser

DB_PATH = "phoenix.db"

class BusinessManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Business Search")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

        self.sort_column = None
        self.sort_reverse = False

        self.setup_ui()
        self.load_businesses()

    def setup_ui(self):
        # Search frame
        search_frame = ttk.LabelFrame(self.root, text="Search")
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Name:").grid(row=0, column=0, padx=5, pady=3)
        self.name_entry = ttk.Entry(search_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(search_frame, text="Year:").grid(row=0, column=2, padx=5, pady=3)
        self.year_entry = ttk.Entry(search_frame, width=10)
        self.year_entry.grid(row=0, column=3, padx=5, pady=3)

        ttk.Label(search_frame, text="Type:").grid(row=0, column=4, padx=5, pady=3)
        self.type_entry = ttk.Entry(search_frame, width=20)
        self.type_entry.grid(row=0, column=5, padx=5, pady=3)

        ttk.Button(search_frame, text="Search", command=self.load_businesses).grid(row=0, column=6, padx=10)
        ttk.Button(search_frame, text="Reset", command=self.reset_filters).grid(row=0, column=7, padx=5)

        # Action buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(button_frame, text="Add Business", command=self.add_business).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete Business", command=self.delete_business).pack(side="left", padx=5)

        # Treeview
        self.tree = ttk.Treeview(self.root, columns=("biz_id", "Name", "Category", "Start", "End", "URL"), show="headings")
        for col in ("biz_id", "Name", "Category", "Start", "End", "URL"):
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))

        self.tree.column("biz_id", width=10, anchor="w")
        self.tree.column("Name", width=200, anchor="w")
        self.tree.column("Category", width=100, anchor="w")
        self.tree.column("Start", width=80, anchor="w")
        self.tree.column("End", width=80, anchor="w")
        self.tree.column("URL", width=200, anchor="w")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.edit_business)

    def reset_filters(self):
        self.name_entry.delete(0, tk.END)
        self.year_entry.delete(0, tk.END)
        self.type_entry.delete(0, tk.END)
        self.load_businesses()

    def sort_by_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        items.sort(reverse=self.sort_column == col and not self.sort_reverse)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, '', idx)
        self.sort_column = col
        self.sort_reverse = not (self.sort_column == col and self.sort_reverse)

    def load_businesses(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        query = "SELECT biz_id, biz_name, category, start_date, end_date, external_url FROM Biz WHERE 1=1"
        params = []

        name = self.name_entry.get().strip()
        year = self.year_entry.get().strip()
        btype = self.type_entry.get().strip()

        if name:
            query += " AND biz_name LIKE ?"
            params.append(f"%{name}%")
        if year:
            query += " AND (? BETWEEN IFNULL(start_date, '') AND IFNULL(end_date, '9999'))"
            params.append(year)
        if btype:
            query += " AND category LIKE ?"
            params.append(f"%{btype}%")

        query += " ORDER BY biz_name"
        self.cursor.execute(query, params)

        for row in self.cursor.fetchall():
            self.tree.insert('', 'end', values=row)

    def add_business(self):
        import editbiz
        editbiz.open_edit_business_form()

    def edit_business(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        biz_id = self.tree.item(selected[0])['values'][0]
        import editbiz
        editbiz.open_edit_business_form(biz_id)

    def delete_business(self):
        selected = self.tree.selection()
        if not selected:
            return
        biz_id = self.tree.item(selected[0])['values'][0]
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this business?")
        if confirm:
            self.cursor.execute("DELETE FROM Biz WHERE biz_id = ?", (biz_id,))
            self.conn.commit()
            self.load_businesses()


def main():
    root = tk.Tk()
    app = BusinessManager(root)
    root.geometry("1000x600")
    root.mainloop()

if __name__ == "__main__":
    main()
