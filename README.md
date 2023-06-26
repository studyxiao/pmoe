[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

开箱即用的 flask + Gunicorn + Nginx + Docker Web Application 开发、部署方案。满足 12 factor 指导原则和 CI/CD 开发流程。

## Port

- web: 5000
- mysql: 3306
- redis: 6379
- meilisearch: 7700
- celery_flower: 5555
- nginx: 8000

## Checklists

- [ ] pyproject.toml
  - [ ] dependencies version
  - [ ] [tool.black] required-version
  - [ ] [tool.ruff] required-version


## 运行

```sh
# 本地运行文档
pdm doc
# or pdm run doc or pdm run mkdocs serve
```
