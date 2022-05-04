import ssl
from email.message import EmailMessage
import email

def sort_folders(imap):
	# List directories
	resp_code, directories = imap.list()

	folders = {}
	
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

def message_list(imap, folder, id_list):
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
			print("Out of range, Will l34rn 2 c0d3 2morrow!")

	return messages

def get_msg_body(imap, msg_num, folder):
	resp_code, msg_data = imap.fetch(str(msg_num), '(RFC822)') ## Fetch mail data.
	for response_part in msg_data:
		if isinstance(response_part, tuple):
			msg = email.message_from_bytes(response_part[1])
			if msg.get_content_type() == "text/plain":
				return "From: " + str(msg['from']) + "\n" + "Date: " + str(msg['date']) + "\n" + "Subject: " + str(msg['subject']) + "\n\n" + msg.get_payload()
			else:
				for part in msg.walk():
					print(part.get_content_type())
					if part.get_content_type() == "text/plain":
						return "From: " + str(msg['from']) + "\n" + "Date: " + str(msg['date']) + "\n" + "Subject: " + str(msg['subject']) + "\n\n" + str(part)

def get_id_list(imap, folder):
	# Select all mailbox information.
	imap.select(str(folder), readonly=True)

	type, data = imap.search(None, 'ALL')
	mail_ids = data[0].decode('utf-8')
	id_list = mail_ids.split()
	return id_list

