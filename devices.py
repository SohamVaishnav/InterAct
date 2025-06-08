# Use this to create functions and classes to handle logging of devices in the Social Interact setup.
import os
import sys
import threading
import socket
from zeroconf import Zeroconf, ServiceBrowser, ServiceInfo
import datetime
from termcolor import colored
import time

parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)

from user import User

class Radar(object):
    """
    Class to discover online devices. 
    """
    def __init__(self, root_usr_dir: str, curr_device: User):
        """
        Initialises the Radar class for discovering devices. \\
        Note that the service type is set to `_interact._tcp.local.` by default, which is used for service discovery in the InterAct platform.
        Also, the ping port has been set to `12346` by default, which is used for pinging devices to ensure their availability.

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
        self.is_discoverable = threading.Event()
        self.is_browsing = threading.Event()
        self.ping_port = 12346
    
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
                'ip_address': socket.inet_ntoa(info.addresses[0]),
                'port': info.port,
                'status': 'online',
                'last_active': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            if device['name'] == self.curr_device.name:
                return
            
            contact_exists = self.curr_device.get_contacts_by_name(device['name'])
            if not contact_exists.empty:
                self.curr_device.update_contacts_status(device['ip_address'], 'online', port=device['port'], last_active=device['last_active'], name=device['name'], mode=contact_exists['mode'].values[0])
            
            existing_device = next((d for d in self.devices if d['ip_address'] == device['ip_address']), None)
            if existing_device:
                for key in device:
                    existing_device[key] = device[key]
            else:
                self.devices.append(device)
            
            # self.curr_device.update_contacts_status(device['ip_address'], 'online', port=device['port'], last_active=device['last_active'], name=device['name'], mode=device['mode'])
            #

            # print(f"\nDevice {colored(device['name'], 'blue')} at {colored(device['ip_address'], 'cyan')}:{colored(device['port'], 'light_cyan')} found {colored('online', 'green')}.")
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
        # info = zeroconf_instance.get_service_info(type, name)
        # ip_address = socket.inet_ntoa(info.address[0])
        device_info = self.curr_device.get_contacts_by_name(device_name)
        if not device_info.empty:
            self.curr_device.update_contacts_status(device_info['ip_address'], 'offline')
            print(f"Device {colored(device_name, 'blue')} at {colored(device_info['ip_address'].values[0], 'cyan')} went {colored('offline', 'red')}.")
        self.devices = [device for device in self.devices if device['name'] != device_name]

    def update_service(self, zeroconf_instance, type, name): 
        """
        Updates device
        """
        self.add_service(zeroconf_instance, type, name)
    
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
        try:
            socket.setdefaulttimeout(2)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip_address, self.ping_port))
            sock.close()
            print(f"Device {colored(device_name, 'blue')} at {colored(ip_address, 'cyan')}:{colored(port, 'light_cyan')} is online.")
            contact_exists = self.curr_device.get_contacts_by_name(device_name)
            if not contact_exists.empty:
                self.curr_device.update_contacts_status(ip_address, 'online', port=port, last_active=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name=device_name, mode=contact_exists['mode'].values[0])
            
            for device in self.devices:
                if device['ip_address'] == ip_address and device['port'] == port:
                    device['status'] = 'online'
                    device['last_active'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            return True
    
        except (socket.timeout, ConnectionRefusedError):
            print(f"Device {colored(device_name, 'blue')} at {colored(ip_address, 'cyan')}:{colored(port, 'light_cyan')} is offline or unreachable.")
            contact_exists = self.curr_device.get_contacts_by_name(device_name)
            if not contact_exists.empty:
                self.curr_device.update_contacts_status(ip_address, 'offline', port=port, last_active=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name=device_name, mode=contact_exists['mode'].values[0])

            for device in self.devices:
                if device['ip_address'] == ip_address and device['port'] == port:
                    device['status'] = 'offline'
                    device['last_active'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
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
            status_color = 'green' if device['status'] == 'online' else 'red'
            print(f" - {colored(device['name'], 'blue')} (IP: {colored(device['ip_address'], 'cyan')}, Port: {colored(device['port'], 'light_cyan')}, Status: {colored(device['status'], status_color)})")
        
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
            assert 0 <= index-1 < len(self.devices), f"Index {index} is out of range for discovered devices."
            device = self.devices[index-1]
            self.curr_device.update_contacts_status(device['ip_address'], 'online', port=device['port'], last_active=device['last_active'], name=device['name'], mode='auto')
            # print(f"Device {colored(device['name'], 'blue')} at {colored(device['ip_address'], 'cyan')}:{colored(device['port'], 'light_cyan')} saved as contact.")
        print(f"Selected devices have been saved as contacts in your contact list. You can check the contacts using the {colored('show_contacts', 'yellow', attrs=['underline'])} command.")
    
    def announce(self):
        """
        Announces the current device on the network using Zeroconf. This ensures that the device is online and 
        discoverable by other devices on the InterAct platform.
        """
        curr_device_info = self.curr_device.identify.iloc[0]
        if curr_device_info.empty:
            print("Current device information is not available. Please register your device first.")
            return
        self.info_ann = ServiceInfo(
            self.service_type,
            f"{curr_device_info['name']}.{self.service_type}",
            addresses=[socket.inet_aton(curr_device_info['ip_address'])],
            port=int(curr_device_info['port']),
            properties={
                'name': curr_device_info['name'],
                'status': curr_device_info['status'],
                'last_active': curr_device_info['last_active'],
                'mode': curr_device_info['mode']
            },
            server=f"{socket.gethostname()}.local."
        )
        self.zeroconf_ann = Zeroconf()
        self.zeroconf_ann.register_service(self.info_ann)
        # print(f"Your device {colored(curr_device_info['name'], 'blue')} is now online and discoverable.")
        self.is_discoverable.set()
    
    def browse(self):
        """
        Starts the service browser to discover other devices on the InterAct platform - only those that are online will be discovered.
        """
        # self.announce() if not self.is_discoverable.is_set() else None
        self.announce()
        self.zeroconf_browse = Zeroconf()
        self.service_browser = ServiceBrowser(self.zeroconf_browse, self.service_type, self)
        # print("Starting to browse for devices on the InterAct platform...")
        self.is_browsing.set()
    
    def stop_browsing(self):
        """
        Stops the service browser. The current device will still remain discoverable on other devices.
        """
        if not self.is_browsing.is_set():
            print("No active service browser to stop.")
            return
        self.is_browsing.clear()
        if self.zeroconf_browse:
            self.zeroconf_browse.close()
            self.service_browser.cancel()
            self.zerconf_browse = None
            print("Stopped discovering devices on the InterAct platform.")
        
    def stop_announcing(self):
        """
        Stops the announcement of the current device on the network. This makes the device no longer discoverable by other devices.
        """
        if not self.is_discoverable.is_set():
            print("Your device is already undiscoverable.")
            return
        self.is_discoverable.clear()
        if self.zeroconf_browse:
            print("Stopping the service browser before unregistering the service.")
        self.stop_browsing()
        if self.zeroconf_ann:
            self.zeroconf_ann.unregister_service(self.info_ann)
            self.zeroconf_ann.close()
            self.zeroconf_ann = None
            print("Your device is now off-the-grid.")
    
    def pinger(self):
        """
        Pings the other device to ensure its availability.        
        """
        ping_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ping_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            ping_socket.bind(('', self.ping_port))
            ping_socket.listen(1)
            while True:
                connection, address = ping_socket.accept()
                connection.close()
        except OSError as e:
            print(f"Socket error: {e}. Ping port might be already in use. Please try a different port.")
        except KeyboardInterrupt:
            print("Stopping the ping server.")
        except Exception as e:
            print(f"An error occurred while starting the ping server: {e}")
        finally:
            ping_socket.close()
        
# c = Radar(root_usr_dir="./Data", curr_device=User(root_usr_dir="./Data"))

