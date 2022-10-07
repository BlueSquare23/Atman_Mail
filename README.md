# Ātman E-Mail Client

## Overview 

This project is a web-based Email client written in Python using the Flask web
framework. It works the same as any normal webmail client (ie. RoundCube,
Gmail, etc.) allowing the user to login and send and receive Emails. 

I was listening to an Alan Watts lecture about Hinduism and he mentioned Ātman.
The way he introduced it was as the pure and universally understandable
presence shared by all beings. Or rather, the pure feeling of being. To me it
just made sense as the name of an Email client. Ātman, Atman, @man. 

## Installation & Setup

### Server Setup

This is run just like any other Flask application. Of course the instructions
below are for spinning up the dev version. Production setup involves extra
steps depending on your hosting environment.

* First clone the repo:

```
git clone https://github.com/BlueSquare23/Atman_Mail
```

* Then install the required python modules:

```
cd Atman_Mail
virtualenv venv             # Virtual Env Optional
source venv/bin/activate    # Virtual Env Optional
pip3 install -r requirements.txt
```

* Next create the .env password file:

```
echo "PASS=''" > .env
```

* Finally run the project:

```
python3 app.py
```

### Client Setup

When you initially visit the site it will prompt you for the following setup
information.

	Email 
	Password 
	Outgoing Hostname 
	Incoming Hostname 
	SMTP Port 
	IMAP Port

After setup, you should be able to login with the Email and password provided
to send and receive Email. 

If the setup goes wrong you can always just burn the db file and restart the
app.

```
rm app/database.db
python app.py
```

## Technologies

* Language: [Python 3](https://www.python.org/)
* Web-Framework: [Flask](https://palletsprojects.com/p/flask/)
* Database: [SQLite](https://www.sqlite.org/index.html)
* ORM: [SQLAlchemy](https://www.sqlalchemy.org/)
* CSS: [Bootstrap](https://getbootstrap.com/docs/5.0/getting-started/introduction/)
* Protocol Modules: [smtplib](https://docs.python.org/3/library/smtplib.html), [imaplib](https://docs.python.org/3/library/imaplib.html)

## License

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png

#### Created by John R.
