import cmd
from pyfiglet import Figlet
import os
import sys
from termcolor import colored

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(curr_dir))

from user import *

f = Figlet(font='slant')
print(f.renderText('InterAct'))

# registry = DeviceRegistry()

class InterActTerminal(cmd.Cmd):
    prompt = colored("interact~ ","green", attrs=['bold'])

    def __init__(self):
        super().__init__()
        intro = "\nWelcome to InterAct - Social media for devices!\n"
        print(intro)
        self.curr_device = User(root_usr_dir="./Data")
        self.account_exists = self.curr_device.account_exists
        if not self.account_exists:
            print("Hello there! You seem to be new on the platform.")
            print(f"Let's register you as {colored(self.curr_device.name, 'green')} for now. You can change it later.")
        else:
            print(f"Hey, {colored(self.curr_device.name, 'green')}! What's up?")
        print(f"Type {colored('help', 'grey', attrs=['underline'])} or {colored('?', 'grey', attrs=['underline'])} to see available commands.\n")
    
    def do_contacts(self, arg):
        """Lists your contacts: list of known devices."""


    # def do_register(self, arg):
    #     """Register this device with a name: register <device_name>"""
    #     name = arg.strip()
    #     if not name:
    #         print("Usage: register <device_name>")
    #     else:
    #         registry.register(name)
    #         print(f"Device registered as '{name}'")

    # def do_list(self, arg):
    #     """List all registered devices"""
    #     devices = registry.list_devices()
    #     print("Devices:", ", ".join(devices) if devices else "No devices yet.")

    # def do_discover(self, arg):
    #     """Discover nearby devices"""
    #     devices = discover_devices()
    #     print("Discovered devices:")
    #     for d in devices:
    #         print(f" - {d}")

    # def do_send(self, arg):
    #     """Send file to a device: send <device_name> <file_path>"""
    #     parts = arg.split()
    #     if len(parts) != 2:
    #         print("Usage: send <device_name> <file_path>")
    #         return
    #     device, file_path = parts
    #     file_path = Path(file_path)
    #     if not file_path.exists():
    #         print("Error: file does not exist.")
    #         return
    #     send_file(device, file_path)

    def do_exit(self, arg):
        """Exit the terminal"""
        print("Goodbye!")
        return True
    
if __name__ == "__main__":
    InterActTerminal().cmdloop()
