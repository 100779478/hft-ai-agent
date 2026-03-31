# 部署手册

## 1. 项目说明

本项目是一个基于 FastAPI 的本地 HTTP 服务，用于通过以下接口触发 `codex exec`：

- `GET /health`
- `POST /chat`
- `POST /chat/stream`

默认入口文件：

- `codex_http_demo.py`
- `app/codex_http_demo.py`

默认监听端口：

- `8010`

## 2. 部署前提

部署机器需要满足以下条件：

- Python 3.9 及以上
- 已安装 `codex` CLI，并且命令行可直接执行 `codex --version`
- 当前运行账号对工作目录和 `CODEX_HOME` 目录有读写权限

如果 `codex` 不在系统 `PATH` 中，需要显式配置 `CODEX_HTTP_COMMAND`。

## 3. 目录准备

建议部署目录结构如下：

```text
D:\hft-ai-agent
├── app
├── tests
├── requirements.txt
├── codex_http_demo.py
└── run_codex_http_demo.bat
```

建议额外准备一个单独的运行时目录用于 `CODEX_HOME`，例如：

```text
D:\codex-home
```

## 4. 安装依赖

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 5. 环境变量配置

### 必选

如果 `codex` 命令不在系统 `PATH`，配置：

```powershell
$env:CODEX_HTTP_COMMAND="C:\Program Files\nodejs\codex.cmd"
```

如果希望显式隔离 Codex 运行目录，配置：

```powershell
$env:CODEX_HOME="D:\codex-home"
```

### 可选

如果需要 OpenAI 相关能力，按实际环境补充 `.env` 或系统环境变量。项目中保留了 `.env.example` 作为示例，但当前服务本身不直接读取该文件，需要由你的运行方式或外部进程注入。

## 6. 启动方式

### 方式 A：使用项目自带启动脚本

```powershell
.\run_codex_http_demo.bat
```

### 方式 B：直接启动 Uvicorn

本机调试：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.codex_http_demo:app --host 127.0.0.1 --port 8010
```

局域网或服务器部署：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.codex_http_demo:app --host 0.0.0.0 --port 8010
```

如果需要长期运行，建议使用进程守护工具或注册为系统服务，不建议直接依赖交互式终端窗口。

## 7. 部署后验证

启动完成后，验证以下地址：

首页：

```text
http://127.0.0.1:8010/
```

健康检查：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8010/health
```

接口调用：

```powershell
$body = '{"message":"Reply with exactly OK.","cwd":"D:\\hft-ai-agent","timeout_seconds":20}'
Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Body $body http://127.0.0.1:8010/chat
```

流式接口：

```powershell
$body = '{"message":"Reply with exactly OK.","cwd":"D:\\hft-ai-agent","timeout_seconds":20}'
Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Body $body http://127.0.0.1:8010/chat/stream
```

## 8. 常见问题

### `GET /health` 失败

优先检查：

- `codex --version` 是否能在部署机上执行成功
- `CODEX_HTTP_COMMAND` 是否指向正确的可执行文件
- 当前账号是否有权限访问 `codex` 及其运行目录

### `POST /chat` 返回权限错误

优先检查：

- `cwd` 指定目录是否可访问
- `CODEX_HOME` 是否可写
- 当前账号是否具备运行 `codex exec` 所需权限

### 页面可打开，但接口调用失败

优先检查：

- 服务是否真的监听在预期端口
- 浏览器请求是否打到了正确的服务实例
- `codex exec` 是否在后端进程内执行失败，可直接查看终端输出或进程日志

## 9. 建议的发布清单

建议纳入版本控制的文件：

- `app/`
- `tests/`
- `codex_http_demo.py`
- `requirements.txt`
- `README.md`
- `DEPLOYMENT.md`
- `run_codex_http_demo.bat`
- `.env.example`

不建议纳入版本控制的内容：

- `.venv/`
- `.env`
- `.codex-http-demo/`
- `.codex-http-test/`
- `__pycache__/`
