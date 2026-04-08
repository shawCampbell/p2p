# Seeder Code

from socket import *
import random
import json
import threading
import os
import time
import hashlib #****** IMPORT HASHING MODULE

serverName = 'localhost'
serverPort = 12000

clientSocket = socket(AF_INET,  SOCK_DGRAM)
clientSocket.settimeout(3.0)

def send_UDP_tracker(message):
    """ Function to send a string over UDP to tracker """

    #message = input('Input lowercase sentence:')
    clientSocket.sendto(message.encode(),  (serverName, serverPort))
    #modifiedMessage, serverAddress =  clientSocket.recvfrom(2048)
    #print(modifiedMessage.decode())
    #clientSocket.close()

def register_with_server_seeder():
    """Function to register with tracker to be a Seeder"""
    #files = available_files()
    directory = input("Enter the directory path of the files you want to share: ").strip()
    files = list_files_with_sizes(directory)
    rand = random.randint(1, 1000)
    #user_id = "user:"+str(rand)


    # Seeder register request
    message = {
        "code": "register_request",
        "client_type": "seeder",
        "available_files": files,
        "peer_id": "user:"+str(rand)  # Unique ID for this seeder
    }

    # Convert to JSON string
    json_message = json.dumps(message)

    # Send the message via UDP
    send_UDP_tracker(json_message)

    return rand, directory

    

def available_files():
    """Function that returns array of files in a directory"""
    # Prompt user for the directory containing shared files
    shared_directory = input("Enter the directory path of the files you want to share: ").strip()

    # Validate that the directory exists
    if not os.path.isdir(shared_directory):
        print("Error: Directory does not exist.")
        return []

    # Get the list of files in the directory
    shared_files = [f for f in os.listdir(shared_directory) if os.path.isfile(os.path.join(shared_directory, f))]

    if not shared_files:
        print("No files found in the directory.")
        return []

    #print("Files available for sharing:", shared_files)

    return shared_files

def list_files_with_sizes(directory):
    """ Returns a list of tuples containing file names and their sizes in bytes. """
    #directory = input("Enter the directory path of the files you want to share: ").strip()

    try:
        files_with_sizes = [(f, os.path.getsize(os.path.join(directory, f))) 
                            for f in os.listdir(directory) 
                            if os.path.isfile(os.path.join(directory, f))]
        return files_with_sizes
    except Exception as e:
        print(f"Error: {e}")
        return []

def handle_download(directory, ip, port):
    """ Function to send chunk of file to leecher """
    seeder_socket = socket(AF_INET, SOCK_STREAM)
    seeder_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    #print("Binding to port: ", ip, ", ", port)
    seeder_socket.bind((ip, port))
    seeder_socket.listen(1)

    #*****


    #print("Seeder is ready, waiting for connections...")
    conn, addr = seeder_socket.accept()
    #print(f"Connected to leecher at {addr}")

    # Read range request (e.g., "RANGE 1000 2000")
    range_request = conn.recv(1024).decode().strip()
    #print(f"Received range request: {range_request}")

    _, filename, start, end = range_request.split()  # Extract start & end

    # send checksum
    checksum = str(hashlib.md5(open(directory+"/"+filename,'rb').read()).hexdigest())
    #print("checksum:", checksum)
    conn.sendall(checksum.encode())
    time.sleep(1)

    start, end = int(start), int(end)

    # Read that portion from file
    with open(directory+"/"+filename, 'rb') as file:
        file.seek(start)
        chunk = file.read(end - start)

    # Send the requested chunk
    conn.sendall(chunk)
    #
    # print(f"Sent {len(chunk)} bytes.")

    conn.close()
    seeder_socket.close()

def update_with_server_seeder(user_id, directory):
    """ Function to update tracker on current files available to share every five seconds"""
    time.sleep(3)
    while(True):
        #print("updating...")
        time.sleep(5)
        #files = available_files()
        #directory = input("Enter the directory path of the files you want to share: ").strip()
        files = list_files_with_sizes(directory)
        #rand = random.randint(1, 1000)


        # Seeder update request
        message = {
            "code": "update_request",
            "client_type": "seeder",
            "available_files": files,
            "peer_id": "user:"+str(user_id)# Unique ID for this seeder
        }

        # Convert to JSON string
        json_message = json.dumps(message)

        #print("sending update message")
        send_UDP_tracker(json_message)
        #print("sent update message")

def start_seeder():
    """ Start seeder in idle state"""

    user_name, directory = register_with_server_seeder()
    update_thread = threading.Thread(target=update_with_server_seeder, args=(user_name,directory)) # thread to update server about director
    update_thread.start() # update sever every second
    ip, port = clientSocket.getsockname()
    while True:
        #print("Waiting for Download Requests")
        handle_download(directory, ip, port+50)
        #data, client_address = clientSocket.recvfrom(4096)

