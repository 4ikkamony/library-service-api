#!/bin/sh

python manage.py migrate
python manage.py loaddata fixtures/demo_data.json
python manage.py runserver 0.0.0.0:8000
