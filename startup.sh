#!/bin/bash 
python3 manage.py collectstatic --noinput 
gunicorn task_manager.wsgi:application --bind 0.0.0.0:8000