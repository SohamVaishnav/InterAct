import os
import sys
import pandas as pd
import socket
import threading
from datetime import datetime
from termcolor import colored
from tqdm import tqdm

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(curr_dir))

from user import User
from devices import Radar

class DataSharing(object):
    """
    Class to manage data sharing between devices.
    """
    def __init__(self, root_usr_dir:str, curr_device:User, radar:Radar, file_packet_size:int=1024*64):
        """
        Initializes the DataSharing class.

        Args:
            root_usr_dir (str): The root directory where user data is stored.
            curr_device (User): The current device user. Defaults to None.
            radar (Radar): The radar instance for discovering other devices.
            file_packet_size (int): The size of each packet for file transfer. Defaults to 64KB.
        """
        self.root_usr_dir = root_usr_dir
        self.curr_device = curr_device
        self.radar = radar

        assert isinstance(self.curr_device, User), "curr_device must be an instance of User"
        assert isinstance(self.radar, Radar), "radar must be an instance of Radar"
        assert os.path.exists(self.root_usr_dir), "Root user directory does not exist"
        assert isinstance(file_packet_size, int) and file_packet_size > 0, "file_packet_size must be a positive integer"

        self.file_packet_size = file_packet_size
        self.received_files_dir = os.path.join(self.root_usr_dir, "received_files")
        if not os.path.exists(self.received_files_dir):
            os.makedirs(self.received_files_dir)
            print(f"Created directory for received files: {colored(self.received_files_dir, 'green')}")
    
    def file_receiving(self, sender_socket, sender_address):
        """
        Handles the incoming data from the sender device.

        Args:
            sender_socket (socket.socket): The socket object for the sender.
            sender_address (tuple): The address of the sender device.
        """
        sender_ip, sender_port = sender_address
        threading.current_thread().name = f"Receiving_Thread-{sender_ip}:{sender_port}"
        sender_info = self.curr_device.get_contacts_by_ip(sender_ip)
        if sender_info:
            print(f"Sender identified as {colored(sender_info['name'], 'blue')} at {colored(sender_ip, 'cyan')}:{colored(sender_port, 'light_cyan')}")
        else:
            print(f"Sender not in your contacts. Identified at {colored(sender_ip, 'cyan')}:{colored(sender_port, 'light_cyan')}")

        try:
            meta_data = sender_socket.recv(self.file_packet_size)
            if not meta_data:
                print(f"Sender {colored('disconnected', 'red')}. No metadata received.")
                sender_socket.close()
                return
            meta_data = meta_data.decode('utf-8').split('|', 2) # metadata format: "filename|filesize|sender_name"
            if len(meta_data) == 3:
                filename, filesize, sender_name = meta_data
                filesize = int(filesize)

                if not sender_info:
                    print(f"Unknown sender name found in metadata - {colored(sender_name, 'blue')}.")
                if sender_info and sender_info['name'] != sender_name:
                    print(f"Sender name {colored('mismatch', 'red')}: {colored(sender_info['name'], 'blue')} vs {colored(sender_name, 'yellow')}. Using metadata sender name.")
                print(f"Receiving file '{colored(filename, 'yellow')}' ({colored(str(filesize), 'light_yellow')} bytes) from {colored(sender_name, 'blue')}.")
            else:
                print("Sender name not provided in metadata. Naming sender using IP Adress.")
                filename, filesize = meta_data[0], int(meta_data[1])
                sender_name = f"Unknown_({sender_ip})"
            received_file_dir_for_sender = os.path.join(self.received_files_dir, sender_name)
            if not os.path.exists(received_file_dir_for_sender):
                os.makedirs(received_file_dir_for_sender)
            filename = os.path.basename(filename)
            received_file_path = os.path.join(received_file_dir_for_sender, filename)

            filesize_loop = tqdm(range(0, filesize, self.file_packet_size), desc=f"Receiving {filename} from {sender_name}", unit='B')
            received_size = 0
            with open(received_file_path, 'wb') as f:
                for _ in filesize_loop:
                    data = sender_socket.recv(self.file_packet_size)
                    if not data:
                        print(f"Connection lost while receiving {filename}.")
                        break
                    f.write(data)
                    filesize_loop.update(len(data))
                    received_size += len(data)
            if received_size == filesize:
                print(f"File '{colored(filename, 'yellow')}' received successfully from {colored(sender_name, 'blue')}.")
            else:
                print(f"File '{colored(filename, 'yellow')}' received with {colored('incomplete data', 'red')}. Expected {colored(str(filesize), 'light_yellow')} bytes but received {colored(str(received_size), 'light_yellow')} bytes.")
            
        except (socket.error, ConnectionResetError) as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"Unexpected error while receiving file: {e}")
        except (KeyboardInterrupt, SystemExit):
            print("File transfer interrupted by user.")
        finally:
            sender_socket.close()
            print(f"Connection with {colored(sender_name, 'blue')} closed.")

    
    def background_process(self):
        """
        Initialises the background process by making the device ready to accept files. 
        This method is intended to be run in a separate thread to avoid blocking the main thread.

        Raises:
            AssertionError: If the `curr_device` is not an instance of `User`.
        """
        assert isinstance(self.curr_device, User), "curr_device must be an instance of User"
        print(f"Your device {colored(self.curr_device.name, 'blue')} is ready to accept files.")
        usr_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        usr_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            usr_socket.bind(('', self.curr_device.file_transfer_port)) # Bind to all network interfaces on the specified port
            usr_socket.listen(5)
            print(f"Listening for incoming file transfers on {colored(self.curr_device.file_transfer_port, 'light_cyan')}...")

            while True:
                sender_socket, sender_address = usr_socket.accept()
                threading.Thread(target=self.file_receiving, args=(sender_socket, sender_address), 
                                 name=f"Receiving_Thread-{sender_address[0]}:{sender_address[1]}",
                                 daemon=True).start()
        except KeyboardInterrupt:
            print("Stopping the file transfer server.")
        except OSError as e:
            print(f"Socket error: {e}. This port might be already in use. Please try a different port.")
        except Exception as e:
            print(f"An error occurred while starting the file transfer server: {e}")
        finally:
            usr_socket.close()
            print("File transfer server closed.")
    
    def file_sharing(self):
        """
        Handles the file sharing process between two devices.
        """

    
