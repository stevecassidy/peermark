'''
Created on Mar 26, 2012

@author: steve
'''

import unittest

from database import COMP249Db
from http.cookies import SimpleCookie
from bottle import request, response
import os

# import the module to be tested
import users


SUBMISSIONDIR = 'submissions'


class Test(unittest.TestCase):

    
    def setUp(self):
        # open an in-memory database for testing
        self.db = COMP249Db(':memory:')
        self.db.create_tables()
        paths = dict()
        for sid in os.listdir(SUBMISSIONDIR):
            paths[sid] = os.path.join(SUBMISSIONDIR, sid)
        self.db.import_users('testdata.csv', paths)


    @property
    def users(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT sid, email FROM users")
        return cursor.fetchall()

    def test_check_login(self):

        for sid, email in self.users:
            # try the correct sid
            self.assertTrue(users.check_login(self.db, email, sid), "sid check failed for user %s" % email)

            # and now incorrect
            self.assertFalse(users.check_login(self.db, email, "badsid"), "Bad sid check failed for user %s" % email)

        # check for an unknown email
        self.assertFalse(users.check_login(self.db, "whoisthis", "badsid"), "Bad sid check failed for unknown user")

    def get_cookie_value(self, cookiename):
        """Get the value of a cookie from the bottle response headers"""

        headers = response.headerlist
        for h,v in headers:
            if h == 'Set-Cookie':
                cookie = SimpleCookie(v)
                if cookiename in cookie:
                    return cookie[cookiename].value

        return None

    def test_generate_session(self):
        """The generate_session procedure makes a new session cookie
        to be returned to the client
        If there is already a session active for this user, return the
        same session key in the cookie"""

        # run tests for all test users
        for sid, email in self.users:

            users.generate_session(self.db, email)
            # get the sessionid from the response cookie

            sessionid = self.get_cookie_value(users.COOKIE_NAME)

            self.assertFalse(sessionid is None)

            cursor = self.db.cursor()
            cursor.execute('select useremail from sessions where sessionid=?', (sessionid,))

            query_result = cursor.fetchone()
            if query_result is None:
                self.fail("No entry for session id %s in sessions table" % (sessionid,))

            self.assertEqual(email, query_result[0])

            # now try to make a new session for one of the users

            users.generate_session(self.db, email)

            sessionid2 = self.get_cookie_value(users.COOKIE_NAME)

            # sessionid should be the same as before

            self.assertEqual(sessionid, sessionid2)

        # try to generate a session for an invalid user

        sessionid3 = users.generate_session(self.db, "Unknown")
        self.assertEqual(sessionid3, None, "Invalid user should return None from generate_session")


    def test_delete_session(self):
        """The delete_session procedure should remove all sessions for
        a given user in the sessions table.
        Test relies on working generate_session"""

        # run tests for all test users
        for passwd, email in self.users:
            users.generate_session(self.db, email)

            # now remove the session
            users.delete_session(self.db, email)

            # now check that the session is not present

            cursor = self.db.cursor()
            cursor.execute('select sessionid from sessions where useremail=?', (email,))

            rows = cursor.fetchall()
            self.assertEqual(rows, [], "Expected no results for sessions query from deleted session, got %s" % (rows,))



    def test_session_user(self):
        """The session_user procedure finds the name of the logged in
        user from the session cookie if present

        Test relies on working generate_session
        """

        # first test with no cookie
        email_from_cookie = users.session_user(self.db)
        self.assertEqual(email_from_cookie, None, "Expected None in case with no cookie, got %s" % str(email_from_cookie))

        request.cookies[users.COOKIE_NAME] = 'fake sessionid'
        email_from_cookie = users.session_user(self.db)

        self.assertEqual(email_from_cookie, None, "Expected None in case with invalid session id, got %s" % str(email_from_cookie))

        # run tests for all test users
        for sid, email in self.users:

            users.generate_session(self.db, email)

            sessionid = self.get_cookie_value(users.COOKIE_NAME)

            request.cookies[users.COOKIE_NAME] = sessionid

            email_from_cookie = users.session_user(self.db)

            self.assertEqual(email_from_cookie, email)


    def test_choose_submission(self):
        """Choose a random submission for a user"""


        email = 'one@here.com'
        sid = '123'

        sessionid = users.generate_session(self.db, email)

        self.assertNotEqual(sessionid, None)

        # this should have chosen a random submission
        # which we can now retrieve

        sub = users.user_viewing(self.db, email)

        self.assertNotEqual(sub, '123')
        self.assertNotEqual(sub, 'unknown')

        # add marks for this submission, should have the effect of
        # choosing another submission for this user to mark
        for dd in range(3):
            users.add_marks(self.db, email, dd, dd, dd, "Good Work!")
            newsub = users.user_viewing(self.db, email)
            self.assertNotEqual(sub, newsub)
            sub = newsub
            print("SUB", sub)




if __name__ == "__main__":
    unittest.main()