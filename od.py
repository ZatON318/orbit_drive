from telethon import TelegramClient
import json, os, sys, subprocess
from tqdm import tqdm
from datetime import datetime

#lib for .env
from dotenv import load_dotenv
load_dotenv()

api_id = os.environ.get("API_ID") 
api_hash = os.environ.get("API_HASH") 
client = TelegramClient('anon', api_id, api_hash)

output_folder = "./downloads/"
safe = int(os.environ.get("GROUP_CHAT_ID")) 

index_file = "./odrive_sync/files_index.json"
stats_index = "./odrive_sync/stats_index.json"

async def update_total_size(value_to_increase):
    with open(stats_index, 'r') as file:
        data = json.load(file)

    data['total_size'] = data['total_size'] + value_to_increase

    with open(stats_index, 'w') as file:
        json.dump(data, file, indent=2)

    print("Drive stats updated.")

async def upload_file(file_path):
    
    total_size = os.path.getsize(file_path)
    response = None

    with tqdm(total=total_size, unit='B', unit_scale=True, desc='Uploading') as bar:
        def callback(current, total):
            bar.update(current - bar.n)

        response = await client.send_file(safe, file_path, progress_callback=callback)
        print(response)
    
    return response.id


async def download(messid):
    print(safe)
    print(api_id)
    message = await client.get_messages(safe, ids=messid)
    file_name = "untitled"

    with open(index_file, 'r') as file:
        existing_data = json.load(file)

        for f in existing_data:
            if (f["type"] == "single"):
                if (f["message_id"] == str(messid)):
                    file_name = f"file_{messid}{f["file_extension"]}"
            else:
                print("error multi file not supported yet")

    

    output_path = os.path.join(output_folder, file_name)
    if message.media:
        await client.download_media(message.media, file=output_path)


async def upload(file_path, file_virtual_pos):
    try:
        with open(index_file, 'r') as file:
            existing_data = json.load(file)

        file_exists = False
        for f in existing_data:
            if (f["type"] == "single"):
                if (f["client_path"] == file_path):
                    file_exists = True
            else:
                for p in f["client_paths"]:
                    if(p == file_path):
                        file_exists = True

        if(file_exists):
            print(f"{file_name} --- file already uploaded")
        else:
            print("file not uploaded, uploading...")
            file_size = os.path.getsize(file_path)
            print(file_size)


            if file_size > 2 * 1024 * 1024 * 1024:

                file_name, file_extension = os.path.splitext(os.path.basename(file_path))

                directory = os.path.dirname(file_path)
                compressed_file_name = file_name + file_extension
                full_file_path = os.path.join(directory, compressed_file_name)

                #print(compressed_file_name)

                command = ["7z", "a", "-v1900m", f"{full_file_path}.7z", file_path]

                subprocess.run(command, check=False)
                print(f"Archive {compressed_file_name}.7z created successfully. ")

                all_files = os.listdir(directory)
                part_files = [file for file in all_files if compressed_file_name in file]

                file_parts = {}
                for index, part in enumerate(part_files):
                    if(part == compressed_file_name):
                        part_files.pop(index)

                for index, part in enumerate(part_files):
                        file_parts[index] = part

                print(file_parts)

                client_paths = {}
                returnids = []
                for index, part in enumerate(part_files):
                    client_paths[index] = os.path.join(directory, part)
                    print(client_paths[index])

                    returned = await upload_file(client_paths[index])
                    returnids.append(returned)

                data = {
                    "type": "multi",
                    "file_name": f"{file_name}",
                    "file_names": f"{file_parts}",
                    "file_extension": ".7z",
                    "client_paths": f"{client_paths}",
                    "message_ids": f"{returnids}",
                    "virtual_pos": f"{file_virtual_pos}",
                    "size": f"{file_size}"
                }
                await update_total_size(file_size)

                try:
                    with open(index_file, 'r') as file:
                        existing_data = json.load(file)
                except FileNotFoundError:
                    existing_data = []

                existing_data.append(data)

                with open(index_file, 'w') as file:
                    json.dump(existing_data, file, indent=2)

            else:
                print("The file is not larger than 2 gigabytes. Uploading directly...")

                retid = await upload_file(file_path)

                print("File uploaded, adding to index...")
                
                file_name, file_extension = os.path.splitext(os.path.basename(file_path))

                data = {
                        "type": "single",
                        "file_name": f"{file_name}",
                        "file_extension": f"{file_extension}",
                        "client_path": f"{file_path}",
                        "message_id": f"{retid}",
                        "virtual_pos": f"{file_virtual_pos}",
                        "size": f"{file_size}"
                }
                await update_total_size(file_size)

                with open(index_file, 'r') as file:
                    existing_data = json.load(file)

                existing_data.append(data)

                with open(index_file, 'w') as file:
                    json.dump(existing_data, file, indent=2)
    except Exception as e:
        print(f"Error: {e}")

if len(sys.argv) >= 3:
    # Access the first argument (index 1)
    first_argument = sys.argv[1]
    second_arg = sys.argv[2]
    print("First argument:", first_argument)

    if(first_argument == "down"):
        with client:
            client.loop.run_until_complete(download(int(second_arg)))
    elif(first_argument == "up"):
        with client:
            client.loop.run_until_complete(upload(sys.argv[2],sys.argv[3]))
else:
    print("No arguments provided.")

