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


def remove_comments(css):
    """Remove all CSS comment blocks."""
    iemac, preserve = False, False
    comment_start = css.find("/*")
    while comment_start >= 0:  # Preserve comments that look like `/*!...*/`.
        # Slicing is used to make sure we dont get an IndexError.
        preserve = css[comment_start + 2:comment_start + 3] == "!"
        comment_end = css.find("*/", comment_start + 2)
        if comment_end < 0:
            if not preserve:
                css = css[:comment_start]
                break
        elif comment_end >= (comment_start + 2):
            if css[comment_end - 1] == "\\":
                # This is an IE Mac-specific comment; leave this one and the
                # following one alone.
                comment_start = comment_end + 2
                iemac = True
            elif iemac:
                comment_start = comment_end + 2
                iemac = False
            elif not preserve:
                css = css[:comment_start] + css[comment_end + 2:]
            else:
                comment_start = comment_end + 2
        comment_start = css.find("/*", comment_start)
    return css


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

    # if this is the CSS file, scrub comments
    if 'css' in mimetype:
        body = body.read().decode('utf8')
        body = remove_comments(body)

    return HTTPResponse(body, **headers)



if __name__=='__main__':

    print(get_case_insensitive_path('static/peersss.css'))
    print(get_case_insensitive_path('static/PEER.css'))
    print(get_case_insensitive_path('STATIC/peer.css'))