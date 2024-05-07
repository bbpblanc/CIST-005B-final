"""Main class with a Command Line Interface to interact with the 
Facebook-like underlying graph (using a SQL data structure and sqlite infrastructure)"""

__author__ = "Bertrand Blanc (Alan Turing)"


import sys
import argparse
from profiles import *
from person import Person
import logging


class CLIError(Exception):
    pass

class Main():
    """Main class called when the program is run"""
    NAME_LENGTH = 100

    def __init__(self, *args):
        logging.basicConfig(filename="main.log",
                            filemode="w",
                            level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

        self.profiles = Profiles()
        self.parser = None
        if len(*args) == 0:
            args = [['-h']]


        self._parse()
        self.args = self.parser.parse_args(*args)
        self.logger.info("arguments properly parsed")
        self._check()
        self.logger.info("arguments properly checked")
        self._dispatch()
        self.logger.info("arguments properly processed")


    def _parse(self):
        self.parser = argparse.ArgumentParser(
            prog = "main.py",
            description="manipulate social network data",
            epilog="Hope you like it"
        )
        self.parser.add_argument('--author', help="Author of the utility", action="store_true")
        self.parser.add_argument('--first-name', '-fn', help="firstname", action="store")
        self.parser.add_argument('--last-name', '-name', '-ln', help="last name", action="store")
        self.parser.add_argument('--add-profile', help="add a profile to the DB", action="store", metavar="dob:<str>,phone:<str>")
        self.parser.add_argument('--remove-profile', help="remove a profile from the DB", action="store_true")
        self.parser.add_argument('--modify-profile', help="modify data from a profile", action="store", metavar="firstname|lastname|phone|dob:<str>")
        self.parser.add_argument('--add-friend', help="firstname/lastname for the friend to add", action="store", metavar="firstname/lastname")
        self.parser.add_argument('--remove-friend', help="firstname/lastname for the friend to remove", action="store", metavar="firstname/lastname")
        self.parser.add_argument('--show', '-s', '--display', help="display the data for the profile", action="store_true")
        
        self.parser.add_argument('--dump', '-d', help="display all profiles", action="store_true")

    def _check(self):
        # basic checks
        if self.args.author:
            return

        if self.args.dump:
            return

        if self.args.first_name is None or self.args.last_name is None:
            raise CLIError('--first-name and --last-name are both compulsory')
        
        if self.args.add_profile:
            if not (0 <= len(self.args.first_name) < Main.NAME_LENGTH):
                raise CLIError(f'first name expected to have a length in [0,{Main.NAME_LENGTH}[')
            
            if not (0 <= len(self.args.last_name) < Main.NAME_LENGTH):
                raise CLIError(f'last name expected to have a length in [0,{Main.NAME_LENGTH}[')
            
            if self.args.add_profile is None or len(self.args.add_profile.split(',')) != 2:
                raise CLIError('phone:value,dob:value format expected')
            
            for pair in self.args.add_profile.split(','):
                field,value=pair.split(':')
                if not field in ['phone', 'dob']:
                    raise CLIError(f'"{field}" is invalid. phone and dob only')
                if not (0 < len(value) <= Main.NAME_LENGTH):
                    raise CLIError(f'"{field}" value shall be positive, up to {Main.NAME_LENGTH} characters')
            return

        if self.args.remove_profile:
            return

        if self.args.add_friend:
            if self.args.add_friend is None or len(self.args.add_friend.split('/')) != 2:
                raise CLIError('firstname/lastname format expected')
            return

        if self.args.remove_friend:
            if self.args.remove_friend is None or len(self.args.remove_friend.split('/')) != 2:
                raise CLIError('firstname/lastname format expected')
            return

        if self.args.modify_profile:
            if self.args.modify_profile is None or len(self.args.modify_profile.split(':')) != 2:
                raise CLIError('new data:new_value format expected. data = firstname|lastname')
            
            if not self.args.modify_profile.split(':')[0] in ['firstname', 'lastname', 'email', 'phone', 'dob']:
                raise CLIError('new data:new_value format expected. data = firstname|lastname')
            
            return

        if self.args.show:
            return

        self.parser.parse_args(['-h'])


    def _dispatch(self):
        if self.args.author:
            self._author()
            self._terminate()

        if self.args.dump:
            self._dump()
            self._terminate() 


        if self.args.add_profile:
            self._add_profile()
            self._terminate()

        if self.args.remove_profile:
            self._remove_profile()
            self._terminate()

        if self.args.modify_profile:
            self._modify_profile()
            self._terminate()

        if self.args.add_friend:
            self._add_friend()
            self._terminate()

        if self.args.remove_friend:
            self._remove_friend()
            self._terminate()

        if self.args.show:
            self._display()
            self._terminate()


    def _author(self):
        print('Bertrand Blanc (Alan Turing)')

    def _add_profile(self):
        with self.profiles as profiles:
            try:
                data = {}
                for pair in self.args.add_profile.split(','):
                    field, value = pair.split(':')
                    data[field] = value

                person = Person(self.args.first_name, self.args.last_name, **data)
                profiles.add_profile(person)
            except ProfileAlreadyPresent as e:
                self.logger.error(e, exc_info=True)
                print(e)

    def _remove_profile(self):
        with self.profiles as profiles:
            try:
                profiles.remove_profile(Person(self.args.first_name, self.args.last_name))
            except ProfileNotPresent as e:
                self.logger.error(e, exc_info=True)
                print(e)

    def _modify_profile(self):
        with self.profiles as profiles:
            try:
                person = Person(self.args.first_name, self.args.last_name)
                profiles.get_profile(person)
            except ProfileNotPresent as e:
                self.logger.error(e, exc_info=True)
                print(e)
                return
            
            update_data = self.args.modify_profile.split(':')

            profiles.modify_profile(person,update_data[0],update_data[1] )


    def _add_friend(self):
        with self.profiles as profiles:
            try:
                person = Person(self.args.first_name, self.args.last_name)
                profiles.get_profile(person)
            except ProfileNotPresent as e:
                self.logger.error(e, exc_info=True)
                print(e)
                return
            
            try:
                friend_data = self.args.add_friend.split('/')
                friend = Person(friend_data[0], friend_data[1])
                profiles.get_profile(friend)
            except ProfileNotPresent as e:
                self.logger.error(e, exc_info=True)
                print(e)
                return

            profiles.add_friend(person,friend)


    def _remove_friend(self):
        with self.profiles as profiles:
            try:
                person = Person(self.args.first_name, self.args.last_name)
                profiles.get_profile(person)
            except ProfileNotPresent as e:
                self.logger.error(e, exc_info=True)
                print(e)
                return
            
            try:
                friend_data = self.args.remove_friend.split('/')
                friend = Person(friend_data[0], friend_data[1])
                profiles.get_profile(friend)
            except ProfileNotPresent as e:
                self.logger.error(e, exc_info=True)
                print(e)
                return

            profiles.remove_friend(person,friend)

    def _display(self):
        with self.profiles as profiles:
            try:
                person = Person(self.args.first_name, self.args.last_name)
                profiles.get_profile(person)
            except ProfileNotPresent as e:
                self.logger.error(e, exc_info=True)
                print(e)
                return
            
            friends = profiles.get_friends(person)
            print(f'{person.firstname} {person.lastname}, {person.phone}, {person.dob}:')
            if len(friends) == 0:
                print('   has not friend')
            else:
                for friend in friends:
                    print(f'   {friend.firstname} {friend.lastname}')

    def _dump(self):
        with self.profiles as profiles:
            for person, friends in profiles.dump():
                print(f'{person.id:03d} - {person.firstname} {person.lastname}, {person.phone}, {person.dob}')
                for friend in friends:
                    print(f'    friend: {friend.firstname} {friend.lastname}, {friend.phone}, {friend.dob}')


    def _terminate(self,exit_=0):
        exit(exit_)

if __name__ == "__main__":
    try:
        Main(sys.argv[1:])
    except Exception as e:
        logging.error(e, exc_info=True)
        print(e)

    exit(-2)
