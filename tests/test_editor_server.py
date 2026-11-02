import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


class EditorServerDefaultsTests(unittest.TestCase):
    def test_listens_on_port_8886_by_default(self):
        root = Path(__file__).resolve().parents[1]
        process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                str(root / "scripts" / "editor_server.py"),
                "--no-browser",
                "--token",
                "test-token",
            ],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8886/", timeout=0.2) as response:
                        self.assertEqual(response.url, "http://127.0.0.1:8886/editor/?token=test-token")
                        return
                except (urllib.error.URLError, TimeoutError):
                    if process.poll() is not None:
                        break
                    time.sleep(0.05)

            output = process.stdout.read() if process.poll() is not None and process.stdout else ""
            self.fail(f"Editor did not listen on default port 8886.\n{output}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            if process.stdout:
                process.stdout.close()


if __name__ == "__main__":
    unittest.main()
