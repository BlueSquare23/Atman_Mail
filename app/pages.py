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

	def sort_folders(imap):
		# List directories
		resp_code, directories = imap.list()

		folders = {}
		
		print("Directories")
		# Pull out folder names and number of messages.
		for directory in directories:
			directory_name = directory.decode().split('"')[-1].strip()
			try:
				resp_code, mail_count = imap.select(mailbox=directory_name, readonly=True)
				folders.update({directory_name: str(mail_count[0], 'utf-8')})
			except:
				print(f"Cannot get number of messages for: {directory_name}")
		
		sorted_folders = {}

		for key in sorted(folders.keys()):
			sorted_folders.update({key: folders[key]})

		return sorted_folders

	def message_list(id_list):
		# Select all mailbox information.
		imap.select(str(folder), readonly=True)

		# Initialize empty messages list.
		messages = []
		for i in id_list:
			try:
				typ, msg_data = imap.fetch(str(i), '(RFC822)')
				for response_part in msg_data:
					if isinstance(response_part, tuple):
						msg = email.message_from_bytes(response_part[1])
						messages.insert(0, [i, str(msg['from']), str(msg['subject']), str(msg['date'])])
			except:
				print("Out of range, Will l3rn 2 c0d3 2morrow!")

		return messages

	def get_msg_body(msg_num):
		resp_code, msg_data = imap.fetch(str(msg_num), '(RFC822)') ## Fetch mail data.
		for response_part in msg_data:
			if isinstance(response_part, tuple):
				msg = email.message_from_bytes(response_part[1])
				if msg.get_content_type() == "text/plain":
					return "Index Number: " + str(msg_num) + "\n" + "From: " + str(msg['from']) + "\n" + "Subject: " + str(msg['subject']) + "\n\n" + msg.get_payload()
				else:
					for part in msg.walk():
						print(part.get_content_type())
						if part.get_content_type() == "text/plain":
							return "Index Number: " + str(msg_num) + "\n" + "From: " + str(msg['from']) + "\n" + "Subject: " + str(msg['subject']) + "\n\n" + str(part)
	def get_id_list(imap):
		# Select all mailbox information.
		imap.select(str(folder), readonly=True)

		type, data = imap.search(None, 'ALL')
		mail_ids = data[0].decode('utf-8')
		id_list = mail_ids.split()
		return id_list

	# Connection settings.
	imap_host = User.query.first().outgoing_hostname
	imap_user = User.query.first().email
	imap_pass = PASS

	# Initialize connection.
	imap = imaplib.IMAP4(imap_host)
	imap.starttls()
	
	# Auth to the server.
	imap.login(imap_user, imap_pass)
	
	# GET parameters
	msg_num = request.args.get('msg_num', type = int)
	folder = request.args.get('folder')
	page_num = request.args.get('page_num', type = int)

	# Handel if GET parameters are not supplied.
	# num_msg_per_page Messages per page.
	num_msg_per_page = 10

	# If folder is not supplied,
	if bool(folder) != True:
		# Default to loading the INBOX.
		full_url = url_for('.home', folder="INBOX", **request.args)
		return redirect(full_url)

	# If page_num is unspecified,
	if bool(page_num) != True:
		# Go to first page,
		full_url = url_for('.home', page_num=1, **request.args)
		return redirect(full_url)
	
	# If the msg_num is unspecified, 
	if bool(msg_num) != True:
		# And there are messages in the folder, 
		id_list = get_id_list(imap)
		if id_list != []:
			# Default to the latest message on the page.
			print("Page Num: " + str(page_num))
			print("Most Recent Email ID: " + str(id_list[-1]))

			top_msg_on_page = int(id_list[-1]) - (num_msg_per_page * page_num) + num_msg_per_page
			print(top_msg_on_page)
			full_url = url_for('.home', msg_num=top_msg_on_page, **request.args)
			return redirect(full_url)
			# Default to the latest message in the box.
			#full_url = url_for('.home', msg_num=id_list[-1], **request.args)
			#return redirect(full_url)


	# If there are no messages in the folder,
	if get_id_list(imap) == []:
		messages = ""
		body = "No messages in folder!"
		num_pages = 1
	else:
		last_msg_num = int(get_id_list(imap)[-1]) + 1

		# Find page number from msg_num.
		difference = last_msg_num - int(msg_num)
		correct_page_num = int(difference / num_msg_per_page) + (difference % num_msg_per_page > 0)

		# If not on the right page change pages,
		if int(page_num) != correct_page_num:
			full_url = url_for('.home', page_num=correct_page_num, folder=folder, msg_num=msg_num)
			return redirect(full_url)

		# By this point the page_num, and msg_num should be set correctly.

		# Set messages list based off of page_num and msg_num.

		# Round up integer division to get number pages total.
		num_pages = int(last_msg_num / num_msg_per_page) + (last_msg_num % num_msg_per_page > 0)

		#print("Number of pages: " + str(num_pages))

		# Magic pagination algorithm. Do not touch!
		#print(range((last_msg_num - (num_msg_per_page * page_num)), (last_msg_num - ((page_num - 1) * num_msg_per_page))))
		messages = message_list(range((last_msg_num - (num_msg_per_page * page_num)), (last_msg_num - ((page_num - 1) * num_msg_per_page))))
		body = get_msg_body(msg_num)

# All messages on one page.
#		messages = message_list(get_id_list(imap))
#		body = get_msg_body(msg_num)

	return render_template("home.html", user=current_user, sorted_folders=sort_folders(imap), messages=messages, body=body, num_pages=num_pages)

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
