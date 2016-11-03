#!/usr/bin/python

import cgitb
import cgi
import sqlite3
import hashlib
import datetime
import urllib
import Cookie
import os
from random import randint

cgitb.enable()

stored_cookie_string = os.environ.get('HTTP_COOKIE') #look for a cookie

if stored_cookie_string:
	cookie = Cookie.SimpleCookie(stored_cookie_string)
	if 'token' in cookie and 'username' in cookie:
		c.execute('SELECT * FROM cookies WHERE username=?', (cookie['username'],))
		cookieUser = c.fetchall()
		tokenData = cookieUser[3]
		if tokenData == cookie['token']:
			load_content_page = True
			result_string += 'Logged in! Cookies are Great!:)'
			
			
# retrieve form data from GET request
user_form = cgi.FieldStorage()

if not 'username_field' in user_form or not 'password_field' in user_form:
	original_page = urllib.urlopen('http://nimsyllabus.com/index.html')
	original_page_text = original_page.read()
	augmented_text = original_page_text.replace('</body>', "Invalid username or password given. Try again please!" + '</body>')
	print 'Content-Type: text/html\n\n' + augmented_text
else:
	username = user_form['username_field'].value
	password = user_form['password_field'].value
	load_content_page = False

	submit_value = user_form['submit'].value 
	result_string = '<br/><hr/>'

	# connect to database, if exists
	conn = sqlite3.connect('nimbus.db') # automatically creates file if doesn't exist
	c = conn.cursor()

	if submit_value == 'Sign Up':
		confirm_password = user_form['confirm_password_field'].value
		if confirm_password != password:
			result_string += 'Passwords do not match, please try again!'
		else:
			c.execute('CREATE TABLE IF NOT EXISTS accounts(id INTEGER primary key, username varchar(250), password varchar(250), timestamp datetime)')
			c.execute('SELECT * FROM accounts WHERE username=?', (username,))
			existing_accounts = c.fetchall()

			if len(existing_accounts) > 0:
				result_string += 'Account already exists with username <b>' + username + '</b>.'
			else:
				current_time = datetime.datetime.now()
				salt = str(current_time)
				hasher = hashlib.md5()
				hasher.update(password)
				hasher.update(salt)
				encrypted_password = hasher.hexdigest()
				c.execute('INSERT INTO accounts (username, password, timestamp) VALUES (?, ?, ?)', (username, encrypted_password, current_time))
				result_string += 'Created new account with username <b>' + username + '</b>.'
				load_content_page = True

				cookie = Cookie.SimpleCookie()
   				cookie['current_time'] = current_time
    				cookie['username'] = username
				token = randint(0,99999999)
    				cookie['token'] = token
				
				c.execute('CREATE TABLE IF NOT EXISTS cookies(id INTEGER primary key, username varchar(250), token int)')
				c.execute('INSERT INTO cookies(username, token) VALUES (?,?,?)', (username, token))
			
				print cookie # important thing
	else:
		c.execute('SELECT * FROM accounts WHERE username=?', (username,))
		existing_account = c.fetchone()

		if not existing_account:
			result_string += 'Account not found.'
		else:
			existing_timestamp = existing_account[3]
			salt = str(existing_timestamp)
			hasher = hashlib.md5()
			hasher.update(password)
			hasher.update(salt)
			given_encrypted_password = hasher.hexdigest()
			existing_encrypted_password = existing_account[2]

			if given_encrypted_password == existing_encrypted_password:
				load_content_page = True
	 			result_string += 'Logged in! Welcome back :)'
	 		else:
	 			result_string += 'Incorrect password for account, try again please!'

	# read original HTML page and insert stylized result_string
	# original_page_request = urllib2.Request()
	page_url = 'http://nimsyllabus.com/index.html'

	if load_content_page:
		page_url = 'http://nimsyllabus.com/content.html'
		
	original_page = urllib.urlopen(page_url)
	original_page_text = original_page.read()
	augmented_text = original_page_text.replace('</body>', result_string + '</body>')
	print 'Content-Type: text/html\n\n' + augmented_text

	# complete database connection and HTML/CSS stub
	conn.commit()
	conn.close()

	#print '''
	#  </body>
	#</html>
	#'''
	
