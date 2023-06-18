#!/bin/bash

set -o errexit
set -o nounset

worker_ready() {
    celery -A task.app inspect ping
}

until worker_ready; do
  >&2 echo 'Celery workers not available'
  sleep 1
done
>&2 echo 'Celery workers is available'
# task.app celery 实例
exec celery -A task.app flower\
    --basic_auth=${CELERY_FLOWER_USER}:${CELERY_FLOWER_PASSWORD} \
    --persistent=True \
    --db=/home/appuser/flower_db/flower.db \
    --state_save_interval=5000 \
    --port=5555
