#!/usr/bin/python
# -*- Python -*-

from marking  import *
import sqlite3 as sqlite

def initialise_db():
    """Initialise the database tables"""
    connection = sqlite.connect(dbname) 
    cursor = connection.cursor()
    try:
        cursor.execute("DROP TABLE viewing")
        cursor.execute("DROP TABLE votes")
        cursor.execute("DROP TABLE users")
    except:
        pass
	
	# the viewing table records which student stylesheet each user is looking at at the moment
    cursor.execute("CREATE TABLE viewing ( cookie varchar, sid varchar)" )
    cursor.execute("CREATE TABLE votes ( sid varchar, tech integer, look integer, comment varchar )" )
    cursor.execute("CREATE TABLE users ( name varchar, sid varchar, ip varchar, cookie varchar, visits integer )" )
    connection.commit()

                   

def flush_viewing():
    """Flush the viewing table of entries"""
    connection = sqlite.connect(dbname)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM idisd")
    connection.commit()


	
def print_table(cur):
    """print the result of the last query"""

    FIELD_MAX_WIDTH = 20

    if cur.description == None:
        return
    # Print a header.
    for fieldDesc in cur.description:
	print fieldDesc[0].ljust(FIELD_MAX_WIDTH) ,
    print # Finish the header with a newline.
    print '-' * 78

    # For each row, print the value of each field left-justified within
    # the maximum possible width of that field.
    fieldIndices = range(len(cur.description))
    for row in cur:
        for fieldIndex in fieldIndices:
            fieldValue = str(row[fieldIndex])
            print fieldValue.ljust(FIELD_MAX_WIDTH) ,

        print # Finish the row with a newline.	
    print '-' * 78
    print 
	
def list_db():
    """generate a one page listing of the databases"""

    connection = sqlite.connect(dbname)
    cursor = connection.cursor()

    print "VOTES Table"
    cursor.execute("SELECT * from votes ORDER BY sid" )
    print_table(cursor)
	
    print "Scores"
    cursor.execute("SELECT sid, avg(tech) as tech, avg(look) as look from votes group by sid")
    print_table(cursor)

    print "Users Table"
    cursor.execute("SELECT * from users ORDER BY visits")
    print_table(cursor)

    print "Viewing Table"
    cursor.execute("SELECT * from viewing ORDER BY cookie")
    print_table(cursor)
		

    
if __name__=='__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "init":
       initialise_db()
       print "Done"
    else:
       list_db()
 
