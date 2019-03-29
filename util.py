import os
import mimetypes
import time
from bottle import HTTPError, request, HTTPResponse, template

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
        return template("404")
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



if __name__=='__main__':

    print(get_case_insensitive_path('static/peersss.css'))
    print(get_case_insensitive_path('static/PEER.css'))
    print(get_case_insensitive_path('STATIC/peer.css'))