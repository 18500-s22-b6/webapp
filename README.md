# webapp

***** Creating a virtual environment
python3 -m venv venv_18-500

***** Activate a virtual environment
- Mac: source venv_18-500/bin/activate
- Windows: venv_18500\Scripts\activate.bat


Tutorial from here follows https://docs.djangoproject.com/en/4.0/intro/tutorial01/
with some modification from 17-437 (Webapps)

***** Install Django:
pip install django

***** Install requierd Django submodules:
pip install django-phonenumber-field[phonenumbers]
pip install social-auth-app-django

***** Create Django project:
django-admin startproject webapps

***** Create Django app:
python3 manage.py startapp food_tracker

***** Create database:
python3 manage.py makemigrations
python3 manage.py migrate

***** Run server:
python3 manage.py runserver 8080

Common bugs
**no such table ...**
python3 manage.py migrate --run-syncdb


CSS Bootstrap Tutorial from https://www.tutorialrepublic.com/twitter-bootstrap-tutorial/
