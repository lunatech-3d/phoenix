import re
from datetime import datetime
import tkinter as tk
from tkinter import Menu, messagebox

def parse_date_input(date_value):
    if not date_value:
        return "", ""
    
    date_str = str(date_value).strip().upper()
    
    if date_str.startswith('ABT '):
        precision = "ABOUT"
        date_str = date_str[4:]
    elif date_str.startswith('BEF '):
        precision = "BEFORE"
        date_str = date_str[4:]
    elif date_str.startswith('AFT '):
        precision = "AFTER"
        date_str = date_str[4:]
    else:
        precision = "EXACT"

    try:
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):  # YYYY-MM-DD
            return date_str, precision
        elif re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):  # MM-DD-YYYY
            return datetime.strptime(date_str, "%m-%d-%Y").strftime("%Y-%m-%d"), precision
        elif re.match(r'^\d{2}-\d{4}$', date_str):  # MM-YYYY
            return datetime.strptime(date_str, "%m-%Y").strftime("%Y-%m"), "MONTH"
        elif re.match(r'^\d{4}$', date_str):  # YYYY
            return date_str, precision if precision != "EXACT" else "YEAR"
        else:
            raise ValueError(f"Invalid date format: {date_str}")
    except ValueError as e:
        raise ValueError(f"Error parsing date: {e}")

def format_date_for_display(date_str, precision):
    if not date_str:
        return ""
    
    date_str = str(date_str)
    
    try:
        if precision == "EXACT":
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%m-%d-%Y")
        elif precision == "MONTH":
            return datetime.strptime(date_str, "%Y-%m").strftime("%m-%Y")
        elif precision == "YEAR":
            return date_str
        elif precision == "ABOUT":
            return f"Abt {date_str}"
        elif precision == "BEFORE":
            return f"Bef {date_str}"
        elif precision == "AFTER":
            return f"Aft {date_str}"
        else:
            return date_str
    except ValueError:
        print(f"Error formatting date: {date_str}, precision: {precision}")
        return date_str  # Return original string if parsing fails

DATE_FORMAT_INFO = """
Acceptable date formats:
- Exact date: MM-DD-YYYY (e.g., 05-15-1900)
- Month and year: MM-YYYY (e.g., 05-1900)
- Year only: YYYY (e.g., 1900)
- About a year: ABT YYYY (e.g., ABT 1900)
- Before a year: BEF YYYY (e.g., BEF 1900)
- After a year: AFT YYYY (e.g., AFT 1900)
"""

def add_date_format_menu(widget):
    def show_date_format_info():
        info_window = tk.Toplevel(widget)
        info_window.title("Date Format Information")
        info_window.geometry("450x450")
        
        text = tk.Text(info_window, wrap=tk.WORD, padx=10, pady=10)
        text.insert(tk.END, DATE_FORMAT_INFO)
        text.config(state=tk.DISABLED)  # Make the text read-only
        text.pack(expand=True, fill=tk.BOTH)

        # Add a close button
        close_button = tk.Button(info_window, text="Close", command=info_window.destroy)
        close_button.pack(pady=10)

    def show_context_menu(event):
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    context_menu = Menu(widget, tearoff=0)
    context_menu.add_command(label="Show Date Formats", command=show_date_format_info)
    
    widget.bind("<Button-3>", show_context_menu)  # Right-click

# Sort key function using parsed ISO dates
def date_sort_key(value):
    try:
        parsed, _ = parse_date_input(value)
        return datetime.strptime(parsed, "%Y-%m-%d")
    except Exception:
        return datetime.max
