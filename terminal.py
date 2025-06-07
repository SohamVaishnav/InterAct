import cmd
from pyfiglet import Figlet
import os
import sys
from termcolor import colored
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(curr_dir))

from user import *
from devices import *

f = Figlet(font='slant')
print(f.renderText('InterAct'))

word_completer = WordCompleter([
    'register', 'self_config', 'show_contacts', 'discover', 
    'add_manually', 'add', 'clear', 'exit'
    ])
class InterActTerminal(cmd.Cmd):
    prompt = colored("interact~ ","green", attrs=['bold'])

    def __init__(self):
        super().__init__()
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
        print(f"Type {colored('help', 'yellow', attrs=['underline'])} or {colored('?', 'yellow', attrs=['underline'])} to see the available commands.\n")
    
    def do_register(self, arg):
        """Register this device with a name: register <device_name>"""
        name = arg.strip()
        if not name:
            print("Usage: register <device_name>")
        else:
            if self.curr_device.name != name:
                self.curr_device.update_user(name=name)
                print(f"Device registered as '{colored(name, 'blue')}'")
            else:
                print(f"Device is already registered as '{colored(name, 'blue')}'")
    
    def do_self_config(self, arg):
        """Display your device's IP address."""
        print("Details of your device:")
        for index, row in self.curr_device.identify.iterrows():
            print(f" - {colored(row['name'], 'blue')} (IP: {row['ip_address']}, Port: {row['port']}, Status: {row['status']}, Last Active: {row['last_active']}, Mode: {row['mode']})")
        return

    def do_show_contacts(self, arg):
        """Lists your contacts: list of known devices."""
        self.contacts = self.curr_device.contacts
        if self.contacts.empty:
            print("You have no contacts yet. Discover nearby devices or add them manually.")
        else:
            print("Your contacts:")
            for index, row in self.contacts.iterrows():
                print(f" - {colored(row['name'], 'blue')} (IP: {row['ip_address']}, Port: {row['port']}, Status: {row['status']}, Last Active: {row['last_active']})")
        print("Devices discovered:")
        self.do_discover(arg)
    
    def do_discover(self, arg):
        """Discover nearby devices."""
    
    def do_add_manually(self, arg):
        """Manually add device to your contacts: add <device_name> <ip_address> <port>"""
        parts = arg.split()
        if len(parts) != 3:
            print("Usage: add_manual <device_name> <ip_address> <port>")
            return
        device_name, ip_address, port = parts
        self.curr_device.add_manually(device_name, ip_address, port)
        print(f"Device '{colored(device_name, 'blue')}' added to contacts.")
    
    def do_add(self, arge):
        """Add a device to your contacts: add <device_name>"""
    
    def do_clear(self, arg):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def do_exit(self, arg):
        """Exit the terminal"""
        print("Goodbye!")
        return True
    
if __name__ == "__main__":
    InterActTerminal().cmdloop()
