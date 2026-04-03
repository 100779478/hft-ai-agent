# Codex HTTP Service

这是一个本地 FastAPI 服务，用来把浏览器或 HTTP 请求转换成 `codex exec` 调用。

项目主要用途：

- 提供一个可直接测试的本地页面
- 通过 HTTP 调用本机 Codex CLI
- 支持同步调用和流式调用
- 支持基于 `session_id` 的上下文续接
- 使用项目下的 [`.codex/skills/`](/D:/hft-ai-agent/.codex/skills/) 作为 skills 目录

架构说明和流程图见 [docs/architecture.md](/D:/hft-ai-agent/docs/architecture.md)。

## 目录说明

- [codex_http.py](/D:/hft-ai-agent/codex_http.py)
  启动入口，负责启动 Uvicorn
- [app/codex_http.py](/D:/hft-ai-agent/app/codex_http.py)
  FastAPI 服务、测试页面、命令拼装、会话续接逻辑
- [tests/test_codex_http.py](/D:/hft-ai-agent/tests/test_codex_http.py)
  单元测试
- [run_codex_http.bat](/D:/hft-ai-agent/run_codex_http.bat)
  Windows 启动脚本
- [`.env.example`](/D:/hft-ai-agent/.env.example)
  环境变量示例
- [`.codex/skills/`](/D:/hft-ai-agent/.codex/skills/)
  项目本地 skills

## 环境要求

- Python 3.9 或以上
- 已安装 `codex` CLI
- Windows PowerShell 环境

先确认 `codex` 可执行：

```powershell
codex --version
```

如果 `codex` 不在 `PATH` 中，可以设置：

```powershell
$env:CODEX_HTTP_COMMAND = "C:\Program Files\nodejs\codex.cmd"
```

## 安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 环境变量

先复制一份环境变量模板：

```powershell
Copy-Item .env.example .env
```

典型配置如下：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1
OPENAI_PLANNER_MODEL=gpt-4.1
OPENAI_HTML_MODEL=gpt-4.1
```

服务会自动读取项目根目录的 [`.env`](/D:/hft-ai-agent/.env)，并把其中的值传给 `codex exec` 子进程。

## Codex 登录

如果你使用 API Key 模式，除了设置 `.env`，还需要让 Codex CLI 完成一次登录。

当前项目默认把 `CODEX_HOME` 指向 [`.codex`](/D:/hft-ai-agent/.codex)，所以推荐在项目目录执行：

```powershell
$env:CODEX_HOME = "D:\hft-ai-agent\.codex"
Get-Content .env | Where-Object { $_ -like 'OPENAI_API_KEY=*' } | ForEach-Object { $_.Substring('OPENAI_API_KEY='.Length) } | codex login -c 'openai_base_url="https://api.openai.com/v1"' -c 'cli_auth_credentials_store="file"' --with-api-key
```

如果你使用的是兼容 OpenAI 的第三方地址，把上面的 `openai_base_url` 改成你自己的接口地址。

登录成功后，认证信息会保存在 [`.codex/auth.json`](/D:/hft-ai-agent/.codex/auth.json)。

## 启动服务

方式一，使用批处理：

```powershell
.\run_codex_http.bat
```

方式二，直接运行：

```powershell
.\.venv\Scripts\python.exe codex_http.py
```

方式三，使用 Uvicorn：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.codex_http:app --host 127.0.0.1 --port 8010
```

启动后访问：

```text
http://127.0.0.1:8010/
```

## 接口说明

### `GET /`

返回测试页面，用于直接在浏览器中调用：

- `GET /health`
- `POST /chat`
- `POST /chat/stream`

### `GET /health`

检查：

- `codex` 是否可执行
- 当前使用的 `CODEX_HOME`
- 是否检测到 `.env`
- 当前默认模型和 `openai_base_url`

### `POST /chat`

同步调用一次 `codex exec`，等待最终结果后返回。

### `POST /chat/stream`

流式调用 `codex exec`，实时返回 stdout、stderr 和最终结果。

## 请求字段

`POST /chat` 和 `POST /chat/stream` 支持以下字段：

- `message`
  发送给 Codex 的提示词
- `cwd`
  Codex 工作目录
- `model`
  显式指定模型；不传时会回退到 `.env` 中的 `OPENAI_MODEL`
- `profile`
  可选 Codex profile
- `full_auto`
  是否附带 `--full-auto`
- `dangerously_bypass_approvals_and_sandbox`
  是否附带危险执行参数
- `skip_git_repo_check`
  是否跳过 Git 仓库检查
- `continue_context`
  是否续接之前的上下文
- `session_id`
  指定要续接的会话 id
- `ephemeral`
  是否使用临时会话；默认是 `false`
- `add_dirs`
  额外可写目录
- `timeout_seconds`
  超时时间，默认 `300`
- `codex_home`
  可覆盖默认 `CODEX_HOME`

## 上下文续接说明

这个项目的上下文不是靠 HTTP 长连接维持，而是靠 Codex CLI 的持久化 session。

流程如下：

1. 第一次请求时，不传 `session_id`
2. 后端执行 `codex exec`
3. Codex CLI 输出 `session id`
4. 后端把 `session_id` 返回给前端
5. 前端下一次请求时，把这个 `session_id` 带回来
6. 后端改为执行 `codex exec resume <session_id>`

只要以下条件满足，就能续上：

- `CODEX_HOME` 不变
- [`.codex/sessions/`](/D:/hft-ai-agent/.codex/sessions/) 仍然存在
- 继续使用有效的 `session_id`

## Skills 目录

项目技能固定放在：

- [`.codex/skills/`](/D:/hft-ai-agent/.codex/skills/)

当前项目自定义 skills 示例：

- [`.codex/skills/hft-page-orchestrator/SKILL.md`](/D:/hft-ai-agent/.codex/skills/hft-page-orchestrator/SKILL.md)
- [`.codex/skills/requirement-intake/SKILL.md`](/D:/hft-ai-agent/.codex/skills/requirement-intake/SKILL.md)
- [`.codex/skills/reference-html/SKILL.md`](/D:/hft-ai-agent/.codex/skills/reference-html/SKILL.md)
- [`.codex/skills/hft-sdk-contract/SKILL.md`](/D:/hft-ai-agent/.codex/skills/hft-sdk-contract/SKILL.md)
- [`.codex/skills/html-artifact-delivery/SKILL.md`](/D:/hft-ai-agent/.codex/skills/html-artifact-delivery/SKILL.md)

## 常用测试命令

健康检查：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8010/health
```

同步调用：

```powershell
$body = '{"message":"Reply with exactly OK.","cwd":"D:\\hft-ai-agent","timeout_seconds":20}'
Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Body $body http://127.0.0.1:8010/chat
```

流式调用：

```powershell
$body = '{"message":"Reply with exactly OK.","cwd":"D:\\hft-ai-agent","timeout_seconds":20}'
Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Body $body http://127.0.0.1:8010/chat/stream
```

运行测试：

```powershell
.\.venv\Scripts\python.exe -m unittest -v tests.test_codex_http
```

## 故障排查

### `/health` 正常，但 `/chat` 失败

优先检查：

- `.env` 是否存在
- `OPENAI_BASE_URL` 是否正确
- `OPENAI_MODEL` 是否正确
- [`.codex/auth.json`](/D:/hft-ai-agent/.codex/auth.json) 是否已完成登录

### 页面显示旧字段

通常是旧服务进程还在占用端口。先停止旧进程，再重新启动服务。

### 上下文无法续接

优先检查：

- 请求里是否带回了 `session_id`
- `ephemeral` 是否被设成 `true`
- [`.codex/sessions/`](/D:/hft-ai-agent/.codex/sessions/) 是否还在

### README 再次出现乱码

请确认编辑器保存为 UTF-8 编码，不要使用 GBK 或 ANSI。


