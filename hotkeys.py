# hotkeys.py
import tkinter as tk

# Global dictionary to store remembered values for specific fields (currently only used for tax records)
remembered_values = {
    "record_id": None,
    "year": None,
    "description": None,
    "section": None,
    "acres": None,
    "acres_qtr": None,
    "prop_value": None,
    "personal_value": None,
    "notes": None
}

# Explicit hotkey mapping
HOTKEY_MAP = {
    "record_id": "i",
    "year": "y",
    "description": "d",
    "section": "c",
    "acres": "a",
    "acres_qtr": "q",
    "prop_value": "t",
    "personal_value": "l",  # 'L' for personal value
    "notes_value": "n"
    
}

def bind_field_hotkeys(entry_widget, field_key):
    """
    Binds Ctrl+Shift+<letter> to remember the value,
    and Ctrl+<letter> to insert the remembered value.
    Supports both Entry and Text widgets.
    """
    letter = HOTKEY_MAP.get(field_key)
    if not letter:
        return  # Field key not mapped

    def remember(event):
        if isinstance(entry_widget, tk.Text):
            remembered_values[field_key] = entry_widget.get("1.0", "end-1c").strip()
        else:
            remembered_values[field_key] = entry_widget.get()
        print(f"[HOTKEY] Remembered {field_key}: {remembered_values[field_key]}")

    def insert(event):
        value = remembered_values.get(field_key)
        if value is not None:
            if isinstance(entry_widget, tk.Text):
                entry_widget.delete("1.0", "end")
                entry_widget.insert("1.0", value)
            else:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, value)
            print(f"[HOTKEY] Inserted {field_key}: {value}")

    entry_widget.bind(f"<Control-Shift-{letter.upper()}>", remember)
    entry_widget.bind(f"<Control-{letter}>", insert)