#!/bin/bash

set -o errexit
set -o nounset

exec celery -A app.wsgi.celery beat -l info
