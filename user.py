import os 
import sys
import pandas as pd
import json
import argparse

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
            self.usr_file = pd.DataFrame(columns=['name', 'email_id', 'password', 'age', 'education', 'location', 'occupation']).to_csv(os.path.join(self.root_usr_dir, "users.csv"), index=False)
        else:
            self.usr_file = pd.read_csv(os.path.join(self.root_usr_dir, "users.csv"))
        #for now ... might add something later

    def __str__(self):
        return f"User(name={self.name}, email_id={self.email_id})"
    
    def create_account(self, **kwargs):
        """
        Create a new user account with the provided details.

        Args:
            **kwargs: User details such as name, email_id, and password.
        Raises:
            AssertionError: If any required field is missing.
        """
        self.name = kwargs.get('name', self.name)
        self.email_id = kwargs.get('email_id', self.email_id)
        self.password = kwargs.get('password', self.password)
        assert (self.name != None and self.email_id != None and self.password != None), "Name is required to create an account."
        print(f"Welcome, {self.name}!")

    def complete_account(self, **kwargs):
        """
        Update user account details.

        Args:
            **kwargs: Additional user details such as age, education, location, and occupation.
        Raises:
            AssertionError: If any required field is missing.
        """
        print("Updating account details ...")
        self.age = kwargs.get('age', None)
        assert self.age != None,  "Age is required to create an account."

        self.education = kwargs.get('education', None)
        self.education = self.education.lower()
        assert self.education != None, "Education is required to create an account."

        self.location = kwargs.get('location', None)   

        if self.education not in ["school", "college", "university"]:
            self.occupation = kwargs.get('occupation', None)
            assert self.occupation != None, "Since Education is over, Occupation is required to create an account."
        else:
            self.occupation = "Student"
        
    def save_user(self):
        """
        Saves the information about the user to a CSV file and registers the user into the system."
        """
        usr_temp_file_name = f"{self.name}.csv"
        usr_temp_file_path = os.path.join(self.root_usr_dir, usr_temp_file_name)
        usr_temp_file = pd.DataFrame({
            'name': [self.name],
            'email_id': [self.email_id],
            'password': [self.password],
            'age': [self.age],
            'education': [self.education],
            'location': [self.location],
            'occupation': [self.occupation]
        })
        usr_temp_file.to_csv(usr_temp_file_path, index=False)
        self.usr_file = pd.concat([self.usr_file, usr_temp_file], ignore_index=True)
        self.usr_file.to_csv(os.path.join(self.root_usr_dir, "users.csv"), index=False)
    
    def change_profile(self):
        """
        Call to change the profile details of the user.
        """
        pass

    def change_settings(self):
        """
        Call to the change the user settings - permissions, privacy, etc.
        """
        pass
    
    def get_user_stats(self):
        """
        Call to get the user statistics such as number of groups joined, number of connections, etc.
        """
        pass 

    # Add more functions later


