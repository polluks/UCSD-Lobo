#!/usr/bin/env python3
"""Tests for directory creation and file extraction."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from ucsd_fs import Volume, create_volume  # noqa: E402


class VolumeTests(unittest.TestCase):
    def test_create_extract_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            interp = tmp / "interp.bin"
            pascal = tmp / "pascal.bin"
            boot1 = tmp / "boot1.bin"
            boot2 = tmp / "boot2.bin"
            sbios = tmp / "sbios.bin"
            interp.write_bytes(bytes(range(256)) * 6)     # 1536 bytes
            pascal.write_bytes(b"P" * 1000)
            boot1.write_bytes(b"\x01" * 37)
            boot2.write_bytes(b"\xc3" + b"\x02" * 370)
            sbios.write_bytes(b"\xc3" + b"\x00" * 1559)

            components = [
                ("SYSTEM.INTERP", interp, 5),
                ("SYSTEM.PASCAL", pascal, 5),
            ]
            boot_blocks = {
                "boot1": (0, boot1),
                "boot2": (1, boot2),
                "sbios": (10, sbios),
            }
            image = create_volume(components, 1309, boot_blocks)
            image_file = tmp / "disk.img"
            image.save(image_file)

            volume = Volume(image)
            files = volume.files()
            self.assertIn("SYSTEM.INTERP", files)
            self.assertIn("SYSTEM.PASCAL", files)
            self.assertEqual(volume.extract("SYSTEM.INTERP"), interp.read_bytes())
            self.assertEqual(volume.extract("SYSTEM.PASCAL"), pascal.read_bytes())
            self.assertEqual(image.read_block(0)[:37], boot1.read_bytes())
            self.assertEqual(
                image.read_block(1)[:len(boot2.read_bytes())], boot2.read_bytes()
            )
            sbios_on_disk = b"".join(
                image.read_block(10 + i) for i in range(4)
            )[:len(sbios.read_bytes())]
            self.assertEqual(sbios_on_disk, sbios.read_bytes())


if __name__ == "__main__":
    unittest.main()
