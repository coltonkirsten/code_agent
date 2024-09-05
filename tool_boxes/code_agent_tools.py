import os
from backup_manager import backup_manager

def code_write(filename, code):
    """Create (or edit if the file exists) a script with the given filename and code"""

    # Read the allowed path from current_directory.txt
    try:
        with open("current_directory.txt", "r") as f:
            allowed_path = f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError("The file 'current_directory.txt' does not exist.")
    
    # Normalize the paths
    allowed_path = os.path.abspath(allowed_path)
    full_path = os.path.abspath(filename)
    
    # Check if the file is within the allowed path
    if not full_path.startswith(allowed_path):
        raise ValueError("Access to the specified file is not allowed.")
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    # Backup the current state before writing new code (only if the file exists)
    if os.path.exists(full_path):
        backup_manager.backup_file(full_path)
    
    # Write the code to the file (create if it doesn't exist, overwrite if it does)
    with open(full_path, "w", encoding='utf-8') as file:
        file.write(code)
    print(f"< created/updated {filename} >")
    return f"SCRIPT: {filename}"

### INTERFACE ###
available_functions={
    "code_write": code_write
    }

#description

tool_interface = [
    {
        "type": "function",
        "function": {
            "name": "code_write",
            "description": "Create (or edit if the file exists) a Python script with the given filename and code",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the Python file to be created or edited."},
                    "code": {"type": "string", "description": "The source code to be written into the file"}
                },
                "required": ["filename", "code"]
            },
        },
    },
]

### TOOLBOX ###
code_agent_tools = [tool_interface, available_functions]