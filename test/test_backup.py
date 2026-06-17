import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_setting import backup


class BackupCommandSafetyTests(unittest.TestCase):
    def test_configure_hermes_env_skips_timeout_during_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            hermes_dir = home / ".hermes"
            hermes_dir.mkdir(parents=True)
            env_path = hermes_dir / ".env"
            env_path.write_text("FOO=bar\n", encoding="utf-8")
            logs: list[str] = []

            with (
                patch.object(backup, "home_dir", return_value=home),
                patch.object(backup.logger, "log", side_effect=logs.append),
                patch.object(
                    backup.subprocess,
                    "run",
                    side_effect=subprocess.TimeoutExpired(
                        cmd=["hermes", "gateway", "restart"],
                        timeout=backup.COMMAND_TIMEOUT_SECONDS,
                    ),
                ) as run_mock,
            ):
                backup.configure_hermes_env()

            self.assertIn('TELEGRAM_ALLOWED_USERS="7765138435"\n', env_path.read_text(encoding="utf-8"))
            run_mock.assert_called_once()
            _, kwargs = run_mock.call_args
            self.assertEqual(run_mock.call_args.args[0], ["hermes", "gateway", "restart"])
            self.assertEqual(kwargs["check"], False)
            self.assertEqual(kwargs["timeout"], backup.COMMAND_TIMEOUT_SECONDS)
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            self.assertEqual(kwargs["capture_output"], True)
            self.assertEqual(kwargs["text"], True)
            self.assertTrue(any("timed out" in message for message in logs))

    def test_configure_openclaw_writes_json_with_correct_order(self) -> None:
        """configure_openclaw 应直接写入 JSON：先填 allowFrom，再设 allowlist。"""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            openclaw_dir = home / ".openclaw"
            openclaw_dir.mkdir(parents=True)
            json_path = openclaw_dir / "openclaw.json"
            json_path.write_text("{}", encoding="utf-8")
            logs: list[str] = []
            calls: list[list[str]] = []

            def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append(cmd)
                return subprocess.CompletedProcess(cmd, 0)

            with (
                patch.object(backup, "home_dir", return_value=home),
                patch.object(backup.logger, "log", side_effect=logs.append),
                patch.object(backup, "_resolve_command", return_value="/usr/bin/openclaw"),
                patch.object(backup.subprocess, "run", side_effect=fake_run),
            ):
                backup.configure_openclaw()

            data = json.loads(json_path.read_text(encoding="utf-8"))
            telegram = data["channels"]["telegram"]
            self.assertEqual(telegram["allowFrom"], ["7765138435"])
            self.assertEqual(telegram["dmPolicy"], "allowlist")
            self.assertEqual(telegram["groupPolicy"], "open")
            # 仅用 CLI 重启网关，不再用 config set
            self.assertEqual(calls, [["openclaw", "gateway", "restart"]])

    def test_configure_openclaw_preserves_existing_allow_from(self) -> None:
        """已有的 allowFrom 条目应保留并去重。"""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            openclaw_dir = home / ".openclaw"
            openclaw_dir.mkdir(parents=True)
            json_path = openclaw_dir / "openclaw.json"
            json_path.write_text(
                json.dumps({"channels": {"telegram": {"allowFrom": ["111", "111"]}}}),
                encoding="utf-8",
            )

            with (
                patch.object(backup, "home_dir", return_value=home),
                patch.object(backup.logger, "log"),
                patch.object(backup, "_resolve_command", return_value="/usr/bin/openclaw"),
                patch.object(backup.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)),
            ):
                backup.configure_openclaw()

            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["channels"]["telegram"]["allowFrom"], ["111", "7765138435"])

    def test_configure_openclaw_skips_when_command_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            openclaw_dir = home / ".openclaw"
            openclaw_dir.mkdir(parents=True)
            (openclaw_dir / "openclaw.json").write_text("{}", encoding="utf-8")
            logs: list[str] = []

            with (
                patch.object(backup, "home_dir", return_value=home),
                patch.object(backup.logger, "log", side_effect=logs.append),
                patch.object(backup, "_resolve_command", return_value=None),
            ):
                backup.configure_openclaw()

            self.assertTrue(any("'openclaw' command not found" in message for message in logs))


if __name__ == "__main__":
    unittest.main()
