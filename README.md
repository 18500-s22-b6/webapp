# webapp for b6 food tracker


----------
HOW TO RUN

- Tutorial from here follows https://docs.djangoproject.com/en/4.0/intro/tutorial01/
- with some modification from 17-437 (Webapps)

***** Creating a virtual environment
python3 -m venv venv_18-500


***** Activate a virtual environment
- Mac: source venv_18-500/bin/activate
- Windows: venv_18500\Scripts\activate.bat


***** Install Django:
pip install django


***** Install required Django submodules:
pip install -r requirements.txt

(to manually install...)
pip install django-phonenumber-field[phonenumbers]
pip install social-auth-app-django
pip install django-sslserver
pip install jsonschema
pip install django-crispy-forms
pip install crispy-bootstrap5


***** Create database:
python3 manage.py makemigrations
python3 manage.py migrate


***** Run server:
python3 manage.py runserver 8000


----------
COMMON BUGS

***** no such table:
python3 manage.py migrate --run-syncdb

***** no column:
- DELETE db.sqlite3
- python3 manage.py migrate --run-syncdb
- run server :-)

***** Nonetype
- Log out of website
- Log back in again

CSS Bootstrap Tutorial from https://www.tutorialrepublic.com/twitter-bootstrap-tutorial/


----------
INTERNAL DEVELOPMENT NOTES

***** Create Django project:
django-admin startproject webapps

***** Create Django app:
python3 manage.py startapp food_tracker

***** Create Django superuser
python3 manage.py createsuperuser
(Use admin console by using (Base url)/admin) and entering username and password


----------
EC2 INFORMATION

***** aws.amazon.com
ssh -i "food_tracker.pem" 
ubuntu@ec2-XX-XX-XX-XX.compute-1.amazonaws.com


***** "attempt to write a readonly database"
sudo chown www-data:www-data db.sqlite3
