# Emergency Management Back-End

## Purpose
This app will serve three main functions:
1. Host the sample data used for development and testing of the Emergency Management interface. 
The data is kept in an in-memory SQLite database that is modeled after relevant tables in the 
Banner database. 
2. Serve the data to the front-end (Vue) application.  You may want to take advantage of the 
Django REST framework, and/or the django-cors-headers plugin.
3. Simulate a login process that generates a JWT which is passed back to the front-end (Vue) 
application.  All subsequent API calls from the Vue app must provide this JWT in the 
Authorization header. Use Python's PyJWT library for this.

## System Requirements
* Python >= 3.6
* Django  2.2.1

## Running the app locally
The first time you run this app locally, you'll need to do the following to set up the database:
1. `python manage.py makemigrations`
2. `python manage.py migrate`
3. *load the sample data:* 
    * `python manage.py loaddata identity.json`
    * `python manage.py loaddata emergency.json`
    * `python manage.py loaddata contact.json`
    * `python manage.py loaddata relation.yaml`

## JWT Requirements
In order for the finished project to be compatible with the JWT authentication we use in our 
other apps, the JWT you create should provide the following data using the following keys:
* first: First name
* last = Last name
* username = Username / Login name
* email = Campus email address