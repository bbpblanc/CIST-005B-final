"""Data related to a Person.
The underlying graph is labelled, using (firstname,lastname) as the label
"""

__author__ = "Bertrand Blanc (Alan Turing)"

class Person():
    """A person for whom a profile will be created"""
    def __init__(self, firstname, lastname, phone=None, dob=None):
        self.data = {'firstname':firstname.capitalize(), 'lastname':lastname.capitalize(), 'phone':phone, 'dob':dob}
        self._id = None

    @property
    def firstname(self):
        return self.data['firstname']
    @property
    def lastname(self):
        return self.data['lastname']

    @property
    def id(self):
        return self._id
    
    @id.setter
    def id(self, id):
        self._id = id
    
    @property
    def phone(self):
        return self.data['phone']
    
    @phone.setter
    def phone(self, value):
        self.data['phone'] = value

    @property
    def dob(self):
        return self.data['dob']

    @dob.setter
    def dob(self, value):
        self.data['dob'] = value
    
    def __str__(self):
        return f"({self._id}, {self.data['firstname']}, {self.data['lastname']}, , {self.data['phone']}, , {self.data['dob']})"
