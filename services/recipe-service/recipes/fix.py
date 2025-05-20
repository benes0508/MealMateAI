import os

def rename_files_in_folder(folder_path, script_name):
    for filename in os.listdir(folder_path):
        old_path = os.path.join(folder_path, filename)

        # Skip directories and the script itself
        if not os.path.isfile(old_path) or filename == script_name:
            continue

        new_filename = filename.lower().replace(' ', '_')
        new_path = os.path.join(folder_path, new_filename)

        if old_path != new_path:
            os.rename(old_path, new_path)
            print(f"Renamed: {filename} -> {new_filename}")

if __name__ == "__main__":
    folder = os.path.dirname(os.path.abspath(__file__))  # Folder where the script is located
    script_file = os.path.basename(__file__)             # This script's filename
    rename_files_in_folder(folder, script_file)