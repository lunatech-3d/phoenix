import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from edit_deed_dialog import EditDeedDialog
from add_deed_dialog import AddDeedDialog
from geodata import (
    has_geojson_data,
    manage_deed_geodata,
    view_all_geodata,
    add_geojson_data,
    edit_geojson_data,
    delete_geojson_data)

# -------------------------------
# DEEDS SECTION INIT & LOADER
# -------------------------------

def initialize_deed_section(parent_frame, connection, person_id):
    cursor = connection.cursor()

    deed_frame = ttk.LabelFrame(parent_frame, text="Deed Records")
    deed_frame.pack(fill=tk.X, padx=5, pady=5)

    deed_button_frame = ttk.Frame(deed_frame)
    deed_button_frame.pack(fill=tk.X, padx=5, pady=5)

    deed_record_frame = ttk.LabelFrame(deed_button_frame, text="Deed Record")
    deed_record_frame.pack(side=tk.LEFT, padx=5)

    deed_tree = ttk.Treeview(deed_frame,
        columns=("deed_id", "description_id", "map", "date", "type", "role", "with", "amount", "description", "notes"),
        show='headings', height=8)

    column_configs = [
        ("deed_id", 0, False),
        ("description_id", 0, False),
        ("map", 40, False),
        ("date", 75, False),
        ("type", 100, False),
        ("role", 80, False),
        ("with", 250, True),
        ("amount", 100, False),
        ("description", 475, True),
        ("notes", 150, False)
    ]

    for col, width, stretch in column_configs:
        deed_tree.column(col, width=width, stretch=stretch)
        deed_tree.heading(col, text=col.title())
    deed_tree.column("deed_id", width=0, stretch=False)
    deed_tree.column("description_id", width=0, stretch=False)

    ttk.Button(deed_record_frame, text="Add", command=lambda: add_deed_record(deed_tree, person_id)).pack(side=tk.LEFT, padx=2)
    ttk.Button(deed_record_frame, text="Edit", command=lambda: edit_deed_record(deed_tree, person_id)).pack(side=tk.LEFT, padx=2)
    ttk.Button(deed_record_frame, text="Delete", command=lambda: delete_deed_record(deed_tree, person_id)).pack(side=tk.LEFT, padx=2)

    # Add new Map Data buttons group
    map_data_frame = ttk.LabelFrame(deed_button_frame, text="Map Data")
    map_data_frame.pack(side=tk.LEFT, padx=5)
    
    ttk.Button(map_data_frame, text="Add", 
               command=lambda: manage_deed_geodata(deed_tree, person_id)).pack(side=tk.LEFT, padx=2)
    ttk.Button(map_data_frame, text="View All", 
               command=lambda: view_all_geodata(deed_tree, person_id)).pack(side=tk.LEFT, padx=2)


    scrollbar = ttk.Scrollbar(deed_frame, orient="vertical", command=deed_tree.yview)
    deed_tree.configure(yscrollcommand=scrollbar.set)
    deed_tree.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    return deed_tree


def load_deed_records(cursor, tree, person_id):
    tree.delete(*tree.get_children())

    query = """
        WITH CombinedDescriptions AS (
            SELECT 
                d.deed_id,
                GROUP_CONCAT(ld.description_text, ' and ') as combined_desc,
                COUNT(*) as segment_count
            FROM LegalDescriptions ld
            JOIN Deeds d ON ld.deed_id = d.deed_id
            GROUP BY d.deed_id
        )
        SELECT DISTINCT 
            d.deed_id,
            ld.description_id,
            (
                SELECT GROUP_CONCAT(DISTINCT gd.feature_type)
                FROM GeoJSONLink gl
                JOIN GeoJSONData gd ON gl.geojson_id = gd.geojson_id
                WHERE gl.record_type = 'Deed' 
                AND (gl.record_id = d.deed_id 
                     OR gl.legal_description_id IN (
                         SELECT description_id FROM LegalDescriptions WHERE deed_id = d.deed_id
                     ))
            ) as geodata_types,
            d.execution_date,
            d.deed_type,
            dp1.party_role,
            GROUP_CONCAT(CASE WHEN p.id != ? THEN TRIM(p.first_name || ' ' || p.last_name) ELSE '' END),
            d.consideration_amount,
            CASE WHEN cd.segment_count > 1 THEN cd.combined_desc ELSE ld.description_text END as display_description,
            d.notes
        FROM Deeds d
        JOIN DeedParties dp1 ON d.deed_id = dp1.deed_id AND dp1.person_id = ?
        JOIN DeedParties dp2 ON d.deed_id = dp2.deed_id
        JOIN People p ON dp2.person_id = p.id
        LEFT JOIN LegalDescriptions ld ON d.deed_id = ld.deed_id AND (ld.segment_order = 1 OR ld.segment_order IS NULL)
        LEFT JOIN CombinedDescriptions cd ON d.deed_id = cd.deed_id
        WHERE p.id != ?
        GROUP BY d.deed_id, dp1.party_role
        ORDER BY d.execution_date ASC
    """

    cursor.execute(query, (person_id, person_id, person_id))
    records = cursor.fetchall()

    type_icons = { 'POINT': '📍', 'LINE': '〰️', 'POLYGON': '⬡' }
    type_descriptions = {
        'POINT': 'Point Location',
        'LINE': 'Line Feature',
        'POLYGON': 'Boundary Feature'
    }

    for record in records:
        geodata_types = record[2].split(',') if record[2] else []
        map_indicator = ''.join(type_icons.get(t.strip(), '') for t in geodata_types if t.strip())
        amount = f"${float(record[7]):,.2f}" if record[7] else ""
        other_parties = ', '.join(filter(None, (record[6] or '').split(',')))
        description = record[8] or ""

        values = (
            record[0], record[1], map_indicator, record[3], record[4],
            record[5], other_parties, amount, description, record[9] or ""
        )

        tree.insert('', 'end', values=values)


# -------------------------------
# DEED CRUD HANDLERS
# -------------------------------

def add_deed_record(deed_tree, person_id):
    def refresh():
        connection = sqlite3.connect('phoenix.db')
        load_deed_records(connection.cursor(), deed_tree, person_id)
    dialog = AddDeedDialog(deed_tree.winfo_toplevel(), person_id)
    dialog.dialog.transient(deed_tree.winfo_toplevel())
    dialog.dialog.grab_set()
    deed_tree.winfo_toplevel().wait_window(dialog.dialog)
    refresh()

def edit_deed_record(deed_tree, person_id):
    selected_item = deed_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select a deed record to edit.")
        return
    def refresh():
        connection = sqlite3.connect('phoenix.db')
        load_deed_records(connection.cursor(), deed_tree, person_id)
    deed_id = deed_tree.item(selected_item[0])['values'][0]
    dialog = EditDeedDialog(deed_tree.winfo_toplevel(), person_id, deed_id)
    dialog.dialog.transient(deed_tree.winfo_toplevel())
    dialog.dialog.grab_set()
    deed_tree.winfo_toplevel().wait_window(dialog.dialog)
    refresh()

def delete_deed_record(deed_tree, person_id):
    selected_item = deed_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select a deed record to delete.")
        return

    deed_id = deed_tree.item(selected_item[0])['values'][0]
    connection = sqlite3.connect('phoenix.db')
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*) FROM GeoJSONLink 
            WHERE record_type = 'Deed' AND 
                  (record_id = ? OR legal_description_id IN (
                      SELECT description_id FROM LegalDescriptions WHERE deed_id = ?))
        """, (deed_id, deed_id))
        has_geodata = cursor.fetchone()[0] > 0

        confirm_msg = "Are you sure you want to delete this deed record?"
        if has_geodata:
            confirm_msg += "\n\nWarning: This deed has associated geographic data that will also be deleted."

        if not messagebox.askyesno("Confirm Delete", confirm_msg):
            return

        cursor.execute("BEGIN")
        cursor.execute("SELECT description_id FROM LegalDescriptions WHERE deed_id = ?", (deed_id,))
        desc_ids = [row[0] for row in cursor.fetchall()]

        for desc_id in desc_ids:
            cursor.execute("DELETE FROM GeoJSONLink WHERE record_type = 'Deed' AND legal_description_id = ?", (desc_id,))

        cursor.execute("DELETE FROM GeoJSONLink WHERE record_type = 'Deed' AND record_id = ? AND legal_description_id IS NULL", (deed_id,))
        cursor.execute("DELETE FROM GeoJSONData WHERE geojson_id NOT IN (SELECT DISTINCT geojson_id FROM GeoJSONLink)")
        cursor.execute("DELETE FROM LegalDescriptions WHERE deed_id = ?", (deed_id,))
        cursor.execute("DELETE FROM DeedParties WHERE deed_id = ?", (deed_id,))
        cursor.execute("DELETE FROM Deeds WHERE deed_id = ?", (deed_id,))

        connection.commit()
        load_deed_records(cursor, deed_tree, person_id)
        messagebox.showinfo("Success", "Deed record and all associated data deleted successfully.")

    except sqlite3.Error as e:
        connection.rollback()
        messagebox.showerror("Error", f"Failed to delete deed record: {str(e)}")

    finally:
        cursor.close()
        connection.close()
