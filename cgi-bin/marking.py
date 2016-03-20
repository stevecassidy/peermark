#!/usr/bin/python
# -*- Python -*-
"""randomcss.cgi is used as part of the COMP249 peer marking scheme. It
delivers a random CSS stylesheet in response to a random key sent by the browser
while recording the key and the student id of the stylesheet in a database. """

import cgi
import cgitb; cgitb.enable()
import os
import random
import sqlite3 as sqlite

from Cookie import SimpleCookie
from time import strftime

SUBMITTED_CSS_NAME = "clt.css"

MAXVISITS = 10

prefix = "/home/staff/comp/cassidy/peermark/"
prefix = "/Users/steve/Documents/courses/comp249/2010/Assignment_1_CSS_Design/"

# the base directory of the submitted stylesheets, this dir should
# contain one directory per student named for the student ID
basedir = prefix
logfile = prefix + "peermark.log"

# The database will be stored here
dbname = prefix + "peermark.db"

badstylesheet ="""
body {
  background-color: green;
  color: red;
}
h1:before {
  content: "ALL YOUR BASE ARE BELONG TO US!!!!!" 
}
* {
  text-decoration: blink;
}
"""   

userCookie = None

def select_sid ():
    """Select a student id  at random from those submitted"""

    files = os.listdir(basedir)
#    user = get_current_user()
#    files.remove(user) 
    return random.choice(files)


def get_stylesheet(sid):
    """Read the stylesheet for the student sid and return the text"""
    stylesheet = basedir + "/" + sid + "/" + SUBMITTED_CSS_NAME
    try:
        s = open(stylesheet, "r")
        content = s.read()
        s.close()
        return content
    except:
        return ""

def record_cookie_sid(sid, cookie):
    """Record in the database that cookie is associated with SID"""
    connection = sqlite.connect(dbname)
    cursor = connection.cursor()

    # need to ensure this is a unique mapping, remove any existing entries
    # with this id
    cursor.execute("DELETE FROM viewing WHERE cookie=?", (cookie,))
    # now add the new entry
    cursor.execute("INSERT INTO viewing VALUES (?,?)", (cookie,sid) )
    connection.commit()


def sid_from_cookie(cookie):
    """Given a cookie value, find the sid associated with it in the dbase"""
    connection = sqlite.connect(dbname)
    cursor = connection.cursor()
    cursor.execute("SELECT sid FROM viewing WHERE cookie=?", (cookie, ))
    results = cursor.fetchall()

    if len(results) == 0:
        # need to select a sid for this person
        sid = select_sid()
        record_cookie_sid(sid, cookie)
        return sid
    
    # could be more than one but shouldn't be, 
    if len(results) > 1:
        raise CgiException
    else:
        return results[0][0]


def user_from_cookie(cookie):
    """Given a cookie value, find the user associated with it in the dbase"""
    connection = sqlite.connect(dbname)
    cursor = connection.cursor()
    cursor.execute("SELECT sid FROM users WHERE cookie=?", (cookie, ))
    results = cursor.fetchall()

    if len(results) == 0:
        return None
    
    # could be more than one but shouldn't be, 
    if len(results) > 1:
        return None
    else:
        return results[0][0]

        

def record_vote(form) :
    """Record a vote for a stylesheet"""

    connection = sqlite.connect(dbname)
    cursor = connection.cursor() 
    cookieval = makeCookie()
         
    if  form.has_key("tech") and form.has_key("look") and form.has_key("comment"):

        tech = form.getvalue("tech")
        look = form.getvalue("look")
        comment = form.getvalue("comment")
    
       
        sid = sid_from_cookie(cookieval)
    
        # record a vote for sid    
        cursor.execute("INSERT INTO votes VALUES (?,?,?,?)", (sid, tech, look, comment))
        # remove the association with this stylesheet so we don't vote again
        cursor.execute("DELETE FROM viewing WHERE cookie=?", (cookieval,))       
        
        connection.commit()
        # record the visit in the visits table
        recordVisit()
    else:
        # can't record a vote since we have no id
        # ok just to do nothing
        pass
    
    # if we've voted too many times, say so, otherwise process the votes
    if voted_too_often():
        too_many_votes()
        # remove this user from viewing so we don't show any more stylesheets
        cursor.execute("DELETE FROM viewing WHERE cookie=?", (cookieval,))       
        return
            
    output_voteform()

def voted_too_often():
    """Return True if this user has voted too often"""
    
    connection = sqlite.connect(dbname)
    cursor = connection.cursor() 
    cookieval = makeCookie()
    
    user = user_from_cookie(cookieval)
    cursor.execute("SELECT visits FROM users WHERE sid = ?", (user,))
    result = cursor.fetchone() 
    if result != None:
        visits = result[0]
        return result > MAXVISITS
    else:
        return False

    
def output_voteform():
    """Output the voting form page"""

    votepage = """
<html>
<head>
<title>Voting Frame</title>
<link rel='stylesheet' type='text/css' href='../peer.css'>
<script language="javascript" src="../peermark.js"></script>
</head>

<body onload="reloadMainFrame()">
 


    <p id="help">Don't Cheat! <a target='_blank' href='../peermark/help.html'>Help</a></p>

<form name="vote" action="marking.py" method="POST">
<table>

  <tr>  
  <td><b>Visual Appearance</b></td>
  <td style="text-align: right">Poor</td>
  <td class="radio"><input type="radio" name="look" value="1">1</input></td>
  <td class="radio"><input type="radio" name="look" value="2">2</input></td>
  <td class="radio"><input type="radio" name="look" value="3">3</input></td>
  <td class="radio"><input type="radio" name="look" value="4">4</input></td>
  <td class="radio"><input type="radio" name="look" value="5">5</input></td>
  <td style="text-align: left">Good</td> 
  
  <td rowspan='3'><label>Feedback for the student</label><br><textarea name='comment'></textarea></td>
  
  <td rowspan='3'><input type="submit" value="Vote"/></td>
  </tr>

  <tr></tr>
  <tr>  
  <td><b>Use of Technology</b></td>
  <td style="text-align: right">Poor</td>
  <td class="radio"><input type="radio" name="tech" value="1">1</input></td>
  <td class="radio"><input type="radio" name="tech" value="2">2</input></td>
  <td class="radio"><input type="radio" name="tech" value="3">3</input></td>
  <td class="radio"><input type="radio" name="tech" value="4">4</input></td>
  <td class="radio"><input type="radio" name="tech" value="5">5</input></td>
  <td style="text-align: left">Good</td> 
  </tr>

  
  
  

  </table>
  </input>
</form>
</body> 
</html>
"""
    if voted_too_often():
        too_many_votes()
    else:
        header = str(userCookie) + "\nContent-Type: text/html\n\n"
        print header +  votepage
        

def too_many_votes():
    """Output a page for someone who's voted too many times already"""
    
    
    page = """
<html>
<head>
<title>Voting Frame</title>
<link rel='stylesheet' type='text/css' href='../peer.css'>
<script language="javascript" src="../peermark.js"></script>
</head>

<body onload="">

<p>Thanks, you've voted as many times as you're allowed. Please go
and work on Assignment 2!</p>

</body> 
</html>
"""
    header = "Content-Type: text/html\n\n"
    print header + page
    
    
    
    

def output_login(message = ""):
    """Output the login form page"""

    votepage = """
<html>
<head>
<title>Voting Frame</title>
<link rel='stylesheet' type='text/css' href='../peer.css'>
<script language="javascript" src="../peermark.js"></script>
</head>

<body onload="showHelpMainFrame()">
<p class="message">%s</p>
<p id="help"><a target='_blank' href='../peermark/help.html'>Help</a></p
>

<form name="vote" action="marking.py?mode=login" method="POST">
<table width="100%%">
  <tr>
    <td><label>Your Student ID: <input name='sid'></td>
  </tr>
  <tr><td><label>Your Name: <input name='name'></td></tr>
  <tr><td><input type='submit'/></td></tr>
  </table>
</form>

</body> 
</html>
""" 

    header = "Content-Type: text/html\n\n"
    print header +  votepage % message
     

    
def handle_login(form):
    """Handle the submission of a login form"""
    
    if form.has_key('name') and form.has_key('sid'):
        name = form.getvalue('name')
        sid = form.getvalue('sid')
        # get the IP address from the headers
        if os.environ.has_key("REMOTE_ADDR"):
            ipaddr = os.environ["REMOTE_ADDR"]
        else:
            ipaddr = "hidden"
            
        # check that this is a student, look for their submission
        if get_stylesheet(sid) == "":
            output_login("Unknown Student ID")
            return
            
        connection = sqlite.connect(dbname)
        cursor = connection.cursor()           
        
        # check that they haven't logged in already
        cursor.execute("SELECT name FROM users WHERE sid=?", (sid,))
        result = cursor.fetchall()
        if len(result) > 0:
            output_login("This student has already logged in")
            return
            
            
        # make a cookie for this person
        cookie = makeCookie()
        # and add them to our database
        

        cursor.execute("INSERT INTO users VALUES (?,?,?,?,0)", (name, sid, ipaddr, cookie))
        connection.commit()
        
        # now output the main frame
        output_voteform()
    else:
        output_login()
    

    
def have_cookie():
    """Return True if our cookie has been sent, False otherwise."""
    
    if os.environ.has_key("HTTP_COOKIE"):
        userCookie = SimpleCookie(os.environ["HTTP_COOKIE"])
        if userCookie.has_key("id"):
            return True
    return False
   
    
def makeCookie():
   """Generate a cookie if there wasn't one passed to us already
      if there was one, consume it."""

   global userCookie
  
   if os.environ.has_key("HTTP_COOKIE"):
        userCookie = SimpleCookie(os.environ["HTTP_COOKIE"])
        if userCookie.has_key("id"):
           return userCookie["id"].value
   
   # no good cookie found so generate a new one
   userCookie = SimpleCookie()
   userCookie["id"] = randomidentifier()
   userCookie["id"]["max-age"] = str(60*60*24*10) # 10 day cookie
   
   return userCookie["id"].value

def recordVisit():
    """Record a visit from a cookie carrier in the visits table"""

    value = userCookie["id"].value

    connection = sqlite.connect(dbname)
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET visits = visits+1 WHERE cookie=?", (value,))

    connection.commit()


def randomidentifier():
    "Generate a random identifier"
    alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    id = ""
    for i in range(5):
        id += random.choice(alpha)
    id += "-"
    if os.environ.has_key("REMOTE_ADDR"):
        remote_addr = os.environ["REMOTE_ADDR"]
    else:
        remote_addr = "0.0.0.0"
    id += str(remote_addr)
    return id


def log():
    """write a log file entry"""
    global userCookie
    if not os.environ.has_key('QUERY_STRING'):
        return
    h = open(logfile, "a")
    if userCookie != None:
        h.write(strftime("[%a, %d %b %Y %H:%M:%S]")+"\t'"+os.environ["QUERY_STRING"] + "'\t" + userCookie["id"].value + "\n")
    else:
        h.write(strftime("[%a, %d %b %Y %H:%M:%S]")+"\t'"+os.environ["QUERY_STRING"] + "\n")
        
    h.close()

def main (form):
    
    log()    
    
    if not have_cookie():
        handle_login(form)
        return
        
    # get the cookie 
    cookie = makeCookie()

    if form.has_key("mode"):
        if form.getvalue("mode") == "css":
            sid = sid_from_cookie(cookie)
            if userCookie.has_key("id"):
                cookieval = userCookie["id"].value
            else:
                cookieval = "none"
            if voted_too_often():
                stylesheet = badstylesheet
            else:
                stylesheet = get_stylesheet(sid)

            print "Content-Type: text/css\n"
            print "# here's the stylesheet from ", sid
            print stylesheet  
    elif form.has_key("look"):
        record_vote(form)
    elif form.has_key("name"):
        handle_login(form)
    else:
        output_voteform()
    
if __name__=='__main__':

    #sid = select_sid()
    #print "SID: ", sid
    #print get_stylesheet(sid)

    form = cgi.FieldStorage()
    main(form)
    
