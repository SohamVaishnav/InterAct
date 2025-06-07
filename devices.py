# Use this to create functions and classes to handle logging of devices in the Social Interact setup.
import os
import sys
import threading
import socket
from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
import datetime
from termcolor import colored

parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)

from user import User

class Radar(object):
    """
    Class to discover online devices. 
    """
    def __init__(self, root_usr_dir: str, curr_device: User):
        """
        Initialises the Radar class for discovering devices. \
        Note that the service type is set to `_interact._tcp.local.` by default, which is used for service discovery in the InterAct platform.

        Args:
            root_usr_dir (str): The root directory where user data is stored.
            curr_device (User): The current user device instance.

        Raises:
            AssertionError: \\
            1. If the `root_usr_dir` does not exist. \\
            2. If the `curr_device` is not an instance of `User`.
        """
        self.devices = []
        self.root_usr_dir = root_usr_dir
        self.curr_device = curr_device
        # with open(os.path.join(self.root_usr_dir, "devices.json"), 'w') as f:
        #     json.dump(self.devices, f, indent=4)

        assert os.path.exists(self.root_usr_dir), "Root user directory does not exist."
        assert isinstance(self.curr_device, User), "Current device must be an instance of User."

        self.service_type = "_interact._tcp.local."
    
    def add_service(self, zeroconf_instance, type, name):
        """
        Adds device to the list of discovered devices. This method is called when a new service is found by the Zeroconf service browser.

        Args:
            zeroconf_instance (Zeroconf): The Zeroconf instance that discovered the service.
            type (str): The type of the service.
            name (str): The name of the service.
        """
        info = zeroconf_instance.get_service_info(type, name)
        if info:
            device = {
                'name': info.name.split('.')[0],
                'ip_address': socket.inet_ntoa(info.address),
                'port': info.port,
                'status': 'online',
                'last_active': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'mode': 'auto'
            }
            self.devices.append(device)
            # print(f"Device {colored(device['name'], 'blue')} at {colored(device['ip_address'], 'cyan')}:{colored(device['port'], 'light_cyan')} found {colored('online', 'green')}.")
            # self.curr_device.update_contacts_status(device['ip_address'], 'online', port=device['port'], last_active=device['last_active'], name=device['name'], mode=device['mode'])
        else:
            return
    
    def remove_service(self, zeroconf_instance, type, name):
        """
        Removes device from the list of discovered devices. This method is called when a service/device goes offline or is removed."

        Args:
            zeroconf_instance (Zeroconf): The Zeroconf instance that discovered the service.
            type (str): The type of the service.
            name (str): The name of the service.
        """
        device_name = name.split('.')[0]
        info = zeroconf_instance.get_service_info(type, name)
        ip_address = socket.inet_ntoa(info.address)
        self.devices = [device for device in self.devices if device['name'] != device_name]
        self.curr_device.update_contacts_status(ip_address, 'offline')
        print(f"Device {colored(device_name, 'blue')} at {colored(ip_address, 'cyan')} just went {colored('offline', 'red')}.")

    
    def update_service(self): 
        """
        Updates device
        """
        pass
    
    def verify(self, device_name: str, ip_address: str, port: int):
        """
        Verifies if the device with the given name, IP address, and port is online.

        Args:
            device_name (str): The name of the device.
            ip_address (str): The IP address of the device.
            port (int): The port of the device.

        Returns:
            bool: True if the device is truly online, False otherwise.
        """
        # try:
        #     socket.setdefaulttimeout(2)
        #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     sock.connect((ip_address, port))
        #     sock.close()
        #     print(f"Device {colored(device_name, 'blue')} at {colored(ip_address, 'cyan')}:{colored(port, 'light_cyan')} is online.")
        #     return True
        # except (socket.timeout, ConnectionRefusedError):
        #     print(f"Device {colored(device_name, 'blue')} at {colored(ip_address, 'cyan')}:{colored(port, 'light_cyan')} is offline or unreachable.")
        #     return False
        info = Zeroconf().get_service_info(self.service_type, device_name + '.' + self.service_type)
        if info:
            ip_address = socket.inet_ntoa(info.address)
            if ip_address == ip_address and info.port == port:
                return True
        print(f"Device {colored(device_name, 'blue')} at {colored(ip_address, 'cyan')}:{colored(port, 'light_cyan')} is offline or unreachable.")
        return False
    
    def show_devices(self):
        """
        Displays the list of discovered devices in a formatted manner. This function is called only when the user wants to see the discovered devices.
        """
        if not self.devices:
            print("No devices discovered yet.")
            return
        
        print("Discovered devices:")
        for device in self.devices:
            print(f" - {colored(device['name'], 'blue')} (IP: {colored(device['ip_address'], 'cyan')}, Port: {colored(device['port'], 'light_cyan')}, Status: {colored(device['status'], 'green')}, Last Active: {device['last_active']}, Mode: {device['mode']})")
        
    def save_devices_as_contacts(self, indices:list):
        """
        Saves the discovered devices as contacts in the current user's contact list based on the indices provided.

        Args:
            indices (list): A list of indices of the devices to be saved as contacts.
        
        Raises:
            AssertionError: If the `indices` list is empty or if any index is out of range of the discovered devices.
        """
        if not self.devices:
            print("No devices discovered yet.")
            return

        assert indices, "Indices list cannot be empty."

        for index in indices:
            assert 0 <= index < len(self.devices), f"Index {index} is out of range for discovered devices."
            device = self.devices[index]
            self.curr_device.update_contacts_status(device['ip_address'], 'online', port=device['port'], last_active=device['last_active'], name=device['name'], mode=device['mode'])
            # print(f"Device {colored(device['name'], 'blue')} at {colored(device['ip_address'], 'cyan')}:{colored(device['port'], 'light_cyan')} saved as contact.")
        print(f"Selected devices have been saved as contacts in your contact list. You can check the contacts using the {colored('show_contacts', 'yellow', attrs=['underlined'])} command.")
        
    def background_process(self):
        """
        Initialises the background process by announcing the current device and starting the service browser for discovering other devices.
        This method is intended to be run in a separate thread to avoid blocking the main thread.

        Raises:
            AssertionError: If the `curr_device` is not an instance of `User`.
        """
    
    def announce(self):
        """
        Announces the current device on the network using Zeroconf. This ensures that the device is online and 
        discoverable by other devices on the InterAct platform.
        """
    
    def browse(self):
        """
        Starts the service browser to discover other devices on the InterAct platform - only those that are online will be discovered.
        """
    
    def threaded_process(self):
        """
        Runs the background process in a separate thread to avoid blocking the main thread.
        """
        
        
c = Radar(root_usr_dir="./Data", curr_device=User(root_usr_dir="./Data"))

