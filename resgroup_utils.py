import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox
from family_linkage import open_family_linkage_window

# Debug mode for logging
DEBUG_MODE = True

def format_display_name(first_name, middle_name, last_name, married_name, sex):
    """Format the display name for the household tree."""
    parts = []
    if first_name:
        parts.append(first_name.strip())
    if middle_name:
        parts.append(middle_name.strip())

    if sex == 'F' and married_name:
        if last_name:
            parts.append(f"({last_name.strip()}) {married_name.strip()}")
        else:
            parts.append(married_name.strip())
    else:
        if last_name:
            parts.append(last_name.strip())

    return " ".join(parts)

def debug_log(message):
    """Log debug messages if DEBUG_MODE is enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def show_entire_group(cursor, census_tree):
    """Show all members of the Census residence linked to the selected record."""
    # Get selected Census record
    selected = census_tree.selection()
    if not selected:
        messagebox.showinfo("Select Record", "Please select a Census record to view the residence.")
        return

    # Fetch the Census record ID from the TreeView
    values = census_tree.item(selected[0])['values']
    census_record_id = values[0]  # First column should be ID
    print(f"DEBUG - Selected Census record ID: {census_record_id}", flush=True)
    print(f"DEBUG - Full values from selected record: {values}", flush=True)

    try:
        # Query the database for the required details
        cursor.execute("""
            SELECT 
                c.person_id,
                c.res_group_id, 
                c.census_year, 
                t.township_name, 
                t.township_id,
                c.census_dwellnum,
                c.census_householdnum,
                NULL AS address_id,  
                NULL AS address,     
                NULL AS notes,       
                NULL AS res_source   
            FROM Census c
            LEFT JOIN Townships t ON c.township_id = t.township_id
            WHERE c.id = ?
        """, (census_record_id,))
        record = cursor.fetchone()
        print(f"DEBUG - Fetched record details: {record}", flush=True)

        if not record:
            messagebox.showerror("Error", "Failed to fetch details for the selected Census record.")
            return

        # Extract the details for display and linkage
        person_id = record[0]
        res_group_id = record[1]
        census_year = record[2] or "Unknown"
        township_name = record[3] or "Unknown"
        township_id = record[4]
        dwelling_num = record[5] or "N/A"
        household_num = record[6] or "N/A"
        address = record[8] or "Unknown Address"

        print(f"DEBUG - Extracted values:", flush=True)
        print(f"  person_id: {person_id}", flush=True)
        print(f"  res_group_id: {res_group_id}", flush=True)
        print(f"  census_year: {census_year}", flush=True)
        print(f"  dwelling_num: {dwelling_num}", flush=True)
        print(f"  household_num: {household_num}", flush=True)

        # Query for all members in this ResGroup
        members_query = """
            SELECT p.id, p.first_name, p.middle_name, p.last_name, p.married_name,
                   c.person_age, c.person_occupation, c.relation_to_head
            FROM Census c
            JOIN People p ON c.person_id = p.id
            JOIN ResGroupMembers rgm ON c.person_id = rgm.res_group_member AND c.res_group_id = rgm.res_group_id
            WHERE c.census_year = ? AND c.census_dwellnum = ?
            ORDER BY COALESCE(rgm.member_order, 9999)
        """
        cursor.execute(members_query, (census_year, dwelling_num))
        members = cursor.fetchall()

        if not members:
            messagebox.showinfo("No Members", "No members found in this Census residence.")
            return
        print(f"DEBUG - Found {len(members)} members in group", flush=True)
        for member in members:
            print(f"DEBUG - Member: {member}", flush=True)

        # Create residence window
        residence_window = tk.Toplevel()
        residence_window.title("Census Residence Members")
        residence_window.geometry("700x500")

        # Display the members in a new window
        if not members:
            messagebox.showinfo("No Members", "No members found in this Census residence.")
            return

        # Add a TreeView to display the members
        tree = ttk.Treeview(
            residence_window, 
            columns=("ID", "Name", "Age", "Occupation", "Relation"), 
            show="headings", 
            height=15
        )
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Full Name")
        tree.heading("Age", text="Age")
        tree.heading("Occupation", text="Occupation")
        tree.heading("Relation", text="Relation to Head")

        tree.column("ID", width=50, anchor="center")
        tree.column("Name", width=200)
        tree.column("Age", width=70, anchor="center")
        tree.column("Occupation", width=150)
        tree.column("Relation", width=120)

        # Populate the TreeView with members
        for member in members:
            person_id = member[0]
            first_name = member[1] or ""
            middle_name = member[2] or ""
            last_name = member[3] or ""
            married_name = member[4] or ""

            if married_name:
                name = " ".join(filter(None, [
                    first_name,
                    middle_name,
                    f"({last_name}) {married_name}" if last_name else married_name
                ]))
            else:
                name = " ".join(filter(None, [first_name, middle_name, last_name]))

            age = member[5] or ""
            occupation = member[6] or ""
            relation = member[7] or ""

            tree.insert("", "end", values=(person_id, name, age, occupation, relation))

        tree.pack(fill="both", expand=True, padx=10, pady=10)



        # Define the double-click handler
        def on_double_click(event):
            selected_member = tree.selection()
            if not selected_member:
                messagebox.showinfo("No Selection", "Please select a member to edit.")
                return

            # Get person_id from the selected row
            values = tree.item(selected_member[0])['values']
            if not values:
                messagebox.showerror("Error", "Unable to retrieve values from the selected row.")
                return

            person_id = values[0]
            census_id = values[-1]
            print(f"Double-click detected. Selected person_id: {person_id}", flush=True)  # Debugging

            # Validate person_id
            try:
                person_id = int(person_id)  # Ensure person_id is an integer
                census_id = int(census_id)
            except ValueError:
                messagebox.showerror("Invalid ID", f"Invalid person_id: {person_id}")
                return

            # Ensure person_id exists in the People table
            cursor.execute("SELECT id FROM People WHERE id = ?", (person_id,))
            if not cursor.fetchone():
                messagebox.showerror("Error", f"Person with ID {person_id} not found in the database.")
                return

            def refresh_group_tree():
                # Refresh the parent tree with updated data
                load_group_tree(cursor, tree, res_group_id, census_year, dwelling_num)

            from census_records import edit_census_record  # Local import
            print(f"Made it to the call to edit the record. person id is: {person_id}",flush=True)
            edit_census_record(
                cursor=cursor,
                census_tree=tree,
                person_id=person_id,
                refresh_callback=refresh_group_tree,
                census_record_id=census_id  # New parameter used here
            )
        def manage_members():
            """Open the Census Family Linkage window."""
            open_family_linkage_window(
                cursor=cursor,
                census_id=census_record_id,
                res_group_id=res_group_id,
                census_year=census_year,
                township_name=township_name,
                dwelling_num=dwelling_num,
                household_num=household_num,
                address=address,
                person_id=person_id,
                township_id=township_id
            )

        # Bind double-click to the TreeView
        tree.bind("<Double-1>", on_double_click)

        manage_button = ttk.Button(residence_window, text="Manage Census Members", command=manage_members)
        manage_button.pack(pady=10)

        # Add completion checkbox frame
        completion_frame = ttk.Frame(residence_window)
        completion_frame.pack(pady=5)

        # Create BooleanVar for checkbox state
        completed_var = tk.BooleanVar()

        # Get initial completion state from ResGroups table
        cursor.execute("SELECT record_completed FROM ResGroups WHERE id = ?", (res_group_id,))
        initial_state = cursor.fetchone()[0] or False
        completed_var.set(initial_state)

        def toggle_completion():
            """Handle completion state changes"""
            db_connection = cursor.connection
            
            new_state = completed_var.get()
            message = (
                "Are you sure you want to mark this Census household as complete?" if new_state
                else "Are you sure you want to mark this Census household as incomplete?"
            )
            
            # Make confirmation dialog modal to residence_window
            if messagebox.askyesno("Confirm Status Change", message, parent=residence_window):
                try:
                    cursor.execute("""
                        UPDATE ResGroups 
                        SET record_completed = ? 
                        WHERE id = ?
                    """, (new_state, res_group_id))
                    db_connection.commit()
                    
                    # Update manage_button state based on completion status
                    manage_button.config(state="disabled" if new_state else "normal")
                    
                    # Show success message with residence_window as parent
                    messagebox.showinfo(
                        "Status Updated", 
                        "Census household marked as complete." if new_state 
                        else "Census household marked as incomplete.",
                        parent=residence_window
                    )
                    
                    # Force residence_window to the front
                    residence_window.lift()
                    residence_window.focus_force()
                    
                except sqlite3.Error as e:
                    messagebox.showerror(
                        "Database Error", 
                        f"Failed to update completion status: {e}",
                        parent=residence_window
                    )
                    completed_var.set(not new_state)
                    residence_window.lift()
                    residence_window.focus_force()
            else:
                # Revert checkbox if user cancels
                completed_var.set(not new_state)
                residence_window.lift()
                residence_window.focus_force()

        # Create and pack the checkbox
        completion_checkbox = ttk.Checkbutton(
            completion_frame,
            text="Census Household Record Complete",
            variable=completed_var,
            command=toggle_completion
        )
        completion_checkbox.pack(side="left", padx=5)

        # Set initial state of manage_button based on completion status
        manage_button.config(state="disabled" if initial_state else "normal")

        # Add a Close button
        close_button = ttk.Button(residence_window, text="Close", command=residence_window.destroy)
        close_button.pack(pady=10)

    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")

def get_or_create_resgroup(cursor, census_dwellnum, census_year, township_id, household_num, event_type="Census"):
    """
    Get or create a residential group for household tracking.

    Args:
        cursor: SQLite cursor object.
        census_dwellnum (str): Dwelling number (for Census/household events).
        census_year (int): Year the record applies (e.g., 1870, 1880).
        township_id (int): ID of the township (optional for Census).
        household_num (str): Household number (for Census).
        event_type (str): Type of event ("Census", "Marriage", "Move", etc.)

    Returns:
        res_group_id (int): ID of the existing or newly created ResGroup.
    """
    # Try to find an existing ResGroup first
    cursor.execute("""
        SELECT id
        FROM ResGroups
        WHERE dwelling_num = ?
          AND household_num = ?
          AND res_group_year = ?
          AND township_id = ?
          AND event_type = ?
    """, (census_dwellnum, household_num, census_year, township_id, event_type))

    result = cursor.fetchone()

    if result:
        # Found an existing ResGroup — reuse it
        return result[0]

    # Otherwise, create a new ResGroup
    cursor.execute("""
        INSERT INTO ResGroups (
            dwelling_num,
            household_num,
            res_group_year,
            township_id,
            event_type,
            household_notes
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        census_dwellnum,
        household_num,
        census_year,
        township_id,
        event_type,
        "Generated from " + event_type + " Data"
    ))

    return cursor.lastrowid

    
def add_resgroup_member(cursor, res_group_id, person_id, role=""):
    """
    Add a person to the ResGroupMembers table if they are not already linked.
    
    Args:
        cursor: SQLite cursor object
        res_group_id: The ID of the residential group
        person_id: The ID of the person to add
        role: Optional role in the group
        
    Returns:
        bool: True if member was added, False if already existed
    """
    # Verify ResGroup exists
    cursor.execute("SELECT 1 FROM ResGroups WHERE id = ?", (res_group_id,))
    if not cursor.fetchone():
        raise ValueError(f"ResGroup {res_group_id} does not exist")

    # Verify Person exists
    cursor.execute("SELECT 1 FROM People WHERE id = ?", (person_id,))
    if not cursor.fetchone():
        raise ValueError(f"Person {person_id} does not exist")

    # Check if already a member
    cursor.execute("""
        SELECT 1 
        FROM ResGroupMembers 
        WHERE res_group_id = ? AND res_group_member = ?
    """, (res_group_id, person_id))
    
    if cursor.fetchone():
        print(f"Person {person_id} is already a member of ResGroup {res_group_id}")
        return False

    # Add new member
    cursor.execute("""
        INSERT INTO ResGroupMembers (
            res_group_id, 
            res_group_member, 
            res_group_role
        ) VALUES (?, ?, ?)
    """, (res_group_id, person_id, role))
    
    print(f"Added person {person_id} to ResGroup {res_group_id}")
    return True


def update_resgroup_address(cursor, res_group_id, address_id):
    """
    Update the address_id for a residential group.

    Args:
        cursor: SQLite cursor object.
        res_group_id (int): The ID of the residential group to update.
        address_id (int): The new address ID to set.
    """
    cursor.execute("""
        UPDATE ResGroups 
        SET address_id = ? 
        WHERE id = ?
    """, (address_id, res_group_id))


def cleanup_resgroup(cursor, res_group_id, person_id):
    """
    Clean up ResGroup and ResGroupMembers records for a given person.

    Args:
        cursor: SQLite cursor object.
        res_group_id: ID of the ResGroup to clean up.
        person_id: ID of the person being removed.

    Returns:
        dict: A dictionary with cleanup results:
            - "deleted_group" (bool): True if the ResGroup was deleted.
            - "remaining_members" (int): Number of remaining members in the group.
    """
    # Validate that the ResGroup exists
    if not res_group_id:
        debug_log(f"No ResGroup ID provided for cleanup.")
        return {"deleted_group": False, "remaining_members": 0}

    # Check if the person is a member of the group
    cursor.execute("""
        SELECT 1 
        FROM ResGroupMembers 
        WHERE res_group_id = ? AND res_group_member = ?
    """, (res_group_id, person_id))
    if not cursor.fetchone():
        debug_log(f"No membership found for person {person_id} in ResGroup {res_group_id}.")
        return {"deleted_group": False, "remaining_members": 0}

    # Count total members in the group
    cursor.execute("""
        SELECT COUNT(*) 
        FROM ResGroupMembers 
        WHERE res_group_id = ?
    """, (res_group_id,))
    total_members = cursor.fetchone()[0]

    if total_members == 1:
        # If this is the last member, delete the group and its membership
        debug_log(f"ResGroup {res_group_id} has only one member. Deleting group.")
        cursor.execute("DELETE FROM ResGroupMembers WHERE res_group_id = ?", (res_group_id,))
        cursor.execute("DELETE FROM ResGroups WHERE id = ?", (res_group_id,))
        return {"deleted_group": True, "remaining_members": 0}
    else:
        # Remove the person's membership and keep the group
        debug_log(f"Removing person {person_id} from ResGroup {res_group_id}. Remaining members: {total_members - 1}.")
        cursor.execute("""
            DELETE FROM ResGroupMembers 
            WHERE res_group_id = ? AND res_group_member = ?
        """, (res_group_id, person_id))
        return {"deleted_group": False, "remaining_members": total_members - 1}