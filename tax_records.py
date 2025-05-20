import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox, simpledialog
from common_utils import load_townships
from hotkeys import bind_field_hotkeys, HOTKEY_MAP

#  TAX RECORD FUNCTIONS
#
#  1. initialize_tax_section
#  2. load_tax_records
#  3. add_tax_record
#  4. prefill_tax_record
#  5. edit_tax_record
#  6. save_tax_record
#  7. delete_tax_record
#  

#--------------------------
# 1. INITIALIZE TAX SECTION
#--------------------------

def initialize_tax_section(frame_records, connection, person_id):

    cursor = connection.cursor()

    # Tax section
    tax_frame = ttk.LabelFrame(frame_records, text="Tax Records")
    tax_frame.pack(fill='x', padx=5, pady=5)

    # Tax buttons frame
    tax_button_frame = ttk.Frame(tax_frame)
    tax_button_frame.pack(fill='x', padx=5, pady=5)

    # Tax Record buttons group
    tax_record_frame = ttk.LabelFrame(tax_button_frame, text="Tax Record")
    tax_record_frame.pack(side='left', padx=5)
    
    ttk.Button(tax_record_frame, text="Add", 
               command=lambda: add_tax_record(cursor, tax_tree, person_id)).pack(side='left', padx=2)
    ttk.Button(tax_record_frame, text="Prefill Add", 
               command=lambda: prefill_tax_record(cursor, tax_tree, person_id)).pack(side='left', padx=2)
    ttk.Button(tax_record_frame, text="Edit", 
               command=lambda: edit_tax_record(cursor, tax_tree, person_id)).pack(side='left', padx=2)
    ttk.Button(tax_record_frame, text="Delete", 
               command=lambda: delete_tax_record(cursor, tax_tree, person_id)).pack(side='left', padx=2)
    

    # In the tax section
    tax_map_frame = ttk.LabelFrame(tax_button_frame, text="Map Data")
    tax_map_frame.pack(side='left', padx=5)
    
    ttk.Button(tax_map_frame, text="Add", 
               command=lambda: add_geojson_data(tax_tree, "tax")).pack(side='left', padx=2)
    ttk.Button(tax_map_frame, text="Edit", 
               command=lambda: edit_geojson_data(tax_tree, person_id)).pack(side='left', padx=2)
    ttk.Button(tax_map_frame, text="Delete", 
               command=lambda: delete_geojson_data(tax_tree, person_id)).pack(side='left', padx=2)

    # Tax tree (rest of the code remains the same)
    tax_tree = ttk.Treeview(tax_frame,
        columns=("record_id", "Map", "Year", "Description", "Section", "Acres", "Acres Qtr", 
                "Property Value", "Personal Value", "Notes"),
        show='headings',
        height=8)

    # Configure Tax tree columns
    tax_columns = [
        ("record_id", 0),  # Hidden column for record_id
        ("Map", 40),
        ("Year", 60),
        ("Description", 450),
        ("Section", 50),
        ("Acres", 60),
        ("Acres Qtr", 60),
        ("Property Value", 85),
        ("Personal Value", 55),
        ("Notes", 350)
    ]

    for col, width in tax_columns:
        tax_tree.heading(col, text=col)
        tax_tree.column(col, width=width, stretch=False)
        if col == "record_id":  # Hide the record_id column
            tax_tree.column(col, width=0, stretch=False)


    # Tax scrollbar
    tax_scrollbar = ttk.Scrollbar(tax_frame, orient="vertical", 
                                command=tax_tree.yview)
    tax_tree.configure(yscrollcommand=tax_scrollbar.set)
    tax_tree.bind('<Double-1>', lambda event: on_double_click(event, map_controller))
    tax_tree.pack(side='left', fill='x', expand=True)
    tax_scrollbar.pack(side='right', fill='y')

    return tax_tree

#--------------------
# 2. LOAD TAX RECORDS
#--------------------

def load_tax_records(cursor, tax_tree, person_id):
    """Load tax records into the Tax tree"""
    for item in tax_tree.get_children():
        tax_tree.delete(item)


    cursor.execute("""
        SELECT t.record_id, t.year, t.description, t.section, t.acres, 
               t.acres_qtr, t.prop_value, t.personal_value, t.notes,
               a.address, CASE WHEN gl.geojson_id IS NOT NULL THEN 1 ELSE 0 END as has_geojson
        FROM Tax_Records t
        LEFT JOIN Address a ON t.address_id = a.address_id
        LEFT JOIN GeoJSONLink gl ON t.record_id = gl.record_id 
            AND gl.record_type = 'Tax'
        WHERE t.people_id = ?
        ORDER BY t.year
    """, (person_id,))
    
    records = cursor.fetchall()
    for record in records:
        values = [
            record[0],  # record_id (hidden)
            '🌎' if record[-1] else '',  # Map icon
            record[1],  # Year
            record[2],  # Description
            # record[9] if record[9] else "",  # Address
            *[str(value) if value not in (None, 'None', 'N/A') else "" for value in record[3:9]]  # Other fields
        ]
        tax_tree.insert("", "end", values=tuple(values))

    
    # Add double-click binding for map viewing
    tax_tree.bind('<Double-1>', lambda event: on_double_click(event, map_controller))

#------------------
# 3. ADD TAX RECORD
#------------------

def add_tax_record(cursor, tax_tree, person_id):
    """Add a new tax record"""
    tax_window = tk.Toplevel()
    tax_window.title("Add Tax Record")
    tax_window.geometry("600x750")

    main_frame = ttk.Frame(tax_window, padding="10")
    main_frame.pack(fill='both', expand=True)

    # Define fields with their required status
    fields = [
        ("Year", True),
        ("Description", False),
        ("Section", False),
        ("Acres", False),
        ("100ths", False),
        ("Property Value", False),
        ("Personal Value", False),
        ("Notes", False)
    ]

    entries = {}
    row = 0

    # --- Year ---
    tk.Label(main_frame, text="Year:", underline=0).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    year_entry = ttk.Entry(main_frame, width=10)
    year_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(year_entry, "year")
    entries["Year"] = year_entry
    row += 1

    # --- Description ---
    tk.Label(main_frame, text="Description:", underline=0).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    desc_entry = ttk.Entry(main_frame, width=80)
    desc_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(desc_entry, "description")
    entries["Description"] = desc_entry
    row += 1

    # --- Section ---
    tk.Label(main_frame, text="Section:", underline=2).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    section_entry = ttk.Entry(main_frame, width=5)
    section_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(section_entry, "section")
    entries["Section"] = section_entry
    row += 1

    # --- Acres ---
    tk.Label(main_frame, text="Acres:", underline=0).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    acres_entry = ttk.Entry(main_frame, width=6)
    acres_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(acres_entry, "acres")
    entries["Acres"] = acres_entry
    row += 1

    # --- 100ths ---
    tk.Label(main_frame, text="Qtr Acres:", underline=0).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    acres_qtr_entry = ttk.Entry(main_frame, width=6)
    acres_qtr_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(acres_qtr_entry, "acres_qtr")
    entries["100ths"] = acres_qtr_entry
    row += 1

    # --- Property Value ---
    tk.Label(main_frame, text="Property Value:", underline=6).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    prop_entry = ttk.Entry(main_frame, width=12)
    prop_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(prop_entry, "prop_value")
    entries["Property Value"] = prop_entry
    row += 1

    # --- Personal Value ---
    tk.Label(main_frame, text="Personal Value:", underline=7).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    pers_entry = ttk.Entry(main_frame, width=12)
    pers_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(pers_entry, "personal_value")
    entries["Personal Value"] = pers_entry
    row += 1

    # --- Notes ---
    tk.Label(main_frame, text="Notes:", underline=0).grid(row=row, column=0, sticky='ne', padx=5, pady=5)
    notes_entry = tk.Text(main_frame, height=4, width=40)
    notes_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(notes_entry, "notes_value")
    entries["Notes"] = notes_entry
    row += 1

    # Address selection frame as a LabelFrame
    address_frame = ttk.LabelFrame(main_frame, text="Address Selection", padding="10")
    address_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)

    # Search entry and button for address search
    search_address_var = tk.StringVar()
    search_entry = ttk.Entry(address_frame, textvariable=search_address_var, width=40)
    search_entry.grid(row=0, column=1, padx=5, pady=5)

    search_button = ttk.Button(address_frame, text="Search", command=lambda: search_address(address_dropdown))
    search_button.grid(row=0, column=0, padx=5, pady=5)

    address_var = tk.StringVar()
    address_dropdown = ttk.Combobox(address_frame, textvariable=address_var, width=47, state="readonly")
    address_dropdown.grid(row=1, column=1, padx=5, pady=5)

    # Define function to get all addresses
    def get_all_addresses():
        cursor.execute("SELECT address_id, address FROM Address ORDER BY address")
        addresses = cursor.fetchall()
        return {row[1]: row[0] for row in addresses}  # Return a dictionary mapping addresses to IDs

    # Initialize the address map
    address_map = get_all_addresses()

    # Populate the dropdown with all addresses
    address_dropdown['values'] = list(address_map.keys())

    # Define the search function for the Address dropdown
    def search_address(dropdown):
        search_term = search_address_var.get().strip()
        global address_map  # Declare as global to ensure updates persist
        if search_term:
            cursor.execute("SELECT address_id, address FROM Address WHERE address LIKE ?", (f'%{search_term}%',))
            results = cursor.fetchall()
            if results:
                address_map = {row[1]: row[0] for row in results}  # Update the address map
                dropdown['values'] = list(address_map.keys())  # Update dropdown with filtered addresses
                dropdown.set('')  # Clear current selection if results are multiple
            else:
                messagebox.showerror("No results", "No addresses found matching the search term.")
        else:
            address_map = get_all_addresses()  # Reset the address map
            dropdown['values'] = list(address_map.keys())  # Reset dropdown to all addresses
            dropdown.set('')  # Clear current selection

    # Increment the row count after the address frame
    row += 2

    def validate_and_save():
        """Validate and save the new tax record"""
        values = {
            field: (entries[field].get("1.0", "end-1c").strip() if field == "Notes" else entries[field].get().strip())
            for field in entries
        }

        # Validate required fields
        if not values["Year"].isdigit():
            messagebox.showerror("Error", "Please enter a valid year.")
            entries["Year"].focus()
            return

        save_tax_record(cursor, person_id, values, address_var, address_map, tax_window, tax_tree)

    # Button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=row + 1, column=0, columnspan=3, pady=20, sticky="ew")

    ttk.Button(button_frame, text="Save", command=validate_and_save).pack(side='left', padx=10)
    ttk.Button(button_frame, text="Cancel", command=tax_window.destroy).pack(side='left', padx=10)

    main_frame.columnconfigure(1, weight=1)


#-------------------
# 4. PREFILL TAX RECORD
#-------------------

def prefill_tax_record(cursor, tax_tree, person_id):
    selected = tax_tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a tax record to prefill from.")
        return

    record_id = tax_tree.item(selected[0], "values")[0]
    cursor.execute("SELECT * FROM Tax_Records WHERE record_id = ?", (record_id,))
    record = cursor.fetchone()

    if not record:
        messagebox.showerror("Error", "Selected tax record not found.")
        return

    _, people_id, _, description, section, acres, acres_qtr, prop_value, personal_value, notes, address_id, township_id = record

    # Dialog window
    dialog = tk.Toplevel()
    dialog.title("Prefill Tax Record")

    main_frame = ttk.Frame(dialog, padding=10)
    main_frame.pack(fill='both', expand=True)

    entries = {}
    row = 0

    # --- Year (leave blank for new input) ---
    tk.Label(main_frame, text="Year:", underline=0).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    year_entry = ttk.Entry(main_frame, width=10)
    year_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(year_entry, "year")
    entries["Year"] = year_entry
    row += 1

    # --- Description ---
    tk.Label(main_frame, text="Description:", underline=0).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    desc_entry = ttk.Entry(main_frame, width=40)
    desc_entry.insert(0, description or "")
    desc_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(desc_entry, "description")
    entries["Description"] = desc_entry
    row += 1

    # --- Section ---
    tk.Label(main_frame, text="Section:").grid(row=row, column=0, sticky='e', padx=5, pady=5)
    section_entry = ttk.Entry(main_frame, width=5)
    section_entry.insert(0, section or "")
    section_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    entries["Section"] = section_entry
    row += 1

    # --- Acres ---
    tk.Label(main_frame, text="Acres:").grid(row=row, column=0, sticky='e', padx=5, pady=5)
    acres_entry = ttk.Entry(main_frame, width=6)
    acres_entry.insert(0, acres or "")
    acres_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    entries["Acres"] = acres_entry
    row += 1

    # --- 100ths ---
    tk.Label(main_frame, text="100ths:").grid(row=row, column=0, sticky='e', padx=5, pady=5)
    acres_qtr_entry = ttk.Entry(main_frame, width=6)
    acres_qtr_entry.insert(0, acres_qtr or "")
    acres_qtr_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    entries["100ths"] = acres_qtr_entry
    row += 1

    # --- Property Value ---
    tk.Label(main_frame, text="Property Value:", underline=0).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    prop_entry = ttk.Entry(main_frame, width=12)
    prop_entry.insert(0, prop_value or "")
    prop_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(prop_entry, "prop_value")
    entries["Property Value"] = prop_entry
    row += 1

    # --- Personal Value ---
    tk.Label(main_frame, text="Personal Value:", underline=0).grid(row=row, column=0, sticky='e', padx=5, pady=5)
    pers_entry = ttk.Entry(main_frame, width=12)
    pers_entry.insert(0, personal_value or "")
    pers_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(pers_entry, "personal_value")
    entries["Personal Value"] = pers_entry
    row += 1

    # --- Notes ---
    tk.Label(main_frame, text="Notes:").grid(row=row, column=0, sticky='ne', padx=5, pady=5)
    notes_entry = tk.Text(main_frame, height=4, width=40)
    notes_entry.insert("1.0", notes or "")
    notes_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
    bind_field_hotkeys(notes_entry, "notes_value")
    entries["Notes"] = notes_entry
    row += 1

    # Address section
    address_frame = ttk.LabelFrame(main_frame, text="Address Selection", padding="10")
    address_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)

    search_address_var = tk.StringVar()
    search_entry = ttk.Entry(address_frame, textvariable=search_address_var, width=40)
    search_entry.grid(row=0, column=1, padx=5, pady=5)

    address_var = tk.StringVar()
    address_dropdown = ttk.Combobox(address_frame, textvariable=address_var, width=47, state="readonly")
    address_dropdown.grid(row=1, column=1, padx=5, pady=5)

    def get_all_addresses():
        cursor.execute("SELECT address_id, address FROM Address ORDER BY address")
        return {row[1]: row[0] for row in cursor.fetchall()}

    address_map = get_all_addresses()
    address_dropdown['values'] = list(address_map.keys())

    for addr, addr_id in address_map.items():
        if addr_id == address_id:
            address_dropdown.set(addr)
            break

    def search_address():
        search_term = search_address_var.get().strip()
        nonlocal address_map
        if search_term:
            cursor.execute("SELECT address_id, address FROM Address WHERE address LIKE ?", (f'%{search_term}%',))
            results = cursor.fetchall()
            if results:
                address_map = {row[1]: row[0] for row in results}
                address_dropdown['values'] = list(address_map.keys())
                address_dropdown.set('')
            else:
                messagebox.showerror("No results", "No addresses found.")
        else:
            address_map = get_all_addresses()
            address_dropdown['values'] = list(address_map.keys())
            address_dropdown.set('')

    ttk.Button(address_frame, text="Search", command=search_address).grid(row=0, column=0, padx=5, pady=5)

    row += 2

    def validate_and_save():
        
        values = {
            field: (entries[field].get("1.0", "end-1c").strip() if field == "Notes" else entries[field].get().strip())
            for field in entries
        }
        if not values["Year"].isdigit():
            messagebox.showerror("Error", "Please enter a valid year.")
            entries["Year"].focus()
            return

        save_tax_record(cursor, person_id, values, address_var, address_map, dialog, tax_tree)

    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=row + 1, column=0, columnspan=3, pady=20, sticky="ew")

    ttk.Button(button_frame, text="Save", command=validate_and_save).pack(side='left', padx=10)
    ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=10)

#-------------------
# 5. EDIT TAX RECORD
#-------------------

def edit_tax_record(cursor, tax_tree, person_id):
    """Edit an existing tax record."""
    selected = tax_tree.selection()
    if not selected:
        messagebox.showinfo("Select Record", "Please select a tax record to edit.")
        return

    # Get selected record's details
    record_id = tax_tree.item(selected[0], "values")[0]  # Assuming ID is in the first column
    cursor.execute("""
        SELECT 
            year, description, section, acres, acres_qtr,
            prop_value, personal_value, notes, address_id
        FROM Tax_Records
        WHERE record_id = ?
    """, (record_id,))
    record = cursor.fetchone()

    if not record:
        messagebox.showerror("Error", "Record not found in database.")
        return

    # Define function to get all addresses
    def get_all_addresses():
        cursor.execute("SELECT address_id, address FROM Address ORDER BY address")
        addresses = cursor.fetchall()
        return {row[1]: row[0] for row in addresses}  # Return a dictionary mapping addresses to IDs

    # Open edit window
    tax_window = tk.Toplevel()
    tax_window.title("Edit Tax Record")
    tax_window.geometry("600x750")

    main_frame = ttk.Frame(tax_window, padding="10")
    main_frame.pack(fill='both', expand=True)

    # Define fields with their current values
    fields = [
        ("Year", record[0], True),
        ("Description", record[1], False),
        ("Section", record[2], False),
        ("Acres", record[3], False),
        ("100ths", record[4], False),
        ("Property Value", record[5], False),
        ("Personal Value", record[6], False),
        ("Notes", record[7], False)
    ]

    entries = {}
    row = 0

    # Create entry fields
    for field, value, required in fields:
        ttk.Label(main_frame, text=field + ":").grid(
            row=row, column=0, sticky='e', padx=5, pady=5)
        
        if field == "Notes":
            entry = tk.Text(main_frame, height=4, width=40)
            entry.insert("1.0", value or "")
        else:
            entry = ttk.Entry(main_frame, width=40)
            entry.insert(0, value or "")
        
        entry.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
        
        if required:
            ttk.Label(main_frame, text="*Required", font=('TkDefaultFont', 8)).grid(
                row=row, column=2, sticky='w', padx=5)
        
        entries[field] = entry
        row += 1

    # Address selection frame as a LabelFrame
    address_frame = ttk.LabelFrame(main_frame, text="Address Selection", padding="10")
    address_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)

    # Initialize the address map
    address_map = get_all_addresses()

    # Populate the dropdown with all addresses
    address_var = tk.StringVar()
    address_dropdown = ttk.Combobox(address_frame, textvariable=address_var, width=47, state="readonly")
    address_dropdown.grid(row=1, column=1, padx=5, pady=5)
    address_dropdown['values'] = list(address_map.keys())

    # Set current address if exists
    current_address = None
    for addr, addr_id in address_map.items():
        if addr_id == record[8]:  # Map the address ID
            current_address = addr
            break
    if current_address:
        address_dropdown.set(current_address)

    # Search entry and button for address search
    search_address_var = tk.StringVar()
    search_entry = ttk.Entry(address_frame, textvariable=search_address_var, width=40)
    search_entry.grid(row=0, column=1, padx=5, pady=5)

    def search_address(dropdown):
        search_term = search_address_var.get().strip()
        global address_map
        if search_term:
            cursor.execute("SELECT address_id, address FROM Address WHERE address LIKE ?", (f'%{search_term}%',))
            results = cursor.fetchall()
            if results:
                address_map = {row[1]: row[0] for row in results}
                dropdown['values'] = list(address_map.keys())
                dropdown.set('')
            else:
                messagebox.showerror("No results", "No addresses found matching the search term.")
        else:
            address_map = get_all_addresses()
            dropdown['values'] = list(address_map.keys())
            dropdown.set('')

    ttk.Button(address_frame, text="Search", command=lambda: search_address(address_dropdown)).grid(
        row=0, column=0, padx=5, pady=5)

    row += 2

    # Button frame at the bottom
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=row, column=0, columnspan=3, pady=20, sticky="ew")

    # Save and Cancel buttons
    ttk.Button(button_frame, text="Save", 
           command=lambda: save_tax_record(
               cursor, 
               person_id, 
               {field: (entries[field].get("1.0", "end-1c").strip() if field == "Notes" 
                       else entries[field].get().strip())
                for field in entries},  # Get values from entries
               address_var, 
               address_map, 
               tax_window, 
               tax_tree, 
               record_id)).pack(side='left', padx=10)    
    ttk.Button(button_frame, text="Cancel", command=tax_window.destroy).pack(side='left', padx=10)

    main_frame.columnconfigure(1, weight=1)


#-------------------
# 6. SAVE TAX RECORD
#-------------------

def save_tax_record(cursor, person_id, values, address_var, address_map, window, tax_tree, record_id=None):
    """
    Save a tax record to the database.
    
    Args:
        person_id: ID of the person associated with the tax record.
        values: Dictionary of field values from the form.
        address_var: Selected address value.
        address_map: Mapping of addresses to their IDs.
        window: The parent window for the form.
        tree: The Treeview to reload after saving.
        record_id: The ID of the record to update (None for new records).
    """
    try:
        # Get the selected address_id
        address_id = None
        if address_var.get():
            selected_address = address_var.get()
            if selected_address in address_map:
                address_id = address_map[selected_address]
            else:
                messagebox.showerror("Error", "Invalid address selection.")
                return

        # Determine if it's an add or update operation
        if record_id:
            # Update existing record
            cursor.execute("""
                UPDATE Tax_Records
                SET year = ?, description = ?, section = ?, acres = ?, acres_qtr = ?,
                    prop_value = ?, personal_value = ?, notes = ?, address_id = ?
                WHERE record_id = ? AND people_id = ?
            """, (
                values["Year"],
                values["Description"],
                values["Section"],
                values["Acres"],
                values["100ths"],
                values["Property Value"],
                values["Personal Value"],
                values["Notes"],
                address_id,
                record_id,
                person_id
            ))
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO Tax_Records (
                    people_id, year, description, section, acres, acres_qtr, 
                    prop_value, personal_value, notes, address_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_id,
                values["Year"],
                values["Description"],
                values["Section"],
                values["Acres"],
                values["100ths"],
                values["Property Value"],
                values["Personal Value"],
                values["Notes"],
                address_id
            ))

        # Commit and refresh the Treeview
        cursor.connection.commit()
        window.destroy()
        load_tax_records(cursor, tax_tree, person_id)
        messagebox.showinfo("Success", "Tax record saved successfully.")

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Failed to save tax record: {e}")

#---------------------
# 7. DELETE TAX RECORD
#---------------------

def delete_tax_record(cursor, tax_tree, person_id):
    """Delete the selected tax record"""
    selected = tax_tree.selection()
    if not selected:
        messagebox.showinfo("Select Record", "Please select a tax record to delete.")
        return

    # Get the record_id directly from the tree values
    values = tax_tree.item(selected[0])['values']
    record_id = values[0]  # First column is our hidden record_id
    year = values[2]       # Year is now in the third column

    if not messagebox.askyesno("Confirm Delete", 
                               f"Are you sure you want to delete this tax record from {year}?\n"
                               f"Description: {values[2]}"):
        return

    try:
        # Start transaction
        cursor.execute("BEGIN")

        # Check and delete GeoJSON data if it exists
        cursor.execute("""
            SELECT geojson_id 
            FROM GeoJSONLink 
            WHERE record_type = 'Tax' AND record_id = ?
        """, (record_id,))
        
        geojson_result = cursor.fetchone()
        if geojson_result:
            geojson_id = geojson_result[0]
            # Delete the link first
            cursor.execute("DELETE FROM GeoJSONLink WHERE geojson_id = ?", (geojson_id,))
            # Then delete the GeoJSON data
            cursor.execute("DELETE FROM GeoJSONData WHERE geojson_id = ?", (geojson_id,))

        # Delete the tax record
        cursor.execute("DELETE FROM Tax_Records WHERE record_id = ?", (record_id,))
        
        # Commit and reload the tree
        cursor.connection.commit()
        load_tax_records(cursor, tax_tree, person_id)
        messagebox.showinfo("Success", "Tax record deleted successfully")

    except sqlite3.Error as e:
        cursor.execute("ROLLBACK")
        messagebox.showerror("Error", f"Failed to delete tax record: {e}")

