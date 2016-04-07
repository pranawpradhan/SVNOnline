# -*- coding: UTF-8 -*
'''
@author: sintrb
'''
"""

SVNOnline Server.

This module refer to SimpleHTTPServer

"""


__version__ = "0.0.1"

import BaseHTTPServer
import SocketServer
import cgi
import json
import mimetypes
import os
import posixpath
import shutil
import socket
import sys
import urllib
import urlparse


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

libdir = os.path.dirname(__file__)

options = {
        'workdir':os.getcwd(),
        'bind':'0.0.0.0',
        'port':8000
        }


class SVNOnlineRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "SVNOnline/" + __version__
    protocol_version = "HTTP/1.1"
    editortmpl = ''
    def check_auth(self):
        if not options.get('auth'):
            return True
        au = self.headers.getheader('authorization')
        if au and len(au) > 6 and au.endswith(options.get('auth')):
            return True
        self.send_response(401, "Unauthorized")
        self.send_header("Content-Type", "text/html")
        self.send_header("WWW-Authenticate", 'Basic realm="%s"' % (options.get('realm') or self.server_version))
        self.send_header('Connection', 'close')
        self.end_headers()
        return False
    
    def api_xx(self):
        pass
    def do_GET(self):
        if not self.check_auth():
            return
        self.path = self.path.replace('..', '')
        url = urlparse.urlparse(self.path)
        
        contenttype = 'text/html'
        statuscode = 200
        f = StringIO()
        if url.path.startswith('/api/'):
            contenttype = 'text/json'
            apiname = 'api_%s' % (url.path.replace('/api/', ''))
            if hasattr(self, apiname):
                apifunc = getattr(self, apiname)
                res = apifunc() or {'code':0}
            else:
                res = {'code':-1, 'msg':'not such api: %s' % apiname}
            f.write(json.dumps(res))
        else:
            filepath = os.path.join(libdir, url.path.strip('/') or 'index.html')
            if os.path.exists(filepath) and os.path.isfile(filepath):
                f.write(open(filepath, 'rb').read())
            else:
                statuscode = 404
                f.write("404 not found")

        self.send_response(statuscode)
        self.send_header("Content-type", contenttype)
        self.send_header("Content-Length", str(f.tell()))
        self.send_header('Connection', 'close')
        self.end_headers()
        f.seek(0)
        shutil.copyfileobj(f, self.wfile)


class ThreadingHTTPServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = 1  # Seems to make sense in testing environment
    def server_bind(self):
        """Override server_bind to store the server name."""
        SocketServer.TCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port

def start():
    port = options['port'] if 'port' in options else 8000
    server_address = (options['bind'], port)
    httpd = ThreadingHTTPServer(server_address, SVNOnlineRequestHandler)
    sa = httpd.socket.getsockname()
    print "Root Directory: %s" % options.get('workdir')
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()

def main():
    import getopt
    opts, args = getopt.getopt(sys.argv[1:], "u:p:r:hd:")
    for opt, arg in opts:
        if opt == '-u':
            options['username'] = arg
        elif opt == '-p':
            options['password'] = arg
        elif opt == '-r':
            options['realm'] = arg
        elif opt == '-d':
            options['workdir'] = arg
        elif opt == '-h':
            print 'Usage: python -m SVNOnline [-u username] [-p password] [-r realm] [-d workdir] [bindaddress:port | port]'
            print 'Report bugs to <sintrb@gmail.com>'
            exit()

    if options.get('username') and options.get('password'):
        import base64
        options['auth'] = base64.b64encode('%s:%s' % (options.get('username'), options.get('password')))
    if len(args) > 0:
        bp = args[0]
        if ':' in bp:
            options['bind'] = bp[0:bp.index(':')]
            options['port'] = int(bp[bp.index(':') + 1:])
        else:
            options['bind'] = '0.0.0.0'
            options['port'] = int(bp)
    start()
if __name__ == '__main__':
    main()
