#!/bin/bash

set -o errexit
set -o nounset

exec watchfiles --filter python \
    'celery -A task.app worker -P gevent -c 10 --loglevel=info -Q default,email,sms,low_priority,high_priority'
# exec celery -A task.app worker -P gevent -c 10 --loglevel=info -Q default,email,sms,low_priority,high_priority
