'''
Created on Mar 28, 2016

@author: Steve Cassidy
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

def require_valid_user(viewfn):
    """Decorator to ensure that a valid user is logged in
    before a view can be rendered.  Redirect to login if not"""

    def view(*args, **kwargs):
        db = COMP249Db()
        useremail = users.session_user(db)
        if useremail:
            return viewfn(db, useremail, *args, **kwargs)
        else:
            redirect('/')

    return view

def require_admin(viewfn):
    """Decorator to ensure that admin is logged in
    before a view can be rendered.  Redirect to login if not"""

    def view(*args, **kwargs):
        db = COMP249Db()
        useremail = users.session_user(db)
        if useremail == users.ADMIN_USER:
            return viewfn(db, *args, **kwargs)
        else:
            redirect('/')

    return view



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
    print('useremail', useremail)
    if useremail == users.ADMIN_USER:
        return template('admin')
    elif useremail:
        return template('main', title="Main")
    else:
        return template('help', title="Login", loginform=True)


@application.route('/help.html')
def help():
    return template('help')


@application.route('/submission/')
@require_valid_user
def submission_redirect(db, useremail):
    """Redirect to the view of the currently allocated
    submission"""

    viewing = users.user_viewing(db, useremail)
    hash = db.encode(viewing)

    return redirect('/submission/' + hash + "/index.html")


@application.route('/self/<filename:path>')
@require_valid_user
def submission_self(db, useremail, filename):
    """Serve up pages from a student's own submission"""

    root = users.submission_path(db, users.user_sid(db, useremail))

    return serve_submitted_file(root, filename)

@application.route('/submission/<hash>/<filename:path>')
@require_valid_user
def submission(db, useremail, hash, filename):
    """Serve up pages from a student submission"""

    viewing = users.user_viewing(db, useremail)
    if viewing == "COMPLETED":
        return redirect('/static/completed.html')

    root = users.submission_path(db, viewing)

    return serve_submitted_file(root, filename)


@application.route('/admin/view/<sid>')
@require_admin
def view_sid_embedded(db, sid):
    """Serve a submission embedded in an iframe like the
    marking page"""

    email = users.user_email(db, sid)

    return template("admin-iframe", sid=sid, email=email)


@application.route('/admin/view/<sid>/<filename:path>')
@require_admin
def view_sid(db, sid, filename):
    """Serve up the submission from a particular student"""

    root = users.submission_path(db, sid)

    return serve_submitted_file(root, filename)


def serve_submitted_file(root, filename):

    # serve up a fixed index.html file, same for everyone
    if filename == 'index.html':
        return static_file(filename, root='reference')

    # root should contain index.html, if not, look deeper
    if not os.path.exists(os.path.join(root, 'index.html')):

        for dirpath, dirnames, filenames in os.walk(root):
            if 'index.html' in filenames:
                root = dirpath
                break

    return static_file_force(filename=filename, root=root)



@application.post('/feedback')
@require_valid_user
def add_feedback(db, useremail):
    """Handle feedback form submission"""

    try:
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
def top10():
    """Generate a page showing the top 10 submissions"""

    db = COMP249Db()
    
    marks = users.mark_report(db)
    stats = users.stats(db)

    return template("top10", marks=marks, stats=stats)


@application.route('/admin/report')
@require_admin
def report(db):
    """Generate a marking report"""

    userlist = users.get_users(db)
    marks = users.mark_dump(db)
    if marks != []:
        users.aggregate_scores(marks, 'discard_lowest', users.discard_lowest_avg)
        users.aggregate_scores(marks, 'mean', statistics.mean)
        users.aggregate_scores(marks, 'stdev', statistics.stdev)
        stats = users.stats(db)
    else:
        stats = []
    
    return template("report", marks=marks, stats=stats, users=userlist)

@application.route('/admin/all')
@require_admin
def showall(db):

    submissions = users.list_submissions(db)

    return template("allsubmissions", submissions=submissions)

@application.route('/admin/report.csv')
@require_admin
def reportcsv(db):
    """Generate a marking report"""

    userlist = users.get_users(db)
    marks = users.mark_dump(db)
    users.aggregate_scores(marks, 'discard_lowest', users.discard_lowest_avg)
    users.aggregate_scores(marks, 'mean', statistics.mean)
    users.aggregate_scores(marks, 'stdev', statistics.stdev)
    users.aggregate_scores(marks, 'count', len)

    rows = [['email', 'Github', 'Count', 'Discard Lowest', 'Mean', 'StDev', 'Feedback']]
    for sid in marks:
        feedback = '\n'.join([f for f in marks[sid]['feedback'] if f != ''])
        rows.append((userlist[sid], sid, marks[sid]['count'], marks[sid]['discard_lowest'], marks[sid]['mean'], marks[sid]['stdev'], feedback))

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerows(rows)

    response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    response.headers["Content-type"] = "text/csv"

    return si.getvalue()



if __name__ == '__main__':
    application.run(reloader=True)
