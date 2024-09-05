import os
import tkinter as tk
from tkinter import filedialog
import core_bot
import tool_boxes.code_agent_tools as tools
from backup_manager import backup_manager


# < File managment >
CURRENT_DIRECTORY_FILE = 'current_directory.txt'

def select_directory():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    return folder_path

def save_current_directory(directory):
    with open(CURRENT_DIRECTORY_FILE, 'w', encoding='utf-8') as file:
        file.write(directory)

def load_current_directory():
    if os.path.exists(CURRENT_DIRECTORY_FILE):
        with open(CURRENT_DIRECTORY_FILE, 'r', encoding='utf-8') as file:
            return file.read().strip()
    return None

def consolidate_code_to_text_file(directory, output_file):
    consolidated_code = ""
    with open(output_file, 'w', encoding='utf-8') as output:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.js', '.jsx', '.css', '.html', '.json', '.ts', '.tsx')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        output.write(f"// File: {file_path}\n")
                        output.write(file_content)
                        output.write("\n\n")
                        consolidated_code += f"// File: {file_path}\n{file_content}\n\n"
    return consolidated_code

# < end file managment >


# < code agent > 

system_role = """ You are an expert React JS developer.
You are given a program, and a <requested feature> from the user.
Follow these instructions when answering:
1. describe in 1-5 bullet points how you will modify the code
2. call the code_write function once for each script that needs to
change in order to implement the requested feature. When using this
too, Make sure to provide the filename of the file you want to 
modify or create, and the entire script such that it would run
without any modification. ONLY write code to the tool, no need to write
code before calling the tool. """

code_agent = core_bot.Bot(
    tools=tools.code_agent_tools,
    model="gpt-4o",
    save_history=True,
    system_role=system_role, 
    stream=True,
    temperature=0,
    max_tokens=1024,
    logging=False
    )


def update(codebase, instruction):
    code_agent.forget()
    prompt = codebase + "\n<requested feature> " + instruction
    
    while True:
        try:
            print("\n< code agent >")
            streamed_responses = code_agent.prompt(prompt)
            for response in streamed_responses:
                print(response, end="")
            break
        except:
            print("\n\n< ERR retrying... >")



    print("\n")

def follow_up(question):
    code_agent.prompt(question)
    print("\n< code agent >")
    streamed_responses = code_agent.prompt(prompt)
    for response in streamed_responses:
        print(response, end="")

# < end code agent > 



def main():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_directory, 'consolidated_code.txt')
    # Load the last used directory
    current_directory = load_current_directory()
    
    if not current_directory:
        # If no directory has been saved, prompt the user to select one
        current_directory = select_directory()
        if current_directory:
            save_current_directory(current_directory)

    while True:
        command = input("< >")
        if command == "help":
            print("""
< available commands >      
> cd: change directory
> cr: change request
> f: follow up 1uestion or change
> undo: undo last step
> redo: redo last undo
> exit: exit cli      
""")
        elif command == "cd":
            current_directory = select_directory()
            if current_directory:
                save_current_directory(current_directory)
                print(f"Directory changed to {current_directory}")
            else:
                print("No directory selected.")
        elif command == "cr":
            if current_directory:
                codebase = consolidate_code_to_text_file(current_directory, output_file)
                instruction = input("< >< change request >")
                # print(f"All code has been consolidated into {output_file}")
            else:
                print("< ERR > No directory selected.")

            update(codebase, instruction)
        
        elif command == "f":
            if current_directory:
                codebase = consolidate_code_to_text_file(current_directory, output_file)
                instruction = input("< >< follow up >")
                # print(f"All code has been consolidated into {output_file}")
            else:
                print("< ERR > No directory selected.")

            update(codebase, instruction)

            # Inside the main loop, add the following elif block
        elif command == "undo":
            backup_manager.undo_last_step()

        elif command == "redo":
            backup_manager.redo_last_step()

        elif command == "exit":
            break

if __name__ == '__main__':
    main()