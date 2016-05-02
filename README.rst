SVNOnline
===============
A svn online client.

Install
===============
::

 pip install SVNOnline


Use
===============
cd to you working directory and run command:

::

 SVNOnline

on Windows use:
::

 SVNOnline.bat

if can't find SVNOnline command, try:
::

 python -m SVNOnline


open broswer with url **http://127.0.0.1:8000**
	

Editor shortcut
===============
- **Ctrl+S** : save file

- **Ctrl+Shif+N** : new file

- **Ctrl+H** : show help info

Other tips
===============
1.set http port 80
::

 SVNOnline 80

2.authenticate with username and password (admin admin)
::

 SVNOnline -u admin -p admin

3.set the working directory (/tmp)
::

 SVNOnline -d /tmp

4.bind address with 127.0.0.1
::

 SVNOnline 127.0.0.1:8000
 
5.use as wsgi
::

 # set username and passwor
 export WSGI_PARAMS="-u admin -p admin" 
 # run wsgi with gunicorn
 gunicorn -b 0.0.0.0:8000 SVNOnline.wsgi:application

 