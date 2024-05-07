"""Graph manipulation using a sqlite database to represente the graph G=(V,E), with
V: vertices or nodes for the profiles
E: edges or links for the friendship relationships between profiles
The edges are bidirectional.
"""

__author__ = "Bertrand Blanc (Alan Turing)"
__all__ = ['Profiles', 'ProfileAlreadyPresent', 'ProfileNotPresent']


from person import Person
import sqlite3 as sql
import logging

# https://docs.python.org/3/library/sqlite3.html
# https://www.sqlite.org/
# https://www.sqlitetutorial.net/


class ProfileAlreadyPresent(Exception):
    """Exception if a profile is already registered"""
    def __init__(self, person:Person):
        self.person = person

    def __str__(self):
        return f'"{self.person.firstname.capitalize()} {self.person.lastname.capitalize()}" already registered'

class ProfileNotPresent(Exception):
    """Exception if a profile is not registered"""
    def __init__(self, person:Person):
        self.person = person

    def __str__(self):
        return f'"{self.person.firstname.capitalize()} {self.person.lastname.capitalize()}" not registered'


class Profiles():
    """bidirectional graph of profiles and friendships"""

    # name of the local persistent database
    DBNAME = "profiles.sqlite"

    def __init__(self, *, reset=False):
        FORMAT = '%(asctime)s %(message)s'
        logging.basicConfig(filename="profiles.log",
                            filemode="w",
                            level=logging.DEBUG,
                            format=FORMAT)
        self.logger = logging.getLogger(__name__)

        try:
            self.connection = sql.connect(Profiles.DBNAME)
        except Exception as e:
            self.logger.fatal(e, exc_info=True)
            raise e
        
        self.cursor = self.connection.cursor()

        if reset:
            self.cursor.execute('DROP TABLE IF EXISTS Profiles')
            self.cursor.execute('DROP TABLE IF EXISTS Befriend')
            self.logger.info("tables removed")

        self._create()


    # couple of compulsory methods to implement the "with" PY operator
    def __enter__(self):
        return self
    def __exit__(self, *args, **kargs):
        self.connection.close()

    def _create(self):
        query = """    
            CREATE TABLE IF NOT EXISTS Profiles (
                id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
                lastname VARCHAR(100) NOT NULL,
                firstname VARCHAR(100) NOT NULL,
                phone VARCHAR(100),
                dob VARCHAR(100),
                UNIQUE (firstname,lastname)
            )
        """
        self.cursor.execute(query)

        query = """    
            CREATE TABLE IF NOT EXISTS Befriend (
                id_f1 INTEGER NOT NULL,
                id_f2 INTEGER NOT NULL,
                FOREIGN KEY (id_f1)
                    REFERENCES Profiles(id)
                FOREIGN KEY (id_f2)
                    REFERENCES Profiles(id)
                CHECK (id_f1 <> id_f2)
                UNIQUE (id_f1,id_f2)
            )
        """
        self.cursor.execute(query)
        self.connection.commit()
        self.logger.info("tables created")
    

    def add_profile(self, person:Person):
        """Add a profile (aka add a new vertex)"""

        query = """
            SELECT id
            FROM Profiles
            WHERE firstname = ? and lastname = ?
        """
        params = (person.firstname, person.lastname)

        db_data = self.cursor.execute(query, params)
        data = db_data.fetchone()

        if data is None:
            query = """
                INSERT OR IGNORE
                INTO Profiles(firstname,lastname,phone,dob)
                VALUES(?,?,?,?)
            """
            params = (person.firstname, person.lastname, person.phone, person.dob)
            self.cursor.execute(query, params)
            self.connection.commit()

            self.get_profile(person)
            self.logger.info(f'profile "{person.firstname} {person.lastname}" created')
            return
        
        raise ProfileAlreadyPresent(person)


    def get_profile(self, person:Person):
        """Retrieve a profile based on (firstname, lastname) label"""

        if person.id is not None:
            return

        query = """
            SELECT id,phone,dob
            FROM Profiles
            WHERE firstname = ? AND lastname = ?
        """

        data_db = self.cursor.execute(query, (person.firstname, person.lastname))
        data = data_db.fetchone()
        if data is None:
            raise ProfileNotPresent(person)
        
        person.id = data[0]
        person.phone = data[1]
        person.dob = data[2]


    def add_friend(self, person:Person, friend:Person):
        """Add a friendship relationship (aka new edge between two profiles)"""
        self.get_profile(person)
        self.get_profile(friend)

        query = """
            INSERT OR IGNORE
            INTO Befriend(id_f1,id_f2)
            VALUES(?,?)
        """
        self.cursor.execute(query, (person.id, friend.id))
        self.connection.commit()
        

    def get_friends(self, person:Person):
        """Retrieve the friends for a given person"""
        self.get_profile(person)

        query = """
            SELECT Profiles.id, Profiles.firstname, Profiles.lastname
            FROM Profiles,Befriend
            WHERE Befriend.id_f1 = ?1 AND Profiles.id = Befriend.id_f2
                OR Befriend.id_f2 = ?1 AND Profiles.id = Befriend.id_f1
            ORDER BY firstname ASC
        """
        data = self.cursor.execute(query, (person.id,)).fetchall()
        friends = []
        for id_,firstname,lastname in data:
            friends.append(Person(firstname,lastname))
            friends[-1].id = id_
        
        return friends
        
    def remove_profile(self, person:Person):
        """Remove a profile (aka remove a vertex)"""
        self.get_profile(person)
        
        query = """
            DELETE
            FROM Profiles
            WHERE id = ?
        """
        self.cursor.execute(query, (person.id,))
        self.connection.commit()

        query = """
            DELETE
            FROM Befriend
            WHERE id_f1 = ?1 OR id_f2 = ?1
        """
        self.cursor.execute(query, (person.id,))
        self.connection.commit()


    def remove_friend(self, person:Person, friend:Person):
        """Remove a friendship (aka remove an edge)"""
        self.get_profile(person)
        self.get_profile(friend)

        query = """
            DELETE
            FROM Befriend
            WHERE id_f1 = ?1 AND id_f2 = ?2
                OR  id_f1 = ?2 AND id_f2 = ?1
        """
        self.cursor.execute(query, (person.id,friend.id))
        self.connection.commit()


    def modify_profile(self, person:Person, field, value):
        """Update the data for a profile"""
        
        self.get_profile(person)

        query = f"""
            UPDATE OR IGNORE Profiles
            SET {field} = ?1
            WHERE id = ?2
        """
        self.cursor.execute(query, (value, person.id))
        self.connection.commit()


    def dump(self):
        """Displays all profiles"""

        query = """
            SELECT id,firstname,lastname,phone,dob
            FROM Profiles
            ORDER BY firstname ASC, lastname ASC
        """
        data = self.cursor.execute(query).fetchall()
        result = []
        for id_,firstname,lastname,phone,dob in data:
            result.append((Person(firstname, lastname, phone, dob),[]))
            result[-1][0].id = id_
            query = """
                SELECT id,firstname,lastname,phone,dob
                FROM Profiles, Befriend
                WHERE id_f1 = ?1 AND id_f2 = id OR id_f1 = id AND id_f2 = ?1
                ORDER BY firstname ASC, lastname ASC
            """
            friends = self.cursor.execute(query, (id_,)).fetchall()
            for fid_,ffirstname,flastname,fphone,fdob in friends:
                result[-1][1].append(Person(ffirstname, flastname, fphone, fdob))

        return result
    

