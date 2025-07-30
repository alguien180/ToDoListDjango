#!/bin/bash 
set -e  # Exit on first error

python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput 
exec gunicorn ToDoList.wsgi:application --bind 0.0.0.0:8000
