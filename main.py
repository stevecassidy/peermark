'''
Created on Mar 28, 2016

@author: steve
'''

from bottle import Bottle, template, static_file, request, response, HTTPError, debug, redirect, HTTPResponse, error
import mimetypes, time
import statistics
import os

from database import COMP249Db
import users

# for deployment we need to make sure we're in the right directory
import os

if not __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))

application = Bottle()


def get_case_insensitive_path(path):
    """Return a tuple of (path, exists) where
    path is a possibly corrected path name and exists
    is True if we found the file and False otherwise
    """

    if os.path.exists(path):
        return path, True

    d, f = os.path.split(path)

    # if d is not empty, we need to recurse to get it's name
    if not d == '':
        # recurse on dirname if not empty
        d, found = get_case_insensitive_path(d)

        if not found:
            return path, False

    # now d is either empty or a valid directory path
    # try to find the file
    if d == '':
        d = '.'
    files = os.listdir(d)

    for fname in files:
        if fname.lower() == f.lower():
            return os.path.join(d, fname), True

    # we didn't find it
    return path, False


def static_file_force(filename, root):
    """ A version of static_file that will never return a
    304 Not Modified response to ensure that we always get
    the latest version of a student submission file.
    """

    charset = 'UTF-8'

    root = os.path.abspath(root) + os.sep
    filename = os.path.abspath(os.path.join(root, filename.strip('/\\')))
    headers = dict()

    # in case the filename has a different case
    filename, exists = get_case_insensitive_path(filename)

    if not filename.startswith(root):
        return HTTPError(403, "Access denied.")
    if not exists or not os.path.isfile(filename):
        return error404("File does not exist.")
    if not os.access(filename, os.R_OK):
        return HTTPError(403, "You do not have permission to access this file.")

    mimetype, encoding = mimetypes.guess_type(filename)
    if encoding: headers['Content-Encoding'] = encoding

    if mimetype:
        if mimetype[:5] == 'text/' and charset and 'charset' not in mimetype:
            mimetype += '; charset=%s' % charset
        headers['Content-Type'] = mimetype

    stats = os.stat(filename)
    headers['Content-Length'] = clen = stats.st_size
    lm = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stats.st_mtime))
    headers['Last-Modified'] = lm

    body = '' if request.method == 'HEAD' else open(filename, 'rb')

    return HTTPResponse(body, **headers)



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

    # root should contain index.html, if not, look deeper
    if not os.path.exists(os.path.join(root, 'index.html')):

        for dirpath, dirnames, filenames in os.walk(root):
            if 'index.html' in filenames:
                root = dirpath
                break

    return static_file_force(filename=filename, root=root)


@application.route('/submission/<hash>/<filename:path>')
def submission(hash, filename):
    """Serve up pages from a student submission"""

    db = COMP249Db()

    useremail = users.session_user(db)

    viewing = users.user_viewing(db, useremail)
    if viewing == "COMPLETED":
        return redirect('/static/completed.html')

    root = users.submission_path(db, viewing)

    # root should contain index.html, if not, look deeper
    if not os.path.exists(os.path.join(root, 'index.html')):

        for dirpath, dirnames, filenames in os.walk(root):
            if 'index.html' in filenames:
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
    users.aggregate_scores(marks, 'discard_lowest', users.discard_lowest_avg)
    users.aggregate_scores(marks, 'mean', statistics.mean)
    users.aggregate_scores(marks, 'stdev', statistics.stdev)
    stats = users.stats(db)

    return template("report", marks=marks, stats=stats)


import io
import csv


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


@application.route('/admin/view/<sid>/<filename:path>')
def view_sid(sid, filename):
    """Serve up the submission from a particular student"""

    db = COMP249Db()

    root = users.submission_path(db, sid)

    # temp hack to re-root submissions
    root = os.path.basename(root)
    root = os.path.join('submissions', root)

    # root should contain index.html, if not, look deeper
    if not os.path.exists(os.path.join(root, 'index.html')):

        for dirpath, dirnames, filenames in os.walk(root):
            if 'index.html' in filenames:
                root = dirpath
                break

    return static_file_force(filename=filename, root=root)


if __name__ == '__main__':
    application.run()
