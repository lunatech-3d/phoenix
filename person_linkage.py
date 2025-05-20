# person_linkage.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

connection = sqlite3.connect('phoenix.db')
cursor = connection.cursor()


def person_search_popup(callback):
    def search():
        fname = fname_var.get().strip()
        mname = mname_var.get().strip()
        lname = lname_var.get().strip()

        query = """
        SELECT id, first_name, middle_name, last_name, married_name, birth_date, death_date
        FROM People
        WHERE 1=1
        """
        params = []
        if fname:
            query += " AND first_name LIKE ?"
            params.append(f"%{fname}%")
        if mname:
            query += " AND middle_name LIKE ?"
            params.append(f"%{mname}%")
        if lname:
            query += " AND (last_name LIKE ? OR married_name LIKE ?)"
            params.extend([f"%{lname}%", f"%{lname}%"])

        tree.delete(*tree.get_children())
        for row in cursor.execute(query, params):
            tree.insert("", "end", values=row)

    def select_person():
        selected = tree.selection()
        if selected:
            person_id = tree.item(selected[0])["values"][0]
            callback(person_id)
            popup.destroy()

    def cancel():
        popup.destroy()

    popup = tk.Toplevel()
    popup.title("Search for Person")

    fname_var = tk.StringVar()
    mname_var = tk.StringVar()
    lname_var = tk.StringVar()

    form = ttk.Frame(popup)
    form.pack(padx=10, pady=5, fill="x")

    ttk.Label(form, text="First Name:").grid(row=0, column=0, sticky="e")
    ttk.Entry(form, textvariable=fname_var, width=20).grid(row=0, column=1, padx=5)

    ttk.Label(form, text="Middle Name:").grid(row=0, column=2, sticky="e")
    ttk.Entry(form, textvariable=mname_var, width=20).grid(row=0, column=3, padx=5)

    ttk.Label(form, text="Last Name:").grid(row=0, column=4, sticky="e")
    ttk.Entry(form, textvariable=lname_var, width=20).grid(row=0, column=5, padx=5)

    ttk.Button(form, text="Search", command=search).grid(row=0, column=6, padx=10)
    ttk.Button(form, text="Cancel", command=cancel).grid(row=0, column=7)

    tree = ttk.Treeview(popup, columns=("ID", "First", "Middle", "Last", "Married", "Birth", "Death"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    tree.bind("<Double-1>", lambda e: select_person())
    ttk.Button(popup, text="Select", command=select_person).pack(pady=5)

    popup.grab_set()
    popup.focus_set()
    popup.wait_window()


def create_person_search_panel(parent, search_vars, on_search, on_reset):
    search_frame = ttk.Frame(parent)

    # First line: Name fields
    name_labels = ['first_name', 'middle_name', 'last_name']
    for idx, key in enumerate(name_labels):
        ttk.Label(search_frame, text=key.replace('_', ' ').title() + ":").grid(row=0, column=idx * 2, padx=5, pady=2, sticky='e')
        ttk.Entry(search_frame, textvariable=search_vars[key], width=20).grid(row=0, column=idx * 2 + 1, padx=5, pady=2)

    # Second line: Date fields
    date_labels = ['birth_date', 'death_date']
    for idx, key in enumerate(date_labels):
        ttk.Label(search_frame, text=key.replace('_', ' ').title() + ":").grid(row=1, column=idx * 2, padx=5, pady=2, sticky='e')
        ttk.Entry(search_frame, textvariable=search_vars[key], width=20).grid(row=1, column=idx * 2 + 1, padx=5, pady=2)

    # Third line: Buttons
    button_frame = ttk.Frame(search_frame)
    button_frame.grid(row=2, column=0, columnspan=6, pady=8, sticky='w')
    ttk.Button(button_frame, text="Search", command=on_search).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Reset", command=on_reset).pack(side="left", padx=5)

    return search_frame

def open_person_linkage_popup(parent_id, role="child", refresh_callback=None):
    window = tk.Toplevel()
    window.title(f"Add or Link {role.title()}")
    window.geometry("1000x600")

    search_vars = {
        'first_name': tk.StringVar(),
        'middle_name': tk.StringVar(),
        'last_name': tk.StringVar(),
        'birth_date': tk.StringVar(),
        'death_date': tk.StringVar()
    }

    # Setup frames
    search_frame = ttk.Frame(window)
    search_frame.pack(fill="x", padx=10, pady=10)

    tree_frame = ttk.Frame(window)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

    button_frame = ttk.Frame(window)
    button_frame.pack(fill="x", padx=10, pady=(0,10))

    # Setup search panel
    def apply_filters():
        refresh_tree(use_full_database=True)

    def reset_filters():
        for var in search_vars.values():
            var.set("")
        refresh_tree(use_full_database=False)

    search_panel = create_person_search_panel(search_frame, search_vars, apply_filters, reset_filters)
    search_panel.pack()

    # Treeview
    columns = ("id", "first_name", "middle_name", "last_name", "married_name", "birth_date", "death_date")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col.replace('_', ' ').title())
        tree.column(col, width=120)
    tree.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    sort_direction = {col: False for col in columns}
    def sort_column(col):
        direction = sort_direction[col]
        data = [(tree.set(k, col), k) for k in tree.get_children('')]
        data.sort(reverse=direction)
        for idx, (_, k) in enumerate(data):
            tree.move(k, '', idx)
        sort_direction[col] = not direction

    for col in columns:
        tree.heading(col, text=col.replace('_', ' ').title(), command=lambda c=col: sort_column(c))

    def refresh_tree(use_full_database=False):
        tree.delete(*tree.get_children())
        filters = {k: v.get().strip() for k, v in search_vars.items() if v.get().strip()}

        query = "SELECT id, first_name, middle_name, last_name, married_name, birth_date, death_date FROM People WHERE 1=1"
        params = []

        if not use_full_database:
            query += " AND (last_name = (SELECT last_name FROM People WHERE id = ?))"
            params.append(parent_id)

        for k, v in filters.items():
            if k == 'last_name':
                query += " AND (last_name LIKE ? OR married_name LIKE ?)"
                params.extend([f"%{v}%", f"%{v}%"])
            else:
                query += f" AND {k} LIKE ?"
                params.append(f"%{v}%")

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        def extract_year(date_str):
            try:
                return int(date_str.split("-")[0])
            except:
                return 9999

        # Sort results by birth year
        results.sort(key=lambda r: extract_year(r[5] or "9999"))

        for row in results:
            item = tree.insert('', 'end', values=row)
            if row[5] and row[5][:4] == str(datetime.now().year):
                tree.item(item, tags=('highlight',))

        tree.tag_configure('highlight', background='#e8f4fc')

    refresh_tree(use_full_database=False)

    def prompt_parent_role(parent_name, child_name):
        role_win = tk.Toplevel(window)
        role_win.title("Select Parent Role")
        role_var = tk.StringVar(value="father")
        confirmed = {'value': False}

        prompt_text = f"{parent_name} is the:"
        ttk.Label(role_win, text=prompt_text, font=("Arial", 12, "bold")).pack(padx=10, pady=(10, 5))

        ttk.Radiobutton(role_win, text=f"Father of {child_name}", variable=role_var, value="father").pack(anchor="w", padx=20)
        ttk.Radiobutton(role_win, text=f"Mother of {child_name}", variable=role_var, value="mother").pack(anchor="w", padx=20)

        button_frame = ttk.Frame(role_win)
        button_frame.pack(pady=10)

        def confirm():
            confirmed['value'] = True
            role_win.destroy()

        def cancel():
            confirmed['value'] = False
            role_win.destroy()

        ttk.Button(button_frame, text="Link Child", command=confirm).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side="right", padx=10)

        role_win.grab_set()
        role_win.wait_window()
        return role_var.get() if confirmed['value'] else None

    def link_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("No Selection", f"Please select a person to link as {role}.")
            return
        selected_values = tree.item(selected[0])['values']
        linked_id = selected_values[0]
        child_name = f"{selected_values[1]} {selected_values[2]} {selected_values[3]}".strip()

        # Get parent name for prompt
        cursor.execute("SELECT first_name, middle_name, last_name FROM People WHERE id = ?", (parent_id,))
        parent_record = cursor.fetchone()
        parent_name = " ".join(filter(None, parent_record)) if parent_record else "This person"

        if role == 'child':
            parent_role = prompt_parent_role(parent_name, child_name)
            if not parent_role:
                return  # User cancelled the dialog

            father = None
            mother = None

            if parent_role == 'father':
                father = parent_id
            elif parent_role == 'mother':
                mother = parent_id

            # Show confirmation of spouse selection before applying
            cursor.execute("SELECT p.id, p.first_name, p.middle_name, p.last_name FROM Marriages m JOIN People p ON (p.id = m.person1_id OR p.id = m.person2_id) WHERE (m.person1_id = ? OR m.person2_id = ?) AND p.id != ?", (parent_id, parent_id, parent_id))
            spouse = cursor.fetchone()

            spouse_name = " ".join(filter(None, spouse[1:])) if spouse else None

            if spouse:
                spouse_confirm = messagebox.askyesno("Confirm Spouse", f"Do you want to assign {spouse_name} as the other parent?")
                if spouse_confirm:
                    if not father and parent_role == 'mother':
                        father = spouse[0]
                    elif not mother and parent_role == 'father':
                        mother = spouse[0]

            # Confirm final assignment
            summary = (
                f"Linking child '{child_name}' to:\n\n"
                f"Father: {'(none)' if not father else 'ID ' + str(father)}\n"
                f"Mother: {'(none)' if not mother else 'ID ' + str(mother)}\n\n"
                f"Proceed?"
            )
            

            if not messagebox.askyesno("Confirm Link", summary):
                return

            cursor.execute("UPDATE People SET father = ?, mother = ? WHERE id = ?", (father, mother, linked_id))
        elif role == 'father':
            cursor.execute("UPDATE People SET father = ? WHERE id = ?", (linked_id, parent_id))
        elif role == 'mother':
            cursor.execute("UPDATE People SET mother = ? WHERE id = ?", (linked_id, parent_id))

        connection.commit()
        messagebox.showinfo("Linked", f"{role.title()} successfully linked.")
        refresh_tree(use_full_database=False)
        if refresh_callback:
            refresh_callback()
        window.destroy()

    def add_new():
        subprocess.Popen(["python", "editme.py", f"--new-{role}", str(parent_id)])
        window.destroy()

    ttk.Button(button_frame, text=f"Link Selected {role.title()}", command=link_selected).pack(side="left", padx=5)
    ttk.Button(button_frame, text=f"Add New {role.title()}", command=add_new).pack(side="right", padx=5)
