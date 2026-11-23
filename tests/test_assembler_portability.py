#!/usr/bin/env python3
"""Verify that pasmo and vasm produce byte-identical binaries.

Set PASMO and VASM in the environment to point at specific assembler
executables; otherwise the test uses whichever ones are on PATH and skips
itself when either is missing.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("boot1", "boot2", "sbios")

PASMO = os.environ.get("PASMO") or shutil.which("pasmo")
VASM = os.environ.get("VASM") or shutil.which("vasmz80_oldstyle")


@unittest.skipUnless(PASMO and VASM, "requires pasmo and vasmz80_oldstyle")
class AssemblerPortabilityTests(unittest.TestCase):
    def test_both_assemblers_agree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for source in SOURCES:
                src = ROOT / "asm" / f"{source}.z80"
                pasmo_out = tmp / f"{source}.pasmo.bin"
                vasm_out = tmp / f"{source}.vasm.bin"
                subprocess.run(
                    [PASMO, "--bin", "--include-dir", str(ROOT / "asm/include"),
                     str(src), str(pasmo_out)],
                    check=True, capture_output=True,
                )
                subprocess.run(
                    [VASM, "-Fbin", "-I", str(ROOT / "asm/include"),
                     "-o", str(vasm_out), str(src)],
                    check=True, capture_output=True,
                )
                with self.subTest(source=source):
                    self.assertEqual(pasmo_out.read_bytes(), vasm_out.read_bytes())


if __name__ == "__main__":
    unittest.main()
