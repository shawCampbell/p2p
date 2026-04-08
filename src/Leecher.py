# Code for llecher

from socket import *
import threading
import json
import os
import time
import random
import hashlib
import queue

serverName = 'localhost'
serverPort = 12000

clientSocket = socket(AF_INET,  SOCK_DGRAM)

#message = input('Input lowercase sentence:')

def send_UDP_tracker(message):
    """ Send the tracker a UDP message """

    #message = input('Input lowercase sentence:')
    clientSocket.sendto(message.encode(),  (serverName, serverPort))
    response_Message, serverAddress =  clientSocket.recvfrom(2048)
    message = json.loads(response_Message.decode()) 
    print(message['code'])
    return message


def send_message(message):
    """ Send Some JSON message to tracker over UDP """

    json_message = json.dumps(message)

    return send_UDP_tracker(json_message)

def register_with_server():
    """ Register Leecher with Server """

    user_id = rand = random.randint(1, 1000)

    # Leecher Register request message
    message = {
        "code": "register_request",
        "client_type": "leecher",
        "peer_id": user_id  # Unique ID for this leecher
    }

    send_message(message)

def worker(filename, IP, port, start, stop, chunk_file, result_queue):
    """ Function for threads that download file chunks """
    leecher_socket = socket(AF_INET, SOCK_STREAM)

    try:
        leecher_socket.connect((IP, port+50))

        # Send range request
        range_request = f"RANGE {filename} {start} {stop}\n"
        leecher_socket.sendall(range_request.encode())

        # Recieve Checksum
        checksum = leecher_socket.recv(1024).decode()
        print("checksum: ", checksum)

        # Receive data (assumes fixed size for now, could be adapted to dynamic length)
        expected_size = stop - start
        received_data = leecher_socket.recv(expected_size)

        # Save received chunk to file
        with open(chunk_file, 'wb') as file:
            file.write(received_data)

        print(f"[+] Received {len(received_data)} bytes from {IP}:{port}")

    except Exception as e:
        print(f"[!] Error receiving from {IP}:{port}: {e}")

    finally:
        leecher_socket.close()
        #print(checksum)
        result_queue.put(checksum)

def request_file(filename, event):
    """ Function to send request file message to tracker """

    # Leecher request file message
    message = {
        "code": "FR",
        "filename": filename,
        "client_type": "leecher",

    }


    response = send_message(message)
    print(response["file_seeders"])
    print("file size: ", response["size"])
    seeders = response["file_seeders"]
    size = response["size"]
    if (seeders == []):
        print("No available seeders. Try again later.")
        return 0
    num_seeders = len(seeders)
    chunk_size = size/num_seeders

    #leecher_socket = socket(AF_INET, SOCK_STREAM)
    #print("Attempting to connect to: ", seeders[0][0], ", ", seeders[0][1])
    #leecher_socket.connect((seeders[0][0], seeders[0][1]))

    threads = []

    i=0
    chunkfilearr = []
    checksum = 0
    for seeder in seeders:
        result_queue = queue.Queue()
        chunk_file = 'received_chunk'+str(i)+'.dat'
        chunkfilearr.append(chunk_file)
        start = int(i*chunk_size)
        stop = int((i+1)*chunk_size)
        thread = threading.Thread(target=worker, args=(filename, seeder[0], seeder[1], start, stop, chunk_file, result_queue))
        threads.append(thread)
        thread.start()
        checksum = result_queue.get()
        i+=1

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Combine all received chunks into a final file
    with open("download"+filename, 'wb') as target_file:
        for chunk in chunkfilearr:
            print(f"[+] Appending {chunk}")
            with open(chunk, 'rb') as source_file:
                target_file.write(source_file.read())
            os.remove(chunk)

    print("Comparing: ",checksum, str(hashlib.md5(open("download"+filename,'rb').read()).hexdigest()))

    state = (checksum == str(hashlib.md5(open("download"+filename,'rb').read()).hexdigest()))

    if (not(state)):
        print("Something went wrong. Try again")

    free_seeders(seeders, state)

    transition = input("If not already, would you like to become a Leecher? (Y/N):\n")
    if (transition == 'Y'):
        event.set()
        time.sleep(1)

def free_seeders(seeders, state):
    """ Function to send tracker list of seeders to free after download """

    # Leecher Free Seeders Request
    message = {
        "code": "free_seeders",
        "seeders": seeders,
        "client_type": "leecher",
        "checksum": state

    }

    print("Telling Server to free Seeders: ")
    print(seeders)

    response = send_message(message)
    print(response["code"])





def run_leecher(event=None):
    """ Main method for leecher """

    # register with tracker
    usr = input("Register with Server? (Y/N)\n")
    if (usr == 'Y'):
        register_with_server()
        #response = listen(source_ip, source_port)
        #print(response['code'])
    else:
        exit()

    while(True):
        filename = input("Enter a file you want:\n")

        # request file
        request_file(filename, event)


    

#run_leecher()
