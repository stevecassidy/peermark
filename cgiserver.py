#!/usr/bin/python

"""CGI Web server

Will serve pages from the current directory and cgi
scripts from the cgi-bin subdirectory. Listens on port 8000"""

import BaseHTTPServer
import CGIHTTPServer

server_address = ('', 8000)
handler = CGIHTTPServer.CGIHTTPRequestHandler
httpd = BaseHTTPServer.HTTPServer(server_address, handler)

print "Starting server. Connect to http://localhost:8000/"

httpd.serve_forever()


