<h2>Udacity Full Stack Web Developer Project 7</h2>
 
 IP Address: 52.25.48.0
 
 SSH Port : 2200

 Complete URL : http://ec2-52-25-48-0.us-west-2.compute.amazonaws.com

 SSH Key : ~/grader.pub

Programs Installed:
 
 git, sqlalchemy, postgresql, sublime text 3(unused), mod_wsgi, apache2, etc.


Configurations: 

 Change the SSH port to 2200

 Add a new user grader

 Give sudo access to grader

 Configure the local timezone to UTC
 
 Install and configure Apache to serve a Python mod_wsgi application

 	Add the Apache2 configuration file

 	<VirtualHost *:80>
    	ServerName 52.25.48.0
    	WSGIScriptAlias / /var/www/fullstack/myApp.wsgi
    	RewriteEngine On
    	RewriteCond %{HTTP_HOST} ^52\.25\.48\.0$
    	RewriteRule ^/(.*)$ http://ec2-52-25-48-0.us-west-2.compute.amazonaws.com/$$
    	<Directory /var/www/fullstack/Alan/>
        	Order allow, deny
        	Allow from all
    	</Directory>
    	Alias /static /var/www/fullstack/Alan/static
    	<Directory /var/www/fullstack/Alan/static/>
        	Order allow, deny
        	Allow from all
    	</Directory>
    	ErrorLog ${APACHE_LOG_DIR}/error.log
    	LogLevel warn
    	CustomLog ${APACHE_LOG_DIR}/accessFGL.log combined
	</VirtualHost>
	WSGISocketPrefix /var/run/wsgi

	

 	Add the wsgi configuration file /var/www/fullstack/myApp.wsgi

		#!/usr/bin/python
		import sys
		sys.path.insert(0,"/var/www/fullstack/")
		from Alan.application import app as application





 Install and configure PostgreSQL:  Not allowing remote connections by adding a password
 
 Create a new user named alan that has limited access to catalog application database
 
