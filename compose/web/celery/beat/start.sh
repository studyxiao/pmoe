#!/bin/bash

set -o errexit
set -o nounset

exec celery -A task.app beat -l info
