'''
Created on Mar 26, 2012

@author: steve
'''

import bottle
import statistics
import os

# this variable MUST be used as the name for the cookie used by this application
COOKIE_NAME = 'sessionid'

MAX_MARKED = 20
ADMIN_USER = 'admin'
if 'ADMIN_PASSWORD' in os.environ:
    ADMIN_PASSWORD = os.environ['ADMIN_PASSWORD']
else:
    ADMIN_PASSWORD = ''

def check_login(db, email, sid):
    """returns True if password matches stored"""

    if ADMIN_PASSWORD != '' and email == ADMIN_USER and sid == ADMIN_PASSWORD:
        return True

    cursor = db.cursor()
    # get the user details
    cursor.execute('select hash from users where email=?', (email,))
    row = cursor.fetchone()
    if row:
        print('got user', email, sid)
        # check that password matches
        storedsid = row[0]
        hashedsid = db.encode(sid)
        print('stored', storedsid, 'hashed', hashedsid)
        return storedsid == hashedsid
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
    if useremail != ADMIN_USER:  
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


def list_submissions(db):
    """Return a list of all submissions"""

    sql = "SELECT sid FROM users ORDER BY sid"

    cursor = db.cursor()
    cursor.execute(sql)

    return [r[0] for r in cursor.fetchall()]


def choose_submission(db, useremail):
    """Choose a random submission for a user and
        update the sessions table"""

    exclude = user_marked(db, useremail)
    number_marked = len(exclude)
    cursor = db.cursor()
    chosen = ''

    # find submissions marked more than 5 times so we can exclude them
    sql = "SELECT submission from (SELECT submission, count(voter) as count from marks group by submission) where count>5"
    cursor.execute(sql)
    exclude.extend([r[0] for r in cursor.fetchall()])

    if number_marked >= MAX_MARKED:
        chosen = 'COMPLETED'
    else:
        # choose a user who isn't me who I haven't rated before
        sql = "SELECT sid FROM users WHERE email <> ? ORDER BY random()"

        cursor.execute(sql, (useremail,))

        for row in cursor:
            chosen = row[0]
            if chosen not in exclude:
                break

    if chosen:
        sql = "UPDATE sessions SET viewing=? WHERE useremail=?"
        cursor.execute(sql, (chosen, useremail))
    else:
        print("Nothing chosen for user",  useremail)
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


def user_email(db, sid):
    """Return the email for this sid"""

    sql = "SELECT email FROM users WHERE sid=?"

    cursor = db.cursor()
    cursor.execute(sql, (sid,))

    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        # we didn't find the user, so return None
        return None

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

def get_users(db):
    """Return a dictionary of sid -> email"""

    sql = "SELECT sid, email FROM users"

    cursor = db.cursor()
    cursor.execute(sql)

    result = dict()
    for row in cursor:
        result[row[0]]  = row[1]

    return result

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


def add_marks(db, useremail, design, creative, tech, feedback, browser):
    """Add a mark from useremail for the submission by sid
    """

    # who is this user viewing now?
    sid = user_viewing(db, useremail)
    if sid == "COMPLETED":
        return

    sql = "INSERT INTO marks (submission, voter, design, creative, tech, feedback, browser) VALUES (?,?,?,?,?,?,?)"

    cursor = db.cursor()
    cursor.execute(sql, (sid, useremail, design, creative, tech, feedback, browser))

    db.commit()

    # choose someone else for this user to mark
    choose_submission(db, useremail)


def mark_report(db):
    """Generate a report on the marks entered so far
    for each submission give the count and average marks
    Return a list of tuples, one per submission
    (sid, count, design, creative, tech)
        """

    sql = """SELECT submission, count(voter) as count, avg(design) as d, avg(creative) as c, avg(tech) as t, email
    FROM marks, users
    WHERE users.sid = marks.submission
    GROUP BY submission
    ORDER BY d+c+t DESC"""

    cursor = db.cursor()
    cursor.execute(sql)

    return cursor.fetchall()

def user_marked_count(db):
    """Return the number of submissions marked by each user"""

    sql = "SELECT voter, count(voter) from marks group by voter"

    cursor = db.cursor()
    cursor.execute(sql)
    result = {}
    for row in cursor:
        result[row[0]] = row[1]

    return result

def mark_dump(db):
    """Return a dictionary with one key per submission
    the value of each key is a dictionary with keys:

     scores: a list of score tuples (d, c, t)
     feedback: a list of feedback strings

        """

    sql = """SELECT submission, voter, design, creative, tech, feedback, browser, email
    FROM marks, users
    WHERE users.sid = marks.submission
    ORDER BY submission"""

    cursor = db.cursor()
    cursor.execute(sql)
    scores = []
    feedback = []
    browser = [] 

    result = {}
    sid = None
    for row in cursor:
        if not sid == row[0]:
            if sid is not None:
                result[sid] = {'scores': scores, 'feedback': feedback, 'browser': browser}
            sid = row[0] 
            scores = []
            feedback = []
            browser = []
 
        scores.append((row[2], row[3], row[4]))
        feedback.append(row[5])
        browser.append(row[6])

    if sid:
        result[sid] = {'scores': scores, 'feedback': feedback, 'browser': browser}

    marked = user_marked_count(db)
    for key in result:
        if key in marked:
            result[key]['marked'] = marked[key]
        else:
            result[key]['marked'] = 0

    return result


def discard_lowest_avg(scores):
    """Return the mean score from this list of scores
    after discarding the lowest score

    >>> discard_lowest_avg([1, 2, 3])
    2.5
    >>> discard_lowest_avg([3, 2, 3])
    3.0
    >>> discard_lowest_avg([3, 2, 0])
    2.5
    >>> discard_lowest_avg([])
    0
    >>> discard_lowest_avg([1])
    1
    """
    if scores == []:
        return 0
    elif len(scores) == 1:
        return scores[0]
    else:
        return statistics.mean(sorted(scores)[1:])


def aggregate_scores(results, resultkey, fn):
    """Generate scores for each submission based on an aggregation
    function.
    Apply the given function to the list of scores for design, creative and tech
    for each submission and store the mean of these using 'resultkey' in the
    dictionary for this submission.

    >>> results = {\
                   'a': {'scores': [(1,1,1), (2,2,2), (3,3,3)], 'feedback': ['a', 'b', 'c']},\
                   'b': {'scores': [(1,1,1), (2,2,2), (0,0,0)], 'feedback': ['a', 'b', 'c']}\
                    }
    >>> aggregate_scores(results, 'discard_score', discard_lowest_avg)
    >>> results['a']['discard_score']
    2.5
    >>> results['b']['discard_score']
    1.5
    >>> aggregate_scores(results, 'mean', statistics.mean)
    >>> results['a']['mean']
    2.0
    >>> results['b']['mean']
    1.0
    """

    for key in results:
        scores = results[key]['scores']
        if len(scores) == 1:
            d = scores[0][0]
            c = scores[0][1]
            t = scores[0][2]
        else:
            d = fn([s[0] for s in scores])
            c = fn([s[1] for s in scores])
            t = fn([s[2] for s in scores])

        score = (d+c+t)/3

        results[key][resultkey] = score


def stats(db):
    """Generate marking statistics"""

    result = dict()

    cursor = db.cursor()
    # number of voters
    cursor.execute("select count(voter) from (SELECT voter FROM marks GROUP BY voter)")
    if cursor:
        result['voters'] = cursor.fetchone()[0]
    else:
        result['voters'] = 0

    # number of submissions marked
    cursor.execute("select count(submission) from ( SELECT submission FROM marks GROUP BY submission)")
    if cursor:
        result['marked'] = cursor.fetchone()[0]
    else:
        result['marked'] = 0

    # number of submissions overall
    cursor.execute("SELECT count(sid) FROM users")
    result['students'] = cursor.fetchone()[0]

    cursor.execute("select submission, count(submission) as count from marks where design=1 and creative=1 and tech=1 GROUP BY submission ORDER BY count DESC")
    result['singletons'] = cursor.fetchall()

    return result

if __name__=='__main__':

    import doctest
    doctest.testmod()