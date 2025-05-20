import sqlite3
import sys
import subprocess
import tkinter as tk
import re
from datetime import datetime
from tkinter import ttk, messagebox

# Connect to the database
connection = sqlite3.connect('Phoenix.db')
cursor = connection.cursor()

def load_organizations_dropdown():
    try:
        cursor.execute("SELECT org_id, org_name FROM Org")
        organizations = cursor.fetchall()
        return organizations
    except sqlite3.Error as e:
        print("Error loading organizations for dropdown:", e)
        return []

# Setup the GUI

def edit_membership_window(membership_id):
    if not membership_id:
        messagebox.showerror("Error", "No membership selected.")
        return

    print(f"Editing membership with ID: {membership_id}")

    edit_window = tk.Tk()
    edit_window.title("Edit Membership")
    edit_window.geometry("400x400")

    try:
        cursor.execute("""
            SELECT People.id, People.first_name || ' ' || People.last_name, Membership.role, Membership.start_date, Membership.end_date, Membership.org_id, Membership.notes
            FROM Membership
            JOIN People ON Membership.person_id = People.id
            WHERE Membership.id=?
        """, (membership_id,))
        membership_details = cursor.fetchone()

        if membership_details:
            person_id, person_name, role, start_date, end_date, org_id, notes = membership_details

            # Display person's name (non-editable)
            label_person = ttk.Label(edit_window, text="Person:")
            label_person.grid(row=0, column=0, padx=5, pady=5, sticky="e")
            person_name_label = ttk.Label(edit_window, text=person_name)
            person_name_label.grid(row=0, column=1, padx=5, pady=5)

            # Org dropdown
            ttk.Label(edit_window, text="Organization:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            orgs = load_organizations_dropdown()
            org_var = tk.StringVar()
            org_dropdown = ttk.Combobox(edit_window, textvariable=org_var, state="readonly", width=40)
            org_dropdown['values'] = [f"{org[0]} - {org[1]}" for org in orgs]
            for item in org_dropdown['values']:
                if item.startswith(f"{org_id} - "):
                    org_var.set(item)
                    break
            org_dropdown.grid(row=1, column=1, padx=5, pady=5)

            # Role Entry
            label_role = ttk.Label(edit_window, text="Role:")
            label_role.grid(row=2, column=0, padx=5, pady=5, sticky="e")
            entry_role = ttk.Entry(edit_window)
            entry_role.insert(0, role or "")
            entry_role.grid(row=2, column=1, padx=5, pady=5)

            # Start Date Entry
            label_start_date = ttk.Label(edit_window, text="Start Date:")
            label_start_date.grid(row=3, column=0, padx=5, pady=5, sticky="e")
            entry_start_date = ttk.Entry(edit_window)
            entry_start_date.insert(0, start_date or "")
            entry_start_date.grid(row=3, column=1, padx=5, pady=5)

            # End Date Entry
            label_end_date = ttk.Label(edit_window, text="End Date:")
            label_end_date.grid(row=4, column=0, padx=5, pady=5, sticky="e")
            entry_end_date = ttk.Entry(edit_window)
            entry_end_date.insert(0, end_date or "")
            entry_end_date.grid(row=4, column=1, padx=5, pady=5)

            # Notes Entry
            label_notes = ttk.Label(edit_window, text="Notes:")
            label_notes.grid(row=5, column=0, padx=5, pady=5, sticky="ne")
            entry_notes = tk.Text(edit_window, width=30, height=4)
            entry_notes.insert("1.0", notes or "")
            entry_notes.grid(row=5, column=1, padx=5, pady=5)

            # Function to update membership
            def update_membership():
                new_role = entry_role.get().strip()
                new_start_date = entry_start_date.get().strip()
                new_end_date = entry_end_date.get().strip()
                new_notes = entry_notes.get("1.0", "end").strip()
                new_org_id = int(org_var.get().split(" - ")[0]) if org_var.get() else org_id

                if not (new_start_date or new_end_date):
                    messagebox.showerror("Error", "Please provide at least a start date or an end date.")
                    return

                try:
                    cursor.execute("""
                        UPDATE Membership
                        SET org_id = ?, role = ?, start_date = ?, end_date = ?, notes = ?
                        WHERE id = ?
                    """, (new_org_id, new_role, new_start_date, new_end_date, new_notes, membership_id))
                    connection.commit()
                    messagebox.showinfo("Success", "Membership updated successfully.")
                    load_memberships(new_org_id)
                    edit_window.destroy()
                except sqlite3.Error as e:
                    print("Error updating membership:", e)
                    messagebox.showerror("Error", "Failed to update membership.")

            # Button to update membership
            button_update_member = ttk.Button(edit_window, text="Update Membership", command=update_membership)
            button_update_member.grid(row=6, column=1, padx=5, pady=10, sticky="e")

        else:
            messagebox.showerror("Error", "Failed to load membership details.")
            edit_window.destroy()

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Database error: {e}")
        edit_window.destroy()

    edit_window.mainloop()

def add_membership_for_known_person(person_id):
    # Create a simple form window
    form_window = tk.Toplevel(root)
    form_window.title("Add Group Membership")
    form_window.geometry("500x400")

    # Ensure the window is brought to front and captures focus
    form_window.grab_set()
    form_window.focus_force()
    form_window.lift()

    # Get person details
    cursor.execute("SELECT first_name, middle_name, last_name FROM People WHERE id = ?", (person_id,))
    person = cursor.fetchone()
    if not person:
        messagebox.showerror("Error", f"No person found with ID {person_id}")
        form_window.destroy()
        return

    full_name = " ".join(filter(None, person))

    # --- Person Info (read-only) ---
    ttk.Label(form_window, text=f"Person: {full_name} (ID: {person_id})", font=("Arial", 12, "bold")).pack(pady=10)

    # --- Organization Dropdown ---
    ttk.Label(form_window, text="Organization:").pack(pady=(10, 2))
    orgs = load_organizations_dropdown()
    org_var = tk.StringVar()
    org_dropdown = ttk.Combobox(form_window, textvariable=org_var, state="readonly", width=50)
    org_dropdown['values'] = [f"{org[0]} - {org[1]}" for org in orgs]
    org_dropdown.pack()

    # --- Role Entry ---
    ttk.Label(form_window, text="Role (optional):").pack(pady=(10, 2))
    role_entry = ttk.Entry(form_window, width=50)
    role_entry.pack()

    # --- Start Date ---
    ttk.Label(form_window, text="Start Date (e.g., 1901 or 01-01-1901):").pack(pady=(10, 2))
    start_entry = ttk.Entry(form_window, width=20)
    start_entry.pack()

    # --- End Date ---
    ttk.Label(form_window, text="End Date (optional):").pack(pady=(10, 2))
    end_entry = ttk.Entry(form_window, width=20)
    end_entry.pack()

    # --- Save Button ---
    def save_membership():
        selected_org = org_var.get()
        if not selected_org:
            messagebox.showerror("Missing Info", "Please select an organization.")
            return

        org_id = int(selected_org.split(" - ")[0])
        role = role_entry.get().strip()
        start_date = start_entry.get().strip()
        end_date = end_entry.get().strip()

        try:
            cursor.execute("""
                INSERT INTO Membership (person_id, org_id, role, start_date, end_date)
                VALUES (?, ?, ?, ?, ?)
            """, (person_id, org_id, role or None, start_date or None, end_date or None))
            connection.commit()
            messagebox.showinfo("Success", f"Membership added for {full_name}")
            form_window.destroy()
            root.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save membership: {e}")

    button_frame = ttk.Frame(form_window)
    button_frame.pack(pady=20)

    def cancel_membership():
        form_window.destroy()
        root.quit()

    ttk.Button(button_frame, text="Save Membership", command=save_membership).pack(side="left", padx=10)
    ttk.Button(button_frame, text="Cancel", command=cancel_membership).pack(side="left", padx=10)


# Handle edit mode if --edit-membership is passed
if "--edit-membership" in sys.argv:
    try:
        idx = sys.argv.index("--edit-membership") + 1
        membership_id = int(sys.argv[idx])
        edit_membership_window(membership_id)
        sys.exit()
    except (IndexError, ValueError):
        print("Invalid or missing membership ID after --edit-membership")
        sys.exit(1)

# Handle add mode if --for-person is passed
elif "--for-person" in sys.argv:
    try:
        person_index = sys.argv.index("--for-person") + 1
        person_id = int(sys.argv[person_index])
        print(f"[members.py] --for-person detected. Opening form for person_id={person_id}")

        root = tk.Tk()
        root.withdraw()  # Hides the main window, but keeps Tk alive
        add_membership_for_known_person(person_id)

        root.mainloop()
        sys.exit()
    except (IndexError, ValueError):
        print("Invalid or missing person ID after --for-person")
        sys.exit(1)

# Default: Run full Membership Management UI
else:
    root = tk.Tk()
    root.title("Membership Management System")
    root.geometry("1200x600")  # Adjust size as needed

# Capture person_id if passed as command-line argument
initial_person_id = None
if len(sys.argv) > 1:
    try:
        initial_person_id = int(sys.argv[1])
    except ValueError:
        initial_person_id = None

def on_org_select(event):
    org_id = org_dropdown.get().split(' - ')[0]  # Assuming the format is "id - name"
    load_memberships(org_id)

# Function to load organizations from the database and populate the dropdown

def load_memberships(org_id=None):
    member_treeview.delete(*member_treeview.get_children())  # Clear existing items
    if org_id:
        query = """
            SELECT Membership.id, People.id, People.first_name, People.middle_name, People.last_name, People.title, People.nick_name, People.married_name, Membership.role, Membership.start_date, Membership.end_date
            FROM Membership JOIN People ON Membership.person_id = People.id
            WHERE Membership.org_id = ?
        """
        cursor.execute(query, (org_id,))
        for member in cursor.fetchall():
            membership_id = member[0]  # This is the membership ID used as iid
            person_details = member[1:]  # Exclude membership ID from the details
            formatted_member = tuple("" if value is None else value for value in person_details)
            member_treeview.insert("", "end", iid=membership_id, values=formatted_member)  # Insert with Membership ID as the internal ID

# Dropdown for selecting organizations
org_var = tk.StringVar()
org_dropdown = ttk.Combobox(root, textvariable=org_var, state="readonly")
org_dropdown.pack(pady=10, padx=10, fill="x")
org_dropdown.bind("<<ComboboxSelected>>", on_org_select)

# Adding search functionality specific to members
search_frame = ttk.Frame(root)
search_frame.pack(fill="x", padx=10, pady=5)

# First line: First name input and Search button
tk.Label(search_frame, text="First Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
first_name_entry = ttk.Entry(search_frame)
first_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
search_button = ttk.Button(search_frame, text="Search", command=lambda: search_members(org_var.get().split(' - ')[0], first_name_entry.get(), last_name_entry.get()))
search_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")

# Second line: Last name input and Reset button
tk.Label(search_frame, text="Last Name:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
last_name_entry = ttk.Entry(search_frame)
last_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
reset_button = ttk.Button(search_frame, text="Reset", command=lambda: reset_search_fields(first_name_entry, last_name_entry))
reset_button.grid(row=1, column=2, padx=5, pady=5, sticky="w")

def reset_search_fields(first_name_entry, last_name_entry):
    # Clear the text fields
    first_name_entry.delete(0, tk.END)
    last_name_entry.delete(0, tk.END)
    # Optionally reload the tree or reset any other state as necessary
    load_memberships(org_var.get().split(' - ')[0])

def on_double_click(event):
    # Identify the item and region clicked
    region = member_treeview.identify("region", event.x, event.y)
    column = member_treeview.identify_column(event.x)
    selected_item = member_treeview.focus()

    if region == "cell" and selected_item:
        # Use the selected_item as membership_id since it is set as the iid
        membership_id = selected_item

        # Check if the ID column was double-clicked
        if column == "#1":  # Assuming ID is the first column and it is People ID
            person_id = member_treeview.item(selected_item, 'values')[0]  # Fetch the People ID
            # Ask user if they want to edit the person's record
            response = messagebox.askyesno("Edit Person", "Do you want to move to this person's record?")
            if response:
                # Close current window and open the edit person script
                root.destroy()  # Closes the main window, adjust as needed if multiple windows are open
                subprocess.run(["python", "editme.py", str(person_id)])
        else:
            # Handle other columns double-click for editing membership
            edit_membership_window(membership_id)

def on_member_select(event):
    selected = member_treeview.selection()
    
    if selected:
        membership_id = selected[0]  # The iid should be the membership ID
        print(f"Selected membership with ID: {membership_id}")
        sys.stdout.flush()
    
    state = "normal" if selected else "disabled"
    button_edit_member.config(state=state)
    button_delete_member.config(state=state)

def search_members(org_id, first_name, last_name):
    # Clear the existing items
    member_treeview.delete(*member_treeview.get_children())

    # Base query to fetch membership details
    query = """
        SELECT Membership.id, People.id, People.first_name, People.middle_name, People.last_name, People.title, People.nick_name, People.married_name, Membership.role, Membership.start_date, Membership.end_date
        FROM Membership
        JOIN People ON Membership.person_id = People.id
        WHERE Membership.org_id = ?
    """

    # Dynamic list of parameters starting with org_id
    parameters = [org_id]

    # If first name is not empty, append condition and parameter
    if first_name:
        query += " AND People.first_name LIKE ?"
        parameters.append(f'%{first_name}%')

    # If last name is not empty, append condition and parameter
    if last_name:
        query += " AND People.last_name LIKE ?"
        parameters.append(f'%{last_name}%')

    # Execute the query with the dynamic list of parameters
    cursor.execute(query, parameters)

    # Populate the treeview with results
    for member in cursor.fetchall():
        formatted_member = tuple("" if value is None else value for value in member[1:])  # Exclude membership ID
        member_treeview.insert("", "end", iid=member[0], values=formatted_member)

    # Rebind events to ensure proper handling after search results are loaded
    member_treeview.bind("<Double-1>", on_double_click)
    member_treeview.bind("<<TreeviewSelect>>", on_member_select)

# Frame for membership list
frame_member_list = ttk.LabelFrame(root, text="Membership List")
frame_member_list.pack(fill="both", expand=True, padx=10, pady=10)

# Treeview for memberships (excluding Membership ID)
member_treeview = ttk.Treeview(frame_member_list, columns=("ID", "First Name", "Middle Name", "Last Name", "Title", "Nickname", "Married Name", "Role", "Start Date", "End Date"), show='headings')
member_treeview.column("ID", width=50, anchor="w")
member_treeview.column("First Name", width=100, anchor="w")
member_treeview.column("Middle Name", width=100, anchor="w")
member_treeview.column("Last Name", width=100, anchor="w")
member_treeview.column("Title", width=45, anchor="w")
member_treeview.column("Nickname", width=70, anchor="w")
member_treeview.column("Married Name", width=100, anchor="w")
member_treeview.column("Role", width=100, anchor="w")
member_treeview.column("Start Date", width=75, anchor="w")
member_treeview.column("End Date", width=75, anchor="w")

# Configuring headings and sort function
for col in ("ID", "First Name", "Middle Name", "Last Name", "Title", "Nickname", "Married Name", "Role", "Start Date", "End Date"):
    member_treeview.heading(col, text=col, command=lambda c=col: treeview_sort_column(member_treeview, c, False))

member_treeview.pack(fill="both", expand=True)
member_treeview.bind("<Double-1>", on_double_click)
member_treeview.bind("<<TreeviewSelect>>", on_member_select)

def treeview_sort_column(tv, col, reverse):
    def parse_date(date_str):
        date_formats = [
            "%m-%d-%Y", "%m-%d-%y",
            "%Y", "%y",
            "%b-%Y", "%b-%y",
            "%B-%Y", "%B-%y"
        ]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # If no format matched, return the original string for default string comparison
        return date_str

    l = [(parse_date(tv.set(k, col)), k) for k in tv.get_children('')]
    l.sort(reverse=reverse, key=lambda x: (x[0] is None, x[0]))  # Sort by parsed date

    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))

# Update the columns setup to use the enhanced sort function
for col in ("ID", "First Name", "Middle Name", "Last Name", "Title", "Nickname", "Married Name", "Role", "Start Date", "End Date"):
    if col in ("Start Date", "End Date"):
        member_treeview.heading(col, text=col, command=lambda c=col: treeview_sort_column(member_treeview, c, False))
    else:
        member_treeview.heading(col, text=col, command=lambda c=col: treeview_sort_column(member_treeview, c, False))

member_treeview.pack(fill="both", expand=True)
scrollbar = ttk.Scrollbar(frame_member_list, orient="vertical", command=member_treeview.yview)
scrollbar.pack(side="right", fill="y")
member_treeview.configure(yscrollcommand=scrollbar.set)

def add_membership_window(prefill_person_id=None):
    add_window = tk.Toplevel(root)
    add_window.title("Add A New Member")
    add_window.geometry("800x600")  # Adjust size as needed

    # Frame for search
    search_frame = ttk.Frame(add_window)
    search_frame.pack(padx=10, pady=5, fill="x")

    # Search box for first name
    first_name_label = ttk.Label(search_frame, text="First Name:")
    first_name_label.grid(row=0, column=0, padx=5, pady=5)
    first_name_entry = ttk.Entry(search_frame)
    first_name_entry.grid(row=0, column=1, padx=5, pady=5)

    # Search box for last name
    last_name_label = ttk.Label(search_frame, text="Last Name:")
    last_name_label.grid(row=1, column=0, padx=5, pady=5)
    last_name_entry = ttk.Entry(search_frame)
    last_name_entry.grid(row=1, column=1, padx=5, pady=5)

    # Button to trigger search
    search_button = ttk.Button(search_frame, text="Search", command=lambda: search_for_people(first_name_entry.get(), last_name_entry.get(), person_tree))
    search_button.grid(row=0, column=2, rowspan=2, padx=5, pady=5)

    # Button to reset search fields
    reset_button = ttk.Button(search_frame, text="Reset", command=lambda: reset_search(first_name_entry, last_name_entry, person_tree))
    reset_button.grid(row=0, column=3, rowspan=2, padx=5, pady=5)

    # Treeview frame
    treeview_frame = ttk.Frame(add_window)
    treeview_frame.pack(padx=10, pady=10, fill="both", expand=True)

    # Treeview for displaying search results
    person_tree = ttk.Treeview(treeview_frame, columns=("ID", "First Name", "Middle Name", "Last Name", "Title", "Nickname", "Married Name", "Birth Date", "Death Date"), show='headings')
    for col in ["ID", "First Name", "Middle Name", "Last Name", "Title", "Nickname", "Married Name", "Birth Date", "Death Date"]:
        person_tree.heading(col, text=col)
        person_tree.column(col, anchor="center")

    # Customize column widths based on your preference
    person_tree.column("ID", width=50)
    person_tree.column("First Name", width=100)
    person_tree.column("Middle Name", width=75)
    person_tree.column("Last Name", width=100)
    person_tree.column("Title", width=45)
    person_tree.column("Nickname", width=70)
    person_tree.column("Married Name", width=100)
    person_tree.column("Birth Date", width=75)
    person_tree.column("Death Date", width=75)

    # Configuring headings and sort function
    for col in ("ID", "First Name", "Middle Name", "Last Name", "Title", "Nickname", "Married Name", "Birth Date", "Death Date"):
        person_tree.heading(col, text=col, command=lambda c=col: treeview_sort_column(person_tree, c, False))

    person_tree.pack(fill="both", expand=True)

    # Scrollbar for the treeview
    scrollbar = ttk.Scrollbar(treeview_frame, orient="vertical", command=person_tree.yview)
    person_tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Pre-fill person if ID is passed
    if prefill_person_id:
        cursor.execute("""
            SELECT id, first_name, middle_name, last_name, title, nick_name, married_name, birth_date, death_date
            FROM People WHERE id = ?
        """, (prefill_person_id,))
        result = cursor.fetchone()
        if result:
            person_tree.insert("", tk.END, iid=str(result[0]), values=result)
            person_tree.selection_set(str(result[0]))
            person_tree.focus(str(result[0]))

        # Disable search and reset fields
        first_name_entry.config(state="disabled")
        last_name_entry.config(state="disabled")
        search_button.config(state="disabled")
        reset_button.config(state="disabled")

    # Function to populate treeview with search results
    def search_for_people(first_name, last_name, person_tree):
        person_tree.delete(*person_tree.get_children())  # Clear existing entries in the treeview
        query = """
            SELECT id, first_name, middle_name, last_name, title, nick_name, married_name, birth_date, death_date
            FROM People
            WHERE first_name LIKE ? AND last_name LIKE ?
        """
        cursor.execute(query, (f'%{first_name}%', f'%{last_name}%'))
        people_records = cursor.fetchall()
        for record in people_records:
            person_tree.insert("", tk.END, values=record)

    # Function to reset search fields and treeview
    def reset_search(first_name_entry, last_name_entry, person_tree):
        first_name_entry.delete(0, tk.END)
        last_name_entry.delete(0, tk.END)
        person_tree.delete(*person_tree.get_children())  # Clear existing entries in the treeview

    # Input fields
    role_frame = ttk.Frame(add_window)
    role_frame.pack(padx=10, pady=5, fill="x")
    role_label = ttk.Label(role_frame, text="Role:")
    role_label.grid(row=0, column=0, padx=5, pady=5)
    role_entry = ttk.Entry(role_frame)
    role_entry.grid(row=0, column=1, padx=5, pady=5)

    start_date_frame = ttk.Frame(add_window)
    start_date_frame.pack(padx=10, pady=5, fill="x")
    start_date_label = ttk.Label(start_date_frame, text="Start Date:")
    start_date_label.grid(row=0, column=0, padx=5, pady=5)
    start_date_entry = ttk.Entry(start_date_frame)
    start_date_entry.grid(row=0, column=1, padx=5, pady=5)

    end_date_frame = ttk.Frame(add_window)
    end_date_frame.pack(padx=10, pady=5, fill="x")
    end_date_label = ttk.Label(end_date_frame, text="End Date:")
    end_date_label.grid(row=0, column=0, padx=5, pady=5)
    end_date_entry = ttk.Entry(end_date_frame)
    end_date_entry.grid(row=0, column=1, padx=5, pady=5)

    # Button to confirm adding membership
    add_member_button = ttk.Button(add_window, text="Add Member", command=lambda: add_membership(person_tree, role_entry, start_date_entry, end_date_entry))
    add_member_button.pack(pady=20)

    # Define the add_membership function inside add_membership_window
    def add_membership(person_tree, role_entry, start_date_entry, end_date_entry):
        selected = person_tree.selection()
        if selected:
            person_id = person_tree.item(selected[0], 'values')[0]  # Assuming ID is in the first column
            role = role_entry.get().strip()
            start_date = start_date_entry.get().strip()
            end_date = end_date_entry.get().strip()
            org_id = org_dropdown.get().split(' - ')[0]  # Assuming org ID is prefixed in the dropdown values

            if not (person_id and org_id):
                messagebox.showerror("Error", "Please fill out all required fields.")
                return

            try:
                cursor.execute("INSERT INTO Membership (person_id, org_id, role, start_date, end_date) VALUES (?, ?, ?, ?, ?)", 
                               (person_id, org_id, role, start_date, end_date))
                connection.commit()
                load_memberships(org_id)  # Refresh the list
                add_window.destroy()
            except sqlite3.Error as e:
                print("Error adding membership:", e)
                messagebox.showerror("Error", "Failed to add membership.")

def open_add_membership_window():
    # Check if an organization is selected
    if not org_var.get():  # Assuming org_var is the variable linked to the organization dropdown
        messagebox.showerror("Error", "Please select an organization before adding a member.")
        return
    add_membership_window(initial_person_id)  # Open the Add Membership window if an organization is selected

def populate_treeview(org_id=None, search_text=None):
    member_treeview.delete(*member_treeview.get_children())  # Clear existing items in the Treeview
    query = """
        SELECT Membership.id, People.id, People.first_name, People.middle_name, People.last_name, People.title, People.nick_name, People.married_name, Membership.role, Membership.start_date, Membership.end_date
        FROM Membership
        JOIN People ON Membership.person_id = People.id
        WHERE Membership.org_id = ?
    """
    parameters = [org_id]

    if search_text:
        query += " AND (People.first_name LIKE ? OR People.last_name LIKE ?)"
        parameters += [f'%{search_text}%', f'%{search_text}%']

    cursor.execute(query, parameters)
    for member in cursor.fetchall():
        member_treeview.insert("", "end", iid=member[0], values=member[1:])


def delete_membership():
    selected_items = member_treeview.selection()  # This returns a tuple of selected item 'iids'
    if not selected_items:
        messagebox.showerror("Error", "Please select a membership to delete.")
        return

    for selected_item in selected_items:
        membership_id = selected_item  # directly use the selected item id which is the 'iid' we set earlier

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this membership?"):
            try:
                cursor.execute("DELETE FROM Membership WHERE id=?", (membership_id,))
                connection.commit()
            except sqlite3.Error as e:
                print("Error deleting membership:", e)
                messagebox.showerror("Error", "Failed to delete membership.")

    # Refresh the list after deletion
    org_id = org_dropdown.get().split(' - ')[0]  # Extract org ID from the dropdown
    load_memberships(org_id)  # Refresh the list

# Function to update the state of the Delete button based on selection in the Treeview
def update_delete_button_state(event):
    selected = member_treeview.selection()
    if selected:
        button_delete_member.config(state="normal")
    else:
        button_delete_member.config(state="disabled")
    populate_treeview(org_id=selected_org_id)

def on_edit_button_click():
    selected_items = member_treeview.selection()
    if not selected_items:
        messagebox.showerror("Error", "Please select a membership to edit.")
        return
    # Directly use the selected item's iid, which should be the membership_id
    membership_id = selected_items[0]
    edit_membership_window(membership_id)

# Scrollbar for the Treeview
scrollbar = ttk.Scrollbar(frame_member_list, orient="vertical", command=member_treeview.yview)
scrollbar.pack(side="right", fill="y")
member_treeview.configure(yscrollcommand=scrollbar.set)

# Load organizations into the dropdown
organizations = load_organizations_dropdown()
org_dropdown['values'] = [f"{org[0]} - {org[1]}" for org in organizations]

if "--for-person" in sys.argv:
    try:
        person_id_index = sys.argv.index("--for-person") + 1
        target_id = int(sys.argv[person_id_index])
        add_membership_for_known_person(target_id)
        root.mainloop()  # Run only the simple form
        sys.exit()       # Prevent loading the main Membership Management interface
    except (IndexError, ValueError):
        print("Invalid or missing person ID after --for-person")
        sys.exit()


def edit_membership_window(membership_id):
    edit_window = tk.Tk()
    edit_window.title("Edit Membership")
    edit_window.geometry("500x400")

    # Get existing membership info
    cursor.execute("SELECT person_id, org_id, role, start_date, end_date FROM Membership WHERE membership_id = ?", (membership_id,))
    result = cursor.fetchone()
    if not result:
        messagebox.showerror("Error", f"No membership found with ID {membership_id}")
        edit_window.destroy()
        return

    person_id, org_id, role_val, start_val, end_val = result

    # Get person name
    cursor.execute("SELECT first_name, middle_name, last_name FROM People WHERE id = ?", (person_id,))
    person = cursor.fetchone()
    full_name = " ".join(filter(None, person)) if person else f"Person ID {person_id}"

    ttk.Label(edit_window, text=f"Editing Membership for {full_name}", font=("Arial", 12, "bold")).pack(pady=10)

    # Org dropdown
    ttk.Label(edit_window, text="Organization:").pack(pady=(10, 2))
    orgs = load_organizations_dropdown()
    org_var = tk.StringVar()
    org_dropdown = ttk.Combobox(edit_window, textvariable=org_var, state="readonly", width=50)
    org_dropdown['values'] = [f"{org[0]} - {org[1]}" for org in orgs]
    org_dropdown.pack()

    # Preselect the org
    for org in orgs:
        if org[0] == org_id:
            org_var.set(f"{org[0]} - {org[1]}")
            break

    # Role
    ttk.Label(edit_window, text="Role (optional):").pack(pady=(10, 2))
    role_entry = ttk.Entry(edit_window, width=50)
    role_entry.insert(0, role_val or "")
    role_entry.pack()

    # Start Date
    ttk.Label(edit_window, text="Start Date (e.g., 1901 or 01-01-1901):").pack(pady=(10, 2))
    start_entry = ttk.Entry(edit_window, width=20)
    start_entry.insert(0, start_val or "")
    start_entry.pack()

    # End Date
    ttk.Label(edit_window, text="End Date (optional):").pack(pady=(10, 2))
    end_entry = ttk.Entry(edit_window, width=20)
    end_entry.insert(0, end_val or "")
    end_entry.pack()

    def save_edits():
        selected_org = org_var.get()
        if not selected_org:
            messagebox.showerror("Missing Info", "Please select an organization.")
            return
        new_org_id = int(selected_org.split(" - ")[0])
        new_role = role_entry.get().strip()
        new_start = start_entry.get().strip()
        new_end = end_entry.get().strip()

        try:
            cursor.execute("""
                UPDATE Membership
                SET org_id = ?, role = ?, start_date = ?, end_date = ?
                WHERE membership_id = ?
            """, (new_org_id, new_role or None, new_start or None, new_end or None, membership_id))
            connection.commit()
            messagebox.showinfo("Success", "Membership updated successfully.")
            edit_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Could not update membership: {e}")

    ttk.Button(edit_window, text="Save Changes", command=save_edits).pack(pady=20)
    ttk.Button(edit_window, text="Cancel", command=edit_window.destroy).pack()

    edit_window.mainloop()


def handle_member_selection():
    selected_items = member_treeview.selection()
    if selected_items:
        membership_id = selected_items[0]  # Assuming the iid is the membership_id
        edit_membership_window(membership_id)

# Add, Edit, and Delete button setup in the main window
button_add_member = ttk.Button(root, text="Add Member", command=open_add_membership_window)
button_add_member.pack(pady=5)

button_edit_member = ttk.Button(root, text="Edit Member", command=handle_member_selection)
button_edit_member.pack(pady=5)

button_delete_member = ttk.Button(root, text="Delete Member", command=delete_membership, state="disabled")
button_delete_member.pack(pady=5)

member_treeview.bind("<<TreeviewSelect>>", on_member_select)

# Start the Tkinter event loop
root.mainloop()



if "--edit-membership" in sys.argv:
    try:
        idx = sys.argv.index("--edit-membership") + 1
        membership_id = int(sys.argv[idx])
        edit_membership_window(membership_id)
        sys.exit()
    except (IndexError, ValueError):
        print("Invalid or missing membership ID after --edit-membership")
        sys.exit(1)
