# -*- coding: UTF-8 -*
'''
@author: sintrb
'''
"""

SVNOnline Server.

This module refer to SimpleHTTPServer

"""


__version__ = "0.0.7"

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

import svn.local
import re
import inspect

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

reload(sys)
sys.setdefaultencoding("utf-8")

libdir = os.path.dirname(__file__)
if not libdir:
    libdir = os.getcwd()

options = {
        'workdir':os.getcwd(),
        'bind':'0.0.0.0',
        'port':8000
        }


class ApiException(Exception):
    def __init__(self, res):
        self.res = res

def ex(e, c=-1):
    return ApiException({"code":c, "msg":e})

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
    
    def api_list(self, path):
        if path.startswith('/'):
            path = path[1:]
        rootp = os.path.join(options['workdir'], *(path.split('/')))
        os.chdir(rootp)
        l = svn.local.LocalClient(rootp)
        d = {}
        info = None
        for p in os.listdir(rootp):
            if p.startswith('.'):
                continue
            try:
                f = ('%s%s' % (p, '/' if os.path.isdir(os.path.join(rootp, p)) else '')).strip()
                r = {
                    'path':f.decode('utf-8'),
                    'status':''
                    }
                d[f] = r
            except:
                pass

        try:
            linfo = l.info()
#             print linfo
            info = {'rev': linfo.get('commit#revision', None), 'url':linfo.get('url', None)}
            for l in  l.run_command('status', []):
                r = re.findall('([\S+])\s+(\S.*)', l)
                if r:
                    r = r[0]
                    f = r[1].strip()
                    if f in d:
                        d[f]['status'] = r[0].strip().upper()
                    else:
                        d[f] = {
                            'path':r[1],
                            'status':r[0]
                            }
        except:
            pass
        def warp(s):
            if s.endswith('/'):
                return '.' + s
            else:
                return s
        res = d.values()
        res.sort(cmp=lambda a, b:cmp(warp(a['path']), warp(b['path'])))
        return {'info':info, 'list':res}
        
    def api_svn(self, cmd, path, args=""):
        if path.startswith('/'):
            path = path[1:]
        rootp = os.path.join(options['workdir'], *(path.split('/')))
        os.chdir(rootp)
        l = svn.local.LocalClient(rootp)
        try:
            l.info()
        except:
            return ['this path is not a svn copy:', path]
        args = args.split(';')
#         print args
        res = [r for r in l.run_command(cmd, args) if r]
        try:
            return [r.decode('gb2312') for r in res]
        except:
            return res
    
    def do_GET(self):
        if not self.check_auth():
            return
        self.path = self.path.replace('..', '')
        url = urlparse.urlparse(self.path)
        contenttype = 'text/html'
        statuscode = 200
        f = StringIO()
#         print url
        if url.path.startswith('/api/'):
            try:
                from urllib import unquote
                contenttype = 'text/json'
                apiname = 'api_%s' % (url.path.replace('/api/', ''))
                if not hasattr(self, apiname):
                    raise ex('not such api: %s' % apiname)
                
                param = dict([(r[0], unquote(r[1]).replace('+', ' ')) for r in re.findall('([^&^=]+)=([^&^=]*)', url.query)])
                apifunc = getattr(self, apiname)
                
                argspec = inspect.getargspec(apifunc)
                kvargs = {}
                funcagrs = argspec.args
                defaults = argspec.defaults
                if defaults:
                    for i, v in enumerate(funcagrs[-len(defaults):]):
                        kvargs[v] = defaults[i]

                if len(funcagrs):
                    param['_param'] = param
                    argslen = len(funcagrs) - (len(defaults) if defaults else 0) - 1
                    missargs = []
                    for i, k in enumerate(funcagrs[1:]):
                        if k in param:
                            kvargs[k] = param[k]
                        elif i < argslen:
                            missargs.append(k)
                    if missargs:
                        raise ex('need argments: %s' % (', '.join(missargs)))
                data = apifunc(**kvargs)
                res = {'data':data, 'code':0}
            except ApiException, e:
                res = e.res
#             print res
            f.write(json.dumps(res))
        else:
            filepath = os.path.join(libdir, url.path.strip('/') or 'index.html')
#             print filepath
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

def config(argv):
    import getopt
    opts, args = getopt.getopt(argv, "u:p:r:hd:")
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

def main():
    config(sys.argv[1:])
    start()
if __name__ == '__main__':
    main()
