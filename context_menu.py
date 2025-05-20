# context_menu.py

import tkinter as tk
from tkinter import ttk
import subprocess

def paste_from_clipboard(entry):
    try:
        clipboard_text = entry.clipboard_get()
        entry.insert(tk.INSERT, clipboard_text)
    except tk.TclError:
        pass

def add_a_source(id, first_name, middle_name, last_name, married_name):
    full_name = f"{first_name} {' ' + middle_name if middle_name else ''} {last_name}"
    if married_name:
        full_name += f" (née {married_name})"
    command = ['python', 'c:\\sqlite\\citations.py', str(id), full_name]
    # Call the script with subprocess.run
    subprocess.run(command)   


def insert_custom_entry(entry, text):
    entry.delete(0, tk.END)
    entry.insert(0, text)

def create_context_menu(entry, entries=None):
    """
    Create a context menu for a given entry widget.
    If 'entries' are provided, add them to the menu for special fields.
    """
    edit_menu = tk.Menu(entry, tearoff=0)
    edit_menu.add_command(label="Cut", command=lambda: entry.event_generate("<<Cut>>"))
    edit_menu.add_command(label="Copy", command=lambda: entry.event_generate("<<Copy>>"))
    edit_menu.add_command(label="Paste", command=lambda: paste_from_clipboard(entry))
    edit_menu.add_separator()
    edit_menu.add_command(label="Add a Source", command=lambda: add_a_source(id, first_name, middle_name, last_name, married_name))
  
    # Add special entries if provided (for Birthplace and Death Place)
    if entries:
        #print("Adding custom entries:", entries)  # Debug

        edit_menu.add_separator()
        for text in entries:
            edit_menu.add_command(label=text, command=lambda text=text: insert_custom_entry(entry, text))

    def show_context_menu(event):
        #print("Showing context menu for:", entry)  # Debug

        try:
            edit_menu.tk_popup(event.x_root, event.y_root)
        finally:
            edit_menu.grab_release()

    entry.bind("<Button-3>", show_context_menu)


def apply_context_menu_to_all_entries(container):
    from context_menu import create_context_menu
    for widget in container.winfo_children():
        if isinstance(widget, ttk.Entry) or isinstance(widget, tk.Text):
            create_context_menu(widget)
        elif widget.winfo_children():
            apply_context_menu_to_all_entries(widget)