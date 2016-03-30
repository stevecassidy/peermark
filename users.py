'''
Created on Mar 26, 2012

@author: steve
'''

import bottle

# this variable MUST be used as the name for the cookie used by this application
COOKIE_NAME = 'sessionid'

MAX_MARKED = 20

def check_login(db, email, sid):
    """returns True if password matches stored"""

    cursor = db.cursor()
    # get the user details
    cursor.execute('select sid from users where email=?', (email,))
    row = cursor.fetchone()
    if row:
        # check that password matches
        storedsid = row[0]
        return storedsid == sid
    else:
        return False


def generate_session(db, useremail):
    """create a new session and add a cookie to the response object (bottle.response)
    user must be a valid user in the database, if not, return None
    There should only be one session per user at any time, if there
    is already a session active, use the existing sessionid in the cookie
    """

    # test to see whether we have one already
    cursor = db.cursor()
    # first check that this is a valid user
    cursor.execute('select email from users where email=?', (useremail,))
    row = cursor.fetchone()
    if not row:
        # unknown user
        return None

    useremail = row[0]

    cursor.execute('select sessionid from sessions where useremail=?', (useremail,))
    row = cursor.fetchone()
    if row:
        sessionid = row[0]
    else:
        sessionid = db.encode(useremail)
        # insert a new row into session table
        cursor.execute('insert into sessions (sessionid, useremail) values (?, ?)', (sessionid, useremail))
        db.commit()

    # set the cookie in the response
    bottle.response.set_cookie(COOKIE_NAME, sessionid)

    # choose an initial submission for them to view
    choose_submission(db, useremail)

    return sessionid


def delete_session(db, useremail):
    """remove all session table entries for this user"""

    cursor = db.cursor()
    cursor.execute("delete from sessions where useremail=?", (useremail,))
    db.commit()


def session_user(db):
    """try to
    retrieve the user from the sessions table
    return useremail or None if no valid session is present"""

    sessionid = bottle.request.get_cookie(COOKIE_NAME)

    # look in the sessions table
    cursor = db.cursor()
    cursor.execute("select useremail from sessions where sessionid=?", (sessionid,))

    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        # we didn't find the session, so we can't say who this is
        return None


def user_marked(db, useremail):
    """Return a list of the sids that this user has marked"""

    sql = "SELECT submission FROM marks WHERE voter=?"

    cursor = db.cursor()
    cursor.execute(sql, (useremail,))

    return [r[0] for r in cursor.fetchall()]


def choose_submission(db, useremail):
    """Choose a random submission for a user and
        update the sessions table"""

    marked = user_marked(db, useremail)
    cursor = db.cursor()

    if len(marked) > MAX_MARKED:
        chosen = 'COMPLETED'
    else:
        # choose a user who isn't me who I haven't rated before
        sql = "SELECT sid FROM users WHERE email <> ? ORDER BY random()"

        cursor.execute(sql, (useremail,))

        for row in cursor:
            chosen = row[0]
            if not chosen in marked:
                break

    sql = "UPDATE sessions SET viewing=? WHERE useremail=?"
    cursor.execute(sql, (chosen, useremail))

    print("Choosing: ", useremail, chosen)
    db.commit()

def user_viewing(db, useremail):
    """Return the sid that this user is supposed to be
    viewing right now"""

    # look in the sessions table
    cursor = db.cursor()
    cursor.execute("select viewing from sessions where useremail=?", (useremail,))

    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        # we didn't find the session, so we can't say who this is
        return 'unknown'

def user_sid(db, useremail):
    """Return the sid for this useremail"""

    sql = "SELECT sid FROM users WHERE email=?"

    cursor = db.cursor()
    cursor.execute(sql, (useremail,))

    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        # we didn't find the user, so return None
        return None


def submission_path(db, sid):
    """Return the submission for this sid"""

    sql = "SELECT path FROM users WHERE sid=?"

    cursor = db.cursor()
    cursor.execute(sql, (sid,))

    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        # we didn't find the user, so return None
        return None


def add_marks(db, useremail, design, creative, tech, feedback):
    """Add a mark from useremail for the submission by sid
    """

    # who is this user viewing now?
    sid = user_viewing(db, useremail)
    if sid == "COMPLETED":
        return

    sql = "INSERT INTO marks (submission, voter, design, creative, tech, feedback) VALUES (?,?,?,?,?,?)"

    cursor = db.cursor()
    cursor.execute(sql, (sid, useremail, design, creative, tech, feedback))

    db.commit()

    # choose someone else for this user to mark
    choose_submission(db, useremail)
