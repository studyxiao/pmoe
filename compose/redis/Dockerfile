FROM redis:7-alpine

COPY redis.conf /usr/local/etc/redis/redis.conf

CMD ["/bin/sh", "-c", "redis-server /usr/local/etc/redis/redis.conf --requirepass ${REDIS_PASSWORD}"]
