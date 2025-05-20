# geodata.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# These functions were previously in editme.py and handle GeoJSON linking

def has_geojson_data(cursor, record_id, record_type):
    cursor.execute("""
        SELECT COUNT(*) 
        FROM GeoJSONLink 
        WHERE record_type = ? AND record_id = ?
    """, (record_type.capitalize(), record_id))
    return cursor.fetchone()[0] > 0

def manage_deed_geodata(deed_tree, person_id):
    selected_item = deed_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select a deed record to manage map data.")
        return

    deed_id = deed_tree.item(selected_item[0])['values'][0]
    from geodata_dialog import GeoDataDialog
    dialog = GeoDataDialog(deed_tree.winfo_toplevel(), "Deed", deed_id)
    deed_tree.winfo_toplevel().wait_window(dialog.dialog)


def view_all_geodata(deed_tree, person_id):
    messagebox.showinfo("Coming Soon", "The full mapping interface will be available in a future update.")

def add_geojson_data(tree, record_type, person_id):
    """Add GeoJSON data for selected record."""
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Select Record", 
                          f"Please select a {record_type} record to add map data.")
        return

    # Get the record info based on record type
    values = tree.item(selected[0])['values']
    
    if record_type == "tax":
        record_id = values[0]  # tax_id
        year = values[2]       
        title_suffix = f"Tax Record {year}"
        legal_description_id = None
    else:  # deed
        record_id = values[0]        # deed_id
        legal_description_id = values[1]  # description_id from tree
        execution_date = values[3]   # date column
        description = values[8]      # formatted description
        title_suffix = f"Deed Segment - {description}"

    # Check if map icon exists (GeoJSON data already exists)
    if values[2] == '🌎':  # Map column
        messagebox.showinfo("Map Data Exists", 
                          "This record already has map data. Use Edit to modify it.")
        return

    # Create window for GeoJSON entry
    geojson_window = tk.Toplevel()
    geojson_window.title(f"Add Map Data - {title_suffix}")
    geojson_window.geometry("600x500")

    main_frame = ttk.Frame(geojson_window, padding="10")
    main_frame.pack(fill='both', expand=True)

    # Instructions
    instructions = """Enter the coordinate pairs for the property boundary.
Format: longitude,latitude,longitude,latitude,...
Example: -83.45397,42.43816,-83.45344,42.42388"""
    
    ttk.Label(main_frame, text=instructions, 
             justify='left', wraplength=550).pack(pady=(0,10))

    # Coordinates entry
    ttk.Label(main_frame, text="Coordinates:*").pack(anchor='w')
    coords_text = tk.Text(main_frame, height=4, width=60)
    coords_text.pack(fill='x', pady=(0,10))

    # Description entry
    ttk.Label(main_frame, text="Description:").pack(anchor='w')
    desc_entry = ttk.Entry(main_frame, width=60)
    desc_entry.pack(fill='x', pady=(0,10))

    # Source entry
    ttk.Label(main_frame, text="Source:").pack(anchor='w')
    source_entry = ttk.Entry(main_frame, width=60)
    source_entry.pack(fill='x', pady=(0,10))

    # Date entries
    dates_frame = ttk.Frame(main_frame)
    dates_frame.pack(fill='x', pady=(0,10))

    ttk.Label(dates_frame, text="Start Date:").pack(side='left')
    start_date_entry = ttk.Entry(dates_frame, width=20)
    start_date_entry.pack(side='left', padx=(5,20))

    ttk.Label(dates_frame, text="End Date:").pack(side='left')
    end_date_entry = ttk.Entry(dates_frame, width=20)
    end_date_entry.pack(side='left', padx=5)

    def validate_and_save():
        """Validate and save the GeoJSON data"""
        coords = coords_text.get("1.0", "end-1c").strip()
        if not coords:
            messagebox.showerror("Error", "Please enter coordinates.")
            return

        # Basic validation - check if we have pairs of numbers
        coords_list = coords.split(',')
        if len(coords_list) < 6 or len(coords_list) % 2 != 0:
            messagebox.showerror("Error", 
                               "Please enter valid coordinate pairs.\nNeed at least 3 points.")
            return

        try:
            # Start transaction
            cursor.execute("BEGIN")

            # Insert into GeoJSONData
            cursor.execute("""
                INSERT INTO GeoJSONData (
                    geojson_text, description, source, 
                    start_date, end_date
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                coords,
                desc_entry.get().strip(),
                source_entry.get().strip(),
                start_date_entry.get().strip(),
                end_date_entry.get().strip()
            ))
            
            geojson_id = cursor.lastrowid

            # Create link to record with correct record type and legal_description_id if applicable
            if record_type == "deed":
                cursor.execute("""
                    INSERT INTO GeoJSONLink (
                        geojson_id, record_type, record_id, legal_description_id
                    ) VALUES (?, ?, ?, ?)
                """, (geojson_id, record_type.capitalize(), record_id, legal_description_id))
            else:
                cursor.execute("""
                    INSERT INTO GeoJSONLink (
                        geojson_id, record_type, record_id
                    ) VALUES (?, ?, ?)
                """, (geojson_id, record_type.capitalize(), record_id))

            connection.commit()
            geojson_window.destroy()
            
            # Refresh the appropriate tree
            if record_type == "tax":
                load_tax_records(cursor, tax_tree, person_id)
            else:
                load_deed_records(tree, person_id)
                
            messagebox.showinfo("Success", "Map data added successfully.")

        except sqlite3.Error as e:
            cursor.execute("ROLLBACK")
            messagebox.showerror("Error", f"Failed to save map data: {e}")

    # Button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill='x', pady=20)

    ttk.Button(button_frame, text="Save", 
              command=validate_and_save).pack(side='left', padx=5)
    ttk.Button(button_frame, text="Cancel", 
              command=geojson_window.destroy).pack(side='right', padx=5)


def edit_geojson_data(tree, record_type, person_id):
    """Edit GeoJSON data for selected record"""
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Select Record", 
                          f"Please select a {record_type} record to edit map data.")
        return

    values = tree.item(selected[0])['values']

    if record_type == "tax":
        record_id = values[0]
        year = values[2]
        title_suffix = f"Tax Record {year}"
        where_clause = "gl.record_type = ? AND gl.record_id = ?"
        where_params = (record_type.capitalize(), record_id)
    else:  # deed
        record_id = values[0]
        legal_description_id = values[1]  # description_id from tree
        execution_date = values[3]  # date column
        description = values[8]    # formatted description
        title_suffix = f"Deed Segment - {description}"
        where_clause = "gl.record_type = ? AND gl.legal_description_id = ?"
        where_params = (record_type.capitalize(), legal_description_id)

    # Verify GeoJSON data exists
    if values[2] != '🌎':  # Check Map column for icon
        messagebox.showinfo("No Map Data", 
                          f"This {record_type} doesn't have map data. Use Add to create it.")
        return

    # Get existing GeoJSON data
    try:
        cursor.execute(f"""
            SELECT gd.geojson_id, gd.geojson_text, gd.description, 
                   gd.source, gd.start_date, gd.end_date
            FROM GeoJSONData gd
            JOIN GeoJSONLink gl ON gd.geojson_id = gl.geojson_id
            WHERE {where_clause}
        """, where_params)
        
        geojson_data = cursor.fetchone()
        if not geojson_data:
            messagebox.showerror("Error", "Could not find map data.")
            return

        geojson_id, coords, description, source, start_date, end_date = geojson_data

        # Create edit window
        geojson_window = tk.Toplevel()
        geojson_window.title(f"Edit Map Data - {title_suffix}")
        geojson_window.geometry("600x500")

        main_frame = ttk.Frame(geojson_window, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Instructions
        instructions = """Edit the coordinate pairs for the property boundary.
Format: longitude,latitude,longitude,latitude,...
Example: -83.45397,42.43816,-83.45344,42.42388"""
        
        ttk.Label(main_frame, text=instructions, 
                 justify='left', wraplength=550).pack(pady=(0,10))

        # Coordinates entry
        ttk.Label(main_frame, text="Coordinates:*").pack(anchor='w')
        coords_text = tk.Text(main_frame, height=4, width=60)
        coords_text.insert("1.0", coords)
        coords_text.pack(fill='x', pady=(0,10))

        # Description entry
        ttk.Label(main_frame, text="Description:").pack(anchor='w')
        desc_entry = ttk.Entry(main_frame, width=60)
        desc_entry.insert(0, description if description else "")
        desc_entry.pack(fill='x', pady=(0,10))

        # Source entry
        ttk.Label(main_frame, text="Source:").pack(anchor='w')
        source_entry = ttk.Entry(main_frame, width=60)
        source_entry.insert(0, source if source else "")
        source_entry.pack(fill='x', pady=(0,10))

        # Date entries
        dates_frame = ttk.Frame(main_frame)
        dates_frame.pack(fill='x', pady=(0,10))

        ttk.Label(dates_frame, text="Start Date:").pack(side='left')
        start_date_entry = ttk.Entry(dates_frame, width=20)
        start_date_entry.insert(0, start_date if start_date else "")
        start_date_entry.pack(side='left', padx=(5,20))

        ttk.Label(dates_frame, text="End Date:").pack(side='left')
        end_date_entry = ttk.Entry(dates_frame, width=20)
        end_date_entry.insert(0, end_date if end_date else "")
        end_date_entry.pack(side='left', padx=5)

        def validate_and_save():
            """Validate and save the updated GeoJSON data"""
            coords = coords_text.get("1.0", "end-1c").strip()
            if not coords:
                messagebox.showerror("Error", "Please enter coordinates.")
                return

            # Basic validation - check if we have pairs of numbers
            coords_list = coords.split(',')
            if len(coords_list) < 6 or len(coords_list) % 2 != 0:
                messagebox.showerror("Error", 
                                   "Please enter valid coordinate pairs.\nNeed at least 3 points.")
                return

            try:
                # Start transaction
                cursor.execute("BEGIN")

                # Update GeoJSONData
                cursor.execute("""
                    UPDATE GeoJSONData SET
                        geojson_text = ?,
                        description = ?,
                        source = ?,
                        start_date = ?,
                        end_date = ?
                    WHERE geojson_id = ?
                """, (
                    coords,
                    desc_entry.get().strip(),
                    source_entry.get().strip(),
                    start_date_entry.get().strip(),
                    end_date_entry.get().strip(),
                    geojson_id
                ))

                connection.commit()
                geojson_window.destroy()
                
                # Refresh the appropriate tree
                if record_type == "tax":
                    load_tax_records(cursor, tax_tree, person_id)
                else:
                    load_deed_records(tree, person_id)
                    
                messagebox.showinfo("Success", "Map data updated successfully.")

            except sqlite3.Error as e:
                cursor.execute("ROLLBACK")
                messagebox.showerror("Error", f"Failed to update map data: {e}")

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)

        ttk.Button(button_frame, text="Save", 
                  command=validate_and_save).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=geojson_window.destroy).pack(side='right', padx=5)

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Database error: {e}")


def delete_geojson_data(tree, record_type, person_id):
    """Delete GeoJSON data for selected record"""
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Select Record", 
                          f"Please select a {record_type} record to delete map data.")
        return

    values = tree.item(selected[0])['values']
    
    # Set up record-specific parameters
    if record_type == "tax":
        record_id = values[0]
        year = values[2]
        record_display = f"tax record from {year}"
        where_clause = "record_type = ? AND record_id = ?"
        where_params = (record_type.capitalize(), record_id)
    else:  # deed
        record_id = values[0]
        legal_description_id = values[1]
        record_display = f"deed segment - {values[8]}"
        where_clause = "record_type = ? AND legal_description_id = ?"
        where_params = (record_type.capitalize(), legal_description_id)

    # Verify GeoJSON data exists
    if values[2] != '🌎':
        messagebox.showinfo("No Map Data", 
                          f"This {record_type} doesn't have map data to delete.")
        return

    # Confirm deletion
    if not messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete the map data for this {record_display}?"):
        return

    try:
        cursor.execute("BEGIN")

        # Get the geojson_id
        cursor.execute(f"""
            SELECT geojson_id 
            FROM GeoJSONLink 
            WHERE {where_clause}
        """, where_params)
        
        result = cursor.fetchone()
        if result:
            geojson_id = result[0]
            
            # Delete the link first (due to foreign key constraint)
            cursor.execute("DELETE FROM GeoJSONLink WHERE geojson_id = ?", 
                         (geojson_id,))

            # Then delete the GeoJSON data
            cursor.execute("DELETE FROM GeoJSONData WHERE geojson_id = ?", 
                         (geojson_id,))

            connection.commit()
            
            # Refresh the appropriate tree
            if record_type == "tax":
                load_tax_records(cursor, tax_tree, person_id)
            else:
                load_deed_records(tree, person_id)
                
            messagebox.showinfo("Success", "Map data deleted successfully.")
        else:
            cursor.execute("ROLLBACK")
            messagebox.showerror("Error", "Could not find map data to delete.")

    except sqlite3.Error as e:
        cursor.execute("ROLLBACK")
        messagebox.showerror("Error", f"Failed to delete map data: {e}")

# The add_geojson_data, edit_geojson_data, delete_geojson_data functions would also be moved here,
# potentially broken out by record_type for modularity if needed.