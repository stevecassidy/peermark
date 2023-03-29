'''
Created on Mar 26, 2012

@author: steve
'''

import sqlite3
import os
import csv

class COMP249Db():
    '''
    Provide an interface to the database for a COMP249 web application
    '''


    def __init__(self, dbname="comp249.db"):
        '''
        Constructor
        '''

        self.dbname = dbname
        self.conn = sqlite3.connect(self.dbname)
        ### ensure that results returned from queries are strings rather
        # than unicode which doesn't work well with WSGI
        self.conn.text_factory = str

    def cursor(self):
        """Return a cursor on the database"""

        return self.conn.cursor()

    def commit(self):
        """Commit pending changes"""

        self.conn.commit()

    def delete(self):
        """Destroy the database file"""
        pass

    def encode(self, text):
        """Return a one-way hashed version of the text suitable for
        storage in the database"""

        import hashlib, binascii

        return hashlib.md5(text.encode()).hexdigest()

    def create_tables(self):
        """Create and initialise the database tables
        This will have the effect of overwriting any existing
        data."""


        sql = """
DROP TABLE IF EXISTS users;
CREATE TABLE users (
           email text unique primary key,
           sid text,
           path text,
           hash text
           );

DROP TABLE IF EXISTS sessions;
CREATE TABLE sessions (
            sessionid text unique primary key,
            useremail text,
            viewing text,
            FOREIGN KEY(useremail) REFERENCES users(email)
            FOREIGN KEY(viewing) REFERENCES users(email)
);

DROP TABLE IF EXISTS marks;
CREATE TABLE marks (
            submission text,
            voter text,
            design integer,
            creative integer,
            tech integer,
            feedback text,
            browser text,
            FOREIGN KEY(submission) REFERENCES users(sid),
            FOREIGN KEY(voter) REFERENCES users(email)
);"""

        self.conn.executescript(sql)
        self.conn.commit()

    def import_users(self, paths):
        """Import student accounts
        paths is a dictionary of email-> (sid, password, directory name)
        """

        cursor = self.cursor()

        sql = "INSERT into users (email, sid, path, hash) values (?, ?, ?, ?)"

        usersql = "SELECT email FROM users WHERE email=?"
 
        for (email, (sid, password, dirname)) in paths.items():
                hash = self.encode(password) 

                cursor.execute(usersql, (email,))
                usersid = cursor.fetchone()

                if usersid == None: 
                    cursor.execute(sql, (email, sid, dirname, hash))
                    #print(email, password, hash) 



        self.commit()

if __name__=='__main__':
    # if we call this script directly, create the database and make sample data
    db = COMP249Db()
    db.create_tables()
