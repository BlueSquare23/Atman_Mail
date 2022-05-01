from flask import Blueprint, render_template, request, flash, url_for, redirect
from flask_login import login_required, current_user
from .models import User
from . import db
import smtplib 
import ssl
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv
import imaplib
import email
import os

# Load environment vars
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

PASS = os.environ['PASS'] 

pages = Blueprint("pages", __name__)

@pages.route("/", methods=['GET'])
@pages.route("/home", methods=['GET'])
@login_required
def home():
	msg_num = request.args.get('msg_num')
	folder = request.args.get('folder')
	page_num = request.args.get('page_num')

	if folder == None:
		full_url = url_for('.home', folder="INBOX", **request.args)
		return redirect(full_url)

	imap_host = User.query.first().outgoing_hostname
	imap_user = User.query.first().email
	imap_pass = PASS

	def message_list(id_list):
		for i in id_list:
			typ, msg_data = imap.fetch(str(i), '(RFC822)')
			for response_part in msg_data:
				if isinstance(response_part, tuple):
					msg = email.message_from_bytes(response_part[1])
					messages.insert(0, [str(msg['from']), str(msg['subject']), str(msg['date'])])

	def get_msg_body(msg_num):
		resp_code, msg_data = imap.fetch(str(msg_num), '(RFC822)') ## Fetch mail data.
		for response_part in msg_data:
			if isinstance(response_part, tuple):
				msg = email.message_from_bytes(response_part[1])
				if msg.get_content_type() == "text/plain":
					return "From: " + msg['from'] + "\n" + "Subject: " + msg['subject'] + "\n\n" + msg.get_payload()
				else:
					for part in msg.walk():
						print(part.get_content_type())
						if part.get_content_type() == "text/plain":
							return "From: " + msg['from'] + "\n" + "Subject: " + msg['subject'] + "\n\n" + str(part)
		
	# connect to host using SSL
	imap = imaplib.IMAP4(imap_host)
	imap.starttls()
	
	# login to server
	imap.login(imap_user, imap_pass)
	
	# List directories
	resp_code, directories = imap.list()
	
	folders = {}
	
	# Pull out folder names and number of messages.
	for directory in directories:
		directory_name = directory.decode().split('"')[-1].strip()
		resp_code, mail_count = imap.select(mailbox=directory_name, readonly=True)
		folders.update({directory_name: str(mail_count[0], 'utf-8')})
	
	sorted_folders = {}

	for key in sorted(folders.keys()):
		sorted_folders.update({key: folders[key]})

	# Select all mailbox information.
	imap.select(str(folder), readonly=True)

	type, data = imap.search(None, 'ALL')
	mail_ids = data[0].decode('utf-8')
	id_list = mail_ids.split()

	# Initialize empty messages list.
	messages = []

	if page_num == None:
		full_url = url_for('.home', page_num=1, **request.args)
		return redirect(full_url)

	# 10 Messages per page.
	if int(id_list[-1]) > 10:
		last_msg_of_page = 11 * int(page_num)
		first_msg_of_page = last_msg_of_page - 10
		id_list = range(int(id_list[-last_msg_of_page]), int(id_list[-first_msg_of_page]))
		print(id_list)

	# If there are messages in the mailbox.
	if id_list:
		# If no GET parameter, do latest message.
		if msg_num == None:
			msg_num = id_list[-1]
			full_url = url_for('.home', msg_num=msg_num, **request.args)
			return redirect(full_url)
		if int(msg_num) > id_list[-1]:
			msg_num = id_list[-1]
			full_url = url_for('.home', msg_num=msg_num, folder=folder)
			return redirect(full_url)
		
		# Get message list info.
		message_list(id_list)

		body=get_msg_body(msg_num)
	else:
		if msg_num != None:
			msg_num = id_list[-1]
			full_url = url_for('.home', **request.args)
			return redirect(full_url)
		if msg_num == None:
			body="No message in folder!"

	return render_template("home.html", user=current_user, sorted_folders=sorted_folders, messages=messages, body=body)

@pages.route("/send", methods=['GET', 'POST'])
@login_required
def send():
	if request.method == 'POST':
		to_addr = request.form.get("to_addr")
		subject = request.form.get("subject")
		body = request.form.get("body")
		from_addr = User.query.first().email
		outgoing_hostname = User.query.first().outgoing_hostname
		smtp_port = User.query.first().smtp_port

		message = EmailMessage()
		message["To"]      = to_addr
		message["From"]    = from_addr
		message["Subject"] = subject 
		message.set_payload(body)

		if smtp_port == 465:
			s = smtplib.SMTP_SSL(outgoing_hostname, smtp_port)
		else:
			s = smtplib.SMTP(outgoing_hostname, smtp_port)
			s.starttls(context=ssl.create_default_context())

		try:
			s.login(from_addr, PASS)
			s.sendmail(from_addr, to_addr, message.as_string())
			s.quit()
			flash("Message Sent!", category='success')
		except:
			flash("Sending Failed!", category='error')


		print("Sent message!")

	return render_template("send.html", user=current_user)
