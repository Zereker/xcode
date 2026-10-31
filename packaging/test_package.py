import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("packager", Path(__file__).with_name("package.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class PackagingTests(unittest.TestCase):
    def test_version_rejects_paths_and_shell_input(self):
        for value in ("../latest", "2.1.0;echo nope", "", "stable", "v2.1.0"):
            with self.assertRaises(ValueError):
                p.valid_version(value)

    def test_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            binary = Path(d) / "xcode"
            binary.write_bytes(b"original")
            expected = p.sha256(binary)
            binary.write_bytes(b"corrupted")
            with self.assertRaises(ValueError):
                p.verify_checksum(binary, expected)

    def test_failed_manifest_download_never_replaces_output(self):
        with tempfile.TemporaryDirectory() as d:
            existing = Path(d) / "xcode-darwin-arm64.tar.gz"
            existing.write_bytes(b"previous good release")
            with patch.object(p.platform, "system", return_value="Darwin"), patch.object(p.platform, "machine", return_value="arm64"), patch.object(p, "download", side_effect=RuntimeError("network failure")):
                with self.assertRaises(RuntimeError):
                    p.build("2.1.316", d)
            self.assertEqual(existing.read_bytes(), b"previous good release")

    def test_wrong_runtime_version_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(p, "run") as run:
                run.return_value.stdout = "0.0.0 (Claude Code)"
                with self.assertRaises(ValueError):
                    p.smoke(Path(d) / "xcode", "2.1.316", d)
                self.assertEqual(run.call_count, 1)

if __name__ == "__main__":
    unittest.main()
