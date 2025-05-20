# editbiz.py
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sqlite3
import webbrowser
import urllib.parse
from datetime import datetime
from date_utils import parse_date_input, format_date_for_display, date_sort_key
from person_linkage import person_search_popup

DB_PATH = "phoenix.db"
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

class EditBusinessForm:
    def __init__(self, master, biz_id=None):
        self.master = master
        self.biz_id = biz_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.entries = {}

        self.master.title("Edit Business")
        self.setup_form()
        if biz_id:
            self.load_data()
            self.load_owners()
            self.load_locations()
            self.load_employees()
            self.load_bizevents()

    def setup_form(self):
        # Split fields into two columns starting from 'aliases'
        fields_column1 = [
            ("biz_name", "Business Name"),
            ("category", "Category"),
            ("start_date", "Start Date"),
            ("end_date", "End Date"),
            ("description", "Description")
        ]

        fields_column2 = [
            ("aliases", "Alternate Names"),
            ("image_path", "Image Path"),
            ("map_link", "Map Link"),
            ("external_url", "External URL")
        ]

        form_frame = ttk.LabelFrame(self.master, text="Business Details")
        form_frame.pack(fill="x", padx=10, pady=10)

        for idx, (field, label) in enumerate(fields_column1):
            ttk.Label(form_frame, text=label + ":").grid(row=idx, column=0, sticky="e", padx=5, pady=2)
            entry = ttk.Entry(form_frame, width=40)
            entry.grid(row=idx, column=1, sticky="w", padx=5, pady=2)
            self.entries[field] = entry

        for idx, (field, label) in enumerate(fields_column2):
            ttk.Label(form_frame, text=label + ":").grid(row=idx, column=2, sticky="e", padx=5, pady=2)
            entry = ttk.Entry(form_frame, width=40)
            entry.grid(row=idx, column=3, sticky="w", padx=5, pady=2)
            self.entries[field] = entry

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=max(len(fields_column1), len(fields_column2)), column=0, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)
        
        # Tree Section for Owners
        self.owner_frame = ttk.LabelFrame(self.master, text="Owners")
        self.owner_frame.pack(fill="both", expand=False, padx=10, pady=5)

        #Start of the Tree Sections
        # 1 - Setup of the Owner Tree Section
        self.owner_tree = ttk.Treeview(self.owner_frame, columns=("person_id", "name", "type", "start", "end", "notes"), show="headings", height=5)
        for col in self.owner_tree["columns"]:
            self.owner_tree.heading(col, text=col, command=lambda c=col: self.sort_owner_tree_by_column(c))
            if col == "person_id":
                self.owner_tree.column(col, width=0, stretch=False)  # Hide ID
            elif col == "name":
                self.owner_tree.column(col, width=180)
            elif col == "type":
                self.owner_tree.column(col, width=60)
            elif col in ("start", "end"):
                self.owner_tree.column(col, width=60)
            elif col == "notes":
                self.owner_tree.column(col, width=300)
            else:
                self.owner_tree.column(col, width=120)

        self.owner_tree.bind("<Double-1>", self.on_owner_double_click)
        self.owner_tree.pack(side="top", fill="x", expand=False, padx=5)

        owner_btns = ttk.Frame(self.owner_frame)
        owner_btns.pack(side="bottom", fill="x")
        ttk.Button(owner_btns, text="Add", command=self.add_owner).pack(side="left", padx=5)
        ttk.Button(owner_btns, text="Edit", command=self.edit_owner).pack(side="left", padx=5)
        ttk.Button(owner_btns, text="Delete", command=self.delete_owner).pack(side="left", padx=5)

        # 2- Setup of the Location Tree Section
        self.location_frame = ttk.LabelFrame(self.master, text="Locations")
        self.location_frame.pack(fill="both", expand=False, padx=10, pady=5)


        self.location_tree = ttk.Treeview(self.location_frame, columns=("address", "start", "end", "notes", "url"), show="headings", height=2)
        for col in self.location_tree["columns"]:
            self.location_tree.heading(col, text=col, command=lambda c=col: self.sort_location_tree_by_column(c))
            if col in ("start", "end"):
                self.location_tree.column(col, width=90)
            elif col == "address":
                self.location_tree.column(col, width=220)
            elif col == "url":
                self.location_tree.column(col, width=200)
            else:
                self.location_tree.column(col, width=180)
        self.location_tree.pack(side="top", fill="x", expand=False, padx=5)
        self.location_tree.bind("<Double-1>", self.on_location_double_click)


        location_btns = ttk.Frame(self.location_frame)
        location_btns.pack(side="bottom", fill="x")
        ttk.Button(location_btns, text="Add", command=self.add_location).pack(side="left", padx=5)
        ttk.Button(location_btns, text="Edit", command=self.edit_location).pack(side="left", padx=5)
        ttk.Button(location_btns, text="Delete", command=self.delete_location).pack(side="left", padx=5)

        # 3 - Setup of the Employee Tree Section
        self.employee_frame = ttk.LabelFrame(self.master, text="Employees")
        self.employee_frame.pack(fill="both", expand=False, padx=10, pady=5)

        self.employee_tree = ttk.Treeview(self.employee_frame, columns=("person_id", "name", "title", "start", "end", "notes"), show="headings", height=5)
        for col in self.employee_tree["columns"]:
            self.employee_tree.heading(col, text=col, command=lambda c=col: self.sort_employee_tree_by_column(c))
            if col == "person_id":
                self.employee_tree.column(col, width=0, stretch=False)  # Hide ID
            elif col == "name":
                self.employee_tree.column(col, width=180)
            elif col in ("start", "end"):
                self.employee_tree.column(col, width=90)
            elif col == "notes":
                self.employee_tree.column(col, width=240)
            else:
                self.employee_tree.column(col, width=120)

        
        self.employee_tree.pack(side="top", fill="x", expand=False, padx=5)
        self.employee_tree.bind("<Double-1>", self.on_employee_double_click)


        emp_btns = ttk.Frame(self.employee_frame)
        emp_btns.pack(side="bottom", fill="x")
        ttk.Button(emp_btns, text="Add", command=self.add_employee).pack(side="left", padx=5)
        ttk.Button(emp_btns, text="Edit", command=self.edit_employee).pack(side="left", padx=5)
        ttk.Button(emp_btns, text="Delete", command=self.delete_employee).pack(side="left", padx=5)

        # 4 - Setup of the Business Events Section
        self.bizevents_frame = ttk.LabelFrame(self.master, text="Business Events")
        self.bizevents_frame.pack(fill="both", expand=False, padx=10, pady=5)

        self.bizevents_tree = ttk.Treeview(self.bizevents_frame, columns=("event_id", "event_type", "date_range", "person", "description", "link_url"), show="headings", height=5)
        
        self.bizevents_tree.column("event_id", width=0, stretch=False)  # Hidden ID
        self.bizevents_tree.heading("event_type", text="Event Type")
        self.bizevents_tree.column("event_type", width=120)
        self.bizevents_tree.heading("date_range", text="Date(s)")
        self.bizevents_tree.column("date_range", width=120)
        self.bizevents_tree.heading("person", text="Person")
        self.bizevents_tree.column("person", width=200)
        self.bizevents_tree.heading("description", text="Description")
        self.bizevents_tree.column("description", width=300)
        self.bizevents_tree.heading("link_url", text="Link")
        self.bizevents_tree.column("link_url", width=200)
        for col in self.bizevents_tree["columns"]:
            self.bizevents_tree.heading(col, text=col, command=lambda c=col: self.sort_bizevents_tree_by_column(c))
        
        self.bizevents_tree.pack(side="top", fill="x", expand=False, padx=5)
        self.bizevents_tree.bind("<Double-1>", self.on_bizevent_double_click)


        bizevents_btns = ttk.Frame(self.bizevents_frame)
        bizevents_btns.pack(side="bottom", fill="x")
        ttk.Button(bizevents_btns, text="Add", command=self.add_bizevent).pack(side="left", padx=5)
        ttk.Button(bizevents_btns, text="Edit", command=self.edit_bizevent).pack(side="left", padx=5)
        ttk.Button(bizevents_btns, text="Delete", command=self.delete_bizevent).pack(side="left", padx=5)
  
    #
    #Support Functions for #1 - Owner Tree
    #
    
    def load_owners(self):
        self.owner_tree.delete(*self.owner_tree.get_children())
        self.cursor.execute("""
            SELECT o.person_id,
                   CASE 
                       WHEN p.married_name IS NOT NULL AND p.married_name != ''
                       THEN p.first_name || ' ' || IFNULL(p.middle_name, '') || ' (' || p.last_name || ') ' || p.married_name
                       ELSE p.first_name || ' ' || IFNULL(p.middle_name || ' ', '') || p.last_name
                   END AS full_name,
                   o.ownership_type, o.start_date, o.end_date, o.notes
            FROM BizOwnership o
            JOIN People p ON o.person_id = p.id
            WHERE o.biz_id = ?
        """, (self.biz_id,))

        rows = self.cursor.fetchall()
        sorted_rows = sorted(rows, key=lambda r: date_sort_key(r[3]))

        for row in sorted_rows:
            person_id, name, otype, start, end, notes = row
            start_display = format_date_for_display(start, "EXACT") if start else ""
            end_display = format_date_for_display(end, "EXACT") if end else ""
            self.owner_tree.insert('', 'end', values=(person_id, name, otype, start_display, end_display, notes))

    def add_owner(self):
        self.open_owner_editor()

    def edit_owner(self):
        selected = self.owner_tree.selection()
        if not selected:
            return
        values = self.owner_tree.item(selected[0])['values']
        self.open_owner_editor(existing=values)

    def open_owner_editor(self, existing=None):
        self.owner_win = tk.Toplevel(self.master)
        self.owner_win.title("Edit Owner" if existing else "Add Owner")

        self.owner_entries = {}
        self.owner_existing = existing

        # --- Person selection only through Lookup ---
        ttk.Label(self.owner_win, text="Selected Person:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        person_frame = ttk.Frame(self.owner_win)
        person_frame.grid(row=0, column=1, padx=5, pady=3, sticky="w")

        person_display = ttk.Label(person_frame, text="(none)", width=50, anchor="w", relief="sunken")
        person_display.pack(side="left", padx=(0, 5))
        self.owner_entries["Selected Person"] = person_display
        self.owner_entries["Person ID"] = None  # Internal, not user-editable

        def set_person_id(pid):
            self.owner_entries["Person ID"] = pid
            self.cursor.execute("SELECT first_name, middle_name, last_name, married_name FROM People WHERE id = ?", (pid,))
            result = self.cursor.fetchone()
            if result:
                name_parts = [result[0], result[1], result[2]]
                name = " ".join(p for p in name_parts if p)
                if result[3]:  # married_name
                    name += f" ({result[3]})"
                person_display.config(text=name)
            else:
                person_display.config(text="(not found)")

        ttk.Button(person_frame, text="Lookup", command=lambda: person_search_popup(set_person_id)).pack(side="left")
        ttk.Button(person_frame, text="Clear", command=lambda: [person_display.config(text="(none)"), self.owner_entries.update({"Person ID": None})]).pack(side="left")

        # --- Additional fields ---
        labels = ["Ownership Type", "Start Date", "End Date", "Notes"]
        for i, label in enumerate(labels, start=1):
            ttk.Label(self.owner_win, text=label + ":").grid(row=i, column=0, padx=5, pady=3, sticky="e")
            entry = ttk.Entry(self.owner_win, width=40)
            entry.grid(row=i, column=1, padx=5, pady=3, sticky="w")
            self.owner_entries[label] = entry

        if existing:
            self.owner_entries["Person ID"] = existing[0]
            set_person_id(existing[0])
            for key, value in zip(labels, existing[2:]):
                self.owner_entries[key].insert(0, value)

        def save_owner():
            person_id = self.owner_entries["Person ID"]
            if not person_id:
                messagebox.showerror("Missing Person", "Please use Lookup to select a person.")
                return

            ownership_type = self.owner_entries["Ownership Type"].get().strip()
            try:
                start_date, _ = parse_date_input(self.owner_entries["Start Date"].get().strip())
                end_input = self.owner_entries["End Date"].get().strip()
                end_date, _ = parse_date_input(end_input) if end_input else (None, None)
            except ValueError as e:
                messagebox.showerror("Date Error", str(e))
                return

            notes = self.owner_entries["Notes"].get().strip()

            try:
                if self.owner_existing:
                    original_start_display = self.owner_existing[3]
                    original_start_date, _ = parse_date_input(original_start_display)
                    self.cursor.execute("""
                        UPDATE BizOwnership SET ownership_type=?, start_date=?, end_date=?, notes=?
                        WHERE biz_id=? AND person_id=? AND start_date=?
                    """, (ownership_type, start_date, end_date, notes, self.biz_id, person_id, original_start_date))
                else:
                    self.cursor.execute("""
                        INSERT INTO BizOwnership (biz_id, person_id, ownership_type, start_date, end_date, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (self.biz_id, person_id, ownership_type, start_date, end_date, notes))

                self.conn.commit()
                self.load_owners()
                self.owner_win.destroy()

            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "An ownership record for this person with the same start date already exists.")

        ttk.Button(self.owner_win, text="Save", command=save_owner).grid(row=len(labels)+2, column=0, pady=10)
        ttk.Button(self.owner_win, text="Cancel", command=self.owner_win.destroy).grid(row=len(labels)+2, column=1, pady=10)
 
    def delete_owner(self):
        selected = self.owner_tree.selection()
        if not selected:
            return
        person_id = self.owner_tree.item(selected[0])['values'][0]
        confirm = messagebox.askyesno("Delete", "Delete selected ownership record?")
        if confirm:
            self.cursor.execute("DELETE FROM BizOwnership WHERE biz_id = ? AND person_id = ?", (self.biz_id, person_id))
            self.conn.commit()
            self.load_owners()
   
    def on_owner_double_click(self, event):
        selected = self.owner_tree.selection()
        if selected:
            values = self.owner_tree.item(selected[0])['values']
            person_id = values[0]
            if person_id:
                self.master.destroy()  # Optional: close current biz form if needed
                subprocess.Popen(["python", "editme.py", str(person_id)])
    
    def sort_owner_tree_by_column(self, col):
        if not hasattr(self, '_owner_sort_state'):
            self._owner_sort_state = {}

        reverse = self._owner_sort_state.get(col, False)

        def date_sort_key(val):
            if not val:
                return datetime.max
            for fmt in ("%m-%d-%Y", "%m-%Y", "%Y"):
                try:
                    return datetime.strptime(val, fmt)
                except ValueError:
                    continue
            return datetime.max

        items = [(self.owner_tree.set(k, col), k) for k in self.owner_tree.get_children('')]

        if col in ("start", "end"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0], reverse=reverse)

        for index, (_, k) in enumerate(items):
            self.owner_tree.move(k, '', index)

        self._owner_sort_state[col] = not reverse

    #
    #Support Functions for #2 - Location Tree
    #

    def load_locations(self):
        self.location_tree.delete(*self.location_tree.get_children())
        self.cursor.execute("""
            SELECT a.address, l.start_date, l.end_date, l.notes, l.url
            FROM BizLocHistory l
            JOIN Address a ON l.address_id = a.address_id
            WHERE l.biz_id = ?
        """, (self.biz_id,))

        rows = self.cursor.fetchall()
        sorted_rows = sorted(rows, key=lambda r: date_sort_key(r[1]))

        for row in sorted_rows:
            address, start, end, notes, url = row
            start_display = format_date_for_display(start, "EXACT") if start else ""
            end_display = format_date_for_display(end, "EXACT") if end else ""
            self.location_tree.insert('', 'end', values=(address, start_display, end_display, notes, url))

        
    def add_location(self):
        self.open_location_editor()

    
    def edit_location(self):
        selected = self.location_tree.selection()
        if not selected:
            return
        values = self.location_tree.item(selected[0])['values']
        self.open_location_editor(existing=values)

    
    def open_location_editor(self, existing=None):
        self.location_win = tk.Toplevel(self.master)
        self.location_win.title("Edit Location" if existing else "Add Location")

        fields = ["Address", "Start Date", "End Date", "Notes", "URL"]
        self.location_entries = {}
        self.location_existing = existing

        for idx, label in enumerate(fields):
            ttk.Label(self.location_win, text=label + ":").grid(row=idx, column=0, padx=5, pady=3, sticky="e")

            if label == "Address":
                address_frame = ttk.Frame(self.location_win)
                address_frame.grid(row=idx, column=1, padx=5, pady=3, sticky="w")

                search_var = tk.StringVar()
                search_entry = ttk.Entry(address_frame, textvariable=search_var, width=30)
                search_entry.pack(side="left", padx=(0, 5))

                # Load address values and create lookup dictionary
                self.cursor.execute("SELECT address_id, address FROM Address ORDER BY address")
                address_rows = self.cursor.fetchall()
                address_list = [row[1] for row in address_rows]
                self.address_lookup = {row[1]: row[0] for row in address_rows}

                address_combo = ttk.Combobox(address_frame, width=40, state="readonly")
                address_combo['values'] = address_list
                address_combo.pack(side="left")

                self.location_entries["Address"] = address_combo

                def filter_addresses():
                    term = search_var.get().lower()
                    filtered = [a for a in address_list if term in a.lower()]
                    address_combo['values'] = filtered

                ttk.Button(address_frame, text="Search", command=filter_addresses).pack(side="left", padx=(5, 0))

            else:
                entry = ttk.Entry(self.location_win, width=50)
                entry.grid(row=idx, column=1, padx=5, pady=3)
                self.location_entries[label] = entry

        if existing:
            for key, value in zip(fields, existing):
                widget = self.location_entries.get(key)
                if widget:
                    widget.delete(0, tk.END)
                    widget.insert(0, value)

        def save_location():
            address_widget = self.location_entries.get("Address")
            if not address_widget:
                messagebox.showerror("Error", "Address field is missing.")
                return

            address = address_widget.get().strip()

            if address not in address_widget['values']:
                messagebox.showerror("Invalid Address", "The address you selected is not in the database.")
                return

            address_id = self.address_lookup.get(address)
            if not address_id:
                messagebox.showerror("Invalid Address", "The address is not recognized.")
                return

            try:
                start_input = self.location_entries["Start Date"].get().strip()
                end_input = self.location_entries["End Date"].get().strip()
                start_date, _ = parse_date_input(start_input)
                end_date, _ = parse_date_input(end_input) if end_input else (None, None)
            except ValueError as e:
                messagebox.showerror("Date Error", str(e))
                return

            notes = self.location_entries["Notes"].get().strip()
            url = self.location_entries["URL"].get().strip()

            try:
                if self.location_existing:
                    # Convert displayed original start date back to DB format
                    original_display_start = self.location_existing[1]
                    original_start_date, _ = parse_date_input(original_display_start)

                    self.cursor.execute("""
                        UPDATE BizLocHistory
                        SET start_date = ?, end_date = ?, notes = ?, url = ?
                        WHERE biz_id = ? AND address_id = ? AND start_date = ?
                    """, (start_date, end_date, notes, url, self.biz_id, address_id, original_start_date))
                else:
                    self.cursor.execute("""
                        INSERT INTO BizLocHistory (biz_id, address_id, start_date, end_date, notes, url)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (self.biz_id, address_id, start_date, end_date, notes, url))

                self.conn.commit()
                self.load_locations()
                self.location_win.destroy()

            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This location record already exists.")

        # Add Save and Cancel buttons
        btn_frame = ttk.Frame(self.location_win)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=save_location).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.location_win.destroy).pack(side="left", padx=10)
    
    def delete_location(self):
        selected = self.location_tree.selection()
        if not selected:
            return

        confirm = messagebox.askyesno("Delete", "Delete selected location record?")
        if confirm:
            values = self.location_tree.item(selected[0])['values']
            address = values[0]
            raw_start_date = values[1]

            try:
                parsed_start_date, _ = parse_date_input(raw_start_date)
            except ValueError:
                messagebox.showerror("Date Error", f"Could not parse start date: {raw_start_date}")
                return

            self.cursor.execute("""
                DELETE FROM BizLocHistory 
                WHERE biz_id = ? 
                  AND start_date = ? 
                  AND address_id = (
                      SELECT address_id FROM Address WHERE address = ? LIMIT 1
                  )
            """, (self.biz_id, parsed_start_date, address))
            self.conn.commit()
            self.load_locations()

    def sort_location_tree_by_column(self, col):
        if not hasattr(self, '_location_sort_state'):
            self._location_sort_state = {}

        reverse = self._location_sort_state.get(col, False)

        def date_sort_key(val):
            if not val:
                return datetime.max
            for fmt in ("%m-%d-%Y", "%m-%Y", "%Y"):
                try:
                    return datetime.strptime(val, fmt)
                except ValueError:
                    continue
            return datetime.max

        items = [(self.location_tree.set(k, col), k) for k in self.location_tree.get_children('')]

        if col in ("start", "end"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0], reverse=reverse)

        for index, (_, k) in enumerate(items):
            self.location_tree.move(k, '', index)

        self._location_sort_state[col] = not reverse
    

    #
    #Support Functions for #3 - Employee Tree
    #

    def load_employees(self):
        self.employee_tree.delete(*self.employee_tree.get_children())
        self.cursor.execute("""
            SELECT e.person_id,
                   CASE 
                       WHEN p.married_name IS NOT NULL AND p.married_name != ''
                       THEN p.first_name || ' ' || IFNULL(p.middle_name || ' ', '') || '(' || p.last_name || ') ' || p.married_name
                       ELSE p.first_name || ' ' || IFNULL(p.middle_name || ' ', '') || p.last_name
                   END AS full_name,
                   e.job_title, e.start_date, e.end_date, e.notes
            FROM BizEmployment e
            JOIN People p ON e.person_id = p.id
            WHERE e.biz_id = ?
        """, (self.biz_id,))

        rows = self.cursor.fetchall()
        sorted_rows = sorted(rows, key=lambda r: date_sort_key(r[3]))

        for row in sorted_rows:
            self.employee_tree.insert('', 'end', values=row)

    def add_employee(self):
        self.open_employee_editor()

    def edit_employee(self):
        selected = self.employee_tree.selection()
        if not selected:
            return
        values = self.employee_tree.item(selected[0])['values']
        self.open_employee_editor(existing=values)

    def open_employee_editor(self, existing=None):
        win = tk.Toplevel(self.master)
        win.title("Edit Employee" if existing else "Add Employee")
        entries = {}

        def set_person_id(pid):
            entries["Person ID"].delete(0, tk.END)
            entries["Person ID"].insert(0, pid)

        ttk.Label(win, text="Person ID:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        person_frame = ttk.Frame(win)
        person_frame.grid(row=0, column=1, padx=5, pady=3)
        person_id_entry = ttk.Entry(person_frame, width=30)
        person_id_entry.pack(side="left")
        ttk.Button(person_frame, text="Lookup", command=lambda: person_search_popup(set_person_id)).pack(side="left", padx=5)
        entries["Person ID"] = person_id_entry

        labels = ["Job Title", "Start Date", "End Date", "Notes"]
        for i, label in enumerate(labels, start=1):
            ttk.Label(win, text=label + ":").grid(row=i, column=0, padx=5, pady=3, sticky="e")
            entry = ttk.Entry(win, width=40)
            entry.grid(row=i, column=1, padx=5, pady=3)
            entries[label] = entry

        if existing:
            entries["Person ID"].insert(0, existing[0])
            for key, value in zip(labels, existing[2:]):
                entries[key].insert(0, value)

        def save_employee():
            person_id = self.employee_entries["Person ID"].get().strip()
            title = self.employee_entries["Job Title"].get().strip()
            try:
                start_date, _ = parse_date_input(self.employee_entries["Start Date"].get().strip())
                end_date, _ = parse_date_input(self.employee_entries["End Date"].get().strip()) if self.employee_entries["End Date"].get().strip() else (None, None)
            except ValueError as e:
                messagebox.showerror("Date Error", str(e))
                return

            notes = self.employee_entries["Notes"].get().strip()

            try:
                if self.employee_existing:
                    self.cursor.execute("""
                        UPDATE BizEmployment SET job_title=?, start_date=?, end_date=?, notes=?
                        WHERE biz_id=? AND person_id=? AND start_date=?
                    """, (title, start_date, end_date, notes, self.biz_id, person_id, self.employee_existing[3]))
                else:
                    self.cursor.execute("""
                        INSERT INTO BizEmployment (biz_id, person_id, job_title, start_date, end_date, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (self.biz_id, person_id, title, start_date, end_date, notes))
                self.conn.commit()
                self.load_employees()
                self.employee_win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This employment record already exists with the same start date.")
        
        ttk.Button(win, text="Save", command=save_employee).grid(row=len(labels)+1, column=0, columnspan=2, pady=10)
        

    def delete_employee(self):
        selected = self.employee_tree.selection()
        if not selected:
            return
        person_id = self.employee_tree.item(selected[0])['values'][0]
        confirm = messagebox.askyesno("Delete", "Delete selected employment record?")
        if confirm:
            self.cursor.execute("DELETE FROM BizEmployment WHERE biz_id = ? AND person_id = ?", (self.biz_id, person_id))
            self.conn.commit()
            self.load_employees()

    
    def on_employee_double_click(self, event):
        selected = self.employee_tree.selection()
        if selected:
            values = self.employee_tree.item(selected[0])['values']
            person_id = values[0]
            if person_id:
                subprocess.Popen(["python", "editme.py", str(person_id)])

    
    def on_location_double_click(self, event):
        region = self.location_tree.identify("region", event.x, event.y)
        column = self.location_tree.identify_column(event.x)

        if region != "cell":
            return

        selected = self.location_tree.selection()
        if not selected:
            return

        values = self.location_tree.item(selected[0])['values']
        address = values[0]
        url = values[4]  # Assuming column 5 is URL

        if column == "#1":  # Address column
            if address:
                query = urllib.parse.quote(address)
                map_url = f"https://www.google.com/maps/search/?api=1&query={query}"
                webbrowser.open(map_url, new=2)
            else:
                messagebox.showinfo("No Address", "No address provided.")
        elif column == "#5":  # URL column
            if url and url.startswith("http"):
                webbrowser.open(url, new=2)
            else:
                messagebox.showinfo("No URL", "No valid link provided.")

    def sort_employee_tree_by_column(self, col):
        if not hasattr(self, '_employee_sort_state'):
            self._employee_sort_state = {}

        reverse = self._employee_sort_state.get(col, False)

        def date_sort_key(val):
            try:
                return datetime.strptime(val, "%m-%d-%Y")
            except Exception:
                return datetime.max

        items = [(self.employee_tree.set(k, col), k) for k in self.employee_tree.get_children('')]

        if col in ("start", "end"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)

        for index, (_, k) in enumerate(items):
            self.employee_tree.move(k, '', index)

        self._employee_sort_state[col] = not reverse

    #
    #Support Functions for #4 - Business Events Tree   
    #
    
    def load_bizevents(self):
        self.bizevents_tree.delete(*self.bizevents_tree.get_children())
        query = """
            SELECT 
                e.event_id,
                e.event_type,
                e.event_start_date,
                e.event_end_date,
                p.first_name, p.middle_name, p.last_name, p.married_name,
                e.description,
                e.link_url
            FROM BusinessEvents e
            LEFT JOIN People p ON e.person_id = p.id
            WHERE e.biz_id = ?
            ORDER BY e.event_start_date
        """
        self.cursor.execute(query, (self.biz_id,))
        for row in self.cursor.fetchall():
            event_id, event_type, start_date, end_date, first, middle, last, married, description, link_url = row
            start_fmt = format_date_for_display(start_date, "EXACT") if start_date else ""
            end_fmt = format_date_for_display(end_date, "EXACT") if end_date else ""
            date_range = start_fmt if not end_fmt else f"{start_fmt} – {end_fmt}"
            if married and last:
                person_name = f"{first or ''} {middle or ''} ({last}) {married}".strip()
            else:
                person_name = f"{first or ''} {middle or ''} {last or ''}".strip()
            self.bizevents_tree.insert('', 'end', values=(event_id, event_type, date_range, person_name, description or '', link_url or ''))
        bizevents_btns = ttk.Frame(self.bizevents_frame)
        bizevents_btns.pack(side="bottom", fill="x")
        

    def add_bizevent(self):
        win = tk.Toplevel(self.master)
        win.title("Add Business Event")
        # win.geometry("650x360")

        labels = ["Event Type", "Start Date", "End Date", "Description", "Link URL"]
        entries = {}

        for i, label in enumerate(labels):
            ttk.Label(win, text=label + ":").grid(row=i, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(win, width=50)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[label] = entry

        row_offset = len(labels)
        ttk.Label(win, text="Person:").grid(row=row_offset, column=0, sticky="e", padx=5, pady=5)
        person_label = ttk.Label(win, text="", width=50, anchor="w")
        person_label.grid(row=row_offset, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        person_label.person_id = None

        def set_person_id(pid):
            self.cursor.execute("SELECT first_name, middle_name, last_name, married_name FROM People WHERE id = ?", (pid,))
            name_parts = self.cursor.fetchone()
            if name_parts:
                first, middle, last, married = name_parts
                if married and last:
                    name_display = f"{first or ''} {middle or ''} ({last}) {married}".strip()
                else:
                    name_display = f"{first or ''} {middle or ''} {last or ''}".strip()
                person_label.config(text=name_display)
            person_label.person_id = pid
            clear_button.grid()

        def clear_person():
            person_label.config(text="")
            person_label.person_id = None
            clear_button.grid_remove()

        ttk.Button(win, text="Lookup Person", command=lambda: person_search_popup(set_person_id)).grid(row=row_offset + 1, column=0, padx=5, pady=5)
        clear_button = ttk.Button(win, text="Clear Person", command=clear_person)
        clear_button.grid(row=row_offset + 1, column=1, padx=5, pady=5)
        clear_button.grid_remove()

        ttk.Separator(win, orient="horizontal").grid(row=row_offset + 2, column=0, columnspan=3, sticky="ew", padx=5, pady=10)

        def save_event():
            data = {k: v.get().strip() for k, v in entries.items()}
            try:
                start_date, _ = parse_date_input(data["Start Date"])
                end_date, _ = parse_date_input(data["End Date"]) if data["End Date"] else (None, None)
            except ValueError as e:
                messagebox.showerror("Date Error", str(e))
                return

            try:
                self.cursor.execute("""
                    INSERT INTO BusinessEvents (biz_id, event_type, event_start_date, event_end_date, person_id, description, link_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.biz_id,
                    data["Event Type"],
                    start_date,
                    end_date,
                    person_label.person_id,
                    data["Description"],
                    data["Link URL"]
                ))
                self.conn.commit()
                win.destroy()
                self.load_bizevents()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add event: {e}")

        btn_frame = ttk.Frame(win)
        btn_frame.grid(row=row_offset + 3, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="Save", command=save_event).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="left", padx=10)
    

    def edit_bizevent(self):
        selected = self.bizevents_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an event to edit.")
            return

        item = self.bizevents_tree.item(selected[0])
        event_id = item['values'][0]

        self.cursor.execute("SELECT event_type, event_start_date, event_end_date, person_id, description, link_url FROM BusinessEvents WHERE event_id = ?", (event_id,))
        result = self.cursor.fetchone()
        if not result:
            messagebox.showerror("Error", "Event not found in database.")
            return

        event_type_val, start_date_val, end_date_val, person_id_val, desc_val, link_val = result

        display_name = ""
        if person_id_val:
            self.cursor.execute("SELECT first_name, middle_name, last_name, married_name FROM People WHERE id = ?", (person_id_val,))
            name_parts = self.cursor.fetchone()
            if name_parts:
                first, middle, last, married = name_parts
                if married and last:
                    display_name = f"{first or ''} {middle or ''} ({last}) {married}".strip()
                else:
                    display_name = f"{first or ''} {middle or ''} {last or ''}".strip()

        win = tk.Toplevel(self.master)
        win.title("Edit Business Event")
        win.geometry("650x460")

        labels = ["Event Type", "Start Date", "End Date", "Description", "Link URL"]
        entries = {}

        for i, label in enumerate(labels):
            ttk.Label(win, text=label + ":").grid(row=i, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(win, width=50)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[label] = entry

        entries["Event Type"].insert(0, event_type_val)
        entries["Start Date"].insert(0, format_date_for_display(start_date_val, "EXACT"))
        entries["End Date"].insert(0, format_date_for_display(end_date_val, "EXACT"))
        entries["Description"].insert(0, desc_val or "")
        entries["Link URL"].insert(0, link_val or "")

        row_offset = len(labels)
        ttk.Label(win, text="Person:").grid(row=row_offset, column=0, sticky="e", padx=5, pady=5)
        person_label = ttk.Label(win, text=display_name, width=50, anchor="w")
        person_label.grid(row=row_offset, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        person_label.person_id = person_id_val

        def set_person_id(pid):
            self.cursor.execute("SELECT first_name, middle_name, last_name, married_name FROM People WHERE id = ?", (pid,))
            name_parts = self.cursor.fetchone()
            if name_parts:
                first, middle, last, married = name_parts
                if married and last:
                    name_display = f"{first or ''} {middle or ''} ({last}) {married}".strip()
                else:
                    name_display = f"{first or ''} {middle or ''} {last or ''}".strip()
                person_label.config(text=name_display)
            person_label.person_id = pid
            clear_button.grid()

        def clear_person():
            person_label.config(text="")
            person_label.person_id = None
            clear_button.grid_remove()

        ttk.Button(win, text="Lookup Person", command=lambda: person_search_popup(set_person_id)).grid(row=row_offset + 1, column=0, padx=5, pady=5)
        clear_button = ttk.Button(win, text="Clear Person", command=clear_person)
        clear_button.grid(row=row_offset + 1, column=1, padx=5, pady=5)
        if not person_id_val:
            clear_button.grid_remove()

        # Separator
        ttk.Separator(win, orient="horizontal").grid(row=row_offset + 2, column=0, columnspan=3, sticky="ew", padx=5, pady=10)

        def update_event():
            data = {k: v.get().strip() for k, v in entries.items()}
            try:
                start_date, _ = parse_date_input(data["Start Date"])
                end_date, _ = parse_date_input(data["End Date"]) if data["End Date"] else (None, None)
            except ValueError as e:
                messagebox.showerror("Date Error", str(e))
                return

            try:
                self.cursor.execute("""
                    UPDATE BusinessEvents
                    SET event_type = ?, event_start_date = ?, event_end_date = ?, person_id = ?, description = ?, link_url = ?
                    WHERE event_id = ?
                """, (
                    data["Event Type"],
                    start_date,
                    end_date,
                    person_label.person_id,
                    data["Description"],
                    data["Link URL"],
                    event_id
                ))
                self.conn.commit()
                win.destroy()
                self.load_bizevents()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update event: {e}")

        btn_frame = ttk.Frame(win)
        btn_frame.grid(row=row_offset + 3, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="Save", command=update_event).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="left", padx=10)


    def delete_bizevent(self):
        selected = self.bizevents_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an event to delete.")
            return

        item = self.bizevents_tree.item(selected[0])
        event_id = item['values'][0]

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected business event?")
        if confirm:
            try:
                self.cursor.execute("DELETE FROM BusinessEvents WHERE event_id = ?", (event_id,))
                self.conn.commit()
                self.load_bizevents()
                messagebox.showinfo("Deleted", "Business event deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete event: {e}")

    
    def on_bizevent_double_click(self, event):
        region = self.bizevents_tree.identify("region", event.x, event.y)
        column = self.bizevents_tree.identify_column(event.x)

        if region != "cell":
            return

        selected = self.bizevents_tree.selection()
        if not selected:
            return

        values = self.bizevents_tree.item(selected[0])['values']

        # Column #4 = person name, Column #6 = link_url
        if column == "#4":
            # We need to fetch the person ID from elsewhere — store it in the hidden first column if not already
            person_name = values[3]  # e.g., "John Doe"
            event_id = self.bizevents_tree.item(selected[0])['values'][0]

            # Assuming your event links to a person_id, you can adjust this part:
            self.cursor.execute("""
                SELECT person_id FROM BusinessEvents WHERE event_id = ?
            """, (event_id,))
            result = self.cursor.fetchone()
            if result:
                person_id = result[0]
                subprocess.Popen(["python", "editme.py", str(person_id)])
            else:
                messagebox.showinfo("Info", f"No linked person found for '{person_name}'.")

        elif column == "#6":
            url = values[5]  # link_url column
            if url and url.startswith("http"):
                webbrowser.open(url, new=2)
            else:
                messagebox.showinfo("No URL", "No valid link provided for this event.")

        def sort_bizevents_tree_by_column(self, col):
            if not hasattr(self, '_bizevent_sort_state'):
                self._bizevent_sort_state = {}

            reverse = self._bizevent_sort_state.get(col, False)

            def date_range_sort_key(val):
                try:
                    if " to " in val:
                        start_str = val.split(" to ")[0]
                        return datetime.strptime(start_str, "%m-%d-%Y")
                    return datetime.strptime(val, "%m-%d-%Y")
                except:
                    return datetime.max

            items = [(self.bizevents_tree.set(k, col), k) for k in self.bizevents_tree.get_children('')]
            if col == "date_range":
                items.sort(key=lambda item: date_range_sort_key(item[0]), reverse=reverse)
            else:
                items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)

            for index, (_, k) in enumerate(items):
                self.bizevents_tree.move(k, '', index)

            self._bizevent_sort_state[col] = not reverse

    def load_data(self):
        self.cursor.execute("SELECT biz_name, category, start_date, end_date, description, aliases, image_path, map_link, external_url FROM Biz WHERE biz_id = ?", (self.biz_id,))
        row = self.cursor.fetchone()
        if row:
            keys = ["biz_name", "category", "start_date", "end_date", "description", "aliases", "image_path", "map_link", "external_url"]
            for k, v in zip(keys, row):
                self.entries[k].insert(0, v or "")

    def save(self):
        data = {k: self.entries[k].get().strip() for k in self.entries}
        if not data["biz_name"]:
            messagebox.showerror("Validation", "Business name is required.")
            return

        if self.biz_id:
            self.cursor.execute("""
                UPDATE Biz SET biz_name = ?, category = ?, start_date = ?, end_date = ?, description = ?, aliases = ?,
                image_path = ?, map_link = ?, external_url = ? WHERE biz_id = ?
            """, (*data.values(), self.biz_id))
        else:
            self.cursor.execute("""
                INSERT INTO Biz (biz_name, category, start_date, end_date, description, aliases, image_path, map_link, external_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(data.values()))
            self.biz_id = self.cursor.lastrowid

        self.conn.commit()
        self.master.destroy()

    
    
    
def open_edit_business_form(biz_id=None):
    win = tk.Tk() if biz_id is None else tk.Toplevel()
    win.geometry("1100x900")
    EditBusinessForm(win, biz_id)
    win.grab_set()
