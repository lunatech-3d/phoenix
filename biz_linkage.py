
import tkinter as tk
from tkinter import ttk
import sqlite3

DB_PATH = "phoenix.db"

def open_biz_linkage_popup(callback):
    def refresh_tree():
        name_filter = name_var.get().strip().lower()
        cat_filter = category_var.get().strip().lower()
        year_filter = year_var.get().strip()

        query = "SELECT biz_id, biz_name, start_date, end_date, category FROM Biz WHERE 1=1"
        params = []

        if name_filter:
            query += " AND LOWER(biz_name) LIKE ?"
            params.append(f"%{name_filter}%")
        if cat_filter:
            query += " AND LOWER(category) LIKE ?"
            params.append(f"%{cat_filter}%")
        if year_filter.isdigit():
            query += " AND (start_date >= ? OR end_date >= ?)"
            params.append(year_filter)
            params.append(year_filter)

        query += " ORDER BY biz_name"

        for item in tree.get_children():
            tree.delete(item)

        cursor = conn.cursor()
        cursor.execute(query, params)
        for row in cursor.fetchall():
            tree.insert('', 'end', values=row)

    def select_and_return():
        selected = tree.selection()
        if selected:
            biz_id = tree.item(selected[0])['values'][0]
            callback(biz_id)
            popup.destroy()

    conn = sqlite3.connect(DB_PATH)
    popup = tk.Toplevel()
    popup.title("Select Business")
    popup.geometry("850x500")

    # Search fields
    search_frame = ttk.Frame(popup)
    search_frame.pack(fill="x", padx=10, pady=5)

    ttk.Label(search_frame, text="Business Name:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
    name_var = tk.StringVar()
    ttk.Entry(search_frame, textvariable=name_var, width=25).grid(row=0, column=1, padx=5, pady=2)

    ttk.Label(search_frame, text="Category:").grid(row=0, column=2, padx=5, pady=2, sticky="e")
    category_var = tk.StringVar()
    ttk.Entry(search_frame, textvariable=category_var, width=20).grid(row=0, column=3, padx=5, pady=2)

    ttk.Label(search_frame, text="Start Year ≥").grid(row=0, column=4, padx=5, pady=2, sticky="e")
    year_var = tk.StringVar()
    ttk.Entry(search_frame, textvariable=year_var, width=8).grid(row=0, column=5, padx=5, pady=2)

    ttk.Button(search_frame, text="Search", command=refresh_tree).grid(row=0, column=6, padx=5)

    # Treeview
    columns = ("ID", "Name", "Start", "End", "Category")
    tree = ttk.Treeview(popup, columns=columns, show='headings', selectmode='browse')
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=160 if col == "Name" else 100)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # Double-click support
    tree.bind("<Double-1>", lambda e: select_and_return())

    # Buttons
    btn_frame = ttk.Frame(popup)
    btn_frame.pack(pady=5)
    ttk.Button(btn_frame, text="Select", command=select_and_return).pack(side="left", padx=10)
    ttk.Button(btn_frame, text="Cancel", command=popup.destroy).pack(side="left", padx=10)

    refresh_tree()  # Initial load

    popup.transient()
    popup.grab_set()
    popup.wait_window(popup)
