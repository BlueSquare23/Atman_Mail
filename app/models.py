from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(150), unique=True)
	password = db.Column(db.String(150))

class Connection(db.Model):
	id =  db.Column(db.Integer, primary_key=True)
	outgoing_hostname = db.Column(db.String(150))
	incoming_hostname = db.Column(db.String(150))
	smtp_port = db.Column(db.Integer)
	imap_port = db.Column(db.Integer)
	date_created = db.Column(db.DateTime(timezone=True), default=func.now())

class Settings(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	del_button_behavior = db.Column(db.String(150), default="trash")
	num_msg_per_page = db.Column(db.Integer, default=10)

