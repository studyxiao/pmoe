#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

# MySQL 是否已成功启动
while !</dev/tcp/$MYSQL_HOST/$MYSQL_PORT; do
    echo "waiting database 1s"
    sleep 1
done
echo "database OK"

exec "$@"
