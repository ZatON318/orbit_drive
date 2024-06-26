from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, redirect
import json, ast, os
import platform , sqlite3, subprocess


app = Flask(__name__)
json_path = "./odrive_sync/files_index.json"
stats_index = "./odrive_sync/stats_index.json"

def convert_bytes(file_size_bytes):
    size_units = ["Bytes", "KB", "MB", "GB", "TB"]
    factor = 1024

    index = 0

    while file_size_bytes > factor and index < len(size_units) - 1:
        file_size_bytes /= factor
        index += 1

    result = "{:.2f} {}".format(file_size_bytes, size_units[index])
    return result

def get_total_size():
    with open(stats_index, 'r') as file:
        data = json.load(file)

    size = convert_bytes(data["total_size"])

    return size

def get_os():
    system = platform.system()
    if system == "Windows":
        return "Windows"
    elif system == "Linux":
        return "Linux"
    else:
        return "Unknown"

def sync_index():
    print(get_os())
    if(get_os() == "Windows"):

        command = f'sync_index.bat'
        try:
            result = subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
    else:

        command = f'./sync_index.sh'
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

def save_files(files):
    file_paths = []
    for file in files:
        # Save each uploaded file to the server
        file_path = 'uploads/' + file.filename
        file.save(file_path)
        file_paths.append(file_path)
    return file_paths

def generate_filestructure():

    structure = []
    splited_structure = []

    conn = sqlite3.connect('files.db')
    cur = conn.cursor()

    cur.execute('SELECT * FROM files')
    rows = cur.fetchall()

    for row in rows:
        structure.append(row[6])

    conn.close()

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
    #print(virtualpath)

    if request.method == 'POST':
        files = request.files.getlist('files')

        for file in files:
            print(file.filename)
            file.filename = file.filename.replace(" ", "_")

        file_paths = save_files(files)

        for fp in file_paths:

            command = f'py .\\od.py up {fp} {virtualpath}'

            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: {e}")

        sync_index()

        return jsonify({'result': "jej"})

    files = []
    conn = sqlite3.connect('files.db')
    cur = conn.cursor()

    cur.execute('SELECT * FROM files')
    rows = cur.fetchall()

    conn.close()

    for f in rows:
        if(f[6] == virtualpath):
            files.append(f)

    splited_subpath = subpath.split("/")
    
    for i, text in enumerate(splited_subpath):
        if(text == ''):
            splited_subpath.pop(i)


    path_length = len(splited_subpath)

    folders, splited_folders = generate_filestructure()
    folders_to_show = []
    for folder in splited_folders:
        if path_length <= 1:
            try:
                if(folder[0] == splited_subpath[0]):
                    if(folder[1] not in folders_to_show):
                        folders_to_show.append(folder[1])
            except:
                continue
        else:
            try:
                if(folder[path_length-1] == splited_subpath[path_length-1]):
                    if(folder[path_length] not in folders_to_show):
                        folders_to_show.append(folder[path_length])
            except:
                continue
    
    total_size = get_total_size()

    return render_template('index.html', files=files, folders=folders_to_show, total_size=total_size)

# this function basicaly dont make folders, but make blank files with path to folder so it will show as empty folder
@app.route('/createfolder', methods=["POST"])
def createfolder():
    if request.method == 'POST':
        foldername = request.json['foldername']
        path = request.json["url"]
        #print(f"creating folder {foldername}...")

        virtual_path = path + foldername + "/"
        #print(virtual_path)

        conn = sqlite3.connect('files.db')
        cur = conn.cursor()

        cur.execute('''
            INSERT INTO files (type, file_name, file_extension, client_path, message_id, virtual_pos) VALUES (?, ?, ?, ?, ?, ?)
        ''', ("single", "blank", "blank", "blank", "blank", virtual_path))

        conn.commit()
        conn.close()

        #with open(json_path, 'r') as file:
            #existing_data = json.load(file)

        #existing_data.append(data)

        #with open(json_path, 'w') as file:
            #json.dump(existing_data, file, indent=2)

        return jsonify({'result': "pixi"})
    
@app.route('/', methods=["GET","POST"])
def index():
    virtualpath = "/"

    if request.method == 'POST':
        files = request.files.getlist('files')
        file_paths = save_files(files)

        for fp in file_paths:
            command = f'py .\\od.py up {fp} {virtualpath}'

            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: {e}")

        sync_index()

        return jsonify({'result': "jej"})
    
    files = []
    conn = sqlite3.connect('files.db')
    cur = conn.cursor()

    cur.execute('SELECT * FROM files')
    rows = cur.fetchall()

    conn.close()

    for f in rows:
        if(f[6] == virtualpath):
            files.append(f)
    
    folders, splited_folders = generate_filestructure()
    folders_to_show = []
    for folder in splited_folders:
        try:
            if(folder[0] not in folders_to_show):
                folders_to_show.append(folder[0])
        except:
            continue

    total_size = get_total_size()

    return render_template('index.html', files=files, folders=folders_to_show, total_size=total_size)

@app.route('/download', methods=['GET'])
def download():
    command = f'py .\\cleaner.py'
    subprocess.run(command, shell=True)

    files = request.args.getlist('file')
    print(files)
    file_extension = ""

    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

    for f in files:

        for local_file in data:
            if(local_file["type"] == "single"):
                if(local_file["message_id"] == f):
                    file_extension = local_file["file_extension"]

        command = f'py .\\od.py down {f}'

        result = subprocess.run(command, shell=True)

        # Check if the subprocess has finished
        if result.returncode == 0:
            print("Subprocess completed successfully")
            file_path = f'./downloads/file_{f}{file_extension}'
            return send_file(file_path, as_attachment=True)
        else:
            print(f"Subprocess failed with exit code {result.returncode}")

        return jsonify({'result': "error"})

@app.route('/remove', methods=['GET'])
def remove():
    command = f'py .\\cleaner.py'
    subprocess.run(command, shell=True)

    files = request.args.getlist('file')

    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

    for f in files:
        for item in data:
            if item['message_id'] == f:
                #data.remove(item)
                print(item)
                break

    return jsonify({'result': "error"})

@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('static/css', filename)



if __name__ == '__main__':
    sync_index()
    app.run(debug=True)
