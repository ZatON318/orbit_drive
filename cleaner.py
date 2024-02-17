import os

folder_path = "./uploads"

files = os.listdir(folder_path)

for file in files:
    file_path = os.path.join(folder_path, file)
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")


folder_path = "./downloads"

files = os.listdir(folder_path)

for file in files:
    file_path = os.path.join(folder_path, file)
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")