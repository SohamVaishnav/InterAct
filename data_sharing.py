import os
import sys
import pandas as pd
import socket
import threading
from datetime import datetime
from termcolor import colored
from tqdm import tqdm
from zeroconf import Zeroconf
import time

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(curr_dir))

from user import User
from devices import Radar

class DataSharing(object):
    """
    Class to manage data sharing between devices.
    """
    def __init__(self, root_usr_dir:str, curr_device:User, radar:Radar, file_packet_size:int=1024*4):
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
        self.service_type = "_interact._tcp.local."
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
        print(f"Sender identified at {colored(sender_ip, 'cyan')}:{colored(sender_port, 'light_cyan')}")
        
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
            if os.path.exists(received_file_path):
                print(f"{colored('WARNING:', 'red')} File '{colored(filename, 'yellow')}' already exists. Overwriting it.")

            received_size = 0
            with open(received_file_path, 'wb') as f:
                with tqdm(total=filesize, desc=f"Receiving {filename} from {sender_name}", unit='B', 
                          unit_scale=True, unit_divisor=1024) as filesize_loop:
                    while received_size < filesize:
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
        print(f"Background processes initiated.\n")
        print(f"Your device {colored(self.curr_device.name, 'blue')} is online, discoverable and browsing on the {colored('InterAct Platform', 'magenta', attrs=['bold'])}.")
        usr_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        usr_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            usr_socket.bind(('', self.curr_device.file_transfer_port)) # Bind to all network interfaces on the specified port
            usr_socket.listen(5)
            # print(f"Listening for incoming file transfers on {colored(self.curr_device.file_transfer_port, 'light_cyan')}...")

            while True:
                sender_socket, sender_address = usr_socket.accept()
                threading.Thread(target=self.file_receiving, args=(sender_socket, sender_address), 
                                 name=f"Receiving_Thread-{sender_address[0]}:{sender_address[1]}",
                                 daemon=True).start()
        except KeyboardInterrupt:
            print("Stopping the file transfer server.")
        except OSError as e:
            print(f"Socket error: {e}. File transfer port might be already in use. Please try a different port.")
        except Exception as e:
            print(f"An error occurred while starting the file transfer server: {e}")
        finally:
            usr_socket.close()
            print("File transfer server closed.")
    
    def file_sharing(self, filepath:str, receiver_name:str, receiver_ip:str, receiver_port:int):
        """
        Handles the file sharing process between two devices.

        Args:
            filepath (str): The path to the file to be shared.
            receiver_name (str): The name of the receiver device.
            receiver_ip (str): The IP address of the receiver device.
            receiver_port (int): The port number of the receiver device.
        
        Raises:
            FileNotFoundError: If the specified file does not exist.
        """
        assert os.path.exists(filepath), f"File {filepath} does not exist."
        assert isinstance(receiver_name, str) and receiver_name, "receiver_name must be a non-empty string"

        receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            receiver_socket.connect((receiver_ip, receiver_port))
            print(f"Connected to {colored(receiver_name, 'blue')} at {colored(receiver_ip, 'cyan')}:{colored(receiver_port, 'light_cyan')}.")
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            metadata = f"{filename}|{filesize}|{self.curr_device.name}"
            receiver_socket.sendall(metadata.encode('utf-8'))
            # time.sleep(0.1)
            print(colored("Metadata sent.", 'green'))

            sent_size = 0
            with open(filepath, 'rb') as f:
                with tqdm(total=filesize, desc=f"Sending {filename} to {receiver_name}", unit='B', 
                                     unit_scale=True, unit_divisor=1024) as filesize_loop:
                    while True:
                        data = f.read(self.file_packet_size)
                        if not data:
                            break
                        receiver_socket.sendall(data)
                        filesize_loop.update(len(data))
                        sent_size += len(data)
            print(colored(f"File '{colored(filename, 'yellow')}' sent successfully to {colored(receiver_name, 'blue')}.", 'green'))
        except (socket.error, ConnectionResetError) as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"Unexpected error while sending file: {e}")
        finally:
            receiver_socket.close()
            print(f"Connection with {colored(receiver_name, 'blue')} closed.")

        



    
