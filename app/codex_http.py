from __future__ import annotations

import json
import os
import queue
import re
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
DEFAULT_DOTENV_PATH = PROJECT_ROOT / ".env"
PLAYGROUND_HTML_PATH = PROJECT_ROOT / "app" / "chat_playground.html"
STREAM_POLL_INTERVAL_SECONDS = 0.1
STREAM_HEARTBEAT_SECONDS = 1.0
STREAM_READ_CHUNK_SIZE = 1024
SESSION_ID_OUTPUT_PATTERN = re.compile(
    r"session id:\s*([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)
SESSION_ID_VALUE_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
RECOVERABLE_STDERR_PATTERNS = (
    re.compile(r"responses_websocket: failed to connect to websocket: HTTP error: 404 Not Found"),
    re.compile(r"^ERROR:\s+Reconnecting\.\.\.\s+\d+/\d+\s*$"),
    re.compile(r"failed to load skill .*missing YAML frontmatter delimited by ---"),
)


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
    continue_context: bool = Field(
        default=False,
        description="Resume the most recent recorded Codex session for this project",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Resume a specific Codex session id, or pass a stable alias such as customerid",
    )
    ephemeral: bool = Field(default=False, description="Do not persist session files")
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
    resume_mode: str
    session_id: Optional[str]
    effective_model: Optional[str]
    effective_openai_base_url: Optional[str]
    stdout: str
    stderr: str


class HealthResponse(BaseModel):
    ok: bool
    codex_available: bool
    version: str
    codex_home: str
    default_cwd: str
    command: str
    dotenv_path: str
    dotenv_exists: bool
    effective_model: Optional[str]
    effective_openai_base_url: Optional[str]


class SkillInfo(BaseModel):
    name: str
    description: Optional[str]
    path: str
    valid: bool
    error: Optional[str] = None


class SkillListResponse(BaseModel):
    ok: bool
    codex_home: str
    skills_dir: str
    skills: list[SkillInfo]


class CodexExecRunner:
    def __init__(
        self,
        *,
        codex_command: Optional[str] = None,
        default_cwd: Path = DEFAULT_CWD,
        default_codex_home: Optional[Path] = DEFAULT_CODEX_HOME,
        dotenv_path: Optional[Path] = DEFAULT_DOTENV_PATH,
    ) -> None:
        self.codex_command = self._resolve_codex_command(codex_command or os.getenv("CODEX_HTTP_COMMAND"))
        self.default_cwd = Path(default_cwd)
        self.default_codex_home = Path(default_codex_home).resolve() if default_codex_home else None
        self.dotenv_path = Path(dotenv_path).resolve() if dotenv_path else None

    def health(self) -> HealthResponse:
        codex_home = self._resolve_codex_home(None)
        env = self._build_env(codex_home)
        try:
            completed = subprocess.run(
                [self.codex_command, "--version"],
                cwd=str(self.default_cwd),
                env=env,
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
                dotenv_path=self._display_dotenv_path(),
                dotenv_exists=self._dotenv_exists(),
                effective_model=self._effective_model(None),
                effective_openai_base_url=self._effective_openai_base_url(),
            )
        except Exception as exc:
            return HealthResponse(
                ok=False,
                codex_available=False,
                version=str(exc),
                codex_home=self._display_codex_home(codex_home),
                default_cwd=str(self.default_cwd),
                command=self.codex_command,
                dotenv_path=self._display_dotenv_path(),
                dotenv_exists=self._dotenv_exists(),
                effective_model=self._effective_model(None),
                effective_openai_base_url=self._effective_openai_base_url(),
            )

    def list_skills(self, codex_home_override: Optional[str] = None) -> SkillListResponse:
        codex_home = self._resolve_codex_home(codex_home_override)
        skills_dir = (codex_home / "skills") if codex_home is not None else (Path.home() / ".codex" / "skills")
        skills: list[SkillInfo] = []

        if skills_dir.exists():
            for skill_dir in sorted((path for path in skills_dir.iterdir() if path.is_dir()), key=lambda path: path.name.lower()):
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    skills.append(
                        SkillInfo(
                            name=skill_dir.name,
                            description=None,
                            path=str(skill_file),
                            valid=False,
                            error="SKILL.md not found",
                        )
                    )
                    continue
                skills.append(self._read_skill_info(skill_file))

        return SkillListResponse(
            ok=True,
            codex_home=self._display_codex_home(codex_home),
            skills_dir=str(skills_dir),
            skills=skills,
        )

    def run_chat(self, payload: ChatRequest) -> ChatResponse:
        cwd = Path(payload.cwd).resolve() if payload.cwd else self.default_cwd.resolve()
        codex_home = self._resolve_codex_home(payload.codex_home)
        if self._should_answer_skill_inventory(payload.message):
            response = self._build_skill_inventory_response(cwd=cwd, codex_home=codex_home)
            return self._build_chat_response(
                cwd=cwd,
                codex_home=codex_home,
                command=["local", "skills"],
                reply=response,
                exit_code=0,
                duration_ms=0,
                resume_mode="new",
                session_id=None,
                stdout=response,
                stderr="",
            )
        resume_mode, resolved_session_id, session_alias = self._resolve_resume_target(payload, codex_home)

        with self._temporary_directory(codex_home) as temp_dir:
            last_message_path = Path(temp_dir) / "last_message.txt"
            command = self._build_command(
                payload=payload,
                cwd=cwd,
                last_message_path=last_message_path,
                resume_mode=resume_mode,
                resolved_session_id=resolved_session_id,
            )
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
                stdout_text = self._safe_output(completed.stdout)
                stderr_text = self._safe_output(completed.stderr)
                actual_session_id = self._extract_session_id(stdout_text, stderr_text)
                self._store_session_alias(codex_home, session_alias, actual_session_id)
                return self._build_chat_response(
                    cwd=cwd,
                    codex_home=codex_home,
                    command=command,
                    reply=reply,
                    exit_code=completed.returncode,
                    duration_ms=duration_ms,
                    resume_mode=resume_mode,
                    session_id=actual_session_id,
                    stdout=stdout_text,
                    stderr=stderr_text,
                )
            except subprocess.TimeoutExpired as exc:
                duration_ms = int((time.perf_counter() - started_at) * 1000)
                stdout_text = self._safe_output(exc.stdout)
                stderr_text = self._safe_output(exc.stderr)
                actual_session_id = self._extract_session_id(stdout_text, stderr_text)
                self._store_session_alias(codex_home, session_alias, actual_session_id)
                return self._build_chat_response(
                    cwd=cwd,
                    codex_home=codex_home,
                    command=command,
                    reply=f"Codex exec timed out after {payload.timeout_seconds}s.",
                    exit_code=-1,
                    duration_ms=duration_ms,
                    resume_mode=resume_mode,
                    session_id=actual_session_id,
                    stdout=stdout_text,
                    stderr=stderr_text,
                )

    def stream_chat(self, payload: ChatRequest) -> Iterator[str]:
        cwd = Path(payload.cwd).resolve() if payload.cwd else self.default_cwd.resolve()
        codex_home = self._resolve_codex_home(payload.codex_home)
        if self._should_answer_skill_inventory(payload.message):
            response_text = self._build_skill_inventory_response(cwd=cwd, codex_home=codex_home)
            yield self._json_line(
                {
                    "type": "start",
                    "data": {
                        "command": ["local", "skills"],
                        "cwd": str(cwd),
                        "codex_home": self._display_codex_home(codex_home),
                        "resume_mode": "new",
                    },
                }
            )
            yield self._json_line({"type": "stdout", "data": response_text})
            response = self._build_chat_response(
                cwd=cwd,
                codex_home=codex_home,
                command=["local", "skills"],
                reply=response_text,
                exit_code=0,
                duration_ms=0,
                resume_mode="new",
                session_id=None,
                stdout=response_text,
                stderr="",
            )
            yield self._json_line({"type": "result", "data": self._chat_response_to_dict(response)})
            return
        resume_mode, resolved_session_id, session_alias = self._resolve_resume_target(payload, codex_home)

        with self._temporary_directory(codex_home) as temp_dir:
            last_message_path = Path(temp_dir) / "last_message.txt"
            command = self._build_command(
                payload=payload,
                cwd=cwd,
                last_message_path=last_message_path,
                resume_mode=resume_mode,
                resolved_session_id=resolved_session_id,
            )
            env = self._build_env(codex_home)
            started_at = time.perf_counter()
            yield self._json_line(
                {
                    "type": "start",
                    "data": {
                        "command": command,
                        "cwd": str(cwd),
                        "codex_home": self._display_codex_home(codex_home),
                        "resume_mode": resume_mode,
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
                    resume_mode=resume_mode,
                    session_id=self._extract_session_id("", str(exc)),
                    stdout="",
                    stderr=str(exc),
                )
                yield self._json_line({"type": "result", "data": self._chat_response_to_dict(response)})
                return

            output_queue: queue.Queue[tuple[str, str]] = queue.Queue()
            stdout_chunks: list[str] = []
            stderr_chunks: list[str] = []
            stderr_pending = ""
            threads = [
                threading.Thread(target=self._pump_stream, args=(process.stdout, "stdout", output_queue), daemon=True),
                threading.Thread(target=self._pump_stream, args=(process.stderr, "stderr", output_queue), daemon=True),
            ]
            for thread in threads:
                thread.start()

            completed_streams = 0
            last_progress_at = started_at
            while completed_streams < 2:
                now = time.perf_counter()
                if now - started_at > payload.timeout_seconds:
                    process.kill()
                    process.wait(timeout=5)
                    duration_ms = int((time.perf_counter() - started_at) * 1000)
                    stdout_text = "".join(stdout_chunks)
                    stderr_text = "".join(stderr_chunks)
                    actual_session_id = self._extract_session_id(stdout_text, stderr_text)
                    self._store_session_alias(codex_home, session_alias, actual_session_id)
                    response = self._build_chat_response(
                        cwd=cwd,
                        codex_home=codex_home,
                        command=command,
                        reply=f"Codex exec timed out after {payload.timeout_seconds}s.",
                        exit_code=-1,
                        duration_ms=duration_ms,
                        resume_mode=resume_mode,
                        session_id=actual_session_id,
                        stdout=stdout_text,
                        stderr=stderr_text,
                    )
                    yield self._json_line({"type": "result", "data": self._chat_response_to_dict(response)})
                    return

                try:
                    source, content = output_queue.get(timeout=STREAM_POLL_INTERVAL_SECONDS)
                except queue.Empty:
                    now = time.perf_counter()
                    if now - last_progress_at >= STREAM_HEARTBEAT_SECONDS:
                        yield self._json_line({"type": "ping", "data": {"elapsed_ms": int((now - started_at) * 1000)}})
                        last_progress_at = now
                    continue

                if source == "stderr:done":
                    visible_chunks, stderr_pending = self._consume_visible_stderr(stderr_pending, finalize=True)
                    for visible_chunk in visible_chunks:
                        last_progress_at = time.perf_counter()
                        yield self._json_line({"type": "stderr", "data": visible_chunk})
                    completed_streams += 1
                    continue

                if source.endswith(":done"):
                    completed_streams += 1
                    continue

                if source == "stdout":
                    stdout_chunks.append(content)
                    last_progress_at = time.perf_counter()
                    yield self._json_line({"type": source, "data": content})
                else:
                    stderr_chunks.append(content)
                    visible_chunks, stderr_pending = self._consume_visible_stderr(stderr_pending + content)
                    for visible_chunk in visible_chunks:
                        last_progress_at = time.perf_counter()
                        yield self._json_line({"type": source, "data": visible_chunk})

            exit_code = process.wait(timeout=5)
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            reply = self._read_last_message(last_message_path)
            if not reply:
                reply = ("".join(stdout_chunks) or "".join(stderr_chunks)).strip()
            stdout_text = "".join(stdout_chunks)
            stderr_text = "".join(stderr_chunks)
            actual_session_id = self._extract_session_id(stdout_text, stderr_text)
            self._store_session_alias(codex_home, session_alias, actual_session_id)
            response = self._build_chat_response(
                cwd=cwd,
                codex_home=codex_home,
                command=command,
                reply=reply,
                exit_code=exit_code,
                duration_ms=duration_ms,
                resume_mode=resume_mode,
                session_id=actual_session_id,
                stdout=stdout_text,
                stderr=stderr_text,
            )
            yield self._json_line({"type": "result", "data": self._chat_response_to_dict(response)})

    def _build_command(
        self,
        *,
        payload: ChatRequest,
        cwd: Path,
        last_message_path: Path,
        resume_mode: Optional[str] = None,
        resolved_session_id: Optional[str] = None,
    ) -> list[str]:
        effective_resume_mode = resume_mode or self._resolve_resume_mode(payload)
        effective_model = self._effective_model(payload.model)
        effective_openai_base_url = self._effective_openai_base_url()
        if effective_resume_mode == "new":
            command = [self.codex_command, "exec", "--output-last-message", str(last_message_path)]
            if effective_openai_base_url:
                command.extend(["-c", self._config_string_value("openai_base_url", effective_openai_base_url)])
            if payload.ephemeral:
                command.append("--ephemeral")
            if payload.skip_git_repo_check:
                command.append("--skip-git-repo-check")
            if payload.profile:
                command.extend(["-p", payload.profile])
            if effective_model:
                command.extend(["-m", effective_model])
            if payload.dangerously_bypass_approvals_and_sandbox:
                command.append("--dangerously-bypass-approvals-and-sandbox")
            elif payload.full_auto:
                command.append("--full-auto")
            command.extend(["-C", str(cwd)])
            for directory in payload.add_dirs:
                command.extend(["--add-dir", str(Path(directory).resolve())])
            command.append(self._prepare_prompt_message(payload.message))
            return command

        command = [self.codex_command, "exec", "resume", "--output-last-message", str(last_message_path)]
        if effective_openai_base_url:
            command.extend(["-c", self._config_string_value("openai_base_url", effective_openai_base_url)])
        if payload.ephemeral:
            command.append("--ephemeral")
        if payload.skip_git_repo_check:
            command.append("--skip-git-repo-check")
        if effective_model:
            command.extend(["-m", effective_model])
        if payload.dangerously_bypass_approvals_and_sandbox:
            command.append("--dangerously-bypass-approvals-and-sandbox")
        elif payload.full_auto:
            command.append("--full-auto")
        if effective_resume_mode == "session_id":
            target_session_id = resolved_session_id or payload.session_id
            if not target_session_id:
                raise ValueError("resume command requires a resolved session id")
            command.append(str(target_session_id))
        else:
            command.append("--last")
        command.append(self._prepare_prompt_message(payload.message))
        return command

    def _prepare_prompt_message(self, message: str) -> str:
        normalized = message.replace("\r\n", "\n").replace("\r", "\n")
        if "\n" not in normalized:
            return message

        lines = normalized.split("\n")
        rendered_lines: list[str] = []
        for index, line in enumerate(lines, start=1):
            content = line if line else "<EMPTY LINE>"
            rendered_lines.append(f"[Line {index}] {content} [/Line {index}]")

        return (
            "The user submitted a multi-line message. Each [Line N] block below is one original line from the same "
            "message. Do not ignore later lines. If there are multiple questions or requirements, answer all of them "
            "in order. "
            + " ".join(rendered_lines)
        )

    def _build_chat_response(
        self,
        *,
        cwd: Path,
        codex_home: Optional[Path],
        command: list[str],
        reply: str,
        exit_code: int,
        duration_ms: int,
        resume_mode: str,
        session_id: Optional[str],
        stdout: str,
        stderr: str,
    ) -> ChatResponse:
        if exit_code == 0:
            stderr = self._filter_recoverable_stderr(stderr)
            if not stdout.strip():
                filtered_reply = self._filter_recoverable_stderr(reply).strip()
                if filtered_reply:
                    reply = filtered_reply
        return ChatResponse(
            ok=exit_code == 0,
            reply=reply,
            exit_code=exit_code,
            duration_ms=duration_ms,
            cwd=str(cwd),
            codex_home=self._display_codex_home(codex_home),
            command=command,
            resume_mode=resume_mode,
            session_id=session_id,
            effective_model=self._extract_model_from_command(command),
            effective_openai_base_url=self._effective_openai_base_url(),
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
            "resume_mode": response.resume_mode,
            "session_id": response.session_id,
            "effective_model": response.effective_model,
            "effective_openai_base_url": response.effective_openai_base_url,
            "stdout": response.stdout,
            "stderr": response.stderr,
        }

    def _resolve_resume_target(
        self,
        payload: ChatRequest,
        codex_home: Optional[Path],
    ) -> tuple[str, Optional[str], Optional[str]]:
        requested_session = (payload.session_id or "").strip()
        if requested_session:
            if self._is_session_uuid(requested_session):
                return "session_id", requested_session, None
            alias = self._normalize_session_alias(requested_session)
            resolved_session_id = self._load_session_aliases(codex_home).get(alias) if alias else None
            if resolved_session_id:
                return "session_id", resolved_session_id, alias
            return "new", None, alias
        if payload.continue_context:
            return "last", None, None
        return "new", None, None

    def _resolve_resume_mode(self, payload: ChatRequest) -> str:
        if payload.session_id and self._is_session_uuid(payload.session_id):
            return "session_id"
        if payload.continue_context and not payload.session_id:
            return "last"
        return "new"

    def _extract_session_id(self, stdout: str, stderr: str) -> Optional[str]:
        combined = f"{stdout}\n{stderr}"
        match = SESSION_ID_OUTPUT_PATTERN.search(combined)
        if match:
            return match.group(1)
        return None

    def _pump_stream(self, stream: Optional[object], source: str, output_queue: queue.Queue[tuple[str, str]]) -> None:
        try:
            if stream is None:
                return

            buffered = getattr(stream, "buffer", None)
            if buffered is not None and hasattr(buffered, "read1"):
                encoding = getattr(stream, "encoding", None) or "utf-8"
                errors = getattr(stream, "errors", None) or "replace"
                while True:
                    chunk = buffered.read1(STREAM_READ_CHUNK_SIZE)
                    if chunk in (b"", ""):
                        break
                    text = chunk.decode(encoding, errors=errors) if isinstance(chunk, bytes) else str(chunk)
                    if text:
                        output_queue.put((source, text))
                return

            read = getattr(stream, "read", None)
            if callable(read):
                while True:
                    chunk = read(STREAM_READ_CHUNK_SIZE)
                    if chunk in ("", b""):
                        break
                    text = self._safe_output(chunk)
                    if text:
                        output_queue.put((source, text))
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
        env = self._load_dotenv()
        env.update(os.environ)
        base_url = env.get("OPENAI_BASE_URL") or env.get("OPENAI_API_BASE")
        if base_url:
            env.setdefault("OPENAI_BASE_URL", base_url)
            env.setdefault("OPENAI_API_BASE", base_url)
        if codex_home is not None:
            env["CODEX_HOME"] = str(codex_home)
        return env

    def _load_dotenv(self) -> dict[str, str]:
        if self.dotenv_path is None or not self.dotenv_path.exists():
            return {}

        env: dict[str, str] = {}
        content = self.dotenv_path.read_text(encoding="utf-8-sig", errors="ignore")
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            env[key] = value
        return env

    def _effective_model(self, request_model: Optional[str]) -> Optional[str]:
        if request_model:
            return request_model
        env = self._load_dotenv()
        return os.environ.get("OPENAI_MODEL") or env.get("OPENAI_MODEL")

    def _effective_openai_base_url(self) -> Optional[str]:
        env = self._load_dotenv()
        return (
            os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("OPENAI_API_BASE")
            or env.get("OPENAI_BASE_URL")
            or env.get("OPENAI_API_BASE")
        )

    def _extract_model_from_command(self, command: list[str]) -> Optional[str]:
        if "-m" not in command:
            return None
        index = command.index("-m") + 1
        if index >= len(command):
            return None
        return command[index]

    def _config_string_value(self, key: str, value: str) -> str:
        return f"{key}={json.dumps(value, ensure_ascii=False)}"

    def _display_codex_home(self, codex_home: Optional[Path]) -> str:
        if codex_home is not None:
            return str(codex_home)
        return "<inherit default ~/.codex>"

    def _display_dotenv_path(self) -> str:
        if self.dotenv_path is not None:
            return str(self.dotenv_path)
        return "<disabled>"

    def _dotenv_exists(self) -> bool:
        return self.dotenv_path is not None and self.dotenv_path.exists()

    def _safe_output(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)

    def _is_recoverable_stderr_line(self, line: str) -> bool:
        normalized = line.strip()
        if not normalized:
            return False
        return any(pattern.search(normalized) for pattern in RECOVERABLE_STDERR_PATTERNS)

    def _filter_recoverable_stderr(self, text: str) -> str:
        if not text:
            return text
        filtered_lines = [line for line in text.splitlines(keepends=True) if not self._is_recoverable_stderr_line(line)]
        filtered_text = "".join(filtered_lines)
        return filtered_text.strip() if not filtered_text.strip() else filtered_text

    def _consume_visible_stderr(self, buffer: str, *, finalize: bool = False) -> tuple[list[str], str]:
        if not buffer:
            return [], ""

        lines: list[str] = []
        while True:
            newline_index = buffer.find("\n")
            if newline_index < 0:
                break
            lines.append(buffer[: newline_index + 1])
            buffer = buffer[newline_index + 1 :]

        if finalize and buffer:
            lines.append(buffer)
            buffer = ""

        visible_lines = [line for line in lines if not self._is_recoverable_stderr_line(line)]
        return visible_lines, buffer

    def _combine_output(self, stdout: object, stderr: object) -> str:
        stdout_text = self._safe_output(stdout)
        if stdout_text:
            return stdout_text
        return self._safe_output(stderr)

    def _read_last_message(self, last_message_path: Path) -> str:
        if not last_message_path.exists():
            return ""
        return last_message_path.read_text(encoding="utf-8", errors="ignore").strip()

    def _read_skill_info(self, skill_file: Path) -> SkillInfo:
        content = skill_file.read_text(encoding="utf-8-sig", errors="ignore")
        if not content.startswith("---"):
            return SkillInfo(
                name=skill_file.parent.name,
                description=None,
                path=str(skill_file),
                valid=False,
                error="missing YAML frontmatter delimited by ---",
            )

        lines = content.splitlines()
        if not lines or lines[0].strip() != "---":
            return SkillInfo(
                name=skill_file.parent.name,
                description=None,
                path=str(skill_file),
                valid=False,
                error="invalid YAML frontmatter",
            )

        closing_index = None
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                closing_index = index
                break

        if closing_index is None:
            return SkillInfo(
                name=skill_file.parent.name,
                description=None,
                path=str(skill_file),
                valid=False,
                error="invalid YAML frontmatter",
            )

        name = skill_file.parent.name
        description: Optional[str] = None
        for raw_line in lines[1:closing_index]:
            line = raw_line.strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            normalized_key = key.strip()
            normalized_value = value.strip().strip("\"'")
            if normalized_key == "name" and normalized_value:
                name = normalized_value
            elif normalized_key == "description" and normalized_value:
                description = normalized_value

        missing_fields: list[str] = []
        if not name:
            missing_fields.append("name")
        if not description:
            missing_fields.append("description")

        if missing_fields:
            return SkillInfo(
                name=name or skill_file.parent.name,
                description=description,
                path=str(skill_file),
                valid=False,
                error=f"missing frontmatter field(s): {', '.join(missing_fields)}",
            )

        return SkillInfo(
            name=name,
            description=description,
            path=str(skill_file),
            valid=True,
            error=None,
        )

    def _should_answer_skill_inventory(self, message: str) -> bool:
        normalized = message.strip().lower()
        patterns = (
            "what skill",
            "which skill",
            "available skill",
            "current skill",
            "skill list",
            "有什么skill",
            "都有什么skill",
            "当前有什么skill",
            "当前都有什么skill",
            "有哪些skill",
            "技能列表",
            "有什么技能",
            "当前有什么技能",
        )
        return any(pattern in normalized for pattern in patterns)

    def _build_skill_inventory_response(self, *, cwd: Path, codex_home: Optional[Path]) -> str:
        inventory = self.list_skills(str(codex_home) if codex_home is not None else None)
        visible_skills = [skill for skill in inventory.skills if skill.valid]
        if not visible_skills:
            return "当前本地没有可用的 skill。"

        lines = [
            f"当前本地可见 skill 共 {len(visible_skills)} 个，来自 {inventory.skills_dir}：",
            "",
        ]
        for skill in visible_skills:
            lines.append(f"- {skill.name}")
            if skill.description:
                lines.append(f"  {skill.description}")
        return "\n".join(lines)

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

    def _is_session_uuid(self, value: Optional[str]) -> bool:
        return bool(value and SESSION_ID_VALUE_PATTERN.fullmatch(value.strip()))

    def _normalize_session_alias(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        alias = value.strip()
        if not alias or self._is_session_uuid(alias):
            return None
        return alias

    def _session_aliases_path(self, codex_home: Optional[Path]) -> Optional[Path]:
        if codex_home is None:
            return None
        return codex_home / "session_aliases.json"

    def _load_session_aliases(self, codex_home: Optional[Path]) -> dict[str, str]:
        path = self._session_aliases_path(codex_home)
        if path is None or not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        aliases: dict[str, str] = {}
        for key, value in data.items():
            if isinstance(key, str) and isinstance(value, str) and self._is_session_uuid(value):
                aliases[key] = value
        return aliases

    def _store_session_alias(
        self,
        codex_home: Optional[Path],
        alias: Optional[str],
        session_id: Optional[str],
    ) -> None:
        normalized_alias = self._normalize_session_alias(alias)
        if codex_home is None or normalized_alias is None or not self._is_session_uuid(session_id):
            return
        path = self._session_aliases_path(codex_home)
        if path is None:
            return
        aliases = self._load_session_aliases(codex_home)
        aliases[normalized_alias] = str(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(aliases, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


runner = CodexExecRunner()
app = FastAPI(title="Codex HTTP Service")


def load_playground_html() -> str:
    content = PLAYGROUND_HTML_PATH.read_text(encoding="utf-8")
    return content.replace("__DEFAULT_CWD__", json.dumps(str(DEFAULT_CWD)))


@app.get("/", response_class=HTMLResponse)
def playground() -> HTMLResponse:
    return HTMLResponse(load_playground_html())


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return runner.health()


@app.get("/internal/skills", response_model=SkillListResponse, include_in_schema=False)
def list_skills(codex_home: Optional[str] = None) -> SkillListResponse:
    return runner.list_skills(codex_home)


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return runner.run_chat(payload)


@app.post("/chat/stream")
def chat_stream(payload: ChatRequest) -> StreamingResponse:
    return StreamingResponse(runner.stream_chat(payload), media_type="application/x-ndjson")
