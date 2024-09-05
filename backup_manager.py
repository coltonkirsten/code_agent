# backup_manager.py

import os
from collections import defaultdict, deque

class BackupManager:
    def __init__(self, max_steps=3):
        self.max_steps = max_steps
        self.backups = defaultdict(lambda: deque(maxlen=max_steps))
        self.modified_files = deque(maxlen=max_steps)
        self.redo_stack = defaultdict(lambda: deque(maxlen=max_steps))

    def backup_file(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
                self.backups[filename].append(content)
                self.modified_files.append(filename)
                # Clear redo stack because a new action has been performed
                self.redo_stack[filename].clear()

    def undo_last_change(self, filename):
        if filename in self.backups and self.backups[filename]:
            last_backup = self.backups[filename].pop()
            current_content = self._read_file(filename)
            self._write_file(filename, last_backup)
            self.redo_stack[filename].append(current_content)
            print(f"< undid changes to {filename} >")
        else:
            print(f"< ERR > No backup found for {filename}")

    def redo_last_change(self, filename):
        if filename in self.redo_stack and self.redo_stack[filename]:
            last_redo = self.redo_stack[filename].pop()
            current_content = self._read_file(filename)
            self._write_file(filename, last_redo)
            self.backups[filename].append(current_content)
            print(f"< redid changes to {filename} >")
        else:
            print(f"< ERR > No redo available for {filename}")

    def undo_last_step(self):
        if self.modified_files:
            last_modified_files = list(self.modified_files)
            for filename in last_modified_files:
                self.undo_last_change(filename)
            self.modified_files.clear()
        else:
            print("< ERR > No files were modified in the last step.")

    def redo_last_step(self):
        if self.modified_files:
            last_modified_files = list(self.modified_files)
            for filename in last_modified_files:
                self.redo_last_change(filename)
            self.modified_files.clear()
        else:
            print("< ERR > No files were modified in the last step.")
    
    def _read_file(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        return ""

    def _write_file(self, filename, content):
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)

# Instantiate a global backup manager for use in the code_write function
backup_manager = BackupManager()