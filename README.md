### 			Linux Server configuration for Catalog

------

**Summary:**

This is a project of Udacity Full Stack Web Developer Nanodegree. It is the last puzzle part for the whole picture of my [*catalog*](https://github.com/yihuicai/Catalog_FSND) website so that you can experience what I actually created.

- ​ <u>IP Address</u> : 52.25.48.0
- <u>SSH Port</u> : 2200

- <u>Complete URL</u> : http://ec2-52-25-48-0.us-west-2.compute.amazonaws.com

- <u>SSH Key</u> : `~/grader.pub`

- <u>Programs Installed</u> : `git, sqlalchemy, postgresql, mod_wsgi, apache2, etc.`



**Configurations:** 

1. Change the SSH port to 2200.

2. Add a new user grader.

3. Give sudo access to grader.

4. Configure the local timezone to UTC.

5. Install and configure Apache to serve a Python mod_wsgi application.

6. Add the Apache2 configuration file `alan.conf`.

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

7. Add the wsgi configuration file `/var/www/fullstack/myApp.wsgi`.

```python
	#!/usr/bin/python
	import sys
	sys.path.insert(0,"/var/www/fullstack/")
	from Alan.application import app as application
```

8. Install and configure PostgreSQL:  Not allowing remote connections by adding a password
9. Create a new user named **alan** that has limited access to catalog application database.
10. Modify the database address for connection in `application.py` and `database_setup.py` .
11. Modify the SQLAlchemy database session management in `application.py`.

