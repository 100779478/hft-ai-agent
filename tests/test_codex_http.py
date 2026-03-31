import json
import subprocess
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
        self.assertIn(r'"D:\\hft-ai-agent"', body)
        self.assertIn('buffer.indexOf("\\n")', body)
        self.assertIn('JSON.stringify(event.data)}\\n`', body)

    def test_build_command_should_include_expected_flags(self) -> None:
        runner = CodexExecRunner(codex_command="codex")
        request = ChatRequest(
            message="Reply with OK",
            cwd="D:/hft-ai-agent",
            model="gpt-5.4",
            profile="default",
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
        runner = CodexExecRunner(codex_command="codex")

        self.assertEqual(runner.default_codex_home, (PROJECT_ROOT / ".codex").resolve())

    def test_run_chat_should_return_last_message(self) -> None:
        runner = CodexExecRunner(codex_command="codex", default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"))
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
        self.assertIn("codex", response.command[0])

    def test_run_chat_should_fallback_to_stderr_when_stdout_missing(self) -> None:
        runner = CodexExecRunner(codex_command="codex", default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"))
        request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent")

        def fake_run(command, cwd, env, capture_output, text, encoding, errors, timeout):
            return subprocess.CompletedProcess(args=command, returncode=1, stdout=None, stderr="stderr fallback")

        with patch("app.codex_http.subprocess.run", side_effect=fake_run):
            response = runner.run_chat(request)

        self.assertFalse(response.ok)
        self.assertEqual(response.reply, "stderr fallback")
        self.assertEqual(response.stdout, "")
        self.assertEqual(response.stderr, "stderr fallback")

    def test_run_chat_should_handle_timeout(self) -> None:
        runner = CodexExecRunner(codex_command="codex", default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"))
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
        runner = CodexExecRunner(codex_command="codex", default_codex_home=Path("D:/hft-ai-agent/.codex-http-test"))
        request = ChatRequest(message="Reply with OK", cwd="D:/hft-ai-agent")

        with patch("app.codex_http.subprocess.Popen", new=FakePopen):
            events = [json.loads(line) for line in runner.stream_chat(request)]

        event_types = [event["type"] for event in events]
        self.assertEqual(event_types[0], "start")
        self.assertIn("stdout", event_types)
        self.assertIn("stderr", event_types)
        self.assertEqual(event_types[-1], "result")
        self.assertEqual(events[-1]["data"]["reply"], "OK")
        self.assertTrue(events[-1]["data"]["ok"])


if __name__ == "__main__":
    unittest.main()
