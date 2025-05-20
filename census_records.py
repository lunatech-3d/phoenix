import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox
from common_utils import load_townships
from resgroup_utils import get_or_create_resgroup, add_resgroup_member, update_resgroup_address, cleanup_resgroup, show_entire_group

current_address_mapping = {}

# In add_census_record and edit_census_record:
def create_address_section(main_frame, cursor):
    """Create the address search and selection section"""
    address_frame = ttk.LabelFrame(main_frame, text="Address")
    address_frame.pack(fill="x", pady=10)

    # Add search functionality
    search_var = tk.StringVar()
    search_frame = ttk.Frame(address_frame)
    search_frame.pack(fill="x", pady=5)
    
    ttk.Label(search_frame, text="Search Address:").pack(side="left", padx=5)
    search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
    search_entry.pack(side="left", padx=5)
    
    address_var = tk.StringVar()
    address_dropdown = ttk.Combobox(address_frame, textvariable=address_var, width=50)
    address_dropdown.pack(pady=5)

    # Initialize with all addresses
    addresses = get_all_addresses(cursor)
    address_dropdown['values'] = list(addresses.keys())
    global current_address_mapping
    current_address_mapping = addresses
    
    ttk.Button(search_frame, text="Search", 
               command=lambda: search_address(cursor, search_var, address_dropdown, address_var)
              ).pack(side="left", padx=5)

    return address_var, address_dropdown


def validate_census_input(entries, year, township, address, editing=False):
    
    # Validate Census year
    if not year:
        messagebox.showerror("Error", "Please select a Census year.")
        return False

    # Validate Township
    if not township:
        messagebox.showerror("Error", "Please select a Township.")
        return False

    # Validate required fields based on year
    for field, entry in entries.items():
        if "Required" in field:  # Required fields are labeled in the mapping
            if editing and field in ["Dwelling No.", "Household No."]:
                continue
            if not entry.get().strip():
                messagebox.showerror("Error", f"The field '{field}' is required.")
                entry.focus()  # Set focus on the first invalid entry
                return False

    return True


def get_census_fields():
    """Return the Census year-to-fields mapping."""
    return {
        '1830': [
            ("Sex", "M/F"),
            ("Race",""),
            ("Relation to Head","")
            ],
        '1840': [
            ("Age", "Required"),
            ("Sex", "M/F"),
            ("Race", ""),
            ("Relation to Head", "")
        ],
        '1850': [
            ("Age", "Required"),
            ("Sex", "M/F"),
            ("Race", ""),
            ("Relation to Head", ""),
            ("Real Estate Value", "$"),
            ("Estate Value", "$"),
            ("Birth Place", ""),
            ("Occupation", ""),
            ("Dwelling No.", ""),
            ("Household No.", "")
        ],
        '1860': [
            ("Dwelling No.", "Required"),
            ("Household No.", "Required"),
            ("Age", "Required"),
            ("Sex", "M/F"),
            ("Race", ""),
            ("Occupation", ""),
            ("Real Estate Value", "$"),
            ("Estate Value", "$"),
            ("Birth Place", ""),         
            ("Attended School", "Y/N") 
        ],
        '1870': [
            ("Dwelling No.", "Required"),
            ("Household No.", "Required"),
            ("Age", "Required"),
            ("Sex", "M/F"),
            ("Race", ""),
            ("Occupation", ""),
            ("Real Estate Value", "$"),
            ("Estate Value", "$"),
            ("Birth Place", "")        
        ],
        '1880': [
            ("Dwelling No.", "Required"),
            ("Household No.", "Required"),
            ("Race", ""),
            ("Sex", "M/F"),
            ("Age", "Required"),
            ("Relation to Head", ""),
            ("Occupation", ""),
            ("Attended School", ""),
            ("Birth Place", ""),
            ("Fathers Birth Place", ""),
            ("Mothers Birth Place", "")
        ],
        '1900': [
            ("Age", "Required"),
            ("Sex", "M/F"),
            ("Race", ""),
            ("Relation to Head", ""),
            ("Birth Place", ""),
            ("Fathers Birth Place", ""),
            ("Mothers Birth Place", ""),
            ("Years Married", ""),
            ("Number of Children Born", ""),
            ("Number of Children Living", ""),
            ("Occupation", ""),
            ("Dwelling No.", "Required"),
            ("Household No.", "Required"),
            ("Farm Owner", "Yes/No")
        ],
        '1910': [
            ("Age", "Required"),
            ("Sex", "M/F"),
            ("Race", ""),
            ("Relation to Head", ""),
            ("Birth Place", ""),
            ("Fathers Birth Place", ""),
            ("Mothers Birth Place", ""),
            ("Years Married", ""),
            ("Number of Children Born", ""),
            ("Number of Children Living", ""),
            ("Occupation", ""),
            ("Dwelling No.", "Required"),
            ("Household No.", "Required"),
            ("Farm Owner", "Yes/No")
        ],
        '1920': [
            ("Age", "Required"),
            ("Sex", "M/F"),
            ("Race", ""),
            ("Relation to Head", ""),
            ("Birth Place", ""),
            ("Fathers Birth Place", ""),
            ("Mothers Birth Place", ""),
            ("Native Language", ""),
            ("Occupation", ""),
            ("Dwelling No.", "Required"),
            ("Household No.", "Required"),
            ("City", ""),
            ("State", "")
        ],
        '1930': [
            ("Age", "Required"),
            ("Sex", "M/F"),
            ("Race", ""),
            ("Relation to Head", ""),
            ("Birth Place", ""),
            ("Fathers Birth Place", ""),
            ("Mothers Birth Place", ""),
            ("Native Language", ""),
            ("Occupation", ""),
            ("Dwelling No.", "Required"),
            ("Household No.", "Required"),
            ("City", ""),
            ("State", "")
        ],
        '1940': [
            ("Age", "Required"),
            ("Sex", "M/F"),
            ("Race", ""),
            ("Relation to Head", ""),
            ("Birth Place", ""),
            ("Fathers Birth Place", ""),
            ("Mothers Birth Place", ""),
            ("Occupation", ""),
            ("Dwelling No.", "Required"),
            ("Household No.", "Required"),
            ("City", ""),
            ("State", ""),
            ("Attended School", "Y/N")
        ]
    }


def initialize_dynamic_fields(parent_frame, year_var, fields_mapping):
    """Create dynamic fields based on selected Census year."""
    entries = {}
    print("Dynamic Fields Initialized:", entries.keys())

    def update_fields(*args):
        # Clear existing fields
        for widget in parent_frame.winfo_children():
            widget.destroy()
        entries.clear()

        selected_year = year_var.get()
        if selected_year in fields_mapping:
            for row, (field, hint) in enumerate(fields_mapping[selected_year]):
                ttk.Label(parent_frame, text=f"{field}:").grid(row=row, column=0, padx=5, pady=2, sticky="e")
                entry = ttk.Entry(parent_frame)
                entry.grid(row=row, column=1, padx=5, pady=2, sticky="w")
                entries[field] = entry

    year_var.trace_add("write", update_fields)
    return entries

    
def create_dropdown(parent, label, values, width=50):
    """Create a labeled dropdown in a parent frame.
    Returns:
        tuple: (StringVar, Combobox widget)
    """
    frame = ttk.Frame(parent)
    frame.pack(fill="x", pady=5)
    ttk.Label(frame, text=f"{label}:").pack(side="left", padx=5)
    var = tk.StringVar()
    dropdown = ttk.Combobox(frame, textvariable=var, state="readonly", width=width)
    dropdown.pack(side="left", padx=5)
    dropdown['values'] = values
    return var, dropdown  # Return both the variable and the widget

def get_all_addresses (cursor):
    cursor.execute("SELECT address_id, address FROM Address ORDER BY address")
    addresses = cursor.fetchall()
    # Use a dictionary to map displayed addresses to their IDs
    return {row[1]: row[0] for row in addresses}  # Return the mapping


def search_address(cursor, search_var, dropdown):
    """Filter addresses based on a search term."""
    search_term = search_var.get().strip()
    
    if search_term:
        cursor.execute("SELECT address_id, address FROM Address WHERE address LIKE ?", (f'%{search_term}%',))
        results = cursor.fetchall()
        if results:
            # Create mapping of addresses and update dropdown
            addresses = {row[1]: row[0] for row in results}
            dropdown['values'] = list(addresses.keys())
            
            # Store the current mapping in the global variable
            global current_address_mapping
            current_address_mapping = addresses
            
            print(f"Found {len(results)} matching addresses")  # Debug print
            dropdown.set('')  # Clear current selection
        else:
            messagebox.showerror("No results", "No addresses found matching the search term.")
    else:
        addresses = get_all_addresses(cursor)
        dropdown['values'] = list(addresses.keys())
        current_address_mapping = addresses
        dropdown.set('')


#-----------------------------
# 1. INITIALIZE CENSUS SECTION
#-----------------------------

def initialize_census_section(frame_records, connection, person_id):
    cursor = connection.cursor()

    """Initialize the Census section."""
    census_frame = ttk.LabelFrame(frame_records, text="Census Records")
    census_frame.pack(fill='x', padx=5, pady=5)

    census_button_frame = ttk.Frame(census_frame)
    census_button_frame.pack(fill='x', padx=5, pady=5)

    # Treeview with hidden 'id' column
    census_tree = ttk.Treeview(
        census_frame,
        columns=("id", "Census Year", "Age", "Sex", "Race","Occupation", "Relation to Head",
                 "Real Estate Value", "Estate Value", "Township", "Address"),
        show='headings',
        height=5
    )

    # Column setup: 'id' hidden, others visible
    census_tree.column("#0", width=0, stretch=tk.NO)  # Hide implicit first column
    census_tree.column("id", width=0, stretch=tk.NO)  # Hide 'id' column
    census_tree.heading("id", text="")  # No header for 'id'

    # Define visible columns
    census_columns = [
        ("Census Year", 100),
        ("Age", 50),
        ("Sex", 50),
        ("Race", 50),
        ("Occupation", 150),
        ("Relation to Head", 150),
        ("Real Estate Value", 100),
        ("Estate Value", 100),
        ("Township", 300),
        ("Address", 200)
    ]

    for col, width in census_columns:
        census_tree.heading(col, text=col)
        census_tree.column(col, width=width, stretch=False)

    # Scrollbar setup
    census_scrollbar = ttk.Scrollbar(census_frame, orient="vertical", command=census_tree.yview)
    census_tree.configure(yscrollcommand=census_scrollbar.set)
    census_tree.pack(side="left", fill="x", expand=True)
    census_scrollbar.pack(side="right", fill="y")

    # Add buttons
    ttk.Button(
        census_button_frame,
        text="Add Census Record",
        command=lambda: add_census_record(cursor, census_tree, person_id)
    ).pack(side="left", padx=5)
    ttk.Button(
        census_button_frame,
        text="Edit Census Record",
        command=lambda: edit_census_record(
            cursor=cursor,
            census_tree=census_tree,
            person_id=person_id,
            refresh_callback=None,
            census_record_id=None
        )
    ).pack(side="left", padx=5)
    ttk.Button(
        census_button_frame,
        text="Delete Census Record",
        command=lambda: delete_census_record(cursor, census_tree, person_id)
    ).pack(side="left", padx=5)
    ttk.Button(
        census_button_frame,
        text="Show Entire Residence",
        command=lambda: show_entire_group(cursor, census_tree)
    ).pack(side="left", padx=5)

    return census_tree


#-----------------------
# 2. LOAD CENSUS RECORDS
#-----------------------

def load_census_records(cursor, census_tree, person_id):
    """Load Census records into the Census tree with hidden ID"""
    try:
        # Clear existing Census records
        for item in census_tree.get_children():
            census_tree.delete(item)

        # Modified query to include ID and address
        query = """
            SELECT 
                c.id,                 -- Hidden ID
                c.census_year,
                c.person_age,
                c.sex,
                c.race,
                c.person_occupation,
                c.relation_to_head,
                c.real_estate_value,
                c.estate_value,
                t.township_name,
                a.address
            FROM Census c
            LEFT JOIN Townships t ON c.township_id = t.township_id
            LEFT JOIN ResGroups rg ON c.res_group_id = rg.id
            LEFT JOIN Address a ON rg.address_id = a.address_id
            WHERE c.person_id = ?
            ORDER BY c.census_year
        """

        cursor.execute(query, (person_id,))
        census_records = cursor.fetchall()

        # Insert census records with ID as iid
        for record in census_records:
            record_id = record[0]  # 'id' for internal tracking
            values = tuple(
                str(value) if value not in (None, 'None', 'N/A') else ""
                for value in record
            )
            census_tree.insert("", tk.END, iid=record_id, values=values)

    except sqlite3.Error as e:
        print(f"Database error in load_census_records: {e}")
        messagebox.showerror("Error", "Failed to load census records")
    except Exception as e:
        print(f"Unexpected error in load_census_records: {e}")
        messagebox.showerror("Error", "An unexpected error occurred while loading census records")

#---------------------
# 3. ADD CENSUS RECORD
#---------------------

def add_census_record(cursor, census_tree, person_id):
    """Add a new Census record with dynamic field handling and household/address integration."""

    # Load necessary mappings
    fields_mapping = get_census_fields()  # Retrieves the year-to-fields mapping
    township_details, township_map, reverse_township_map = load_townships(cursor)  # Loads township details

    # Create the Census window
    census_window = tk.Toplevel()
    census_window.title("Add Census Record")
    census_window.geometry("700x800")

    main_frame = ttk.Frame(census_window, padding="10")
    main_frame.pack(fill="both", expand=True)

    # Create critical fields - all enabled in add mode
    year_var, year_dropdown = create_dropdown(
        main_frame, 
        "Census Year*", 
        list(fields_mapping.keys()), 
        10
    )

    township_var, township_dropdown = create_dropdown(
        main_frame, 
        "Township*", 
        township_details, 
        75
    )

    # Create the Census field section
    census_frame = ttk.LabelFrame(main_frame, text="Census Information")
    census_frame.pack(fill="both", expand=True, pady=10)
    entries = initialize_dynamic_fields(census_frame, year_var, fields_mapping)

    # Address section
    address_frame = ttk.LabelFrame(main_frame, text="Address")
    address_frame.pack(fill="x", pady=10)

    # Add search functionality to the Address dropdown
    search_var = tk.StringVar()
    search_frame = ttk.Frame(address_frame)
    search_frame.pack(fill="x", pady=5)
    
    ttk.Label(search_frame, text="Search Address:").pack(side="left", padx=5)
    search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
    search_entry.pack(side="left", padx=5)
    
    address_var, address_dropdown = create_dropdown(address_frame, "Address", 
                                                  get_all_addresses(cursor), 50)
    
    ttk.Button(search_frame, text="Search", 
               command=lambda: search_address(cursor, search_var, address_dropdown)).pack(side="left", padx=5)

    # Add Save and Cancel buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=20)

    ttk.Button(button_frame, text="Save",
           command=lambda: save_census_record(
               cursor, entries, year_var.get(),
               address_var.get() if address_var.get() != "Select Address" else None,
               township_var.get(), township_map, person_id, census_window, census_tree,
               township_id=(township_dropdown.get() if township_dropdown.get() else None)  # Ensure it's not empty
           )).pack(side="left", padx=5)

    ttk.Button(button_frame, text="Cancel", command=census_window.destroy).pack(side="right", padx=5)

#-----------------------
# 4. EDIT CENSUS RECORDS
#-----------------------

def edit_census_record(cursor, census_tree, person_id=None, refresh_callback=None, census_record_id=None):
    """Edit the selected Census record with dynamic field handling."""
        
    try:
        # Initialize variables
        record_id = None
        township_id = None

        # Retrieve the correct record ID
        if census_record_id:  # First priority - use provided census record ID
            record_id = census_record_id
            print(f"Using provided census_record_id: {record_id}", flush=True)
        else:  # Fall back to tree selection or person_id
            selected = census_tree.selection()
            if selected:
                values = census_tree.item(selected[0])['values']
                record_id = values[0]
                print(f"Selected record ID from tree: {record_id}", flush=True)
            elif person_id:
                cursor.execute("""SELECT id FROM Census WHERE person_id = ? LIMIT 1""", (person_id,))
                result = cursor.fetchone()
                if not result:
                    messagebox.showerror("Error", f"No Census record found for person ID {person_id}.")
                    return
                record_id = result[0]
            else:
                messagebox.showinfo("Select Record", "Please select a Census record to edit.")
                return

        print(f"Editing Census record with ID: {record_id}", flush=True)

        # Query the database for the full record
        cursor.execute("""
            SELECT 
                c.id, c.residence_id, c.census_year, c.person_age,
                c.person_occupation, c.real_estate_value, c.estate_value,
                c.sex, c.race, c.married_this_year, c.relation_to_head, c.attended_school,
                c.city, c.state, c.birth_place, c.father_birth_place, c.mother_birth_place,
                c.native_language, c.years_married, c.number_of_children_born, c.number_of_children_living,
                c.farm_owner, c.rented_home_or_farm, c.res_group_id,
                c.census_dwellnum, c.census_householdnum, c.township_id,
                a.address as current_address
            FROM Census c
            LEFT JOIN ResGroups rg ON c.res_group_id = rg.id
            LEFT JOIN Address a ON rg.address_id = a.address_id
            WHERE c.id = ?
        """, (record_id,))
        record = cursor.fetchone()
        
        if not record:
            print(f"DEBUG: No record found for record_id={record_id}")
            messagebox.showerror("Error", f"Record not found in the database. ID: {record_id}")
            return

        # Store necessary IDs
        record_id = record[0]
        residence_id = record[1]
        res_group_id = record[23]  # Corrected index
        township_id = record[26]  # Corrected index

        # Load required data
        fields_mapping = get_census_fields()
        selected_fields = fields_mapping.get(str(record[2]), [])  # record[2] is census_year
        township_details, township_map, reverse_township_map = load_townships(cursor)

        # Create the edit window
        edit_window = tk.Toplevel()
        edit_window.title(f"Edit {record[2]} Census Record")  # record[2] is census_year
        edit_window.geometry("700x800")

        main_frame = ttk.Frame(edit_window, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Create dropdowns for Census Year and Township
        year_var, year_dropdown_widget = create_dropdown(main_frame, "Census Year", list(fields_mapping.keys()), 10)
        year_var.set(record[2])  # Census Year
        year_dropdown_widget.config(state="disabled")  # Lock field

        township_var, township_dropdown_widget = create_dropdown(main_frame, "Township", township_details, 75)
        if township_id:
            if township_id in reverse_township_map:
                township_var.set(reverse_township_map[township_id])  # Set the township dropdown to the correct value
            else:
                print(f"DEBUG: township_id {township_id} not found in reverse_township_map")
        else:
            print("DEBUG: No valid township_id found for this record")
        township_dropdown_widget.config(state="disabled")  # Lock field

        # Census Information Section
        census_frame = ttk.LabelFrame(main_frame, text="Census Information")
        census_frame.pack(fill="both", expand=True, pady=10)

        # Create dynamic fields for census record
        entries = {}
        for field, placeholder in selected_fields:
            label = ttk.Label(census_frame, text=f"{field}:")
            label.pack(anchor="w", pady=2)
            entry = ttk.Entry(census_frame, width=30)
            entry.pack(anchor="w", pady=2)
            entries[field] = entry
            if "Required" in placeholder:
                label.config(text=f"{field}:*")

        # Address Section
        address_frame = ttk.LabelFrame(main_frame, text="Address")
        address_frame.pack(fill="x", pady=10)

        search_var = tk.StringVar()
        search_frame = ttk.Frame(address_frame)
        search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Search Address:").pack(side="left", padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.pack(side="left", padx=5)

        address_var = tk.StringVar()
        address_dropdown = ttk.Combobox(address_frame, textvariable=address_var, width=50)
        address_dropdown.pack(pady=5)
        addresses = get_all_addresses(cursor)
        address_dropdown["values"] = list(addresses.keys())

        current_address = record[-1]  # Last column from query
        if current_address:
            address_var.set(current_address)

        ttk.Button(search_frame, text="Search",
                   command=lambda: search_address(cursor, search_var, address_dropdown)).pack(side="left", padx=5)

        # Map census field labels to their actual column names
        field_to_column = {
            "Age": "person_age",
            "Occupation": "person_occupation",
            "Real Estate Value": "real_estate_value",
            "Estate Value": "estate_value",
            "Sex": "sex",
            "Race": "race",
            "Married this Year": "married_this_year",
            "Relation to Head": "relation_to_head",
            "Attended School": "attended_school",
            "City": "city",
            "State": "state",
            "Birth Place": "birth_place",
            "Fathers Birth Place": "father_birth_place",
            "Mothers Birth Place": "mother_birth_place",
            "Native Language": "native_language",
            "Years Married": "years_married",
            "Number of Children Born": "number_of_children_born",
            "Number of Children Living": "number_of_children_living",
            "Farm Owner": "farm_owner",
            "Attended School": "attended_school",
            "Rented Home or Farm": "rented_home_or_farm"
        }

        # Map column names to their actual positions in the SQL SELECT record
        column_indexes = {
            "person_age": 3,
            "person_occupation": 4,
            "real_estate_value": 5,
            "estate_value": 6,
            "sex": 7,
            "race": 8,
            "married_this_year": 9,
            "relation_to_head": 10,
            "attended_school": 11,
            "city": 12,
            "state": 13,
            "birth_place": 14,
            "father_birth_place": 15,
            "mother_birth_place": 16,
            "native_language": 17,
            "years_married": 18,
            "number_of_children_born": 19,
            "number_of_children_living": 20,
            "farm_owner": 21,
            "rented_home_or_farm": 22
        }

        # Now safely pull values from the correct positions
        field_values = {}
        for field, _ in selected_fields:
            column_name = field_to_column.get(field)
            if column_name and column_name in column_indexes:
                idx = column_indexes[column_name]
                value = record[idx]
                if value not in (None, "None", ""):
                    field_values[field] = value

        # Fill the Entry widgets with corresponding values
        for field, entry in entries.items():
            value = field_values.get(field, "")
            entry.delete(0, tk.END)
            entry.insert(0, str(value))

        # Lock Dwelling and Household No. fields
        for field in ["Dwelling No.", "Household No."]:
            if field in entries:
                entries[field].config(state="disabled")

        # Save and Cancel Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)

        def validate_and_save_edit():
            if not validate_census_input(entries, year_var.get(), township_var.get(), address_var.get(), editing=True):
                return
            save_census_record(
                cursor=cursor,
                entries=entries,
                census_year=year_var.get(),
                address=address_var.get() if address_var.get() != "Select Address" else None,
                township=township_var.get(),
                township_map=township_map,
                person_id=person_id,
                window=edit_window,
                tree=census_tree,
                record_id=record_id,
                residence_id=residence_id,
                township_id=township_id,
                editing=True
            )

        save_button = ttk.Button(
            button_frame,
            text="Save",
            command=lambda: (
                validate_and_save_edit()
            )
        )
        save_button.pack(side="left", padx=5)    

        ttk.Button(button_frame, text="Cancel", command=edit_window.destroy).pack(side="right", padx=5)

    except sqlite3.Error as e:
        print(f"Database error in edit_census_record: {e}")
        messagebox.showerror("Error", "Failed to edit census record.")
    except Exception as e:
        import traceback
        print(f"Unexpected error in edit_census_record: {e}")
        traceback.print_exc()
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")

#-----------------------
# 5. SAVE CENSUS RECORDS
#-----------------------

def save_census_record(cursor, entries, census_year, address, township, township_map, person_id, window, tree, record_id=None, residence_id=None, township_id=None, editing=False):
    """Save or update Census record with proper ResGroup handling."""
    transaction_started = False
    
    try:
        # Extract form data
        census_data = {field: entry.get().strip() for field, entry in entries.items()}
        census_dwellnum = census_data.get('Dwelling No.', '').strip()
        census_householdnum = census_data.get('Household No.', '').strip()

        # Initial validations
        if not census_year:
            raise ValueError("Census year is required.")

        if not editing:
            if not census_dwellnum or not census_householdnum:
                raise ValueError("Dwelling number and Household number are required for new records.")

        # Set township_id based on mode
        if record_id:  # Edit mode
            if not township_id:  # Fallback only if not provided
                cursor.execute("SELECT township_id FROM Census WHERE id = ?", (record_id,))
                result = cursor.fetchone()
                township_id = result[0] if result else None
        else:  # Add mode
            if not township or township not in township_map:
                raise ValueError("Valid township selection is required.")
            township_id = township_map[township]

        if not township_id:
            raise ValueError("Township ID could not be determined.")

        # Start transaction
        cursor.execute("BEGIN")
        transaction_started = True

        # Get or create ResGroup with all required identifiers
        res_group_id = get_or_create_resgroup(
            cursor=cursor,
            census_dwellnum=census_dwellnum,
            census_year=census_year,
            township_id=township_id,
            household_num=census_householdnum,
            event_type="Census"
        )

        # Handle address if provided
        address_id = None
        if address and address != "Select Address":
            if address in current_address_mapping:
                address_id = current_address_mapping[address]

        if address_id:
            update_resgroup_address(cursor, res_group_id, address_id)

        if record_id:  # Update existing record
            cursor.execute("""
                UPDATE Census
                SET 
                    person_age = ?,
                    person_occupation = ?,
                    real_estate_value = ?,
                    estate_value = ?,
                    sex = ?,
                    race = ?,
                    married_this_year = ?,
                    relation_to_head = ?,
                    attended_school = ?,
                    city = ?,
                    state = ?,
                    birth_place = ?,
                    father_birth_place = ?,
                    mother_birth_place = ?,
                    native_language = ?,
                    years_married = ?,
                    number_of_children_born = ?,
                    number_of_children_living = ?,
                    farm_owner = ?,
                    rented_home_or_farm = ?,
                    res_group_id = ?
                WHERE id = ?
            """, (
                census_data.get('Age', ''),
                census_data.get('Occupation', ''),
                census_data.get('Real Estate Value', ''),
                census_data.get('Estate Value', ''),
                census_data.get('Sex', ''),
                census_data.get('Race', ''),
                census_data.get('Married this Year', ''),
                census_data.get('Relation to Head', ''),
                census_data.get('Attended School', ''),
                census_data.get('City', ''),
                census_data.get('State', ''),
                census_data.get('Birth Place', ''),
                census_data.get('Fathers Birth Place', ''),
                census_data.get('Mothers Birth Place', ''),
                census_data.get('Native Language', ''),
                census_data.get('Years Married', ''),
                census_data.get('Number of Children Born', ''),
                census_data.get('Number of Children Living', ''),
                census_data.get('Farm Owner', ''),
                census_data.get('Rented Home or Farm', ''),
                res_group_id,
                record_id
            ))
        else:  # Insert new record
            cursor.execute("""
                INSERT INTO Census (
                    person_id, census_year, person_age, sex, race,
                    relation_to_head, real_estate_value, estate_value,
                    person_occupation, census_dwellnum, census_householdnum,
                    attended_school, birth_place, father_birth_place,
                    mother_birth_place, native_language, years_married,
                    number_of_children_born, number_of_children_living,
                    farm_owner, rented_home_or_farm, township_id, res_group_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_id,
                census_year,
                census_data.get('Age', ''),
                census_data.get('Sex', ''),
                census_data.get('Race', ''),
                census_data.get('Relation to Head', ''),
                census_data.get('Real Estate Value', ''),
                census_data.get('Estate Value', ''),
                census_data.get('Occupation', ''),
                census_dwellnum,
                census_householdnum,
                census_data.get('Attended School', ''),
                census_data.get('Birth Place', ''),
                census_data.get('Fathers Birth Place', ''),
                census_data.get('Mothers Birth Place', ''),
                census_data.get('Native Language', ''),
                census_data.get('Years Married', ''),
                census_data.get('Number of Children Born', ''),
                census_data.get('Number of Children Living', ''),
                census_data.get('Farm Owner', ''),
                census_data.get('Rented Home or Farm', ''),
                township_id,
                res_group_id
            ))

            # Add person to ResGroup
            add_resgroup_member(cursor, res_group_id, person_id, 
                                role=census_data.get('Relation to Head', ''))

        # Commit transaction
        cursor.execute("COMMIT")
        transaction_started = False

        # Update display
        messagebox.showinfo("Success", "Census record saved successfully.")
        window.destroy()
        load_census_records(cursor, tree, person_id)

    except Exception as e:
        if transaction_started:
            cursor.execute("ROLLBACK")
        messagebox.showerror("Error", str(e))
        raise


#-------------------------
# 6. DELETE CENSUS RECORD
#-------------------------

def delete_census_record(cursor, census_tree, person_id):
    """Delete the selected Census record with proper ResGroup handling."""
    selected = census_tree.selection()
    if not selected:
        messagebox.showinfo("Select Record", "Please select a Census record to delete.")
        return

    # Get the Census record's ID from the selected item
    values = census_tree.item(selected[0])['values']
    census_id = values[0]  # First column is the hidden Census ID

    if not census_id:
        messagebox.showerror("Error", "Census record ID not found in selection.")
        return

    # First fetch the full record including res_group_id
    cursor.execute("""
        SELECT c.id, c.res_group_id, c.census_year, c.census_dwellnum, c.census_householdnum
        FROM Census c
        WHERE c.id = ?
    """, (census_id,))

    record = cursor.fetchone()
    if not record:
        messagebox.showerror("Error", "Census record not found in database.")
        return

    census_id, res_group_id, census_year, dwelling_num, household_num = record

    if not messagebox.askyesno("Confirm Delete", 
                              "Are you sure you want to delete this Census record?"):
        return

    try:
        # Start transaction
        cursor.execute("BEGIN")

        # IMPORTANT: Check for other census records in this group BEFORE deleting anything
        if res_group_id:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM Census c
                JOIN ResGroupMembers rgm ON c.res_group_id = rgm.res_group_id
                WHERE rgm.res_group_id = ? AND c.id != ?
            """, (res_group_id, census_id))
            other_records_count = cursor.fetchone()[0]

            # Also check specifically for ResGroupMembers entries
            cursor.execute("""
                SELECT COUNT(*) 
                FROM ResGroupMembers 
                WHERE res_group_id = ?
            """, (res_group_id,))
            total_members = cursor.fetchone()[0]

            print(f"Found {other_records_count} other census records and {total_members} total members in group")

        # Delete the Census record first
        cursor.execute("DELETE FROM Census WHERE id = ?", (census_id,))

        # Handle ResGroup cleanup
        if res_group_id:
            # Delete this person's ResGroupMembers entry
            cursor.execute("""
                DELETE FROM ResGroupMembers 
                WHERE res_group_id = ? AND res_group_member = ?
            """, (res_group_id, person_id))

            if other_records_count == 0:
                # This was the last Census record in the group
                cursor.execute("DELETE FROM ResGroups WHERE id = ?", (res_group_id,))
                print(f"Deleted ResGroup {res_group_id} - was last member")
                
                messagebox.showinfo(
                    "Group Deleted",
                    f"Census household group for Year {census_year}, "
                    f"Dwelling {dwelling_num}, Household {household_num} "
                    f"has been deleted as this was the last member."
                )
            else:
                # Other records exist - keep the ResGroup
                print(f"Kept ResGroup {res_group_id} - {other_records_count} other records exist")
                
                messagebox.showinfo(
                    "Group Maintained",
                    f"Census household group for Year {census_year}, "
                    f"Dwelling {dwelling_num}, Household {household_num} "
                    f"has been maintained as other members exist."
                )

        # Commit the transaction
        cursor.execute("COMMIT")
        
        # Refresh the display
        load_census_records(cursor, census_tree, person_id)
        
        messagebox.showinfo("Success", "Census record deleted successfully")

    except sqlite3.Error as e:
        cursor.execute("ROLLBACK")
        messagebox.showerror("Error", f"Failed to delete Census record: {e}")
        print(f"Database error: {e}")  # For debugging
    except Exception as e:
        cursor.execute("ROLLBACK")
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        print(f"Unexpected error: {e}")  # For debugging



