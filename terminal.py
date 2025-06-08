import cmd
from pyfiglet import Figlet
import os
import sys
from termcolor import colored
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import logging

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(curr_dir))

from user import *
from devices import *
from data_sharing import *

f = Figlet(font='slant')
print(f.renderText('InterAct'))

class InterActTerminal(cmd.Cmd):
    prompt = colored("interact~ ","green", attrs=['bold'])

    def __init__(self):
        super().__init__()
        # self.logging_handler()

        intro = "\nWelcome to InterAct - Social media platform for devices!\n"
        print(intro)

        self.curr_device = User(root_usr_dir="./Data")

        self.account_exists = self.curr_device.account_exists
        if not self.account_exists:
            print("Hey! You seem to be new on the platform.")
            print(f"Enter the name of your device - you will be visible to others by this name.")
            new_name = input("Enter your device name: ").strip()
            if new_name:
                self.curr_device.update_user(name=new_name)
            else:
                print("No name entered. Using default name based on IP address.")
                self.curr_device.update_user(name=f'Device_{self.curr_device.ip_address}')
            print("\n")
        print(f"Hey, {colored(self.curr_device.name, 'green')}! What's up?")
        self.curr_device.update_user()
        print(f"Type {colored('help', 'yellow', attrs=['underline'])} or {colored('?', 'yellow', attrs=['underline'])} to see the available commands.\n")

        self.radar = Radar(root_usr_dir="./Data", curr_device=self.curr_device)
        self.data_transferer = DataSharing(root_usr_dir="./Data", curr_device=self.curr_device, radar=self.radar)
        self.initiate_background_processes()
    
    def initiate_background_processes(self):
        """
        Initiates background processes for device discovery and file transfer.
        """
        print("Initiating background processes for device discovery and file transfer...")
        ping_thread = threading.Thread(target=self.radar.pinger,
                                       name='Ping_Thread',
                                       daemon=True).start()
        background_thread = threading.Thread(target=self.data_transferer.background_process,
                                             name='Background_Thread',
                                            daemon=True).start()
        
        self.do_browse(arg='') 
        print("You can now discover nearby devices and share files with them!")

    def check_for_send(self, file_path, receiver_name):
        self.send_file_flag = False
        receiver_info = self.curr_device.get_contacts_by_name(receiver_name)
        if receiver_info.empty:
            print(f"Receiver {colored(receiver_name, 'blue')} not found in contacts. Do you wish to continue? ({colored('y[es]}', 'green')}/{colored('n[o])', 'red')}")
            choice = input().strip().lower()
            if choice != 'y':
                print(colored("File sharing cancelled.", 'red'))
                return None, None
            print(f"Checking for Receiver {colored(receiver_name, 'blue')} availability...")
            
            for device in self.radar.devices:
                if device['name'] == receiver_name:
                    receiver_ip = device['ip_address']
                    receiver_port = device['port']
                    self.send_file_flag = device['status'] == 'online'
                    break
        else:
            print(f"Receiver {colored(receiver_name, 'blue')} found in contacts. Checking availability...")
            self.send_file_flag = (receiver_info['status'] == 'online').values[0]
            receiver_ip = receiver_info['ip_address'].values[0]
            receiver_port = int(receiver_info['port'].values[0])
        if not self.send_file_flag:
            print(f"Receiver {colored(receiver_name, 'blue')} is {colored('offline', 'red')}. Please check the device and try again.")
            return None, None
        
        print(colored("Receiver is online.", 'green'))
        print(f"Initiating file transfer to {colored(receiver_name, 'blue')} at {colored(receiver_ip, 'cyan')}...")

        return receiver_ip, receiver_port
    
    # def do_register(self, arg):
    #     """Register this device with a name: register <device_name>"""
    #     name = arg.strip()
    #     if not name:
    #         print("Usage: register <device_name>")
    #     else:
    #         if self.curr_device.name != name:
    #             self.curr_device.update_user(name=name)
    #             print(f"Device registered as '{colored(name, 'blue')}'")
    #         else:
    #             print(f"Device is already registered as '{colored(name, 'blue')}'")
    
    def do_self_config(self, arg):
        """
        Display your device's IP address.
        """
        print("Details of your device:")
        for index, row in self.curr_device.identify.iterrows():
            print(f" - {colored(row['name'], 'blue')} (IP: {row['ip_address']}, Port: {row['port']}, Status: {row['status']}, Last Active: {row['last_active']}, Mode: {row['mode']})")
        return

    def do_show_contacts(self, arg):
        """
        Lists your contacts: list of known devices.
        """
        self.contacts = self.curr_device.contacts
        if self.contacts.empty:
            print("You have no contacts yet. Discover nearby devices or add them manually.")
        else:
            if self.radar.is_browsing.is_set():
                print("Your contacts:")
                for index, row in self.contacts.iterrows():
                    if row['status'] == 'online':
                        status_color = 'green'
                    else:
                        status_color = 'red'
                    print(f" - {colored(row['name'], 'blue')} (IP: {colored(row['ip_address'], 'cyan')}, Port: {colored(row['port'], 'light_cyan')}, Status: {colored(row['status'], status_color)}, Last Active: {colored(row['last_active'], 'light_yellow')}, Mode: {colored(row['mode'], 'yellow')})")
            else:
                for index, row in self.contacts.iterrows():
                    self.radar.verify(row['name'], row['ip_address'], int(row['port']))

        if not self.radar.is_browsing.is_set():
            print(f"No nearby devices to show because browsing is not active. Use {colored('browse', 'yellow', attrs=['underline'])} to discover devices.")
        else:
            self.radar.show_devices()
    
    def do_browse(self, arg):
        """Discover nearby devices."""
        self.radar.browse()
        print("Browsing...")
    
    def do_stop_browsing(self, arg):
        """Stop discovering devices."""
        self.radar.stop_browsing()
    
    def do_announce(self, arg):
        """
        Announce your device to nearby devices.
        """
        self.radar.announce()
    
    def do_stop_announce(self, arg):
        """
        Stop announcing your device to nearby devices.
        """
        self.radar.stop_announcing()
    
    def do_share(self, arg):
        """
        Share a file with a device: share <device_name> <file_path>
        """
    
    def do_add_manually(self, arg):
        """
        Manually add device to your contacts: add <device_name> <ip_address> <port>
        """
        parts = arg.split()
        if len(parts) != 3:
            print("Usage: add_manual <device_name> <ip_address> <port>")
            return
        device_name, ip_address, port = parts
        device_info = self.curr_device.get_contacts_by_name(device_name)
        if device_info.empty:
            device_reachable = self.radar.verify(device_name, ip_address, int(port))
            if device_reachable:
                self.curr_device.add_manually(device_name, ip_address, port)
                print(f"Device '{colored(device_name, 'blue')}' added to contacts.")
        else:
            print(f"Device '{colored(device_name, 'blue')}' already exists in contacts.")
            self.curr_device.update_contacts_status(ip_address, status='online', port=int(port), name=device_name)
    
    def do_add(self, arg):
        """
        Add a device to your contacts: add <indices>
        """
        if not arg:
            print("Usage: add <indices>")
            print("Example: add 0 1 2")
            return
        indices_str = arg.strip()
        indices = indices_str.split(' ')
        self.radar.save_devices_as_contacts([int(i) for i in indices if i.isdigit()])
    
    def do_send(self, arg):
        """
        Send a file to a device: send <device_name> <file_path>
        """
        parts = arg.split()
        if len(parts) != 2:
            print("Usage: send <device_name> <file_path>")
            return
        receiver_name, file_path = parts

        if not os.path.isfile(file_path):
            print(f"File '{file_path}' does not exist.")
            return
        
        receiver_ip, receiver_port = self.check_for_send(file_path, receiver_name)
        if self.send_file_flag:
            self.data_transferer.file_sharing(file_path, receiver_name, receiver_ip, receiver_port)
    
    def do_ping(self, arg):
        """
        Ping a device to check its availability: ping <device_name> <ip_address> <port>
        """
        parts = arg.split()
        if len(parts) != 3:
            print("Usage: ping <device_name> <ip_address> <port>")
            return
        device_name, ip_address, port = parts
        self.radar.verify(device_name, ip_address, int(port))
    
    def do_clear(self, arg):
        """
        Clear the terminal screen.
        """
        os.system('cls' if os.name == 'nt' else 'clear')

    def do_exit(self, arg):
        """
        Exit the terminal
        """
        self.do_stop_announce(arg='')
        print("Goodbye!")
        return True
    
if __name__ == "__main__":
    InterActTerminal().cmdloop()
