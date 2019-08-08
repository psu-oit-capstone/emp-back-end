@REM Call with a -p flag to populate the dummy database
@REM eg 'launch.bat -p' to populate and launch, 'launch.bat' to just launch

@echo off

IF "%1" NEQ "-p" goto:nopopulate

echo Populating back-end test

echo making migrations
python manage.py makemigrations
python manage.py migrate

echo Populating Identity table
python manage.py loaddata identity.json
echo Populating Emergency table
python manage.py loaddata emergency.json
echo Populating Contact table
python manage.py loaddata contact.json
echo Populating Relation table
python manage.py loaddata relation.yaml
echo Populating Nation table
python manage.py loaddata nation.yaml
echo Populating State table
python manage.py loaddata state.yaml


:nopopulate

echo launching back-end
start python manage.py runserver