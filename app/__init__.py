from os import path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import sys

# Prevent creation of __pycache__. Cache fucks up auth.
sys.dont_write_bytecode = True

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
	app = Flask(__name__)
	app.config['SECRET_KEY'] = "AllYourBaseAreBelongToUs"
	app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	db.init_app(app)

	# Pull in our pages route(s)
	from .pages import pages 
	app.register_blueprint(pages, url_prefix="/")

	# Pull in our auth route(s)
	from .auth import auth 
	app.register_blueprint(auth, url_prefix="/")

	# Initialize DB
	from .models import User
	create_database(app)

	# Setup LoginManager
	login_manager = LoginManager()
	# Redirect to auth.login if not already logged in.
	login_manager.login_view = "auth.login"
	login_manager.login_message = None
	login_manager.init_app(app)

	# Decorator to set up login session.
	@login_manager.user_loader
	def load_user(id):
		return User.query.get(int(id))

	return app

# DB Setup
def create_database(app):
	if not path.exists("app/" + DB_NAME):
		db.create_all(app=app)
		print(" * Created Database!")
