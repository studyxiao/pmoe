# syntax=docker/dockerfile:1
# builder 安装依赖
FROM python:3.11.3-slim-bullseye AS builder

# security updates and bug fixes
RUN <<EOF
    apt-get update
    apt-get upgrade -y
EOF

# activate virtual environment
ENV VIRTUAL_ENV=/home/appuser/.venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# install dependencies
RUN --mount=type=cache,target=/root/.cache/pip <<EOF
    pip install --upgrade pip setuptools wheel
    pip install pdm
EOF
COPY --link pyproject.toml pdm.lock ./
RUN --mount=type=cache,target=/root/.cache/pdm pdm sync

# stage 2
FROM python:3.11.3-slim-bullseye

# security updates and bug fixes
RUN <<EOF
    apt-get update
    apt-get upgrade -y
    rm -rf /var/lib/apt/lists/*
EOF

# switch to non-root user
RUN useradd -m -s /bin/bash -u 1000 appuser
USER appuser
WORKDIR /home/appuser

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# activate virtual environment
COPY --link --from=builder /home/appuser/.venv /home/appuser/.venv
ENV VIRTUAL_ENV=/home/appuser/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# copy shell script
COPY --link --chown=appuser compose/web/entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENTRYPOINT [ "./entrypoint.sh" ]

CMD ["flask", "run", "--host","0.0.0.0", "--port", "8000"]
