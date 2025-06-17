import os
import ast
import json

DEBUG = False
COMPATIBLE_EXTENSIONS = ["py", "mel"]

current_dir = os.path.dirname(os.path.abspath(__file__)) # Get the directory where this script is located
root_dir = os.path.dirname(current_dir)
script_dir = os.path.join(root_dir, "scripts")

def findIconPath(content, entry_path):
    icon = ""
    try:
        tree = ast.parse(content, filename=entry_path)

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__image__':
                        icon = ast.literal_eval(node.value)  # safely get string value
    except: pass
    return icon

def loadScriptFolder(path=script_dir, file_type="folder"):
    # Initialize the result dictionary with 
    # folder name, type, and an empty list for children
    result = {'name': os.path.basename(path), 
              'type': file_type, 'children': []}

    # Check if the path is a directory
    if not os.path.isdir(path):
        return False # if its file in the path just return False/reject

    # Iterate over the entries in the directory
    for entry in os.listdir(path):
      # Create the full path for the current entry
        entry_path = os.path.join(path, entry)  
        if DEBUG: print(entry_path)

        # If the entry is a directory, recursively call the function
        if os.path.isdir(entry_path):
            if DEBUG: print("entry is ", entry)
            if entry.startswith("(category)"):
                if DEBUG: print("is a category")
                entry_type = "category"
            elif entry.startswith("(divider)"):
                if DEBUG: print("is a divider")
                entry_type = "divider"
            else:
                entry_type = "folder"
            result['children'].append(loadScriptFolder(entry_path, entry_type))
        else:  # If the entry is a file, create a dictionary with name and type
            try:
                extension = os.path.splitext(entry)[1][1:].lower() # [1:] to remove the dot before file extension
                if extension not in COMPATIBLE_EXTENSIONS: 
                    print("Warning: %s extension is not compatible, skipped\nFULL PATH -> %s"%(extension,entry_path))
                    continue
                if extension == "py": extension = "python"
                with open(entry_path, "r", encoding='utf-8') as f:  # sometimes you encounter text that require other encoding (e.g. japan text use "shift_jis")
                        content = f.read()
                icon = findIconPath(content, entry_path)

                result['children'].append({'name': os.path.splitext(entry)[0], 'type': extension, 'content': content, "icon":icon})
            except Exception as e: print(e)

    return result

# DEBUG PURPOSE
folder_path = script_dir
folder_json = loadScriptFolder(folder_path)  
folder_json_str = json.dumps(folder_json, indent=4)  
output_file = os.path.join(current_dir, "scriptsData.json")

with open(output_file, 'w') as f:
    f.write(folder_json_str)  # Write the JSON string to the file