from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db
from .models import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from pathlib import Path

# Load environment vars
env_path = Path('.') / '.env'

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=['GET', 'POST'])
def login():
	if User.query.first() == None:
		flash("Please add a user!", category='success')
		return redirect(url_for('auth.signup'))

	if request.method == 'POST':
		email = request.form.get("email")
		password = request.form.get("password")

		# Check login info
		user = User.query.filter_by(email=email).first()
		if user:
			if check_password_hash(user.password, password):
				flash("Logged in!", category='success')
				login_user(user, remember=True)
				return redirect(url_for('pages.home'))
			else:
				flash('Password incorrect.', category='error')
		else:
			flash('Email does not exist.', category='error')

	return render_template("login.html", user=current_user)

@auth.route("/signup", methods=['GET', 'POST'])
def signup():
	if request.method == 'POST':
		# Collect form data
		email = request.form.get("email")
		password1 = request.form.get("password1")
		password2 = request.form.get("password2")
		outgoing_hostname = request.form.get("outgoing_hostname")
		incoming_hostname = request.form.get("incoming_hostname")
		smtp_port = request.form.get("smtp_port")
		imap_port = request.form.get("imap_port")

		# Check if submitted form data for issues 
		email_exists = User.query.filter_by(email=email).first()

		if email_exists:
			flash('Email is already in use.', category='error')
		elif password1 != password2:
			flash('Passwords don\'t match!', category='error')
		elif len(password1) < 8:
			flash('Password is too short.', category='error')
		else:
			# Add the new_user to the database, then redirect home
			new_user = User(email=email, password=generate_password_hash(password1, method='sha256'), incoming_hostname=incoming_hostname, outgoing_hostname=outgoing_hostname, smtp_port=smtp_port, imap_port=imap_port)
			db.session.add(new_user)
			db.session.commit()

			# Write password to .env file.
			f = open(env_path, "w")
			f.write(f"PASS='{password1}'")
			f.close()

			os.chmod(env_path, 0o600)

			flash('User created!')
			login_user(new_user, remember=True)
			return redirect(url_for('pages.home'))

	if User.query.first() == None:
		return render_template("signup.html", user=current_user)
	else:
		flash("User already added. Please sign in!", category='success')
		return redirect(url_for('auth.login'))

@auth.route("/logout")
@login_required
def logout():
	logout_user()
	flash('Logged out!', category='success')
	return redirect(url_for("pages.home"))
