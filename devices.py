# Use this to create functions and classes to handle logging of devices in the Social Interact setup.
import os
import sys
import threading
import socket
from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange

parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)

from user import User

class Radar(object):
    """
    Class to discover online devices. 
    """
    def __init__(self, root_usr_dir: str, curr_device: User):
        """
        Initialises the Radar class for discovering devices.

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

        assert os.path.exists(self.root_usr_dir), "Root user directory does not exist."
        assert isinstance(self.curr_device, User), "Current device must be an instance of User."

    def discover(self, port, service_type="_interact._tcp.local."):
        """
        Discover nearby devices and update the list.

        Returns:
            list: List of discovered devices.
        """
        
        

