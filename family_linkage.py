import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from search_controls import SearchControls

temp_orders = {}  # Store member ordering changes: {member_id: new_order}
original_orders = {}  # Store original orders for comparison

def move_member_up(tree):
    """Move selected member up in the order."""
    selected = tree.selection()
    if not selected:
        return
        
    curr_item = selected[0]
    prev_item = tree.prev(curr_item)
    
    if prev_item:
        # Get the values for both items
        curr_values = tree.item(curr_item)['values']
        prev_values = tree.item(prev_item)['values']
        
        # Swap their positions in the tree
        tree.move(curr_item, tree.parent(curr_item), tree.index(prev_item))
        
        # Update temp_orders with new positions
        member_id = curr_values[0]  # Assuming ID is first column
        prev_id = prev_values[0]
        
        # Update the order in temp_orders
        if member_id not in temp_orders:
            temp_orders[member_id] = tree.index(curr_item)
        if prev_id not in temp_orders:
            temp_orders[prev_id] = tree.index(prev_item)
        
        # Swap their orders
        temp_orders[member_id], temp_orders[prev_id] = temp_orders[prev_id], temp_orders[member_id]

def move_member_down(tree):
    """Move selected member down in the order."""
    selected = tree.selection()
    if not selected:
        return
        
    curr_item = selected[0]
    next_item = tree.next(curr_item)
    
    if next_item:
        # Get the values for both items
        curr_values = tree.item(curr_item)['values']
        next_values = tree.item(next_item)['values']
        
        # Swap their positions in the tree
        tree.move(curr_item, tree.parent(curr_item), tree.index(next_item))
        
        # Update temp_orders with new positions
        member_id = curr_values[0]  # Assuming ID is first column
        next_id = next_values[0]
        
        # Update the order in temp_orders
        if member_id not in temp_orders:
            temp_orders[member_id] = tree.index(curr_item)
        if next_id not in temp_orders:
            temp_orders[next_id] = tree.index(next_item)
        
        # Swap their orders
        temp_orders[member_id], temp_orders[next_id] = temp_orders[next_id], temp_orders[member_id]




# Move format_value outside both functions so it can be used globally
def format_value(value):
    """Format date values and handle None values consistently."""
    if value is None or str(value).lower() == 'none':
        return ""
    try:
        # Try to parse as full date
        date = datetime.strptime(value, '%Y-%m-%d')
        return date.strftime('%m-%d-%Y')
    except ValueError:
        try:
            # Try to parse as year-month
            date = datetime.strptime(value, '%Y-%m')
            return date.strftime('%m-%Y')
        except ValueError:
            # If it's just a year or any other format, return as is
            return value


def prompt_for_census_details(cursor, person_id, census_year):
    
    from census_records import get_census_fields

    """Prompt the user to enter census details for a newly added member."""
    fields_mapping = get_census_fields()
    field_defs = fields_mapping.get(str(census_year), [])
    result_data = {}

    # Fetch person info
    cursor.execute("SELECT first_name, middle_name, last_name, birth_date FROM People WHERE id = ?", (person_id,))
    person = cursor.fetchone()
    name_str = " ".join(filter(None, person[:3]))

    def submit():
        for field, _ in field_defs:
            result_data[field] = entry_vars[field].get().strip()
        popup.destroy()

    popup = tk.Toplevel()
    popup.title(f"Census Details for {name_str}")
    popup.geometry("400x500")
    popup.grab_set()

    tk.Label(popup, text=f"{name_str}\nCensus Year: {census_year}", font=("Arial", 12, "bold")).pack(pady=10)

    form_frame = tk.Frame(popup)
    form_frame.pack(pady=5)

    entry_vars = {}
    for idx, (field, hint) in enumerate(field_defs):
        tk.Label(form_frame, text=f"{field}:", anchor="w").grid(row=idx, column=0, sticky="w", padx=10, pady=3)
        var = tk.StringVar()
        entry = tk.Entry(form_frame, textvariable=var, width=30)
        entry.grid(row=idx, column=1, padx=5, pady=3)
        if "Required" in hint:
            entry.config(background="#ffffcc")  # Light yellow to indicate required
        entry_vars[field] = var

    submit_btn = tk.Button(popup, text="Save", command=submit)
    submit_btn.pack(pady=10)

    popup.wait_window()
    return result_data


def get_available_family_members(cursor, person_id, household_num, census_year):
    """Get list of available family members not in current household."""
    available_family_members = []
    
    # Get current household members' IDs
    cursor.execute("""
        SELECT person_id
        FROM Census
        WHERE census_year = ? AND census_dwellnum = ?
    """, (census_year, household_num))
    household_member_ids = {row[0] for row in cursor.fetchall()}
    
    # Fetch the person's details
    cursor.execute("SELECT father, mother FROM People WHERE id = ?", (person_id,))
    person_details = cursor.fetchone()
    
    if not person_details:
        print(f"No details found for person_id: {person_id}")
        return []
        
    father_id, mother_id = person_details
    
    # Fetch father if not in household
    if father_id and father_id not in household_member_ids:
        cursor.execute("""
            SELECT id, first_name, middle_name, last_name, married_name, birth_date, death_date 
            FROM People WHERE id = ?
        """, (father_id,))
        father = cursor.fetchone()
        if father:
            available_family_members.append(father + ('Father',))

    # Fetch mother if not in household
    if mother_id and mother_id not in household_member_ids:
        cursor.execute("""
            SELECT id, first_name, middle_name, last_name, married_name, birth_date, death_date 
            FROM People WHERE id = ?
        """, (mother_id,))
        mother = cursor.fetchone()
        if mother:
            available_family_members.append(mother + ('Mother',))

    # Fetch spouse(s) not in household
    cursor.execute("""
        SELECT p.id, p.first_name, p.middle_name, p.last_name, p.married_name, p.birth_date, p.death_date
        FROM Marriages m
        JOIN People p ON (m.person1_id = p.id OR m.person2_id = p.id)
        WHERE (m.person1_id = ? OR m.person2_id = ?) AND p.id != ?
    """, (person_id, person_id, person_id))
    spouses = cursor.fetchall()
    for spouse in spouses:
        if spouse[0] not in household_member_ids:
            available_family_members.append(spouse + ('Spouse',))

    # Fetch children not in household
    cursor.execute("""
        SELECT id, first_name, middle_name, last_name, married_name, birth_date, death_date
        FROM People
        WHERE father = ? OR mother = ?
    """, (person_id, person_id))
    children = cursor.fetchall()
    for child in children:
        if child[0] not in household_member_ids:
            available_family_members.append(child + ('Child',))

    # Fetch siblings only if at least one parent is known
    if father_id or mother_id:
        sibling_query = """
            SELECT id, first_name, middle_name, last_name, married_name, birth_date, death_date
            FROM People
            WHERE id != ? AND (
        """
        query_params = [person_id]
        
        if father_id:
            sibling_query += "(father = ? AND father IS NOT NULL)"
            query_params.append(father_id)
        
        if mother_id:
            if father_id:
                sibling_query += " OR "
            sibling_query += "(mother = ? AND mother IS NOT NULL)"
            query_params.append(mother_id)
        
        sibling_query += ")"
        
        cursor.execute(sibling_query, tuple(query_params))
        siblings = cursor.fetchall()
        for sibling in siblings:
            if sibling[0] not in household_member_ids:
                available_family_members.append(sibling + ('Sibling',))

    return available_family_members

def open_family_linkage_window(cursor, census_id, res_group_id, census_year, township_name, 
                             dwelling_num, household_num, address, person_id, township_id):
    """Open window to manage Census record members."""

    # Connect to the database
    connection = sqlite3.connect('phoenix.db')
    cursor = connection.cursor()

    # Store the passed person_id as a global variable
    global current_person_id
    current_person_id = person_id

    # Temporary storage for changes
    temp_links = set()
    temp_unlinks = set()
    temp_record_nums = {}

    def populate_search_results(records):
        """Populate search results tree with found records."""
        tree_search_results.delete(*tree_search_results.get_children())
        for record in records:
            tree_search_results.insert("", "end", values=(
                record[0],             # ID
                record[1] or "",       # first_name
                record[2] or "",       # middle_name
                record[3] or "",       # last_name
                record[4] or "",       # married_name
                format_value(record[5]) if record[5] else "",  # birth_date
                format_value(record[6]) if record[6] else "",  # death_date
                ""                     # No relationship for search results
            ))

    def refresh_family_treeviews():
        """Refresh family trees for current and available members."""
        # Clear existing tree data
        for tree in [tree_linked, tree_available]:
            for item in tree.get_children():
                tree.delete(item)

        # Get current members with their order
        cursor.execute("""
        SELECT p.id, p.first_name, p.middle_name, p.last_name, p.married_name, 
               p.birth_date, p.death_date, 
               COALESCE(rgm.member_order, 9999) as display_order
        FROM People p
        JOIN ResGroupMembers rgm ON p.id = rgm.res_group_member
        WHERE rgm.res_group_id = ?
        ORDER BY 
            CASE 
                WHEN rgm.member_order IS NULL THEN 1 
                ELSE 0 
            END,
            COALESCE(rgm.member_order, 9999)
    """, (res_group_id,))
        
        members = cursor.fetchall()
        
        # Store original orders
        for member in members:
            order_value = member[7] if member[7] is not None else None
            original_orders[member[0]] = order_value


        # Show current household members in the linked tree (if not unlinked)
        for member in members:
            if member[0] not in temp_unlinks:
                tree_linked.insert("", "end", values=(
                    member[0],             # ID
                    member[1] or "",       # first_name
                    member[2] or "",       # middle_name
                    member[3] or "",       # last_name
                    member[4] or "",       # married_name
                    format_value(member[5]) if member[5] else "",  # birth_date
                    format_value(member[6]) if member[6] else "",  # death_date
                    ""                     # relationship
                ))

        # Get available family members
        available_members = get_available_family_members(cursor, person_id, household_num, census_year)

        # First, add family members who are available
        for member in available_members:
            id_, first_name, middle_name, last_name, married_name, birth_date, death_date, relationship = member
            if id_ not in temp_links and id_ not in [m[0] for m in members if m[0] not in temp_unlinks]:
                tree_available.insert("", "end", values=(
                    id_,
                    first_name or "",
                    middle_name or "",
                    last_name or "",
                    married_name or "",
                    format_value(birth_date) if birth_date else "",
                    format_value(death_date) if birth_date else "",
                    relationship
                ))

        # Then, add any unlinked members back to available tree
        for member in members:
            if member[0] in temp_unlinks:
                # Get their relationship from available_members if they're family
                relationship = next((m[7] for m in available_members if m[0] == member[0]), "")
                tree_available.insert("", "end", values=(
                    member[0],             # ID
                    member[1] or "",       # first_name
                    member[2] or "",       # middle_name
                    member[3] or "",       # last_name
                    member[4] or "",       # married_name
                    format_value(member[5]) if member[5] else "",  # birth_date
                    format_value(member[6]) if member[6] else "",  # death_date
                    relationship          # relationship if they're family
                ))

        # Add members from temp_links to linked tree
        for member_id in temp_links:

            # First check if it's a family member
            member = next((m for m in available_members if m[0] == member_id), None)
            
            if member:
                # Handle family member
                if member_id not in [tree_linked.item(i)["values"][0] for i in tree_linked.get_children()]:
                    id_, first_name, middle_name, last_name, married_name, birth_date, death_date, relationship = member
                    tree_linked.insert("", "end", values=(
                        id_,
                        first_name or "",
                        middle_name or "",
                        last_name or "",
                        married_name or "",
                        format_value(birth_date) if birth_date else "",
                        format_value(death_date) if birth_date else "",
                        relationship if id_ != person_id else ""
                    ))
            else:
                # If not a family member, fetch from database
                cursor.execute("""
                    SELECT id, first_name, middle_name, last_name, married_name, 
                           birth_date, death_date 
                    FROM People 
                    WHERE id = ?
                """, (member_id,))
                db_member = cursor.fetchone()
                
                if db_member and member_id not in [tree_linked.item(i)["values"][0] for i in tree_linked.get_children()]:
                    tree_linked.insert("", "end", values=(
                        db_member[0],            # id
                        db_member[1] or "",      # first_name
                        db_member[2] or "",      # middle_name
                        db_member[3] or "",      # last_name
                        db_member[4] or "",      # married_name
                        format_value(db_member[5]) if db_member[5] else "",  # birth_date
                        format_value(db_member[6]) if db_member[6] else "",  # death_date
                        ""                       # relationship (empty for non-family)
                    ))

    def link_selected():
        """Link selected members from available tree."""
        selected_items = tree_available.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select members to link.")
            return

        for item in selected_items:
            member_id = tree_available.item(item)["values"][0]
            temp_links.add(member_id)
            if member_id in temp_unlinks:
                temp_unlinks.remove(member_id)

        refresh_family_treeviews()

    def unlink_selected():
        """Unlink selected members from linked tree."""
        selected_items = tree_linked.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select members to unlink.")
            return

        for item in selected_items:
            member_id = tree_linked.item(item)["values"][0]
            temp_unlinks.add(member_id)
            if member_id in temp_links:
                temp_links.remove(member_id)

        refresh_family_treeviews()

    def cancel_changes():
        """Cancel all temporary changes and optionally exit."""
        if temp_links or temp_unlinks:  # Only ask if there are unsaved changes
            if messagebox.askyesno("Confirm Cancel", 
                                 "Are you sure you want to cancel all changes? The window will close."):
                temp_links.clear()
                temp_unlinks.clear()
                window.destroy()
        else:
            if messagebox.askyesno("Exit Window", "Would you like to exit?"):
                window.destroy()

    # START OF NEW CODE

    def save_changes():
        """Show summary and save changes if confirmed."""
        changes_made = []
        
        if temp_links:
            changes_made.append(f"{len(temp_links)} member(s) added")
        if temp_unlinks:
            # Check which members actually need to be unlinked
            cursor.execute("""
                SELECT person_id 
                FROM Census 
                WHERE census_year = ? AND census_dwellnum = ?
            """, (census_year, dwelling_num))
            existing_members = {row[0] for row in cursor.fetchall()}
            
            real_unlinks = {member_id for member_id in temp_unlinks 
                           if member_id in existing_members}
            
            if real_unlinks:
                changes_made.append(f"{len(real_unlinks)} member(s) removed")
                
        order_changes = any(
            member_id in temp_orders and 
            temp_orders[member_id] != original_orders.get(member_id)
            for member_id in temp_orders
        )
        if order_changes:
            changes_made.append("Member order updated")

        if not changes_made:
            messagebox.showinfo("No Changes", "No changes to save.")
            return

        summary = "Changes to be made:\n\n"
        
        if temp_links:
            summary += "\nMembers to be ADDED:\n"
            for member_id in sorted(temp_links):
                cursor.execute("""
                    SELECT first_name, last_name 
                    FROM People 
                    WHERE id = ?
                """, (member_id,))
                name = cursor.fetchone()
                if name:
                    summary += f"- {name[0]} {name[1]} (ID: {member_id})\n"

        if temp_unlinks:
            if real_unlinks:
                summary += "\nMembers to be REMOVED:\n"
                for member_id in sorted(real_unlinks):
                    cursor.execute("""
                        SELECT first_name, last_name 
                        FROM People 
                        WHERE id = ?
                    """, (member_id,))
                    name = cursor.fetchone()
                    if name:
                        summary += f"- {name[0]} {name[1]} (ID: {member_id})\n"

        if order_changes:
            summary += "\nMember order will be updated according to current display order."

        if not messagebox.askyesno("Confirm Changes", summary):
            return

        def save_data_changes():
            """Process all database changes within a transaction, including deferred census entry."""
            try:
                # Remove unlinked members
                for member_id in temp_unlinks:
                    cursor.execute("""
                        SELECT 1 FROM Census 
                        WHERE person_id = ? AND census_year = ? AND census_dwellnum = ?
                    """, (member_id, census_year, dwelling_num))

                    if cursor.fetchone():
                        cursor.execute("""
                            DELETE FROM ResGroupMembers 
                            WHERE res_group_member = ? 
                            AND res_group_id IN (
                                SELECT id FROM ResGroups 
                                WHERE res_group_year = ? AND census_dwellnum = ?
                            )
                        """, (member_id, census_year, dwelling_num))

                        cursor.execute("""
                            DELETE FROM Census 
                            WHERE person_id = ? AND census_year = ? AND census_dwellnum = ?
                        """, (member_id, census_year, dwelling_num))

                # Add linked members
                for member_id in temp_links:
                    cursor.execute("""
                        SELECT 1 FROM Census 
                        WHERE person_id = ? AND census_year = ? AND census_dwellnum = ?
                    """, (member_id, census_year, dwelling_num))

                    if not cursor.fetchone():
                        cursor.execute("""
                            SELECT id FROM ResGroups 
                            WHERE res_group_year = ? AND census_dwellnum = ?
                        """, (census_year, dwelling_num))

                        res_group = cursor.fetchone()
                        if res_group:
                            res_group_id = res_group[0]
                        else:
                            print(f"[DEBUG] Creating new ResGroup for Census Year: {census_year}, Dwelling: {dwelling_num}")
                            cursor.execute("""
                                INSERT INTO ResGroups (
                                    res_group_year, census_dwellnum, event_type, household_notes, census_notes
                                ) VALUES (?, ?, ?, ?, ?)
                            """, (
                                census_year,
                                dwelling_num,
                                'Census',
                                'Generated from Census Data',
                                f'Census Year: {census_year}'
                            ))
                            res_group_id = cursor.lastrowid
                            print(f"[DEBUG] New ResGroup Created with ID: {res_group_id}")

                        print(f"[DEBUG] Adding {member_id} to Census with ResGroup ID: {res_group_id}")

                        # Prompt for missing census fields
                        census_details = prompt_for_census_details(cursor, member_id, census_year)

                        # Try estimating age if birth date is known
                        if "Age" in census_details and not census_details["Age"]:
                            cursor.execute("SELECT birth_date FROM People WHERE id = ?", (member_id,))
                            bdate = cursor.fetchone()[0]
                            if bdate and bdate[:4].isdigit():
                                est_age = int(census_year) - int(bdate[:4])
                                census_details["Age"] = str(est_age)

                        # Insert full Census record
                        cursor.execute("""
                            INSERT INTO Census (
                                person_id, census_year, township_id, census_dwellnum, 
                                census_householdnum, res_group_id,
                                person_age, person_occupation, real_estate_value, estate_value,
                                sex, race, married_this_year, relation_to_head, attended_school,
                                city, state, birth_place, father_birth_place, mother_birth_place,
                                native_language, years_married, number_of_children_born,
                                number_of_children_living, farm_owner, rented_home_or_farm
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            member_id,
                            census_year,
                            township_id,
                            dwelling_num,
                            household_num,
                            res_group_id,
                            census_details.get("Age", ""),
                            census_details.get("Occupation", ""),
                            census_details.get("Real Estate Value", ""),
                            census_details.get("Estate Value", ""),
                            census_details.get("Sex", ""),
                            census_details.get("Race", ""),
                            census_details.get("Married this Year", ""),
                            census_details.get("Relation to Head", ""),
                            census_details.get("Attended School", ""),
                            census_details.get("City", ""),
                            census_details.get("State", ""),
                            census_details.get("Birth Place", ""),
                            census_details.get("Fathers Birth Place", ""),
                            census_details.get("Mothers Birth Place", ""),
                            census_details.get("Native Language", ""),
                            census_details.get("Years Married", ""),
                            census_details.get("Number of Children Born", ""),
                            census_details.get("Number of Children Living", ""),
                            census_details.get("Farm Owner", ""),
                            census_details.get("Rented Home or Farm", "")
                        ))
                        print(f"[DEBUG] Inserted {member_id} into Census.")

                        # Add to ResGroupMembers
                        cursor.execute("""
                            SELECT 1 FROM ResGroupMembers 
                            WHERE res_group_id = ? AND res_group_member = ?
                        """, (res_group_id, member_id))
                        if not cursor.fetchone():
                            print(f"[DEBUG] Adding {member_id} to ResGroupMembers.")
                            cursor.execute("""
                                INSERT INTO ResGroupMembers (res_group_id, res_group_member)
                                VALUES (?, ?)
                            """, (res_group_id, member_id))
                        else:
                            print(f"[DEBUG] {member_id} already exists in ResGroupMembers.")

                return True

            except Exception as e:
                print(f"Error in save_data_changes: {e}")
                return False

    # END OF NEW CODE

    def add_non_family_to_census():
        """Add selected non-family member from search results."""
        selected_items = tree_search_results.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a person to add.")
            return

        for item in selected_items:
            member_id = int(tree_search_results.item(item)["values"][0])  # Convert to int
            
            # Check if member is already in linked tree
            existing_members = [int(tree_linked.item(i)["values"][0]) for i in tree_linked.get_children()]
            if member_id in existing_members:
                messagebox.showwarning("Already Added", 
                    f"Person ID {member_id} is already in the household. Cannot add them again.")
                continue

            print(f"Adding member {member_id} to temp_links", flush=True)
            temp_links.add(member_id)
            if member_id in temp_unlinks:
                print(f"Removing member {member_id} from temp_unlinks", flush=True)
                temp_unlinks.remove(member_id)

        # Clear search controls
        search_controls.clear_search_fields()
        # Clear search results tree
        tree_search_results.delete(*tree_search_results.get_children())
        # Refresh the trees to show the new member in linked tree
        refresh_family_treeviews()


    # Main window setup
    window = tk.Toplevel()
    window.title("Manage Census Record Members")
    window.geometry("1600x900")

    # Informational section
    info_frame = ttk.Frame(window)
    info_frame.pack(fill="x", pady=10)

    info_label = ttk.Label(
        info_frame,
        text=f"Census Year: {census_year}\nTownship: {township_name}\nDwelling: {dwelling_num} Household: {household_num}",
        font=("Arial", 12, "bold"),
        anchor="w"
    )
    info_label.pack(padx=10)

    # Treeview section
    tree_frame = ttk.Frame(window)
    tree_frame.pack(fill="both", expand=True, pady=10)

    # Configure columns including Relationship
    columns_config = [
        ("ID", 50), 
        ("First", 100), 
        ("Middle", 75), 
        ("Last", 100),
        ("Married", 100),
        ("Birth", 80), 
        ("Death", 80),
        ("Relationship", 100)  # Added Relationship column
    ]

    # Linked members tree
    tree_linked_frame = ttk.LabelFrame(tree_frame, text="Current Census Record Members")
    tree_linked_frame.pack(side="left", fill="both", expand=True, padx=5)
    tree_linked = ttk.Treeview(tree_linked_frame, 
        columns=[col[0] for col in columns_config], 
        show="headings")
    
    for col, width in columns_config:
        tree_linked.heading(col, text=col)
        tree_linked.column(col, width=width)
    tree_linked.pack(fill="both", expand=True)

    # Frame for linked members controls
    linked_controls_frame = ttk.Frame(tree_linked_frame)
    linked_controls_frame.pack(fill="x", pady=5)

    # Left side - Member order controls
    order_controls = ttk.Frame(linked_controls_frame)
    order_controls.pack(side="left", padx=5)
    
    ttk.Button(
        order_controls, 
        text="↑ Move Up", 
        command=lambda: move_member_up(tree_linked)
    ).pack(side="left", padx=2)
    
    ttk.Button(
        order_controls, 
        text="↓ Move Down", 
        command=lambda: move_member_down(tree_linked)
    ).pack(side="left", padx=2)

    # Right side - Unlink button
    ttk.Button(
        linked_controls_frame, 
        text="Unlink Selected", 
        command=unlink_selected
    ).pack(side="right", padx=5)

    # Available members tree
    tree_available_frame = ttk.LabelFrame(tree_frame, text="Available Family Members")
    tree_available_frame.pack(side="right", fill="both", expand=True, padx=5)
    tree_available = ttk.Treeview(tree_available_frame, 
        columns=[col[0] for col in columns_config], 
        show="headings")
    
    for col, width in columns_config:
        tree_available.heading(col, text=col)
        tree_available.column(col, width=width)
    tree_available.pack(fill="both", expand=True)

    # Add Link button under available members tree
    link_button_frame = ttk.Frame(tree_available_frame)
    link_button_frame.pack(fill="x", pady=5)
    ttk.Button(link_button_frame, text="Link Selected", command=link_selected).pack(side="right", padx=5)   
    
    # ---------------------------------------------------
    # Start of Bottom Half Section for Seach and Addition
    # ---------------------------------------------------

    # Bottom section frame with horizontal split
    bottom_frame = ttk.Frame(window)
    bottom_frame.pack(fill="x", pady=10, padx=10)

    #Left side - Search Section
    search_frame = ttk.LabelFrame(bottom_frame, text="Add Non-Family Members")
    search_frame.pack(side="left", fill="both", expand=True, padx=(0,5))

    # Configure columns including Relationship - use same config as other trees
    search_tree_columns = [
        ("ID", 50), 
        ("First", 100), 
        ("Middle", 75), 
        ("Last", 100),
        ("Married", 100),
        ("Birth", 80), 
        ("Death", 80)
    ]

    tree_search_results = ttk.Treeview(search_frame, 
        columns=[col[0] for col in search_tree_columns], 
        show="headings", height=5)
        
    # Apply the same column configuration as other trees
    for col, width in search_tree_columns:
        tree_search_results.heading(col, text=col)
        tree_search_results.column(col, width=width)

    # Create search controls
    search_controls = SearchControls(
        search_frame,
        tree_search_results,
        cursor,
        populate_search_results
    )
    search_controls.show_record_number_search(True)
    search_controls.pack(side="top", fill="x", padx=5)
    
    # Pack tree and add button
    tree_search_results.pack(fill="x", pady=5)
    add_button = ttk.Button(search_frame, text="Add to Census Record", command=add_non_family_to_census)
    add_button.pack(pady=5)

    # ----------------------------------------------------------
    # Right Side of the Bottom Half - Add a New Person to System
    # ----------------------------------------------------------

    # Right side - New Person section
    new_person_frame = ttk.LabelFrame(bottom_frame, text="Add New Person")
    new_person_frame.pack(side="right", fill="both", expand=True, padx=(5,0))

    # First Name entry
    label_first_name = ttk.Label(new_person_frame, text="First Name:")
    label_first_name.grid(row=0, column=0, padx=5, pady=5)
    entry_first_name = ttk.Entry(new_person_frame)
    entry_first_name.grid(row=0, column=1, padx=5, pady=5)

    # Middle Name entry
    label_middle_name = ttk.Label(new_person_frame, text="Middle Name:")
    label_middle_name.grid(row=0, column=2, padx=5, pady=5)
    entry_middle_name = ttk.Entry(new_person_frame)
    entry_middle_name.grid(row=0, column=3, padx=5, pady=5)

    # Last Name entry
    label_last_name = ttk.Label(new_person_frame, text="Last Name:")
    label_last_name.grid(row=0, column=4, padx=5, pady=5)
    entry_last_name = ttk.Entry(new_person_frame)
    entry_last_name.grid(row=0, column=5, padx=5, pady=5)

    # Title entry
    label_title = ttk.Label(new_person_frame, text="Title:")
    label_title.grid(row=1, column=0, padx=5, pady=5)
    entry_title = ttk.Entry(new_person_frame)
    entry_title.grid(row=1, column=1, padx=5, pady=5)

    # Nick Name entry
    label_nick_name = ttk.Label(new_person_frame, text="Nick Name:")
    label_nick_name.grid(row=1, column=2, padx=5, pady=5)
    entry_nick_name = ttk.Entry(new_person_frame)
    entry_nick_name.grid(row=1, column=3, padx=5, pady=5)

    # Married Name entry
    label_married_name = ttk.Label(new_person_frame, text="Married Name:")
    label_married_name.grid(row=1, column=4, padx=5, pady=5)
    entry_married_name = ttk.Entry(new_person_frame)
    entry_married_name.grid(row=1, column=5, padx=5, pady=5)

    # Separator on the form
    separator = ttk.Separator(new_person_frame, orient='horizontal')
    separator.grid(row=2, columnspan=6, pady=10, sticky='ew')

    # Birth Date entry
    label_birth_date = ttk.Label(new_person_frame, text="Birth Date:")
    label_birth_date.grid(row=3, column=0, padx=5, pady=5)
    entry_birth_date = ttk.Entry(new_person_frame)
    entry_birth_date.grid(row=3, column=1, padx=5, pady=5)

    # Birth Location entry
    label_birth_location = ttk.Label(new_person_frame, text="Birth Location:")
    label_birth_location.grid(row=3, column=2, padx=5, pady=5)
    entry_birth_location = ttk.Entry(new_person_frame)
    entry_birth_location.grid(row=3, column=3, padx=5, pady=5)

    # Death Date entry
    label_death_date = ttk.Label(new_person_frame, text="Death Date:")
    label_death_date.grid(row=4, column=0, padx=5, pady=5)
    entry_death_date = ttk.Entry(new_person_frame)
    entry_death_date.grid(row=4, column=1, padx=5, pady=5)

    # Death Location entry
    label_death_location = ttk.Label(new_person_frame, text="Death Location:")
    label_death_location.grid(row=4, column=2, padx=5, pady=5)
    entry_death_location = ttk.Entry(new_person_frame)
    entry_death_location.grid(row=4, column=3, padx=5, pady=5)

    # Separator on the form
    separator = ttk.Separator(new_person_frame, orient='horizontal')
    separator.grid(row=5, columnspan=6, pady=10, sticky='ew')

    # Father entry
    label_father = ttk.Label(new_person_frame, text="Father:")
    label_father.grid(row=6, column=0, padx=5, pady=5)
    entry_father = ttk.Entry(new_person_frame)
    entry_father.grid(row=6, column=1, padx=5, pady=5)

    # Mother entry
    label_mother = ttk.Label(new_person_frame, text="Mother:")
    label_mother.grid(row=6, column=2, padx=5, pady=5)
    entry_mother = ttk.Entry(new_person_frame)
    entry_mother.grid(row=6, column=3, padx=5, pady=5)

    #Married entry
    label_married = ttk.Label(new_person_frame, text="Married To:")
    label_married.grid(row=6, column=4, padx=5, pady=5)
    entry_married_to = ttk.Entry(new_person_frame)
    entry_married_to.grid(row=6, column=5, padx=5, pady=5)

    # Separator for buttons
    separator = ttk.Separator(new_person_frame, orient='horizontal')
    separator.grid(row=7, columnspan=6, pady=10, sticky='ew')

    # Button frame
    button_frame = ttk.Frame(new_person_frame)
    button_frame.grid(row=8, column=0, columnspan=6, pady=10)

    def add_new_person():
        """Add new person to database and temp_links with validation."""
        error_messages = []
        create_marriage_record = False
        marriage_partner_id = None
        
        # Trim all input fields
        first_name = entry_first_name.get().strip()
        middle_name = entry_middle_name.get().strip()
        last_name = entry_last_name.get().strip()
        married_name = entry_married_name.get().strip()
        title = entry_title.get().strip()
        nick_name = entry_nick_name.get().strip()
        birth_date = entry_birth_date.get().strip()
        birth_location = entry_birth_location.get().strip()
        death_date = entry_death_date.get().strip()
        death_location = entry_death_location.get().strip()
        father_id = entry_father.get().strip()
        mother_id = entry_mother.get().strip()
        married_to_id = entry_married_to.get().strip()

        # Validate required name fields
        if not first_name:
            error_messages.append("First name is required")
        if not last_name and not married_name:
            error_messages.append("Either last name or married name is required")

        # Validate reference IDs
        if father_id:
            try:
                father_id = int(father_id)
                cursor.execute("SELECT id FROM People WHERE id = ?", (father_id,))
                if not cursor.fetchone():
                    error_messages.append(f"Father ID {father_id} does not exist in the system")
            except ValueError:
                error_messages.append("Father ID must be a valid number")

        if mother_id:
            try:
                mother_id = int(mother_id)
                cursor.execute("SELECT id FROM People WHERE id = ?", (mother_id,))
                if not cursor.fetchone():
                    error_messages.append(f"Mother ID {mother_id} does not exist in the system")
            except ValueError:
                error_messages.append("Mother ID must be a valid number")

        if married_to_id:
            try:
                married_to_id = int(married_to_id)
                cursor.execute("SELECT id FROM People WHERE id = ?", (married_to_id,))
                if not cursor.fetchone():
                    error_messages.append(f"Married To ID {married_to_id} does not exist in the system")
                else:
                    # Flag for potential marriage record creation after person is added
                    create_marriage_record = True
                    marriage_partner_id = married_to_id
            except ValueError:
                error_messages.append("Married To ID must be a valid number")

        # Validate dates if provided
        if birth_date:
            try:
                birth_date, birth_precision = parse_date_input(birth_date)
            except ValueError as e:
                error_messages.append(f"Invalid birth date format: {str(e)}")

        if death_date:
            try:
                death_date, death_precision = parse_date_input(death_date)
            except ValueError as e:
                error_messages.append(f"Invalid death date format: {str(e)}")

        # If any validation errors, show them and return
        if error_messages:
            messagebox.showerror("Validation Error", "\n".join(error_messages))
            return

        try:
            # Insert new person into database
            cursor.execute("""
                INSERT INTO People (
                    first_name, middle_name, last_name, title, nick_name, 
                    married_name, birth_date, birth_location, death_date, 
                    death_location, father, mother, married_to
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                first_name,
                middle_name,
                last_name,
                title,
                nick_name,
                married_name,
                birth_date if birth_date else "",
                birth_location,
                death_date if death_date else "",
                death_location,
                father_id if father_id else "",
                mother_id if mother_id else "",
                married_to_id if married_to_id else ""
            ))
            
            connection.commit()
            new_person_id = cursor.lastrowid

            # Handle marriage record creation if needed
            if create_marriage_record:
                if messagebox.askyesno("Add Marriage Record", 
                                     "Would you like to create a marriage record for this couple?"):
                    cursor.execute("""
                        INSERT INTO Marriages (person1_id, person2_id)
                        VALUES (?, ?)
                    """, (new_person_id, marriage_partner_id))
                    connection.commit()

            # Add to temp_links
            temp_links.add(new_person_id)
            
            # Refresh trees - this will handle updating both linked and available trees
            # including any changes due to new marriage relationships
            refresh_family_treeviews()
            
            # Clear form
            reset_new_person_form()
            
            messagebox.showinfo("Success", 
                f"Person added successfully (ID: {new_person_id}) and added to household.")
                
        except sqlite3.Error as e:
            connection.rollback()
            messagebox.showerror("Error", f"Failed to add person: {str(e)}")

    def reset_new_person_form():
        """Clear all fields in the new person form."""
        for entry in [
            entry_first_name, entry_middle_name, entry_last_name,
            entry_title, entry_nick_name, entry_married_name,
            entry_birth_date, entry_birth_location,
            entry_death_date, entry_death_location,
            entry_father, entry_mother, entry_married_to
        ]:
            entry.delete(0, tk.END)

    # Add and Reset buttons
    ttk.Button(button_frame, text="Add Person", command=add_new_person).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Reset Form", command=reset_new_person_form).pack(side=tk.LEFT, padx=5)

#----------------------------    
# Buttons for the Entire Form
#----------------------------

    # Action buttons
    button_frame = ttk.Frame(window)
    button_frame.pack(fill="x", pady=10)

    # Add Save and Cancel buttons to button_frame
    ttk.Button(button_frame, text="Save Changes", command=save_changes).pack(side="right", padx=5)
    ttk.Button(button_frame, text="Cancel Changes", command=cancel_changes).pack(side="right", padx=5)

    refresh_family_treeviews()
    # No modal behavior - allow both windows to remain open
    window.transient(window.master)