# webapp

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

***** Create database: 
python3 manage.py migrate

***** Run server: 
python3 manage.py runserver 8000


COMMON BUGS

***** no such table: 
python3 manage.py migrate --run-syncdb


CSS Bootstrap Tutorial from https://www.tutorialrepublic.com/twitter-bootstrap-tutorial/


INTERNAL DEVELOPMENT NOTES

***** Create Django project: 
django-admin startproject webapps

***** Create Django app: 
python3 manage.py startapp food_tracker