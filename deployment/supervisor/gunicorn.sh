#!/bin/sh

# from config, needs values!
: "${PROJECT_ENV:?Need to set PROJECT_ENV non-empty}"
: "${PROJECT_NAME:?Need to set PROJECT_NAME non-empty}"
: "${PROJECT_SITE:?Need to set PROJECT_SITE non-empty}"
: "${WORKER_CLASS:?Need to set WORKER_CLASS non-empty}"
: "${WORKER_AMOUNT:?Need to set WORKER_AMOUNT non-empty}"

# build up
PROJECT_DIR="$HOME/sites/$PROJECT_NAME-$PROJECT_ENV"
THE_VENV="$PROJECT_DIR/virtualenv"
SOCKET="$PROJECT_DIR/../$PROJECT_SITE-$PROJECT_ENV.sock"

# launch
cd $PROJECT_DIR && \
./virtualenv/bin/gunicorn \
  --bind unix:///$SOCKET \
  --worker-class $WORKER_CLASS \
  --workers $WORKER_AMOUNT \
  project.wsgi \
