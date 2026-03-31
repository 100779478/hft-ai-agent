import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.codex_http import ChatRequest, CodexExecRunner, PROJECT_ROOT, playground


class FakeStream:
    def __init__(self, lines: list[str]) -> None:
        self._lines = list(lines)

    def readline(self) -> str:
        if not self._lines:
            return ""
        return self._lines.pop(0)

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


class CodexHttpTests(unittest.TestCase):
    def test_playground_should_render_html_page(self) -> None:
        response = playground()
        body = response.body.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Codex HTTP Test Page", body)
        self.assertIn("/chat", body)
        self.assertIn("/health", body)
        self.assertIn("/chat/stream", body)
        self.assertIn("Reset Context", body)
        self.assertIn("continue_context", body)
        self.assertIn("session_id", body)
        self.assertIn(r'"D:\\hft-ai-agent"', body)
        self.assertIn('buffer.indexOf("\\n")', body)
        self.assertIn('JSON.stringify(event.data)}\\n`', body)

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
        session_id = runner._extract_session_id("", "session id: 019d4250-293e-7182-88e1-be2e7449b847")

        self.assertEqual(session_id, "019d4250-293e-7182-88e1-be2e7449b847")

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

    def test_run_chat_should_return_last_message(self) -> None:
        runner = CodexExecRunner(codex_command="codex", default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"), dotenv_path=None)
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
        runner = CodexExecRunner(codex_command="codex", default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"), dotenv_path=None)
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
        runner = CodexExecRunner(codex_command="codex", default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"), dotenv_path=None)
        request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent", timeout_seconds=5)

        with patch(
            "app.codex_http.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["codex"], timeout=5),
        ):
            response = runner.run_chat(request)

        self.assertFalse(response.ok)
        self.assertEqual(response.exit_code, -1)
        self.assertIn("timed out", response.reply)

    def test_stream_chat_should_emit_progress_and_result(self) -> None:
        runner = CodexExecRunner(codex_command="codex", default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"), dotenv_path=None)
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
