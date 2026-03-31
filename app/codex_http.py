from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Iterator, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CODEX_HOME: Optional[Path] = PROJECT_ROOT / ".codex"
DEFAULT_CWD = PROJECT_ROOT
DEFAULT_PORT = 8010

TEST_PAGE_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Codex HTTP Service</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0b1220;
      --panel: #111827;
      --panel-2: #0f172a;
      --line: #243041;
      --text: #e5edf7;
      --muted: #8fa1b8;
      --accent: #22c55e;
      --accent-2: #38bdf8;
      --danger: #ef4444;
      --warn: #f59e0b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .wrap {
      max-width: 1320px;
      margin: 0 auto;
      padding: 20px;
    }
    .title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
    }
    .title h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }
    .title span {
      color: var(--muted);
      font-size: 12px;
    }
    .grid {
      display: grid;
      grid-template-columns: 420px 1fr;
      gap: 16px;
    }
    .panel {
      background: linear-gradient(180deg, var(--panel), var(--panel-2));
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
    }
    .panel h2 {
      margin: 0 0 12px;
      font-size: 14px;
      font-weight: 600;
    }
    .field {
      margin-bottom: 10px;
    }
    label {
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 12px;
    }
    input, textarea {
      width: 100%;
      padding: 10px 12px;
      color: var(--text);
      background: #0a0f1c;
      border: 1px solid var(--line);
      border-radius: 8px;
      outline: none;
      font: inherit;
    }
    textarea {
      min-height: 110px;
      resize: vertical;
    }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 12px;
    }
    button {
      padding: 10px 14px;
      border: 0;
      border-radius: 8px;
      cursor: pointer;
      color: #04110a;
      background: var(--accent);
      font-weight: 600;
    }
    button.secondary {
      color: #03111a;
      background: var(--accent-2);
    }
    button.warn {
      color: #1a1203;
      background: var(--warn);
    }
    .meta {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 12px;
    }
    .chip {
      padding: 10px 12px;
      background: #0a0f1c;
      border: 1px solid var(--line);
      border-radius: 8px;
      font-size: 12px;
      color: var(--muted);
    }
    .chip b {
      color: var(--text);
    }
    .output-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    pre {
      margin: 0;
      padding: 12px;
      min-height: 420px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      background: #08101d;
      border: 1px solid var(--line);
      border-radius: 10px;
      color: #d7e3f4;
      font-size: 12px;
      line-height: 1.5;
    }
    .stream {
      min-height: 420px;
    }
    .status-ok { color: var(--accent); }
    .status-fail { color: var(--danger); }
    @media (max-width: 980px) {
      .grid, .output-grid { grid-template-columns: 1fr; }
      .meta, .row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="title">
      <div>
        <h1>Codex HTTP Test Page</h1>
        <span>Real HTTP calls to the local service, then the service runs codex exec.</span>
      </div>
      <span id="statusText">Idle</span>
    </div>
    <div class="grid">
      <section class="panel">
        <h2>Request</h2>
        <div class="field">
          <label for="message">message</label>
          <textarea id="message">Reply with exactly OK.</textarea>
        </div>
        <div class="field">
          <label for="cwd">cwd</label>
          <input id="cwd" value="" />
        </div>
        <div class="row">
          <div class="field">
            <label for="model">model</label>
            <input id="model" value="" placeholder="for example gpt-5.4" />
          </div>
          <div class="field">
            <label for="timeout">timeout_seconds</label>
            <input id="timeout" type="number" min="5" max="3600" value="300" />
          </div>
        </div>
        <div class="actions">
          <button type="button" id="healthBtn" class="secondary">GET /health</button>
          <button type="button" id="chatBtn">POST /chat</button>
          <button type="button" id="streamBtn" class="warn">POST /chat/stream</button>
        </div>
      </section>
      <section class="panel">
        <h2>Result</h2>
        <div class="meta">
          <div class="chip">Endpoint: <b id="calledApi">-</b></div>
          <div class="chip">Status: <b id="calledStatus">-</b></div>
          <div class="chip">HTTP: <b id="httpStatus">-</b></div>
          <div class="chip">Duration: <b id="calledDuration">-</b></div>
        </div>
        <div class="output-grid">
          <div>
            <label>Final Response</label>
            <pre id="output">Click a button to show the request payload and response body.</pre>
          </div>
          <div>
            <label>Stream Log</label>
            <pre id="streamOutput" class="stream">Streaming calls will show stdout and stderr here.</pre>
          </div>
        </div>
      </section>
    </div>
  </div>
  <script>
    const cwdInput = document.getElementById("cwd");
    const messageInput = document.getElementById("message");
    const modelInput = document.getElementById("model");
    const timeoutInput = document.getElementById("timeout");
    const output = document.getElementById("output");
    const streamOutput = document.getElementById("streamOutput");
    const statusText = document.getElementById("statusText");
    const calledApi = document.getElementById("calledApi");
    const calledStatus = document.getElementById("calledStatus");
    const calledDuration = document.getElementById("calledDuration");
    const httpStatus = document.getElementById("httpStatus");

    cwdInput.value = window.location.origin.includes("127.0.0.1") ? "D:\\\\hft-ai-agent" : "";

    function setMeta(endpoint, rawStatus, startedAt, ok) {
      calledApi.textContent = endpoint;
      calledDuration.textContent = `${Date.now() - startedAt} ms`;
      httpStatus.textContent = String(rawStatus);
      calledStatus.textContent = ok ? "success" : "failed";
      calledStatus.className = ok ? "status-ok" : "status-fail";
      statusText.textContent = ok ? "Done" : "Failed";
    }

    function buildPayload() {
      return {
        message: messageInput.value,
        cwd: cwdInput.value || null,
        model: modelInput.value || null,
        timeout_seconds: Number(timeoutInput.value || 300)
      };
    }

    function render(endpoint, response, startedAt, requestBody, rawStatus) {
      const ok = rawStatus >= 200 && rawStatus < 300 && (!response || response.ok !== false);
      setMeta(endpoint, rawStatus, startedAt, ok);
      output.textContent = JSON.stringify({ endpoint, request: requestBody, response }, null, 2);
    }

    function resetStream() {
      streamOutput.textContent = "";
    }

    function appendStream(line) {
      streamOutput.textContent += line;
      streamOutput.scrollTop = streamOutput.scrollHeight;
    }

    async function callHealth() {
      const startedAt = Date.now();
      resetStream();
      statusText.textContent = "Calling /health...";
      const resp = await fetch("/health");
      const data = await resp.json();
      render("/health", data, startedAt, null, resp.status);
    }

    async function callChat() {
      const startedAt = Date.now();
      const payload = buildPayload();
      resetStream();
      statusText.textContent = "Calling /chat...";
      const resp = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      render("/chat", data, startedAt, payload, resp.status);
    }

    async function callChatStream() {
      const startedAt = Date.now();
      const payload = buildPayload();
      resetStream();
      output.textContent = JSON.stringify({ endpoint: "/chat/stream", request: payload }, null, 2);
      statusText.textContent = "Calling /chat/stream...";
      calledApi.textContent = "/chat/stream";
      const resp = await fetch("/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      httpStatus.textContent = String(resp.status);

      if (!resp.body) {
        throw new Error("The browser did not return a readable stream.");
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalResult = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        while (true) {
          const index = buffer.indexOf("\\n");
          if (index === -1) {
            break;
          }
          const line = buffer.slice(0, index).trim();
          buffer = buffer.slice(index + 1);
          if (!line) {
            continue;
          }
          const event = JSON.parse(line);
          if (event.type === "stdout") {
            appendStream(`[stdout] ${event.data}`);
          } else if (event.type === "stderr") {
            appendStream(`[stderr] ${event.data}`);
          } else if (event.type === "start") {
            appendStream(`[start] ${JSON.stringify(event.data)}\\n`);
          } else if (event.type === "result") {
            finalResult = event.data;
          }
        }
      }

      if (finalResult) {
        render("/chat/stream", finalResult, startedAt, payload, resp.status);
      } else {
        setMeta("/chat/stream", resp.status, startedAt, false);
      }
    }

    document.getElementById("healthBtn").addEventListener("click", () => {
      callHealth().catch((error) => {
        statusText.textContent = "Failed";
        output.textContent = String(error);
      });
    });

    document.getElementById("chatBtn").addEventListener("click", () => {
      callChat().catch((error) => {
        statusText.textContent = "Failed";
        output.textContent = String(error);
      });
    });

    document.getElementById("streamBtn").addEventListener("click", () => {
      callChatStream().catch((error) => {
        statusText.textContent = "Failed";
        output.textContent = String(error);
      });
    });
  </script>
</body>
</html>
"""


class ChatRequest(BaseModel):
    message: str = Field(..., description="Prompt sent to Codex")
    cwd: Optional[str] = Field(default=None, description="Working directory for Codex")
    model: Optional[str] = Field(default=None, description="Optional model override")
    profile: Optional[str] = Field(default=None, description="Optional Codex profile")
    full_auto: bool = Field(default=True, description="Run with --full-auto by default")
    dangerously_bypass_approvals_and_sandbox: bool = Field(
        default=False,
        description="Pass --dangerously-bypass-approvals-and-sandbox",
    )
    skip_git_repo_check: bool = Field(default=True, description="Allow running outside git repos")
    ephemeral: bool = Field(default=True, description="Do not persist Codex session files")
    add_dirs: list[str] = Field(default_factory=list, description="Additional writable directories")
    timeout_seconds: int = Field(default=300, ge=5, le=3600)
    codex_home: Optional[str] = Field(default=None, description="Override CODEX_HOME for the subprocess")


class ChatResponse(BaseModel):
    ok: bool
    reply: str
    exit_code: int
    duration_ms: int
    cwd: str
    codex_home: str
    command: list[str]
    stdout: str
    stderr: str


class HealthResponse(BaseModel):
    ok: bool
    codex_available: bool
    version: str
    codex_home: str
    default_cwd: str
    command: str


class CodexExecRunner:
    def __init__(
        self,
        *,
        codex_command: Optional[str] = None,
        default_cwd: Path = DEFAULT_CWD,
        default_codex_home: Optional[Path] = DEFAULT_CODEX_HOME,
    ) -> None:
        self.codex_command = self._resolve_codex_command(codex_command or os.getenv("CODEX_HTTP_COMMAND"))
        self.default_cwd = Path(default_cwd)
        self.default_codex_home = Path(default_codex_home).resolve() if default_codex_home else None

    def health(self) -> HealthResponse:
        codex_home = self._resolve_codex_home(None)
        try:
            completed = subprocess.run(
                [self.codex_command, "--version"],
                cwd=str(self.default_cwd),
                env=self._build_env(codex_home),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            version = self._combine_output(completed.stdout, completed.stderr).strip()
            return HealthResponse(
                ok=completed.returncode == 0,
                codex_available=completed.returncode == 0,
                version=version,
                codex_home=self._display_codex_home(codex_home),
                default_cwd=str(self.default_cwd),
                command=self.codex_command,
            )
        except Exception as exc:
            return HealthResponse(
                ok=False,
                codex_available=False,
                version=str(exc),
                codex_home=self._display_codex_home(codex_home),
                default_cwd=str(self.default_cwd),
                command=self.codex_command,
            )

    def run_chat(self, payload: ChatRequest) -> ChatResponse:
        cwd = Path(payload.cwd).resolve() if payload.cwd else self.default_cwd.resolve()
        codex_home = self._resolve_codex_home(payload.codex_home)

        with self._temporary_directory(codex_home) as temp_dir:
            last_message_path = Path(temp_dir) / "last_message.txt"
            command = self._build_command(payload=payload, cwd=cwd, last_message_path=last_message_path)
            env = self._build_env(codex_home)
            started_at = time.perf_counter()
            try:
                completed = subprocess.run(
                    command,
                    cwd=str(cwd),
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=payload.timeout_seconds,
                )
                duration_ms = int((time.perf_counter() - started_at) * 1000)
                reply = self._read_last_message(last_message_path)
                if not reply:
                    reply = self._combine_output(completed.stdout, completed.stderr).strip()
                return self._build_chat_response(
                    cwd=cwd,
                    codex_home=codex_home,
                    command=command,
                    reply=reply,
                    exit_code=completed.returncode,
                    duration_ms=duration_ms,
                    stdout=self._safe_output(completed.stdout),
                    stderr=self._safe_output(completed.stderr),
                )
            except subprocess.TimeoutExpired as exc:
                duration_ms = int((time.perf_counter() - started_at) * 1000)
                return self._build_chat_response(
                    cwd=cwd,
                    codex_home=codex_home,
                    command=command,
                    reply=f"Codex exec timed out after {payload.timeout_seconds}s.",
                    exit_code=-1,
                    duration_ms=duration_ms,
                    stdout=self._safe_output(exc.stdout),
                    stderr=self._safe_output(exc.stderr),
                )

    def stream_chat(self, payload: ChatRequest) -> Iterator[str]:
        cwd = Path(payload.cwd).resolve() if payload.cwd else self.default_cwd.resolve()
        codex_home = self._resolve_codex_home(payload.codex_home)

        with self._temporary_directory(codex_home) as temp_dir:
            last_message_path = Path(temp_dir) / "last_message.txt"
            command = self._build_command(payload=payload, cwd=cwd, last_message_path=last_message_path)
            env = self._build_env(codex_home)
            started_at = time.perf_counter()
            yield self._json_line(
                {
                    "type": "start",
                    "data": {
                        "command": command,
                        "cwd": str(cwd),
                        "codex_home": self._display_codex_home(codex_home),
                    },
                }
            )

            try:
                process = subprocess.Popen(
                    command,
                    cwd=str(cwd),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    encoding="utf-8",
                    errors="replace",
                )
            except Exception as exc:
                duration_ms = int((time.perf_counter() - started_at) * 1000)
                response = self._build_chat_response(
                    cwd=cwd,
                    codex_home=codex_home,
                    command=command,
                    reply=str(exc),
                    exit_code=-1,
                    duration_ms=duration_ms,
                    stdout="",
                    stderr=str(exc),
                )
                yield self._json_line({"type": "result", "data": self._chat_response_to_dict(response)})
                return

            output_queue: queue.Queue[tuple[str, str]] = queue.Queue()
            stdout_chunks: list[str] = []
            stderr_chunks: list[str] = []
            threads = [
                threading.Thread(target=self._pump_stream, args=(process.stdout, "stdout", output_queue), daemon=True),
                threading.Thread(target=self._pump_stream, args=(process.stderr, "stderr", output_queue), daemon=True),
            ]
            for thread in threads:
                thread.start()

            completed_streams = 0
            while completed_streams < 2:
                if time.perf_counter() - started_at > payload.timeout_seconds:
                    process.kill()
                    process.wait(timeout=5)
                    duration_ms = int((time.perf_counter() - started_at) * 1000)
                    response = self._build_chat_response(
                        cwd=cwd,
                        codex_home=codex_home,
                        command=command,
                        reply=f"Codex exec timed out after {payload.timeout_seconds}s.",
                        exit_code=-1,
                        duration_ms=duration_ms,
                        stdout="".join(stdout_chunks),
                        stderr="".join(stderr_chunks),
                    )
                    yield self._json_line({"type": "result", "data": self._chat_response_to_dict(response)})
                    return

                try:
                    source, content = output_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if source.endswith(":done"):
                    completed_streams += 1
                    continue

                if source == "stdout":
                    stdout_chunks.append(content)
                else:
                    stderr_chunks.append(content)
                yield self._json_line({"type": source, "data": content})

            exit_code = process.wait(timeout=5)
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            reply = self._read_last_message(last_message_path)
            if not reply:
                reply = ("".join(stdout_chunks) or "".join(stderr_chunks)).strip()
            response = self._build_chat_response(
                cwd=cwd,
                codex_home=codex_home,
                command=command,
                reply=reply,
                exit_code=exit_code,
                duration_ms=duration_ms,
                stdout="".join(stdout_chunks),
                stderr="".join(stderr_chunks),
            )
            yield self._json_line({"type": "result", "data": self._chat_response_to_dict(response)})

    def _build_command(self, *, payload: ChatRequest, cwd: Path, last_message_path: Path) -> list[str]:
        command = [self.codex_command, "exec", "--output-last-message", str(last_message_path)]
        if payload.ephemeral:
            command.append("--ephemeral")
        if payload.skip_git_repo_check:
            command.append("--skip-git-repo-check")
        if payload.profile:
            command.extend(["-p", payload.profile])
        if payload.model:
            command.extend(["-m", payload.model])
        if payload.dangerously_bypass_approvals_and_sandbox:
            command.append("--dangerously-bypass-approvals-and-sandbox")
        elif payload.full_auto:
            command.append("--full-auto")
        command.extend(["-C", str(cwd)])
        for directory in payload.add_dirs:
            command.extend(["--add-dir", str(Path(directory).resolve())])
        command.append(payload.message)
        return command

    def _build_chat_response(
        self,
        *,
        cwd: Path,
        codex_home: Optional[Path],
        command: list[str],
        reply: str,
        exit_code: int,
        duration_ms: int,
        stdout: str,
        stderr: str,
    ) -> ChatResponse:
        return ChatResponse(
            ok=exit_code == 0,
            reply=reply,
            exit_code=exit_code,
            duration_ms=duration_ms,
            cwd=str(cwd),
            codex_home=self._display_codex_home(codex_home),
            command=command,
            stdout=stdout,
            stderr=stderr,
        )

    def _chat_response_to_dict(self, response: ChatResponse) -> dict[str, object]:
        return {
            "ok": response.ok,
            "reply": response.reply,
            "exit_code": response.exit_code,
            "duration_ms": response.duration_ms,
            "cwd": response.cwd,
            "codex_home": response.codex_home,
            "command": response.command,
            "stdout": response.stdout,
            "stderr": response.stderr,
        }

    def _pump_stream(self, stream: Optional[object], source: str, output_queue: queue.Queue[tuple[str, str]]) -> None:
        try:
            if stream is None:
                return
            while True:
                line = stream.readline()
                if line == "":
                    break
                output_queue.put((source, line))
        finally:
            if stream is not None:
                stream.close()
            output_queue.put((f"{source}:done", ""))

    def _resolve_codex_home(self, override: Optional[str]) -> Optional[Path]:
        if override:
            path = Path(override).resolve()
            path.mkdir(parents=True, exist_ok=True)
            return path
        inherited = os.environ.get("CODEX_HOME")
        if inherited:
            path = Path(inherited).resolve()
            path.mkdir(parents=True, exist_ok=True)
            return path
        if self.default_codex_home is not None:
            self.default_codex_home.mkdir(parents=True, exist_ok=True)
            return self.default_codex_home
        return None

    def _temporary_directory(self, codex_home: Optional[Path]) -> tempfile.TemporaryDirectory:
        if codex_home is not None:
            return tempfile.TemporaryDirectory(dir=str(codex_home))
        return tempfile.TemporaryDirectory()

    def _build_env(self, codex_home: Optional[Path]) -> dict[str, str]:
        env = os.environ.copy()
        if codex_home is not None:
            env["CODEX_HOME"] = str(codex_home)
        return env

    def _display_codex_home(self, codex_home: Optional[Path]) -> str:
        if codex_home is not None:
            return str(codex_home)
        return "<inherit default ~/.codex>"

    def _safe_output(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)

    def _combine_output(self, stdout: object, stderr: object) -> str:
        stdout_text = self._safe_output(stdout)
        if stdout_text:
            return stdout_text
        return self._safe_output(stderr)

    def _read_last_message(self, last_message_path: Path) -> str:
        if not last_message_path.exists():
            return ""
        return last_message_path.read_text(encoding="utf-8", errors="ignore").strip()

    def _resolve_codex_command(self, configured: Optional[str]) -> str:
        if configured:
            return configured
        for candidate in ("codex.cmd", "codex", "codex.ps1"):
            path = shutil.which(candidate)
            if path:
                return path
        return "codex"

    def _json_line(self, payload: dict[str, object]) -> str:
        return json.dumps(payload, ensure_ascii=False) + "\n"


runner = CodexExecRunner()
app = FastAPI(title="Codex HTTP Service")


@app.get("/", response_class=HTMLResponse)
def playground() -> HTMLResponse:
    return HTMLResponse(TEST_PAGE_HTML)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return runner.health()


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return runner.run_chat(payload)


@app.post("/chat/stream")
def chat_stream(payload: ChatRequest) -> StreamingResponse:
    return StreamingResponse(runner.stream_chat(payload), media_type="application/x-ndjson")
