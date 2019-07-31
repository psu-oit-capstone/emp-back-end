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

## Setup Instructions
### Python
This program calls on several packages while it runs. To install these packages use
```bash
pip3 install -r requirements.txt
```
This tells `pip3` (the Python 3 package manager) to install each of the noted package versions
in the requirements file.

### Sqlite3
Sqlite is a lightweight database which is really easy to interface with. We can install sqlite3 using
```bash
sudo apt install sqlite3
```
Conveniently, the Python package for interfacing with sqlite is default to Python -- no download
required. You can now interact with the database via the command `sqlite3` on the command line, or
using a GUI like "DB Browser for SQLite" found on the Ubuntu Software Store (free). Our sqlite
databases will be stored in the file "db.sqlite3".

## Running the app locally
The first time you run this app locally, you'll need to do the following to set up the database:
1. `python manage.py makemigrations`
2. `python manage.py migrate`
3. *load the sample data:*
    * `python manage.py loaddata identity.json`
    * `python manage.py loaddata emergency.json`
    * `python manage.py loaddata contact.json`
    * `python manage.py loaddata relation.yaml`
    * `python manage.py loaddata nation.yaml`
    * `python manage.py loaddata state.yaml`

## JWT Requirements
In order for the finished project to be compatible with the JWT authentication we use in our
other apps, the JWT you create should provide the following data using the following keys:
* first: First name
* last = Last name
* username = Username / Login name
* email = Campus email address
