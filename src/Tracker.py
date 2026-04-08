# Tracker Code

from socket import *
import threading
import json
import os

lock = threading.Lock()

# global dictionary for seeders:
seeders = {}

# global dictionary for seeders
leechers = {}

# glocal list of busy seeders
busy_seeders = []

def return_capitalised_UDP():
    """ The UDP example we saw in class """
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('', serverPort))
    print("The server is ready to receive")
    while True:
        message, clientAddress = serverSocket.recvfrom(2048)
        modifiedMessage = message.decode().upper()
        serverSocket.sendto(modifiedMessage.encode(),
        clientAddress)

def send_UDP_message(socket, clientAddress, message):
    """ Function to send a string over UDP to client """
    eval(socket).sendto(message.encode(),
                clientAddress)

def send_message(socket, clientAddress, message):
    """ Send Some JSON message to tracker over UDP """

    json_message = json.dumps(message)

    send_UDP_message(socket, clientAddress, json_message)

def handle_message(clientAddress, data):
    """ Handle various UDP messages coming from clients """
    try:
        message = json.loads(data.decode())  # Convert JSON string back to dictionary
        #print((message["code"] == "update_request") and (message["client_type"] == "seeder"))

        if (message["code"] == "register_request") and (message["client_type"] == "seeder"):
            return register_seeder(clientAddress, message)
        elif (message["code"] == "register_request") and (message["client_type"] == "leecher"):
            return register_leecher(clientAddress, message)
        elif (message["code"] == "update_request") and (message["client_type"] == "seeder"):
             return update_seeder(clientAddress, message)
        elif (message["code"] == "free_seeders"):
             return free_seeders(message)
        else:
             return 0
            
    except json.JSONDecodeError:
        print("Error: Received invalid JSON data")

def register_seeder(clientAddress, message):
            """ Function for registering seeder """
            peer_id = message["peer_id"]  # Unique identifier (IP:Port)
            available_files = message["available_files"]
            client_type = message["client_type"]

            # Store the seeder info in the dictionary
            seeders[peer_id] = {
                "client_type": client_type,
                "available_files": available_files,
                "IP": clientAddress[0],
                "Port": clientAddress[1]
            }

            print(f"Registered Seeder: {peer_id} with data: {seeders[peer_id]}\n")

            # Tracker registration success response message
            response_message = {
                "code": "request_success"
            }

            json_message = json.dumps(response_message)

            return json_message

def update_seeder(clientAddress, message):
            """ Function for registering seeder """
            
            if (did_seeder_change(message)):   
                print("Updater:") 
                # delete old seeder in dictionary
                
                del seeders[message["peer_id"]]


                peer_id = message["peer_id"]  # Unique identifier (IP:Port)
                available_files = message["available_files"]
                client_type = message["client_type"]

                # Store the seeder info in the dictionary
                seeders[peer_id] = {
                    "client_type": client_type,
                    "available_files": available_files,
                    "IP": clientAddress[0],
                    "Port": clientAddress[1]
                }

                print(f"Updated Seeder: {peer_id} with data: {seeders[peer_id]}\n")

                # Tracker update success message
                response_message = {
                    "code": "update_success"
                }

                json_message = json.dumps(response_message)

                return json_message
            return 0

def did_seeder_change(message):
     user_id = message["peer_id"]
     available_files = message["available_files"]
     if (seeders[user_id]["available_files"] == available_files):
          return False
     return True


def register_leecher(clientAddress, message):
            """ Function for registering leecher """
            peer_id = message["peer_id"]  # Unique identifier (IP:Port)
            client_type = message["client_type"]

            # Store the seeder info in the dictionary
            leechers[peer_id] = {
                "client_type": client_type,
                "IP": clientAddress[0],
                "Port": clientAddress[1]
            }

            print(f"Registered Leecher: {peer_id} with data: {leechers[peer_id]}")

            response_message = {
                "code": "request_success"
            }

            json_message = json.dumps(response_message)

            print(clientAddress)
            print("\n")

            return json_message

            #send_message(source_ip, clientAddress, response_message)

def handle_file_request(data):
     """ Function for handling file requests """
     message = json.loads(data.decode()) 
     if (message['code'] == 'FR'):

        file_seeders = find_seeders_for_file(seeders, message['filename'])

        # add seeders to busy seeders list for now
        busy_seeders.append(file_seeders)
        print("Busy seeders upon request:", busy_seeders)

        size = get_file_size_from_seeders(seeders, message['filename'])

        # Tracker file request response
        response_message = {
            "code": "available_seeders",
            "file_seeders": file_seeders,
            "size": size
        }

        json_message = json.dumps(response_message)

        return json_message


     2


     return 0

def find_seeders_for_file(seeders, file_name):
    """ Returns a list of (IP, Port) tuples for seeders that have the specified file. """
    matching_seeders = []

    for seeder_name, seeder_data in seeders.items():
        available_files = [file[0] for file in seeder_data.get("available_files", [])]  # Extract only file names
        if file_name in available_files:  # Check if file exists in the list
            matching_seeders.append((seeder_data["IP"], seeder_data["Port"]))
    # remove all of the busy seeders
    for seeder in busy_seeders:
         matching_seeders.remove(seeder)

    return matching_seeders

def get_file_size_from_seeders(seeders, file_name):
    """ Returns the size of one instance of the specified file from the first seeder that has it. """
    for seeder_data in seeders.values():
        for available_file in seeder_data.get("available_files", []):
            if available_file[0] == file_name:  # Check if file name matches
                return available_file[1]  # Return file size of one instance
    return None
     
def free_seeders(message):
     """ Function to free seeders when recievng free seeders message from leecher """
     print("Current Busy Seeders:")
     print(busy_seeders)
     for seeder in message["seeders"]:
          for busy in busy_seeders:
            #print("Seeder[0]: ", seeder[0], ", busy[0]: ", busy[0][0])
            if seeder[0] == busy[0][0]:
                busy_seeders.remove(busy)
     print("Busy Seeders after download: ")
     print(busy_seeders)

     print("Download Success: ",message["checksum"])

     if (not(message["checksum"])):
        response = "**Something went wrong. Try again.**"
     else:
        response = "**Download Success**"

     # Tracker download complete message
     response_message = {
            "code": response,
        }

     json_message = json.dumps(response_message)

     return json_message
     

def start_tracker():
    """ Starts the tracker to receive various client messages. """
    tracker_ip = "0.0.0.0"  # Listen on all interfaces
    tracker_port = 12000

    with socket(AF_INET, SOCK_DGRAM) as tracker_socket:
        tracker_socket.bind((tracker_ip, tracker_port))
        print(f"Tracker running on {tracker_ip}:{tracker_port}")

        while True:
            data, client_address = tracker_socket.recvfrom(4096)  # Receive UDP message

            # register client 
            registration_out = handle_message(client_address, data)
            if (registration_out != 0):
                if(registration_out != None):
                    tracker_socket.sendto(registration_out.encode(),
                        client_address)
            
            # respond to download request
            download_out = handle_file_request(data)
            if (download_out != 0):
                 tracker_socket.sendto(download_out.encode(),
                    client_address)




start_tracker()