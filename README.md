
# djangocms4test

Test the new django-cms v4

## Quickstart

To bootstrap the project on your machine::

    cd djangocms4test
    mkvirtualenv djangocms4test  # or any other way to have your virtualenv
    pip install -U pip setuptools wheel
    pip install -r requirements/dev.txt
    cp project/env-dev-example ./.env  # adapt some lines in there.
    manage.py createsuperuser
    manage.py runserver

