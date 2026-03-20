"""E2E tests for the diff subcommand using temporary directories."""

import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from run import run_diff, _diff_files, _diff_dirs


class TestDiffFiles(unittest.TestCase):

    def test_no_diff_when_identical(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "a.txt"
            b = Path(d) / "b.txt"
            a.write_text("hello\n")
            b.write_text("hello\n")
            self.assertFalse(_diff_files(str(a), str(b)))

    def test_diff_when_content_differs(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "a.txt"
            b = Path(d) / "b.txt"
            a.write_text("hello\n")
            b.write_text("world\n")
            with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertTrue(_diff_files(str(a), str(b)))
                self.assertIn("-world", out.getvalue())
                self.assertIn("+hello", out.getvalue())

    def test_diff_when_dst_missing(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "a.txt"
            b = Path(d) / "b.txt"
            a.write_text("content\n")
            with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertTrue(_diff_files(str(a), str(b)))
                self.assertIn("+content", out.getvalue())

    def test_no_diff_when_both_missing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(_diff_files(str(Path(d) / "x"), str(Path(d) / "y")))


class TestDiffDirs(unittest.TestCase):

    def test_no_diff_when_identical(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src"
            dst = Path(d) / "dst"
            src.mkdir()
            dst.mkdir()
            (src / "f.txt").write_text("same\n")
            (dst / "f.txt").write_text("same\n")
            self.assertFalse(_diff_dirs(str(src), str(dst)))

    def test_diff_when_file_content_differs(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src"
            dst = Path(d) / "dst"
            src.mkdir()
            dst.mkdir()
            (src / "f.txt").write_text("aaa\n")
            (dst / "f.txt").write_text("bbb\n")
            with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertTrue(_diff_dirs(str(src), str(dst)))
                self.assertIn("-bbb", out.getvalue())
                self.assertIn("+aaa", out.getvalue())

    def test_diff_extra_file_in_src(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src"
            dst = Path(d) / "dst"
            src.mkdir()
            dst.mkdir()
            (src / "new.txt").write_text("new\n")
            with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertTrue(_diff_dirs(str(src), str(dst)))
                self.assertIn("+new", out.getvalue())

    def test_diff_extra_file_in_dst(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src"
            dst = Path(d) / "dst"
            src.mkdir()
            dst.mkdir()
            (dst / "old.txt").write_text("old\n")
            with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertTrue(_diff_dirs(str(src), str(dst)))
                self.assertIn("-old", out.getvalue())


class TestRunDiffE2E(unittest.TestCase):
    """Integration test: patch config and call run_diff end-to-end."""

    def test_run_diff_with_copy_files(self):
        from config import CopyFiles
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "a.txt"
            dst = Path(d) / "b.txt"
            src.write_text("hello\n")
            dst.write_text("world\n")
            fake_config = [
                CopyFiles(
                    os_=['linux'],
                    tags=['dotfiles'],
                    files=[[str(src), str(dst)]],
                ),
            ]
            with mock.patch("run.config", fake_config):
                with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                    rc = run_diff("linux-ubuntu")
                    self.assertEqual(rc, 1)
                    self.assertIn("-world", out.getvalue())
                    self.assertIn("+hello", out.getvalue())

    def test_run_diff_no_changes(self):
        from config import CopyFiles
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "a.txt"
            dst = Path(d) / "b.txt"
            src.write_text("same\n")
            dst.write_text("same\n")
            fake_config = [
                CopyFiles(
                    os_=['linux'],
                    tags=['dotfiles'],
                    files=[[str(src), str(dst)]],
                ),
            ]
            with mock.patch("run.config", fake_config):
                rc = run_diff("linux-ubuntu")
                self.assertEqual(rc, 0)

    def test_run_diff_with_copy_dirs(self):
        from config import CopyDirs
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "srcdir"
            dst = Path(d) / "dstdir"
            src.mkdir()
            dst.mkdir()
            (src / "x.txt").write_text("new\n")
            (dst / "x.txt").write_text("old\n")
            fake_config = [
                CopyDirs(
                    os_=['linux'],
                    tags=['dotfiles'],
                    dirs=[[str(src), str(dst)]],
                ),
            ]
            with mock.patch("run.config", fake_config):
                with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                    rc = run_diff("linux-ubuntu")
                    self.assertEqual(rc, 1)
                    self.assertIn("-old", out.getvalue())
                    self.assertIn("+new", out.getvalue())


if __name__ == "__main__":
    unittest.main()
