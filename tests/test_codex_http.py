import json
import queue
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.codex_http import ChatRequest, CodexExecRunner, PROJECT_ROOT, playground


SESSION_UUID = "019d4250-293e-7182-88e1-be2e7449b847"

NOISY_STDERR = (
    "2026-04-01T10:02:01.452837Z ERROR codex_core::codex: failed to load skill D:\\hft-ai-agent\\.codex\\skills\\html_generation\\SKILL.md: missing YAML frontmatter delimited by ---\n"
    "2026-04-01T10:02:02.199556Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: HTTP error: 404 Not Found, url: wss://api.zectai.com/v1/responses\n"
    "ERROR: Reconnecting... 2/5\n"
)


class FakeStream:
    def __init__(self, lines: list[str]) -> None:
        self._lines = list(lines)

    def readline(self) -> str:
        if not self._lines:
            return ""
        return self._lines.pop(0)

    def close(self) -> None:
        return None



class FakeChunkStream:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = list(chunks)

    def read(self, size: int = -1) -> str:
        if not self._chunks:
            return ""
        chunk = self._chunks.pop(0)
        if size >= 0 and len(chunk) > size:
            self._chunks.insert(0, chunk[size:])
            return chunk[:size]
        return chunk

    def close(self) -> None:
        return None
class FakePopen:
    def __init__(self, command, cwd, env, stdout, stderr, text, bufsize, encoding, errors):
        self.command = command
        self.returncode = 0
        self.stdout = FakeStream(["stream line 1\n", "stream line 2\n"])
        self.stderr = FakeStream(["warn line\n"])
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text("OK", encoding="utf-8")

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.returncode = -9


class FakeNoisyPopen:
    def __init__(self, command, cwd, env, stdout, stderr, text, bufsize, encoding, errors):
        self.command = command
        self.returncode = 0
        self.stdout = FakeStream(["assistant reply\n"])
        self.stderr = FakeStream([
            "2026-04-01T10:02:01.452837Z ERROR codex_core::codex: failed to load skill D:\\hft-ai-agent\\.codex\\skills\\html_generation\\SKILL.md: missing YAML frontmatter delimited by ---\n",
            "2026-04-01T10:02:02.199556Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: HTTP error: 404 Not Found, url: wss://api.zectai.com/v1/responses\n",
            "ERROR: Reconnecting... 2/5\n",
            "real warning\n",
        ])
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text("OK", encoding="utf-8")

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.returncode = -9


class CodexHttpTests(unittest.TestCase):
    def test_playground_should_render_html_page(self) -> None:
        response = playground()
        body = response.body.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("HTML &#x5bf9;&#x8bdd;&#x5de5;&#x4f5c;&#x53f0;", body)
        self.assertIn("/chat/stream", body)
        self.assertIn("customerid", body)
        self.assertIn("&#x5f53;&#x524d;&#x7528;&#x6237;", body)
        self.assertIn("renderMarkdown", body)
        self.assertIn("createArtifactCard", body)
        self.assertIn("renderArtifactCards", body)
        self.assertIn("openPreviewDrawer", body)
        self.assertIn("previewDrawerFrame", body)
        self.assertIn("parseReplySegments", body)
        self.assertIn("startTypewriter", body)
        self.assertIn("cancelTypewriter", body)
        self.assertIn("flushTypewriter", body)
        self.assertIn("buildPendingMessage", body)
        self.assertIn("renderPendingProgress", body)
        self.assertIn('event.type==="ping"', body)
        self.assertIn("elapsed_ms", body)
        self.assertIn("Shift + &#x56de;&#x8f66;&#x6362;&#x884c;", body)
        self.assertIn("--bg-base", body)
        self.assertIn("\\u6b63\\u5728\\u7b49\\u5f85\\u6a21\\u578b\\u8fd4\\u56de", body)
        self.assertIn("\\u6b63\\u5728\\u63a5\\u6536\\u6267\\u884c\\u8f93\\u51fa", body)
        self.assertNotIn("\\u5904\\u7406\\u4e2d...\\\\n\\u6b63\\u5728\\u63a5\\u6536\\u6267\\u884c\\u8f93\\u51fa", body)
        self.assertIn("const DEFAULT_CWD =", body)
        self.assertIn("hft-ai-agent", body)

    def test_requirement_intake_skill_should_accumulate_context_and_stop_reasking(self) -> None:
        body = (PROJECT_ROOT / ".codex" / "skills" / "requirement_intake" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("始终合并当前轮与之前轮次里已经确认的信息", body)
        self.assertIn("只允许一次性列出当前全部缺失项", body)
        self.assertIn("[INTAKE_COMPLETE]", body)

    def test_build_command_should_include_expected_flags(self) -> None:
        runner = CodexExecRunner(codex_command="codex", dotenv_path=None)
        request = ChatRequest(
            message="Reply with OK",
            cwd="D:/hft-ai-agent",
            model="gpt-5.4",
            profile="default",
            ephemeral=True,
            add_dirs=["D:/hft-ai-agent/skills"],
        )

        command = runner._build_command(
            payload=request,
            cwd=Path("D:/hft-ai-agent"),
            last_message_path=Path("D:/tmp/last.txt"),
        )

        self.assertIn("exec", command)
        self.assertIn("--output-last-message", command)
        self.assertIn("--ephemeral", command)
        self.assertIn("--skip-git-repo-check", command)
        self.assertIn("--full-auto", command)
        self.assertIn("-m", command)
        self.assertIn("gpt-5.4", command)
        self.assertIn("-p", command)
        self.assertIn("default", command)
        self.assertIn("--add-dir", command)
        self.assertIn("Reply with OK", command)

    def test_default_codex_home_should_use_project_dot_codex(self) -> None:
        runner = CodexExecRunner(codex_command="codex", dotenv_path=None)

        self.assertEqual(runner.default_codex_home, (PROJECT_ROOT / ".codex").resolve())

    def test_extract_session_id_should_parse_cli_output(self) -> None:
        runner = CodexExecRunner(codex_command="codex", dotenv_path=None)
        session_id = runner._extract_session_id("", f"session id: {SESSION_UUID}")

        self.assertEqual(session_id, SESSION_UUID)

    def test_build_command_should_resume_last_context(self) -> None:
        runner = CodexExecRunner(codex_command="codex", dotenv_path=None)
        request = ChatRequest(message="Follow up", cwd="D:/hft-ai-agent", continue_context=True)

        command = runner._build_command(
            payload=request,
            cwd=Path("D:/hft-ai-agent"),
            last_message_path=Path("D:/tmp/last.txt"),
        )

        self.assertEqual(command[:3], ["codex", "exec", "resume"])
        self.assertIn("--last", command)
        self.assertNotIn("-C", command)
        self.assertNotIn("--add-dir", command)
        self.assertEqual(command[-1], "Follow up")

    def test_build_command_should_expand_multiline_message_into_line_blocks(self) -> None:
        runner = CodexExecRunner(codex_command="codex", dotenv_path=None)
        request = ChatRequest(message="line1\nline2\nline3", cwd="D:/hft-ai-agent")

        command = runner._build_command(
            payload=request,
            cwd=Path("D:/hft-ai-agent"),
            last_message_path=Path("D:/tmp/last.txt"),
        )

        self.assertIn("The user submitted a multi-line message.", command[-1])
        self.assertIn("[Line 1] line1 [/Line 1]", command[-1])
        self.assertIn("[Line 2] line2 [/Line 2]", command[-1])
        self.assertIn("[Line 3] line3 [/Line 3]", command[-1])
        self.assertNotIn("\nline2", command[-1])

    def test_run_chat_should_return_last_message(self) -> None:
        runner = CodexExecRunner(
            codex_command="codex",
            default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"),
            dotenv_path=None,
        )
        request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent")

        def fake_run(command, cwd, env, capture_output, text, encoding, errors, timeout):
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text("OK", encoding="utf-8")
            return subprocess.CompletedProcess(args=command, returncode=0, stdout="stdout", stderr="")

        with patch("app.codex_http.subprocess.run", side_effect=fake_run):
            response = runner.run_chat(request)

        self.assertTrue(response.ok)
        self.assertEqual(response.reply, "OK")
        self.assertEqual(response.exit_code, 0)
        self.assertEqual(response.resume_mode, "new")
        self.assertIsNone(response.session_id)
        self.assertIn("codex", response.command[0])

    def test_run_chat_should_fallback_to_stderr_when_stdout_missing(self) -> None:
        runner = CodexExecRunner(
            codex_command="codex",
            default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"),
            dotenv_path=None,
        )
        request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent")

        def fake_run(command, cwd, env, capture_output, text, encoding, errors, timeout):
            return subprocess.CompletedProcess(args=command, returncode=1, stdout=None, stderr="stderr fallback")

        with patch("app.codex_http.subprocess.run", side_effect=fake_run):
            response = runner.run_chat(request)

        self.assertFalse(response.ok)
        self.assertEqual(response.reply, "stderr fallback")
        self.assertEqual(response.resume_mode, "new")
        self.assertIsNone(response.session_id)
        self.assertEqual(response.stdout, "")
        self.assertEqual(response.stderr, "stderr fallback")

    def test_run_chat_should_handle_timeout(self) -> None:
        runner = CodexExecRunner(
            codex_command="codex",
            default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"),
            dotenv_path=None,
        )
        request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent", timeout_seconds=5)

        with patch(
            "app.codex_http.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["codex"], timeout=5),
        ):
            response = runner.run_chat(request)

        self.assertFalse(response.ok)
        self.assertEqual(response.exit_code, -1)
        self.assertIn("timed out", response.reply)

    def test_run_chat_should_filter_recoverable_stderr_noise_on_success(self) -> None:
        runner = CodexExecRunner(
            codex_command="codex",
            default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"),
            dotenv_path=None,
        )
        request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent")

        def fake_run(command, cwd, env, capture_output, text, encoding, errors, timeout):
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text("OK", encoding="utf-8")
            return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr=NOISY_STDERR + "real warning\n")

        with patch("app.codex_http.subprocess.run", side_effect=fake_run):
            response = runner.run_chat(request)

        self.assertTrue(response.ok)
        self.assertEqual(response.reply, "OK")
        self.assertEqual(response.stderr, "real warning\n")

    def test_run_chat_should_preserve_recoverable_stderr_noise_on_failure(self) -> None:
        runner = CodexExecRunner(
            codex_command="codex",
            default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"),
            dotenv_path=None,
        )
        request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent")

        def fake_run(command, cwd, env, capture_output, text, encoding, errors, timeout):
            return subprocess.CompletedProcess(args=command, returncode=1, stdout="", stderr=NOISY_STDERR)

        with patch("app.codex_http.subprocess.run", side_effect=fake_run):
            response = runner.run_chat(request)

        self.assertFalse(response.ok)
        self.assertIn("responses_websocket", response.stderr)
        self.assertIn("missing YAML frontmatter", response.reply)

    def test_stream_chat_should_emit_progress_and_result(self) -> None:
        runner = CodexExecRunner(
            codex_command="codex",
            default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"),
            dotenv_path=None,
        )
        request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent")

        with patch("app.codex_http.subprocess.Popen", new=FakePopen):
            events = [json.loads(line) for line in runner.stream_chat(request)]

        event_types = [event["type"] for event in events]
        self.assertEqual(event_types[0], "start")
        self.assertIn("stdout", event_types)
        self.assertIn("stderr", event_types)
        self.assertEqual(event_types[-1], "result")
        self.assertEqual(events[-1]["data"]["reply"], "OK")
        self.assertEqual(events[-1]["data"]["resume_mode"], "new")
        self.assertIsNone(events[-1]["data"]["session_id"])
        self.assertTrue(events[-1]["data"]["ok"])

    def test_stream_chat_should_filter_recoverable_stderr_noise_on_success(self) -> None:
        runner = CodexExecRunner(
            codex_command="codex",
            default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"),
            dotenv_path=None,
        )
        request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent")

        with patch("app.codex_http.subprocess.Popen", new=FakeNoisyPopen):
            events = [json.loads(line) for line in runner.stream_chat(request)]

        stderr_events = [event for event in events if event["type"] == "stderr"]
        self.assertEqual([event["data"] for event in stderr_events], ["real warning\n"])
        self.assertEqual(events[-1]["data"]["stderr"], "real warning\n")
        self.assertNotIn("responses_websocket", events[-1]["data"]["stderr"])

    def test_pump_stream_should_emit_partial_chunks_without_newline(self) -> None:
        runner = CodexExecRunner(codex_command="codex", dotenv_path=None)
        output_queue: queue.Queue[tuple[str, str]] = queue.Queue()

        runner._pump_stream(FakeChunkStream(["partial", " output"]), "stdout", output_queue)

        events: list[tuple[str, str]] = []
        while not output_queue.empty():
            events.append(output_queue.get())

        self.assertEqual(events[:-1], [("stdout", "partial"), ("stdout", " output")])
        self.assertEqual(events[-1], ("stdout:done", ""))

    def test_run_chat_should_persist_customerid_alias_and_resume_with_real_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            runner = CodexExecRunner(codex_command="codex", default_codex_home=codex_home, dotenv_path=None)
            request = ChatRequest(
                message="Build page",
                cwd="D:/hft-ai-agent",
                continue_context=True,
                session_id="admin",
            )
            commands: list[list[str]] = []
            replies = ["FIRST", "SECOND"]
            results = [
                subprocess.CompletedProcess(args=["codex"], returncode=0, stdout="", stderr=f"session id: {SESSION_UUID}"),
                subprocess.CompletedProcess(args=["codex"], returncode=0, stdout="", stderr=""),
            ]

            def fake_run(command, cwd, env, capture_output, text, encoding, errors, timeout):
                commands.append(command)
                output_path = Path(command[command.index("--output-last-message") + 1])
                output_path.write_text(replies[len(commands) - 1], encoding="utf-8")
                return results[len(commands) - 1]

            with patch("app.codex_http.subprocess.run", side_effect=fake_run):
                first = runner.run_chat(request)
                second = runner.run_chat(request)

            alias_map = json.loads((codex_home / "session_aliases.json").read_text(encoding="utf-8"))
            self.assertEqual(alias_map["admin"], SESSION_UUID)
            self.assertEqual(first.resume_mode, "new")
            self.assertEqual(first.session_id, SESSION_UUID)
            self.assertEqual(first.reply, "FIRST")
            self.assertEqual(commands[0][:2], ["codex", "exec"])
            self.assertNotIn("resume", commands[0])
            self.assertEqual(second.resume_mode, "session_id")
            self.assertEqual(second.reply, "SECOND")
            self.assertEqual(commands[1][:3], ["codex", "exec", "resume"])
            self.assertIn(SESSION_UUID, commands[1])

    def test_build_command_should_use_dotenv_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / ".env"
            dotenv_path.write_text(
                "OPENAI_MODEL=gpt-5.4\nOPENAI_BASE_URL=https://api.zectai.com/v1\n",
                encoding="utf-8",
            )
            runner = CodexExecRunner(codex_command="codex", dotenv_path=dotenv_path)
            request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent")

            command = runner._build_command(
                payload=request,
                cwd=Path("D:/hft-ai-agent"),
                last_message_path=Path("D:/tmp/last.txt"),
            )

        self.assertIn("-m", command)
        self.assertIn("gpt-5.4", command)
        self.assertIn("-c", command)
        self.assertIn('openai_base_url="https://api.zectai.com/v1"', command)

    def test_build_env_should_load_dotenv_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / ".env"
            dotenv_path.write_text(
                "OPENAI_API_KEY=test-key\nOPENAI_BASE_URL=https://api.zectai.com/v1\n",
                encoding="utf-8",
            )
            runner = CodexExecRunner(codex_command="codex", dotenv_path=dotenv_path)

            env = runner._build_env(Path("D:/hft-ai-agent/.codex-test"))

        self.assertEqual(env["OPENAI_API_KEY"], "test-key")
        self.assertEqual(env["OPENAI_BASE_URL"], "https://api.zectai.com/v1")
        self.assertEqual(env["OPENAI_API_BASE"], "https://api.zectai.com/v1")
        self.assertEqual(env["CODEX_HOME"], str(Path("D:/hft-ai-agent/.codex-test")))

    def test_run_chat_should_report_effective_model_and_base_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / ".env"
            dotenv_path.write_text(
                "OPENAI_MODEL=gpt-5.4\nOPENAI_BASE_URL=https://api.zectai.com/v1\n",
                encoding="utf-8",
            )
            runner = CodexExecRunner(
                codex_command="codex",
                default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"),
                dotenv_path=dotenv_path,
            )
            request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent")

            def fake_run(command, cwd, env, capture_output, text, encoding, errors, timeout):
                output_path = Path(command[command.index("--output-last-message") + 1])
                output_path.write_text("OK", encoding="utf-8")
                return subprocess.CompletedProcess(args=command, returncode=0, stdout="stdout", stderr="")

            with patch("app.codex_http.subprocess.run", side_effect=fake_run):
                response = runner.run_chat(request)

        self.assertEqual(response.effective_model, "gpt-5.4")
        self.assertEqual(response.effective_openai_base_url, "https://api.zectai.com/v1")
        self.assertIn("-m", response.command)
        self.assertIn('openai_base_url="https://api.zectai.com/v1"', response.command)


if __name__ == "__main__":
    unittest.main()

