from flask import Flask, render_template, request, jsonify
import json, ast, os
import subprocess

app = Flask(__name__)
json_path = "files_index.json"


def save_files(files):
    file_paths = []
    for file in files:
        # Save each uploaded file to the server
        file_path = 'uploads/' + file.filename
        file.save(file_path)
        file_paths.append(file_path)
    return file_paths

def generate_filestructure(data):

    structure = []
    splited_structure = []

    for f in data:
        if(f["virtual_pos"] not in structure):
            structure.append(f["virtual_pos"])

    for f in structure:
        splited_folder = f.split("/")
        for i, text in enumerate(splited_folder):
                if(text == ''):
                    splited_folder.pop(i)

        if splited_folder[0] == "":
            splited_folder = []
        splited_structure.append(splited_folder)
           


    return structure, splited_structure

@app.route('/<path:subpath>', methods=["GET","POST"])
def browser(subpath):
    virtualpath = "/"+subpath
    print(virtualpath)

    if request.method == 'POST':
        files = request.files.getlist('files')
        file_paths = save_files(files)
        print(file_paths)

        for fp in file_paths:
            command = f'py .\\od.py up {fp} {virtualpath}'

            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: {e}")

        return jsonify({'result': "jej"})

    files = []
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

    for f in data:
        if(f["virtual_pos"] == virtualpath):
            files.append(f)

    splited_subpath = subpath.split("/")
    
    for i, text in enumerate(splited_subpath):
        if(text == ''):
            splited_subpath.pop(i)

    print("Splited path: " + str(splited_subpath))

    path_length = len(splited_subpath)
    print("Path length: " + str(path_length))

    folders, splited_folders = generate_filestructure(data)
    print(splited_folders)
    print("Filtering folders")
    folders_to_show = []
    for folder in splited_folders:
        if path_length <= 1:
            try:
                print(folder[0])
                if(folder[0] == splited_subpath[0]):
                    if(folder[1] not in folders_to_show):
                        folders_to_show.append(folder[1])
            except:
                continue
        else:
            try:
                print("Folder path" + str(folder[path_length-1]))
                print("Url path" + str(splited_subpath[path_length-1]))
                if(folder[path_length-1] == splited_subpath[path_length-1]):
                    if(folder[path_length] not in folders_to_show):
                        folders_to_show.append(folder[path_length])
            except:
                continue
    
    print("Folders to show: " + str(folders_to_show))

    return render_template('index.html', files=files, folders=folders_to_show)

@app.route('/')
def index():
    virtualpath = "/"
    files = []
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

    for f in data:
        if(f["virtual_pos"] == virtualpath):
            files.append(f)
    
    folders, splited_folders = generate_filestructure(data)
    folders_to_show = []
    for folder in splited_folders:
        try:
            if(folder[0] not in folders_to_show):
                folders_to_show.append(folder[0])
        except:
            continue
    
    print(folders_to_show)

    return render_template('index.html', files=files, folders=folders_to_show)

if __name__ == '__main__':
    app.run(debug=True)
