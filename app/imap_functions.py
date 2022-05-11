import ssl
from email.message import EmailMessage
import email

def check_for_trash_folder(imap):
	resp_code, directories = imap.list()

	print("IMAP List Response Code : {}".format(resp_code))

	for directory in directories:
		print(directory.decode('utf-8'))
		directory_name = directory.decode().split('"')[-1].strip()
		if directory_name == "INBOX.Trash":
			print("Has Trash Folder!")
			return True

	return False

def delete_msg(imap, msg_num):
		resp_code, response = imap.store(str(msg_num), '+FLAGS', '\\Deleted')
		print("Response Code : {}".format(resp_code))
		print("Response      : {}\n".format(response[0].decode()))

		resp_code, response = imap.expunge()
		print("Response Code : {}".format(resp_code))
		print("Response      : {}\n".format(response[0].decode()))

def move_msg(imap, msg_num, src_folder, dst_folder):

	imap.select(mailbox=src_folder, readonly=False)

	try:
		# Copy Message to dst_folder
		resp_code, response = imap.copy(str(msg_num), dst_folder)
		print("Response Code : {}".format(resp_code))
		print("Response      : {}".format(response[0].decode()))

		# Delete Message from src_folder
		resp_code, response = imap.store(str(msg_num), '+FLAGS', '\\Deleted')
		print("Response Code : {}".format(resp_code))
		print("Response      : {}\n".format(response[0].decode()))

		# Expunge src_folder
		resp_code, response = imap.expunge()
		print("Response Code : {}".format(resp_code))
		print("Response      : {}\n".format(response[0].decode()))

		return True

	except:
		return False
	

def move_msg_to_trash(imap, msg_num, folder, del_pref):
	if check_for_trash_folder(imap) == True:

		imap.select(mailbox=folder, readonly=False)

		# Delete message if already in trash.
		if folder == "INBOX.Trash" or folder == "INBOX.Drafts" or del_pref == "delete":
			delete_msg(imap, msg_num)
			return "Deleted"
		# Otherwise move message to the trash and then delete from current
		# folder.
		else:
			resp_code, response = imap.copy(str(msg_num), "INBOX.Trash")
			print("Response Code : {}".format(resp_code))
			print("Response      : {}".format(response[0].decode()))
			
			delete_msg(imap, msg_num)

			return "Trashed"
	else:
		return False

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
			pass

	return messages

def get_msg_body_string(msg):
	msg_string_header = f"From: {msg['from']}\nDate: {msg['date']}\nSubject: {msg['subject']}\n\n"
	
	if msg.get_content_type() == "text/plain":
		return msg_string_header + msg.get_payload()

	for parte in msg.walk():
		if parte.get_content_type() == "text/plain":
			return msg_string_header + str(parte)

def get_msg_body(imap, msg_num, folder):
	imap.select(str(folder), readonly=True)
	resp_code, msg_data = imap.fetch(str(msg_num), '(RFC822)') ## Fetch mail data.
	for response_part in msg_data:
		if isinstance(response_part, tuple):
			msg_bytes = response_part[1]
			msg = email.message_from_bytes(msg_bytes)
			return get_msg_body_string(msg)

def get_id_list(imap, folder):
	# Select all mailbox information.
	imap.select(str(folder), readonly=True)

	type, data = imap.search(None, 'ALL')
	mail_ids = data[0].decode('utf-8')
	id_list = mail_ids.split()
	return id_list

