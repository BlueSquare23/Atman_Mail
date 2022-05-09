from flask import Blueprint, render_template, request, flash, url_for, redirect
from flask_login import login_required, current_user
from .models import User, Settings, Connection
from . import db
import smtplib 
import time
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv
import imaplib
import email
import os
import re
from .imap_functions import sort_folders, message_list, get_msg_body, get_id_list, move_msg_to_trash, move_msg

# Load environment vars
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

PASS = os.environ['PASS'] 

pages = Blueprint("pages", __name__)


def use_imap():
	# Connection settings.
	imap_host = Connection.query.first().outgoing_hostname
	imap_user = User.query.first().email
	imap_pass = PASS

	# Initialize connection.
	imap = imaplib.IMAP4(imap_host)
	imap.starttls()
	
	# Auth to the server.
#	try:
	imap.login(imap_user, imap_pass)
	imap.select()
#		return imap
#	except:
#		exception = sys.exc_info()[0]
#		print(type(exception))
#
	return imap
	



######### Home Page #########

@pages.route("/", methods=['GET'])
@pages.route("/home", methods=['GET'])
@login_required
def home():
	# Settings db object.
	if Settings.query.first() is None:
		settings = Settings(del_button_behavior="trash", num_msg_per_page=10)
		db.session.add(settings)
		db.session.commit()
	
	settings = Settings.query.first()

	# num_msg_per_page Messages per page.
	num_msg_per_page = settings.num_msg_per_page

	imap = use_imap()
	print("------------")
	print(imap)
	print("------------")

	# GET parameters
	msg_num = request.args.get('msg_num', type = int)
	folder = request.args.get('folder')
	page_num = request.args.get('page_num', type = int)

	# Handel if GET parameters are not supplied.

	# If folder is not supplied,
	if bool(folder) != True:
		# Default to loading the INBOX.
		full_url = url_for('.home', folder="INBOX", **request.args)
		imap.close()
		imap.logout()
		return redirect(full_url)

	# If page_num is unspecified,
	if bool(page_num) != True:
		# Go to first page,
		full_url = url_for('.home', page_num=1, folder=folder)
		imap.close()
		imap.logout()
		return redirect(full_url)
	
	# If the msg_num is unspecified, 
	if bool(msg_num) != True:
		# And there are messages in the folder, 
		id_list = get_id_list(imap, folder)
		if id_list != []:
			# Default to the latest message on the page.
			print("Page Num: " + str(page_num))
			print("Most Recent Email ID: " + str(id_list[-1]))

			top_msg_on_page = int(id_list[-1]) - (num_msg_per_page * page_num) + num_msg_per_page
			print(top_msg_on_page)
			full_url = url_for('.home', msg_num=top_msg_on_page, folder=folder, page_num=page_num)
			imap.close()
			imap.logout()
			return redirect(full_url)

	# If there are no messages in the folder,
	if get_id_list(imap, folder) == []:
		messages = ""
		body = "No messages in folder!"
		num_pages = 1
	else:
		last_msg_num = int(get_id_list(imap, folder)[-1]) 

		# Find page number from msg_num.
		difference = last_msg_num - int(msg_num)
		correct_page_num = int(difference / num_msg_per_page) + 1

		# If not on the right page change pages,
		if int(page_num) != correct_page_num:
			print("I Farted")
			full_url = url_for('.home', page_num=correct_page_num, folder=folder, msg_num=msg_num)
			imap.close()
			imap.logout()
			return redirect(full_url)

		# By this point the page_num, and msg_num should be set correctly.

		# Set messages list based off of page_num and msg_num.

		# Round up integer division to get number pages total.
		print("-----------")
		print("Last Msg Num: "+str(last_msg_num))
		print("Num Msg Per Page: "+str(num_msg_per_page))
		print("Last Msg Num % Num Msg Per Page: "+str(last_msg_num % num_msg_per_page))
		print("-----------")
		num_pages = int(last_msg_num / num_msg_per_page) + (last_msg_num % num_msg_per_page > 0)

		# Magic pagination algorithm. Do not touch!
		messages = message_list(imap, folder, range((last_msg_num - (num_msg_per_page * page_num) + 1), (last_msg_num - ((page_num - 1) * num_msg_per_page) + 1)))
		body = get_msg_body(imap, msg_num, folder)

# All messages on one page.
#		messages = message_list(imap, folder, get_id_list(imap))
#		body = get_msg_body(msg_num)

	sorted_folders = sort_folders(imap)

	return render_template("home.html", user=current_user, sorted_folders=sorted_folders, messages=messages, body=body, num_pages=num_pages)



######### Send Page #########

@pages.route("/send", methods=['GET', 'POST'])
@login_required
def send():
	if request.method == 'POST':
		to_addr = request.form.get("to_addr")
		subject = request.form.get("subject")
		body = request.form.get("body")
		draft = request.form.get("draft")
		from_addr = Connection.query.first().email
		outgoing_hostname = Connection.query.first().outgoing_hostname
		smtp_port = Connection.query.first().smtp_port

		message = EmailMessage()
		message["To"]      = to_addr
		message["From"]    = from_addr
		message["Subject"] = subject 
		message.set_payload(body)

		if bool(draft) == True:
			imap = use_imap()
			imap.select('INBOX.Drafts')
			imap.append('INBOX.Drafts', '', imaplib.Time2Internaldate(time.time()), str(message).encode("utf-8"))
			flash("Message saved to Drafts.", category='success')
			imap.close()
			imap.logout()

			full_url = url_for('.home')
			return redirect(full_url)

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
			full_url = url_for('.home')
			return redirect(full_url)
		except:
			flash("Sending Failed!", category='error')
			full_url = url_for('.send')
			return redirect(full_url)
	else:
		# GET parameters
		msg_num = request.args.get('msg_num', type = int)
		folder = request.args.get('folder')
		mode = request.args.get('mode')

		if bool(msg_num) != True or bool(msg_num) != True or bool(mode) != True:
			body = None
			to_addr = None
			subject = None
		else:
			imap = use_imap()
			body = get_msg_body(imap, msg_num, folder)
			print("#############  Message Body")

			# Get subject.
			subject_line = body.split('\n', 3)[2]
			subject = subject_line.split(":",1)[1].strip()

			# Reformat body text.
			if mode == "reply":
				# Pull out from addr using regex.
				from_line = body.partition('\n')[0]
				from_addr = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', from_line).group(0)
				to_addr = from_addr
				if folder == "INBOX.Drafts":
					new_body_list = []
					should_append = False
					for line in body.splitlines():
						if should_append == True:
							new_body_list.append(line)
						if "Subject" in line:
							should_append = True

					# First line after "Subject:" is always a space.
					new_body_list.pop(0)

					body = '\n'.join(new_body_list)

					# Delete message from drafts.
					move_msg_to_trash(imap, msg_num, folder)
					flash("Message removed from Drafts!", category='success')
				else:
					subject = "Re: " + subject

					results = []
					results.append("> --------------- Original Message ---------------")
					results.append("> ")

					# Add leading > Chars to body.
					for line in body.split('\n'):
						results.append("> " + line)

					body = '\n\n' + '\n'.join(results)

			elif mode == "forward":
				to_addr = None
				subject = "Fwd: " + subject

				results = []
				results.append("--------------- Original Message ---------------")

				# Add leading > Chars to body.
				for line in body.split('\n'):
					results.append(line)

				body = '\n\n' + '\n'.join(results)


			imap.close()
			imap.logout()

		return render_template("send.html", user=current_user, body=body, to_addr=to_addr, subject=subject)



######### Settings Page #########

@pages.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
	gen_settings = Settings.query.first()

	num_msg_per_page = gen_settings.num_msg_per_page
	del_button_behavior = gen_settings.del_button_behavior

	if request.method == 'POST':
		page = request.form.get("page")
		num_msg_per_page = request.form.get("num_msg_per_page", type = int)
		del_button_behavior = request.form.get("del_button_behavior")

		if bool(page) == True and page == "general":
			if bool(num_msg_per_page) != True or bool(del_button_behavior) != True:
				flash("Settings Missing!", category='error')
				return render_template("settings.html", user=current_user, page="general")
			else:
				Settings.query.first().del_button_behavior = del_button_behavior
				Settings.query.first().num_msg_per_page = num_msg_per_page
				db.session.commit()
				flash('General Settings Updated!', category='success')
				full_url = url_for('.settings', page="general")
				return redirect(full_url)

		print("Page: " + page)
		print("Num Msg Per Page: " + str(num_msg_per_page))
		print("Del Button Behavior: " + del_button_behavior)

		return render_template("settings.html", user=current_user, page="general", num_msg_per_page=num_msg_per_page, del_button_behavior=del_button_behavior)
	else:
		page = request.args.get("page")

		if bool(page) != True:
			page = "general"


		return render_template("settings.html", user=current_user, page="general", num_msg_per_page=num_msg_per_page, del_button_behavior=del_button_behavior)
	


######### Delete Page #########

@pages.route("/delete", methods=['POST'])
@login_required
def trash():
	gen_settings = Settings.query.first()

	msg_num = request.form.get("msg_num")
	folder = request.form.get("folder")

	if bool(msg_num) != True or bool(folder) != True:
		full_url = url_for('.home')
		return redirect(full_url)
	else:
		imap = use_imap()
		response = move_msg_to_trash(imap, msg_num, folder, del_pref=gen_settings.del_button_behavior)
		if response == "Trashed":
			flash("Message moved to Trash!", category='success')
			full_url = url_for('.home', folder=folder)
			imap.close()
			imap.logout()
			return redirect(full_url)
		elif response == "Deleted":
			flash("Message Permanently Deleted!", category='success')
			full_url = url_for('.home', folder=folder)
			imap.close()
			imap.logout()
			return redirect(full_url)
		else:
			flash("Error!", category='error')
			full_url = url_for('.home', folder=folders)
			imap.close()
			imap.logout()
			return redirect(full_url)
		imap.close()
		imap.logout()



######### Move Page #########

@pages.route("/move", methods=['GET'])
@login_required
def msg_move():
	msg_num = request.args.get('msg_num', type = int) 
	src_folder = request.args.get("src_folder", type  = str)
	dst_folder = request.args.get("dst_folder", type = str)

	if bool(msg_num) != True or bool(src_folder) != True or bool(dst_folder) != True:
		flash("Error!", category='error')
		full_url = url_for('.home')
		return redirect(full_url)
	elif src_folder == dst_folder:
		flash(f"Message already in {src_folder}!", category='error')
		full_url = url_for('.home')
		return redirect(full_url)
	else:
		print(msg_num)
		print(src_folder)
		print(dst_folder)

		imap = use_imap()

		result = move_msg(imap, msg_num, src_folder, dst_folder)
		if result == True:
			flash(f"Message moved to {dst_folder}!", category='success')
			return redirect(f"/home?folder={src_folder}")
		else:
			flash("Error moving message!", category='error')
			return redirect(f"/home?folder={src_folder}")




	






