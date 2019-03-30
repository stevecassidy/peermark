'''
Created on Mar 28, 2016

@author: steve
'''

from bottle import Bottle, template, static_file, request, response, HTTPError, debug, redirect, HTTPResponse, error
import statistics
import io
import csv
from util import static_file_force

from database import COMP249Db
import users

# for deployment we need to make sure we're in the right directory
import os

if not __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))

application = Bottle()


@error(404)
def error404(error):
    """Custom 404 Page"""

    return template("404")


@application.route('/static/<filename:path>')
def static(filename):
    return static_file(filename=filename, root='static')


@application.route('/')
def home():
    """Home page is a login form or the frame page
    that presents the feedback form and a submission"""

    db = COMP249Db()

    useremail = users.session_user(db)
    if useremail:
        return template('main', title="Main")
    else:
        return template('help', title="Login", loginform=True)


@application.route('/help.html')
def help():
    return template('help')


@application.route('/submission/')
def submission_redirect():
    """Redirect to the view of the currently allocated
    submission"""

    db = COMP249Db()

    useremail = users.session_user(db)
    viewing = users.user_viewing(db, useremail)
    hash = db.encode(viewing)

    return redirect('/submission/' + hash + "/index.html")


@application.route('/self/<filename:path>')
def submission_self(filename):
    """Serve up pages from a student's own submission"""

    db = COMP249Db()

    useremail = users.session_user(db)
    root = users.submission_path(db, users.user_sid(db, useremail))

    return serve_submitted_file(root, filename)



@application.route('/submission/<hash>/<filename:path>')
def submission(hash, filename):
    """Serve up pages from a student submission"""

    db = COMP249Db()

    useremail = users.session_user(db)

    viewing = users.user_viewing(db, useremail)
    if viewing == "COMPLETED":
        return redirect('/static/completed.html')

    root = users.submission_path(db, viewing)

    return serve_submitted_file(root, filename)


@application.route('/admin/view/<sid>')
def view_sid_embedded(sid):
    """Serve a submission embedded in an iframe like the
    marking page"""

    db = COMP249Db()
    email = users.user_email(db, sid)

    return template("admin-iframe", sid=sid, email=email)


@application.route('/admin/view/<sid>/<filename:path>')
def view_sid(sid, filename):
    """Serve up the submission from a particular student"""

    db = COMP249Db()

    root = users.submission_path(db, sid)

    return serve_submitted_file(root, filename)


def serve_submitted_file(root, filename):

    # serve up a fixed index.html file, same for everyone
    if filename == 'index.html':
        return static_file(filename, root='reference')

    # root should contain index.html, if not, look deeper
    if not os.path.exists(os.path.join(root, 'style.css')):

        for dirpath, dirnames, filenames in os.walk(root):
            if 'style.css' in filenames:
                root = dirpath
                break

    return static_file_force(filename=filename, root=root)



@application.post('/feedback')
def add_feedback():
    """Handle feedback form submission"""

    db = COMP249Db()

    try:
        useremail = users.session_user(db)
        design = int(request.forms.get('design'))
        tech = int(request.forms.get('tech'))
        creative = int(request.forms.get('creative'))
        feedback = request.forms.get('feedback')
        # browser info from request
        browser = request.get_header("User-Agent")

        users.add_marks(db, useremail, design, tech, creative, feedback, browser)
    except:
        pass  #

    return redirect('/')


@application.post('/login')
def login():
    """Process a login request"""

    db = COMP249Db()

    email = request.forms.get('email')
    sid = request.forms.get('sid')

    if users.check_login(db, email, sid):

        users.generate_session(db, email)

        redirect('/', 303)

        response.status = 303
        response.set_header('Location', '/')
        return "Redirect"
    else:
        return template('login', title='Login Error', message='Login Failed, please try again')


@application.post('/logout')
def logout():
    """Process a logout request"""

    db = COMP249Db()

    useremail = users.session_user(db)
    users.delete_session(db, useremail)

    response.status = 303
    response.set_header('Location', '/')
    return "Redirect"


@application.route('/top10')
def report():
    """Generate a page showing the top 10 submissions"""

    db = COMP249Db()

    marks = users.mark_report(db)
    stats = users.stats(db)

    return template("top10", marks=marks, stats=stats)


@application.route('/admin/report')
def report():
    """Generate a marking report"""

    db = COMP249Db()

    marks = users.mark_dump(db)
    if marks != []:
        users.aggregate_scores(marks, 'discard_lowest', users.discard_lowest_avg)
        users.aggregate_scores(marks, 'mean', statistics.mean)
        users.aggregate_scores(marks, 'stdev', statistics.stdev)
        stats = users.stats(db)
    else:
        stats = []

    return template("report", marks=marks, stats=stats)

@application.route('/admin/all')
def showall():

    db = COMP249Db()

    submissions = users.list_submissions(db)

    return template("allsubmissions", submissions=submissions)

@application.route('/admin/report.csv')
def reportcsv():
    """Generate a marking report"""

    db = COMP249Db()

    marks = users.mark_dump(db)
    users.aggregate_scores(marks, 'discard_lowest', users.discard_lowest_avg)
    users.aggregate_scores(marks, 'mean', statistics.mean)
    users.aggregate_scores(marks, 'stdev', statistics.stdev)

    rows = []
    for sid in marks:
        feedback = '\n'.join([f for f in marks[sid]['feedback'] if f != ''])
        rows.append((sid, marks[sid]['discard_lowest'], marks[sid]['mean'], marks[sid]['stdev'], feedback))

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerows(rows)

    response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    response.headers["Content-type"] = "text/csv"

    return si.getvalue()



if __name__ == '__main__':
    application.run()
