"""End-to-end tests for the reverse (pull) direction.

These tests run inside a docker container AFTER:
  1. ./run.py setup --tag dotfiles  (forward: decrypt secrets to filesystem)
  2. ./run.py pull --tag secrets    (reverse: re-encrypt secrets back to git store)

They verify that the round-trip encryption produces a file that can be
decrypted back to the original plaintext.
"""

import os
import subprocess
import unittest
from pathlib import Path

from config import CopySecretFiles, config


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(path)))


class TestReverseRoundTrip(unittest.TestCase):
    """Verify that pull re-encrypts secrets and the result decrypts correctly."""

    def test_encrypted_files_exist_after_pull(self):
        missing = []
        for entry in config:
            if not isinstance(entry, CopySecretFiles):
                continue
            for pair in entry.files:
                src = Path(pair[0])
                if not src.exists():
                    missing.append(str(src))
        self.assertFalse(missing, f"Encrypted files missing after pull: {missing}")

    def test_round_trip_decrypts_to_original(self):
        """Decrypt the re-encrypted file and compare to the plaintext that was set up."""
        for entry in config:
            if not isinstance(entry, CopySecretFiles):
                continue
            for pair in entry.files:
                encrypted = Path(pair[0])
                plaintext = _expand(pair[1])
                if not encrypted.exists() or not plaintext.exists():
                    continue

                original_content = plaintext.read_text()

                result = subprocess.run(
                    [
                        "gpg", "--batch", "--pinentry-mode", "loopback",
                        "--decrypt", "--passphrase-fd", "0",
                        str(encrypted),
                    ],
                    input=b"testpassword",
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0,
                                 f"Failed to decrypt {encrypted}: {result.stderr.decode()}")
                decrypted_content = result.stdout.decode()
                self.assertEqual(decrypted_content, original_content,
                                 f"Round-trip mismatch for {encrypted}")
