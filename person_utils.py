def launch_new_person_form(role=None, related_id=None):
    """
    Launch the editme.py script to add a new person.
    
    Args:
        role (str): Optional. 'child', 'father', or 'mother'
        related_id (int): Optional. The ID of the related person
    """
    command = ["python", "editme.py"]
    if role in ("child", "father", "mother") and related_id:
        command.extend([f"--new-{role}", str(related_id)])
    else:
        command.append("--new-person")
    subprocess.Popen(command)
