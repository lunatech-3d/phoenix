import sqlite3
import sys
import csv
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk, Image

# Connect to the database
connection = sqlite3.connect('phoenix.db')
cursor = connection.cursor()

# Function to close the form
def close_form():
    if messagebox.askquestion("Close Form", "Are you sure you want to close the form?") == "yes":
        window.destroy()
        load_records()

def open_address_management():
    subprocess.run(["python", "address_management.py"])

def export_data():
    # Connect to the database
    connection = sqlite3.connect('phoenix.db')
    cursor = connection.cursor()

    # Execute the query to retrieve all records from the People table
    cursor.execute("SELECT * FROM People")
    records = cursor.fetchall()

    # Prompt the user to select the destination and name of the CSV file
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if not file_path:
        print("Export canceled.")
        return

    # Open the selected file in write mode
    with open(file_path, 'w', newline='') as file:
        # Create a CSV writer object
        writer = csv.writer(file)

        # Write the header row
        writer.writerow([description[0] for description in cursor.description])

        # Write the data rows
        writer.writerows(records)

    # Close the database connection
    connection.close()

    # Print the number of records exported
    record_count = len(records)
    print(f"{record_count} records have been exported to {file_path}")
       

def populate_tree(records):
    tree.delete(*tree.get_children())  # Clear existing records in the tree

    for record in records:
        try:
            #person_id = record[0]  # Assuming the first column in the record is the person's ID
            person_id = record[0]  # ID
            first_name = record[1] if record[1] is not None else ""  # Replace None with empty string
            middle_name = record[2] if record[2] is not None else ""
            last_name = record[3] if record[3] is not None else ""
            title = record[4] if record[4] is not None else ""
            nick_name = record[5] if record[5] is not None else ""
            married_name = record[6] if record[6] is not None else ""
            married_to = record[7] if record[7] is not None else ""  # This might be different, adjust according to actual data
            father = record[8] if record[8] is not None else ""
            mother = record[9] if record[9] is not None else ""
            birth_date = record[10] if record[10] is not None else ""
            birth_location = record[11] if record[11] is not None else ""
            death_date = record[12] if record[12] is not None else ""
            death_location = record[13] if record[13] is not None else ""
            buried_link = record[26] if record[26] is not None else ""
            obit_link = record[22] if record[22] is not None else ""


            # Check for an image for the person
            cursor.execute("SELECT image_path FROM Photos WHERE person_id = ?", (person_id,))
            image_result = cursor.fetchone()
            image_symbol = '\U0001F4F7' if image_result else ""  # Camera symbol if image exists

            # Fetch the first spouse's ID for displaying in the Married To column
            cursor.execute("""
                SELECT CASE
                    WHEN person1_id = ? THEN person2_id
                    ELSE person1_id
                END AS spouse_id
                FROM Marriages
                WHERE person1_id = ? OR person2_id = ?
                LIMIT 1
            """, (person_id, person_id, person_id))
            spouse_result = cursor.fetchone()
            spouse_id_display = spouse_result[0] if spouse_result else ""

            # Construct the record for display. Adjust according to your treeview columns
            display_record = [image_symbol, person_id] + list(record[1:-1]) + [spouse_id_display]  # Adjust the slicing as needed

            # Insert the record into the treeview
            tree.insert("", tk.END, values=display_record)

        except Exception as e:
            print(f"Failed to insert record {record}: {e}")  # Error handling

        
def search_by_name():
    last_name = entry_last_name.get().strip()
    first_name = entry_first_name.get().strip()

    query = "SELECT * FROM People WHERE"
    parameters = []

    if last_name:
        query += " (last_name LIKE ? OR married_name LIKE ?)"
        parameters.append(f"{last_name}%")
        parameters.append(f"{last_name}%")

    if first_name:
        if parameters:
            query += " AND"
        query += " first_name LIKE ?"
        parameters.append(f"{first_name}%")

    if not parameters:  # No names entered
        messagebox.showinfo("No Input", "Please enter a first name, a last name, or both.")
        return

    display_records(query, parameters)


def clear_search_fields():
    entry_last_name.delete(0, tk.END)
    entry_first_name.delete(0, tk.END)
    entry_record_number.delete(0, tk.END) 

def search_by_record_number():
    record_number = entry_record_number.get().strip()
    try:
        record_number = int(record_number)

        # The new query and parameters for the search
        query = "SELECT * FROM People WHERE id = ?"
        parameters = [record_number] 

        cursor.execute(query, parameters)
        records = cursor.fetchall()

        #print("Query results:", records)  # Debugging line to check the fetched records

        if records:
            # Clear the treeview before populating with new records
            tree.delete(*tree.get_children())

            # Populate the tree with the fetched record
            populate_tree(records)
        else:
            print("No records found for the provided record number.")
            messagebox.showinfo("No Records", "No records found for the provided record number.")

    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid record number.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    
    # Clear input fields after search
    

# Function to create a tree based on the selected record
def build_a_tree():
    selected_item = tree.focus()
    if selected_item:
        record_id = tree.item(selected_item)['values'][1]
        subprocess.run(["python", "buildatree.py", str(record_id)])
    else:
        messagebox.showinfo("No One Selected", "Please select a record in the table.")

# Function to create a tree based on the selected record
def build_an_ancestor_tree():
    selected_item = tree.focus()
    if selected_item:
        record_id = tree.item(selected_item)['values'][1]
        subprocess.run(["python", "buildancestortree.py", str(record_id)])
    else:
        messagebox.showinfo("No One Selected", "Please select a record in the table.")


def view_busineses():
    # Run the showbusinesses.py script with the necessary arguments
        subprocess.run(["python", "showbusinesses.py"])

def view_residents():
    # Run the showresidents.py script with the necessary arguments
        subprocess.run(["python", "showresidents.py"])

def view_sources():
     # Run the sources.py script with the necessary arguments
        subprocess.run(["python", "sources.py"])

def view_addresses():
    # Run the viewtheaddresses.py script with the necessary arguments
        subprocess.run(["python", "viewtheaddresses.py"])

def view_mayors():
    # Run the showmayors.py script with the necessary arguments
        subprocess.run(["python", "showmayors.py"])

def view_doc_types():
    # Run the doctypesupport.py script
        subprocess.run(["python", "doctypesupport.py"])
def view_census_recs():
    # Run the showcensusrecs.py script
        subprocess.run(["python", "showcensusrecs.py"])

def view_orgs():
    # Run the orgs.py script
        subprocess.run(["python", "orgs.py"])

def view_members():
    # Run the members.py script
        subprocess.run(["python", "members.py"])


# Function to add a census record
def add_census_rec():
    selected_item = tree.focus()
    if selected_item:
        record_id = tree.item(selected_item)['values'][0]

        # Retrieve the information of the person from the database
        cursor.execute("SELECT first_name, middle_name, last_name, married_name FROM People WHERE id = ?", (record_id,))
        person_info = cursor.fetchone()

        if person_info is None:
            messagebox.showerror("Error", "Person information not found in the database.")
            return

        # Replace None with a suitable placeholder
        person_info = tuple("" if value is None else value for value in person_info)

        # Run the addcensus.py script with the necessary arguments
        subprocess.Popen(["python", "addcensus.py", str(record_id)] + list(person_info))

    else:
        messagebox.showinfo("No One Selected", "Please select someone from the table.")

# Function to open the FindAGrave Matching Interface
def open_findagrave_matching():
    subprocess.run(["python", "matchgraverecords.py"])

def open_edit_form(event):
    selected_item = tree.focus()
    # Get the column order of the clicked column
    clicked_column_order = int(tree.identify_column(event.x).replace("#", "")) - 1

    # Get the record
    record = tree.item(selected_item)['values']

    # Define a dictionary mapping column orders to their respective indexes in record
    column_orders = {
        1: 1,  # "ID"
        8: 8,  # "Married To"
        9: 9,  # "Father"
        10: 10  # "Mother"
    }

    # If clicked column is one of ["ID", "Married To", "Father", "Mother"], then use it to find the record_id
    if clicked_column_order in column_orders:
        record_id_index = column_orders[clicked_column_order]
        record_id = record[record_id_index]
    else:
        record_id = record[1]  # ID field value

    # Check if record_id is not empty
    if record_id:
        subprocess.Popen(["python", "editme.py", str(record_id)])
    else:
        messagebox.showinfo("No Record Found", "The record you're trying to access does not exist.")

column_name_mapping = {
    "ID" : "id",
    "First Name" : "first_name",
    "Middle Name" : "middle_name",
    "Last Name" : "last_name",
    "Title" : "title",
    "Nick Name" : "nick_name",
    "Married Name" : "married_name",
    "Married To" : "married_to",
    "Father" : "father",
    "Mother" : "mother",
    "Birth Date" : "birth_date",
    "Birth Location" : "birth_location",
    "Death Date" : "death_date",
    "Death Location" : "death_location",
    "Death Cause" : "death_cause",
    "Buried Date" : "buried_date",
    "Buried Location" : "buried_location",
    "Buried Notes" : "buried_notes",
    "Buried Source" : "buries_source",
    "Marriage Date" : "marriage_date",
    "Marriage Location" : "marriage_location",
    "Business" : "business",
    "Obit Link" :"obit_link",
    "Occupation" : "occupation"
}

# Global variables for current query and its parameters
current_query = "SELECT * FROM People"
current_parameters = []

def display_records(query, parameters=[]):
    global current_query
    global current_parameters
    global sort_order  # Add this line

    current_query = query
    current_parameters = parameters
    sort_order = {col: True for col in tree["columns"]}  # Reset the sort order

    cursor.execute(query, parameters)
    records = cursor.fetchall()
    #print("Fetched records:", records)  # Debugging line


    for row in tree.get_children():
        tree.delete(row)

    populate_tree(records)

def on_column_header_double_click(column):
    global current_sort_column
    global sort_order
    global current_query
    global current_parameters

    # Check if the column is already sorted in ascending order
    ascending = column == current_sort_column and sort_order[column]
    sort_order[column] = not ascending

    order = "ASC" if sort_order[column] else "DESC"

    # Use column_name_mapping to get the correct database column name
    if column in column_name_mapping:  # Check if the column exists in the mapping
        db_column_name = column_name_mapping[column]
    else:
        print(f"Column {column} not found in column_name_mapping.")
        return

    # Run the current query, but add an ORDER BY clause to sort the results
    sorted_query = current_query + f' ORDER BY "{db_column_name}" {order}'
    print(f"Sorted query: {sorted_query}")
    try:
        cursor.execute(sorted_query, current_parameters)
    except Exception as e:
        print(f"Failed to execute query: {e}")
        return
    records = cursor.fetchall()

    # Clear the existing records in the tree
    for row in tree.get_children():
        tree.delete(row)

    # Insert the sorted records into the tree
    populate_tree(records)

    # Store the current sort column and order
    current_sort_column = column

def delete_record():
    selected_item = tree.focus()
    if selected_item:
        record_id = tree.item(selected_item)['values'][1]
        
        # Check for ResHistory records
        cursor.execute("SELECT COUNT(*) FROM ResHistory WHERE person_id = ?", (record_id,))
        res_history_count = cursor.fetchone()[0]
        if res_history_count > 0:
            messagebox.showerror("Error", "Cannot delete this person because they are linked to residence history records. Please unlink the person from all residences first.")
            return

        # Check for existing marriage records
        cursor.execute("SELECT COUNT(*) FROM Marriages WHERE person1_id = ? OR person2_id = ?", (record_id, record_id))
        marriage_count = cursor.fetchone()[0]
        if marriage_count > 0:
            messagebox.showerror("Error", "Cannot delete this person because there are existing marriage records. Please delete the marriage records first.")
            return
        
        # Check if the person is listed as a father or mother
        cursor.execute("SELECT COUNT(*) FROM People WHERE father = ? OR mother = ?", (record_id, record_id))
        parent_count = cursor.fetchone()[0]
        if parent_count > 0:
            messagebox.showerror("Error", "Cannot delete this person because they are listed as a parent. Please update the relevant records first.")
            return
            
        
        # Confirm deletion
        if messagebox.askyesno("Confirmation", "Are you sure you want to delete this record?"):
            try:
                cursor.execute("DELETE FROM People WHERE id = ?", (record_id,))
                cursor.execute("DELETE FROM Photos WHERE person_id = ?", (record_id,))
                connection.commit()
                messagebox.showinfo("Success", "Record deleted successfully.")
                # Refresh the tree view
                display_records(current_query, current_parameters)
            except sqlite3.Error as e:
                messagebox.showerror("Error", str(e))
    else:
        messagebox.showinfo("No Record Selected", "Please select a record to delete.")

# Function to open the add form
def open_add_form():
    subprocess.Popen(["python", "addme.py"])


def open_business_management():
    subprocess.Popen(["python", "business.py"])

# Function to open the census form for the selected record
def open_census_window():
    selected_item = tree.focus()
    if selected_item:  # Check if a record is selected
        record_id = tree.item(selected_item)['values'][0]
        subprocess.Popen(["python", "censusform.py", str(record_id)])
    else:
        messagebox.showinfo("No One Selected", "Please select a record in the table.")

# Create the GUI window
window = tk.Tk()
window.title("The Plymouth Journal DB")

# Set the window size and position
window_width = 1400
window_height = 800
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Create a navigation menu
menu = tk.Menu(window)
window.config(menu=menu)

# File Menu
file_menu = tk.Menu(menu, tearoff=False)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Sources Table", command=view_sources)
file_menu.add_command(label="Address Table", command=view_addresses)
file_menu.add_command(label="Business Management", command=open_business_management)
file_menu.add_command(label="Resident Table", command=view_residents)
file_menu.add_command(label="Doc Type Table", command=view_doc_types)
file_menu.add_command(label="Census Record Table", command=view_census_recs)
file_menu.add_command(label="Export",command=export_data)
file_menu.add_command(label="Exit", command=close_form)

file_menu.add_command(label="Address Management", command=open_address_management)

# Groups Menu
groups_menu = tk.Menu(menu, tearoff=False)
menu.add_cascade(label="Groups", menu=groups_menu)
groups_menu.add_command(label="Mayor Table", command=view_mayors)
groups_menu.add_command(label="Organization Table", command=view_orgs)
groups_menu.add_command(label="Org Members Table", command=view_members)

# Tools Menu
tools_menu = tk.Menu(menu, tearoff=False)
menu.add_cascade(label="Tools", menu=tools_menu)
tools_menu.add_command(label="FindAGrave Matching", command=open_findagrave_matching)


# Create a frame for the title
frame_title = ttk.Frame(window)
frame_title.pack(pady=20)

# Title label
label_title = ttk.Label(frame_title, text="The Phoenix DB", font=("Helvetica", 20, "bold"))
label_title.pack()

# ----------------------------
# Search Control Functionality
# ----------------------------

# Create a frame for the search controls
frame_search = ttk.Frame(window)
frame_search.pack(pady=10)

# Last Name entry
label_first_name = ttk.Label(frame_search, text="First Name:")
label_first_name.grid(row=0, column=0, padx=5, pady=5)
entry_first_name = ttk.Entry(frame_search)
entry_first_name.grid(row=0, column=1, padx=5, pady=5)

# Last Name entry
label_last_name = ttk.Label(frame_search, text="Last Name:")
label_last_name.grid(row=1, column=0, padx=5, pady=5)
entry_last_name = ttk.Entry(frame_search)
entry_last_name.grid(row=1, column=1, padx=5, pady=5)

#Bind the Return key to the Last Name entry field
entry_last_name.bind("<Return>", lambda event: search_by_name())

# Sort order radio buttons
#label_order = ttk.Label(frame_search, text="Order:")
#label_order.grid(row=2, column=0, padx=5, pady=5)
var_order = tk.IntVar(value=0)
#radio_asc = ttk.Radiobutton(frame_search, text="Ascending", variable=var_order, value=0)
#radio_asc.grid(row=2, column=1, padx=5, pady=5)
#radio_desc = ttk.Radiobutton(frame_search, text="Descending", variable=var_order, value=1)
#radio_desc.grid(row=2, column=2, padx=5, pady=5)

# Search by Name button
button_search_name = ttk.Button(frame_search, text="Search by Name", command=search_by_name)
button_search_name.grid(row=0, column=2, padx=5, pady=5)

#Clear Fields button
button_clear_fields = ttk.Button(frame_search, text="Reset", command=clear_search_fields)
button_clear_fields.grid(row=1, column=2, padx=5, pady=5)

# Record Number entry
label_record_number = ttk.Label(frame_search, text="Record Number:")
label_record_number.grid(row=3, column=0, padx=5, pady=5)
entry_record_number = ttk.Entry(frame_search)
entry_record_number.grid(row=3, column=1, padx=5, pady=5)

# Search by Record Number button
button_search_record_number = ttk.Button(frame_search, text="Search by Record Number", command=search_by_record_number)
button_search_record_number.grid(row=3, column=2, padx=5, pady=5)

# Create a frame for the buttons
frame_buttons = ttk.Frame(window)
frame_buttons.pack(pady=10)

# Add button
button_add = ttk.Button(frame_buttons, text="Add Person", command=open_add_form)
button_add.pack(side=tk.LEFT, padx=5)

# Delete button
button_delete = ttk.Button(frame_buttons, text="Delete Person", command=delete_record)
button_delete.pack(side=tk.LEFT, padx=5)

# Create a frame for the treeview
frame_tree = ttk.Frame(window)
frame_tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a horizontal scrollbar
x_scrollbar = ttk.Scrollbar(frame_tree, orient=tk.HORIZONTAL)

# Create a vertical scrollbar
y_scrollbar = ttk.Scrollbar(frame_tree)

# Create a treeview to display the records
tree = ttk.Treeview(frame_tree, xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set, show='headings')
tree["columns"] = (
    "Image","ID", "First Name", "Middle Name", "Last Name",
    "Title", "Nick Name", "Married Name", "Married To",
    "Father", "Mother", "Birth Date", "Birth Location",
    "Death Date", "Death Location", "Death Cause",
    "Buried Date", "Buried Location", "Buried Notes",
    "Buried Source", "Marriage Date", "Marriage Location",
    "Business", "Obit Link","Occupation"
)

# Global variables for column sorting
global current_sort_column
global sort_order
current_sort_column = ""  # No column is sorted initially
sort_order = {col: True for col in tree["columns"]}  # All columns are sorted in ascending order initially

tree.heading("#0", text="Image", anchor="w")
tree.column("#0", width=1, anchor="w", stretch=False)
tree.heading("Image", text="Image", anchor="w")
tree.column("Image", width=45, anchor="w", stretch=False)
tree.heading("ID", text="ID", anchor="w")
tree.column("ID", width=50, anchor="w", stretch=False)
tree.heading("First Name", text="First Name", anchor="w")
tree.column("First Name", width=100, anchor="w", stretch=False)
tree.heading("Middle Name", text="Middle", anchor="w")
tree.column("Middle Name", width=75, anchor="w", stretch=False)
tree.heading("Last Name", text="Last Name", anchor="w")
tree.column("Last Name", width=100, anchor="w", stretch=False)
tree.heading("Title", text="Title", anchor="w")
tree.column("Title", width=45, anchor="w", stretch=False)
tree.heading("Nick Name", text="Nickname", anchor="w")
tree.column("Nick Name", width=70, anchor="w", stretch=False)
tree.heading("Married Name", text="Married Name", anchor="w")
tree.column("Married Name", width=100, anchor="w", stretch=False)
tree.heading("Married To", text="Spouse #", anchor="w")
tree.column("Married To", width=55, anchor="w", stretch=False)
tree.heading("Father", text="Dad #", anchor="w")
tree.column("Father", width=40, anchor="w", stretch=False)
tree.heading("Mother", text="Mom #", anchor="w")
tree.column("Mother", width=40, anchor="w", stretch=False)
tree.heading("Birth Date", text="Birth Date", anchor="w")
tree.column("Birth Date", width=75, anchor="w", stretch=False)
tree.heading("Birth Location", text="Birth Location", anchor="w")
tree.column("Birth Location", width=100, anchor="w", stretch=False)
tree.heading("Death Date", text="Death Date", anchor="w")
tree.column("Death Date", width=75, anchor="w", stretch=False)
tree.heading("Death Location", text="Death Location", anchor="w")
tree.column("Death Location", width=100, anchor="w", stretch=False)
tree.heading("Death Cause", text="Death Cause", anchor="w")
tree.column("Death Cause", width=100, anchor="w", stretch=False)
tree.heading("Buried Date", text="Buried Date", anchor="w")
tree.column("Buried Date", width=65, anchor="w", stretch=False)
tree.heading("Buried Location", text="Buried Location", anchor="w")
tree.column("Buried Location", width=100, anchor="w", stretch=False)
tree.heading("Buried Notes", text="Buried Notes", anchor="w")
tree.column("Buried Notes", width=100, anchor="w", stretch=False)
tree.heading("Buried Source", text="Buried Source", anchor="w")
tree.column("Buried Source", width=100, anchor="w", stretch=False)
tree.heading("Marriage Date", text="Marriage Date", anchor="w")
tree.column("Marriage Date", width=65, anchor="w", stretch=False)
tree.heading("Marriage Location", text="Marriage Location", anchor="w")
tree.column("Marriage Location", width=100, anchor="w", stretch=False)
tree.heading("Business", text="Business", anchor="w")
tree.column("Business", width=100, anchor="w", stretch=False)
tree.heading("Obit Link", text="Obit Link", anchor="w")
tree.column("Obit Link", width=100, anchor="w", stretch=False)
tree.heading("Occupation", text="Occupation", anchor="w")
tree.column("Occupation", width=100, anchor="w", stretch=False)

# Set remaining columns to a width of 200
for column in tree["columns"][13:]:
    tree.heading(column, text=column, anchor="w")
#    tree.column(column, width=200, anchor="w", stretch=False)

# Assign the on_column_header_double_click() function to the column headers
    for col in tree["columns"]:
        tree.heading(col, text=col, command=lambda _col=col: on_column_header_double_click(_col))

tree.pack(fill=tk.BOTH, expand=True)

# Retrieve all records from the People table
cursor.execute(f"SELECT * FROM People")

records = cursor.fetchall()

# Insert the records into the treeview for the first time
populate_tree(records)

# Create a frame for the buttons
frame_buttons = ttk.Frame(window)
frame_buttons.pack(pady=10)

# Create a button to build a tree
button_build_a_tree = ttk.Button(frame_buttons, text="Build a Descendent Tree", command=build_a_tree)
button_build_a_tree.pack(side=tk.LEFT, padx=5)

# Create a button to build an ancestor tree
button_build_a_tree = ttk.Button(frame_buttons, text="Build an Ancestor Tree", command=build_an_ancestor_tree)
button_build_a_tree.pack(side=tk.LEFT, padx=5)


#button_review = ttk.Button(frame_buttons, text="Select for Review", command=select_records_for_review)
#button_review.pack(side=tk.LEFT, padx=5)

#Create a button to add a census record
#button_add_census_rec = ttk.Button(frame_buttons, text="Add a Census Rec", command=add_census_rec)
#button_add_census_rec.pack(side=tk.LEFT, padx=5)

# Bind double-click event to open_edit_form function
tree.bind("<Double-1>", open_edit_form)

# Configure the scrollbars
x_scrollbar.config(command=tree.xview)
x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
y_scrollbar.config(command=tree.yview)
y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Run the GUI event loop
window.mainloop()

# Close the connection
connection.close()
