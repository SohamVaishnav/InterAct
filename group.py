import os
import sys
import pandas as pd
import json
import argparse

from user import *

class Group(object):
    """
    Class used for construction, management, and interaction of groups.
    """
    def __init__(self, root_grp_dir:str, root_usr_dir:str):
        """
        Initialises the Group class for a new group. This class is used to manage everything about the group 
        such as creating the group, updating the group, registering it, getting group stats, etc. 

        Args:
            root_grp_dir (str): The root directory where group data is stored.
            root_usr_dir (str): The root directory where user data is stored.
        """
        self.root_grp_dir = root_grp_dir
        if not(os.path.exists(self.root_grp_dir)):
            os.makedirs(self.root_grp_dir)
        if not(os.path.exists(self.root_grp_dir + "/groups.csv")):
            self.grp_file = pd.DataFrame(columns=['name', 'description', 'members']).to_csv(os.path.join(self.root_grp_dir, "groups.csv"), index=False)
        else:
            self.grp_file = pd.read_csv(os.path.join(self.root_grp_dir, "groups.csv"))

        self.usr_dir = root_usr_dir
        self.user_class = User(self.usr_dir)

        last_grp = self.grp_file.tail(1)
        if not last_grp.empty:
            self.grp_id = int(last_grp.index[-1]) + 1
        else:
            self.grp_id = 0

        self.name = f"Group_{self.grp_id}"
        self.tagline = "A new group!"
        self.members = []
        self.max_num_members = 10

    def __str__(self):
        return f"Group(name={self.name} \n tagline={self.tagline} \n members={self.members})"
    
    def create_group(self, **kwargs):
        """
        Create a new group with the provided details.

        Args:
            **kwargs: Group details such as name, description, and maximum number of members.
        Raises:
            AssertionError: If any required field is missing.
        """
        self.name = kwargs.get('name', self.name)
        self.tagline = kwargs.get('tagline', self.tagline)
        self.max_num_members = kwargs.get('max_num_members', self.max_num_members)

        for key, value in kwargs.items():
            if key != 'max_num_members':
                print(f"Since maximum number of members is not defined, the group will have a maximum of {self.max_num_members} members.")
            if key != 'name':
                print(f"Group name is required to create a group. Since name is not defined, the group will be named as {self.name}.") 
            if key != 'tagline':
                print(f"Group tagline is required to create a group. Since tagline is not defined, the group tagline is kept as '{self.tagline}'.")
        print("Note: Any of the above fields can be changed later in the group settings.")

    def complete_group(self, **kwargs):
        """
        Update group details.

        Args:
            **kwargs: Additional group details such as description and members.
        Raises:
            AssertionError: If any required field is missing.
        """
        pass

    def add_members(self, *args):
        """
        Add members to the group.

        Args:
            *args: Usernames of the members to be added.
        Raises:
            AssertionError: If the maximum number of members is exceeded.
        """
        pass

    def save_group(self):
        """
        Saves the group information to a CSV file.
        """
        pass

    def set_roles(self, **kwargs):
        """
        Set roles for members in the group.

        Args:
            **kwargs: Member usernames and their corresponding roles.
        Raises:
            AssertionError: If any required field is missing.
        """
        pass

    def set_member_permissions(self, **kwargs):
        """
        Set permissions for members in the group.

        Args:
            **kwargs: Member usernames and their corresponding permissions.
        Raises:
            AssertionError: If any required field is missing.
        """
        pass

    def change_settings(self):
        """
        Call to change the group settings - permissions, privacy, members-limit, roles, etc.
        """
        pass
    
    def change_profile(self):
        """
        Call to change the profile details of the group.
        """
        pass

    def data_sharing(self):
        """
        Call to manage data sharing settings for the group. \
        This includes datatypes to be shared, data sharing permissions, regulations, etc.
        """
        pass

    def community_memberships(self):
        """
        Call to manage community memberships for the group. \
        This includes joining communities, leaving communities, and managing community settings.
        """
        pass

    def get_group_stats(self):
        """
        Call to get the group statistics such as number of members, number of posts or activities in general, etc.
        """
        pass

