import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).parents[1] / "contrib/plugins/open-in-dashboard"
SCRIPT = PLUGIN / "open.sh"


def write_exe(path, body):
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


@unittest.skipIf(os.name == "nt" or shutil.which("sh") is None, "the plugin is a POSIX shell script")
class OpenInDashboardPluginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.opened = self.tmp / "opened"
        self.probed = self.tmp / "probed"
        write_exe(self.bin / "opener", f'printf "%s\\n" "$@" > "{self.opened}"\n')
        self.curl(0)
        self.config = self.tmp / "config-dir"
        self.config.mkdir()

    def curl(self, code):
        # The last argument is the URL the script probes.
        write_exe(self.bin / "curl", f'for a; do :; done; printf "%s\\n" "$a" > "{self.probed}"; exit {code}\n')

    def run_script(self, **env):
        base = {
            "PATH": f"{self.bin}{os.pathsep}/usr/bin{os.pathsep}/bin",
            "HOME": str(self.tmp),
            "HERDR_PLUGIN_CONFIG_DIR": str(self.config),
            "HERDR_DASHBOARD_OPENER": str(self.bin / "opener"),
        }
        base.update({k: v for k, v in env.items() if v is not None})
        for k in [k for k, v in env.items() if v is None]:
            base.pop(k, None)
        return subprocess.run(["sh", str(SCRIPT)], cwd=PLUGIN, env=base, capture_output=True, text=True, timeout=30)

    def opened_url(self):
        return self.opened.read_text().strip() if self.opened.exists() else None

    def test_manifest_declares_a_pane_action_that_runs_the_script(self):
        text = (PLUGIN / "herdr-plugin.toml").read_text()
        self.assertIn('id = "contrib.open-in-dashboard"', text)
        self.assertIn('contexts = ["pane"]', text)
        self.assertIn('command = ["sh", "open.sh"]', text)
        self.assertIn('min_herdr_version = "', text)

    def test_opens_the_default_url_for_the_focused_pane(self):
        result = self.run_script(HERDR_PANE_ID="wD:p1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.opened_url(), "http://127.0.0.1:8787/3d?focus=wD:p1")
        self.assertEqual(self.probed.read_text().strip(), "http://127.0.0.1:8787/3d?focus=wD:p1")

    def test_falls_back_to_the_active_pane_for_custom_command_keybindings(self):
        result = self.run_script(HERDR_ACTIVE_PANE_ID="w2:p4")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.opened_url(), "http://127.0.0.1:8787/3d?focus=w2:p4")

    def test_url_comes_from_the_environment_or_the_config_file(self):
        (self.config / "config").write_text('# local dashboard\nHERDR_DASHBOARD_URL = "http://127.0.0.1:9000/x?pane={pane_id}&y=1"\n')
        result = self.run_script(HERDR_PANE_ID="wD:p1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.opened_url(), "http://127.0.0.1:9000/x?pane=wD:p1&y=1")
        result = self.run_script(HERDR_PANE_ID="wD:p1", HERDR_DASHBOARD_URL="https://dash.local/{pane_id}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.opened_url(), "https://dash.local/wD:p1")

    def test_nothing_is_opened_when_the_dashboard_does_not_answer(self):
        self.curl(7)
        result = self.run_script(HERDR_PANE_ID="wD:p1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("is the dashboard running", result.stderr)
        self.assertIsNone(self.opened_url())

    def test_refuses_a_missing_or_odd_pane_id_and_a_non_http_url(self):
        for env in (
            {"HERDR_PANE_ID": None, "HERDR_ACTIVE_PANE_ID": None},
            {"HERDR_PANE_ID": "wD:p1;rm -rf ~"},
            {"HERDR_PANE_ID": "wD:p1", "HERDR_DASHBOARD_URL": "file:///etc/passwd"},
        ):
            result = self.run_script(**env)
            self.assertEqual(result.returncode, 1, env)
            self.assertTrue(result.stderr.startswith("open-in-dashboard: "), result.stderr)
            self.assertIsNone(self.opened_url())

    def test_picks_xdg_open_outside_wsl_and_macos(self):
        write_exe(self.bin / "xdg-open", f'printf "%s\\n" "$@" > "{self.opened}"\n')
        write_exe(self.bin / "uname", "echo Linux\n")
        if Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists():
            self.skipTest("this machine is WSL")
        result = self.run_script(HERDR_PANE_ID="wD:p1", HERDR_DASHBOARD_OPENER=None, WSL_DISTRO_NAME=None)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.opened_url(), "http://127.0.0.1:8787/3d?focus=wD:p1")

    def test_prefers_wslview_on_wsl(self):
        write_exe(self.bin / "wslview", f'printf "%s\\n" "$@" > "{self.opened}"\n')
        write_exe(self.bin / "xdg-open", "exit 3\n")
        result = self.run_script(HERDR_PANE_ID="wD:p1", HERDR_DASHBOARD_OPENER=None, WSL_DISTRO_NAME="Ubuntu")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.opened_url(), "http://127.0.0.1:8787/3d?focus=wD:p1")


if __name__ == "__main__":
    unittest.main()
