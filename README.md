[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff)

开箱即用的 flask + Gunicorn + Nginx + Docker Web Application 开发、部署方案。满足 12 factor 指导原则和 CI/CD 开发流程。

![Alt text](image.png)

## Features

- 弹性扩展
- 持续更新
- 可移植性
- 可配置性
- CI/CD

## 开发工具

开发工具不在 12 factor 之内，但是不同工具对于开发效率和开发体验有很大影响。下面是我使用的工具：

- WSL2 (Windows Subsystem for Linux 2)
- VS Code: IDE
  - ms-vscode-remote.remote-wsl: 在 WSL2 中运行 VS Code
  - ms-python.python
  - ms-python.vscode-pylance: Static type checker (static code logic)
  - tamasfe.even-better-toml
  - ms-python.black-formatter: Formatter (code style)
  - charliermarsh.ruff: linter (code style and static code logic and code recommend)
  - njpwerner.autodocstring

- Python 3.11.3
- [PDM](https://pdm.fming.dev/latest/): Project and virtualenv management with dependencies (pyproject.toml)

## 代码库

- 使用 Git 进行项目版本控制，维护远程仓库一份 codebase（main分支），并进行本地多分支（功能分支）开发。

## 开发依赖

依赖要显示声明和项目隔离。PEP 621，

- 项目依赖清单: pyproject.toml （包括开发和生产）
- 项目依赖管理工具: PDM（还包括虚拟环境管理、项目管理、构建管理）

## 环境变量

将配置与代码分离存储在环境变量中（.env 文件）。这是多个部署环境可能发生变化的唯一地方（不同的.env文件）。包括：

- 后端服务资源
- 外部服务凭证
- 部署环境标识

不包括：程序内部的配置（每个部署都不会改变的）。

## 后端服务 Backing Services

通过网络或相关协议使用的服务，如数据库、消息队列、缓存以及第三方服务。统称 attached resources。

基于 Docker Compose 部署本地后端支持服务以缩小与生产的环境差异，并支持只修改config来切换部署环境。

## 开发规范

PEP8 是官方出品的 code style，不少公司也有自己的一套 style，除了平时 coding 时注意遵循外，好的格式化工具和检查工具也是保证代码质量的必要环节。

::: tip
Code Quality: code style, code logic, code recommended (replace or upgrade).
:::

开发依赖中所涉及的 pyproject.toml 不仅可以管理依赖安装还能设置依赖配置。而VS Code中的插件也可以根据配置来进行代码格式化和检查。black 甚至复用了 `.gitignore` 进一步降低了配置复杂度。

``` sh 安装依赖
pdm add -d black ruff
```

::: info
插件内置有 server ，即使不安装依赖也可以使用，但为了保证一致性还是在项目中管理依赖版本。插件会自动切换吗？
:::



## CI/CD

Github Actions

build relase run.

部署时 nginx 端口映射

## 高可用

- 数据隔离（多个app作为独立进程对数据进行操作，进程不存储信息）
- 支持并发（横向扩展）：多线程、多进程（多机器）服务，sign

## 监控

- log 开发不关心具体输出到哪里，统一 stdout，开发直接输出，生成由部署环境决定。
- REPL Shell 在线调试。

## References

- https://12factor.net/
- https://jenciso.github.io/blog/12-factor-app/