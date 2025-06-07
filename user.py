import os 
import sys
import pandas as pd
import json
import socket
import datetime

class User(object):
    """
    Class representing a user in the system.
    """
    def __init__(self, root_usr_dir:str):
        """
        Initialises the User class for a new user. This class is used to manage everything about the user 
        such as creating the account, updating the account, registering it, getting user stats, etc. 

        Args:
            root_usr_dir (str): The root directory where user data is stored.
        """
        self.root_usr_dir = root_usr_dir
        if not(os.path.exists(self.root_usr_dir)):
            os.makedirs(self.root_usr_dir)
        if not(os.path.exists(self.root_usr_dir + "/users.csv")):
            self.usr_file = pd.DataFrame(columns=['name', 'ip_address', 'port', 'self', 'status', 'last_active', 'mode']).to_csv(os.path.join(self.root_usr_dir, "users.csv"), index=False)
    
        self.usr_file = pd.read_csv(os.path.join(self.root_usr_dir, "users.csv"))
        self.make_all_offline()
        
        self.identify = self.usr_file[self.usr_file['self'] == 1]
        if not self.identify.empty:
            self.account_exists = True
            self.name = self.identify['name'].values[0]
            self.file_transfer_port = self.identify['port'].values[0]
            self.ip_address = self.identify['ip_address'].values[0]
        else:
            self.account_exists = False
            self.name = f'Device_new'
            self.file_transfer_port = 9000
            self.ip_address = self.get_ip()

        self.contacts = self.usr_file[self.usr_file['self'] == 0]

    def __str__(self):
        return f"User(name={self.name}, ip_address={self.ip_address}, port={self.port})"
    
    def get_ip(self):
        """
        Get the local IP address of the device.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1' # loopback address in case of connection failure
        finally:
            s.close()
        return ip

    def make_all_offline(self):
        """
        Sets all the contacts to `offline` status in the user file. 
        """
        if not self.usr_file.empty:
            self.usr_file['status'] = 'offline'
            self.usr_file.loc[self.usr_file['self'] == 1, ['status']] = ['online']
            self.usr_file.to_csv(os.path.join(self.root_usr_dir, "users.csv"), index=False)
    
    def update_user(self, **kwargs):
        """
        Update the user details in the user file.
        """
        if 'name' in kwargs:
            self.name = kwargs['name']
        if 'file_transfer_port' in kwargs:
            self.file_transfer_port = kwargs['file_transfer_port']

        if not self.account_exists:
            new_user = pd.DataFrame({
                'name': [self.name],
                'ip_address': [self.ip_address],
                'port': [self.file_transfer_port],
                'self': [1],
                'status': ['online'],
                'last_active': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                'mode': ['auto']
            })
            self.usr_file = pd.concat([self.usr_file, new_user], ignore_index=True)
            self.account_exists = True
        else:
            self.usr_file.loc[self.usr_file['self'] == 1, ['name', 'ip_address', 'port', 'status', 'last_active']] = [
                self.name, self.ip_address, self.file_transfer_port, 'online', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
        
        self.usr_file.to_csv(os.path.join(self.root_usr_dir, "users.csv"), index=False)
        self.identify = self.usr_file[self.usr_file['self'] == 1]
        self.contacts = self.usr_file[self.usr_file['self'] == 0]
    
    def get_contacts(self):
        """
        Get the contacts of the user.
        """
        return self.contacts

    def get_contacts_by_name(self, name:str):
        """
        Get the contacts of the user by name.
        Args:
            name (str): The name of the contact to search for.
        """
        return self.contacts[self.contacts['name'] == name]

    def update_contacts_status(self, ip_address:str, status:str, **kwargs):
        """
        Updates the status of the contact with the given IP address.

        Args:
            ip_address (str): The IP address of the contact.
            status (str): The new status to set for the contact.
            kwargs: Additional keyword arguments to update other fields (like port, last_active, etc.).
        """
        contact_exists = self.contacts[self.contacts['ip_address'] == ip_address]
        if contact_exists.empty:
            self.add_manually(name=kwargs.get('name', 'Unknown'), ip_address=ip_address, port=kwargs.get('port'), mode=kwargs.get('mode', 'auto'), status=status)
        else:
            self.contacts.loc[self.contacts['ip_address'] == ip_address, 'status'] = status
            if 'port' in kwargs:
                self.contacts.loc[self.contacts['ip_address'] == ip_address, 'port'] = kwargs['port']
            if 'last_active' in kwargs:
                self.contacts.loc[self.contacts['ip_address'] == ip_address, 'last_active'] = kwargs['last_active']
            else:
                self.contacts.loc[self.contacts['ip_address'] == ip_address, 'last_active'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.usr_file = pd.concat([self.identify, self.contacts], ignore_index=True)
            self.urs_file.to_csv(os.path.join(self.root_usr_dir, "users.csv"), index=False)

            self.identify = self.usr_file[self.usr_file['self'] == 1]
            self.contacts = self.usr_file[self.usr_file['self'] == 0]
    
    def add_manually(self, name:str, ip_address:str, port:int, mode:str='manual', status:str='offline'):
        """
        Add a contact manually to the user file.

        Args:
            name (str): The name of the contact.
            ip_address (str): The IP address of the contact.
            port (int): The port of the contact.
        """
        if not self.account_exists:
            raise ValueError("User account does not exist. Please create an account first.")
        
        new_contact = pd.DataFrame({
            'name': [name],
            'ip_address': [ip_address],
            'port': [port],
            'self': [0],
            'status': [status],
            'last_active': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'mode': [mode]
        })
        
        self.usr_file = pd.concat([self.usr_file, new_contact], ignore_index=True)
        self.usr_file.to_csv(os.path.join(self.root_usr_dir, "users.csv"), index=False)

        self.contacts = self.usr_file[self.usr_file['self'] == 0]

    def get_user_stats(self):
        """
        Call to get the user statistics such as number of groups joined, number of connections, etc.
        """
        pass 

    # Add more functions later

# c = User(root_usr_dir="./Data")
# c.get_local_ip()

