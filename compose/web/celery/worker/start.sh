#!/bin/bash

set -o errexit
set -o nounset

exec celery -A app.app.celery_app worker --loglevel=info
