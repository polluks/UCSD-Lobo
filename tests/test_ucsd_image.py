#!/usr/bin/env python3
"""Unit tests for the host-side disk image utility."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from ucsd_image import UcsdImage, hexdump  # noqa: E402

TOOL = Path(__file__).resolve().parents[1] / "tools" / "ucsd_image.py"


class UcsdImageTests(unittest.TestCase):
    def test_new_image_geometry(self):
        image = UcsdImage.new(4, fill=0xE5)
        self.assertEqual(image.blocks, 4)
        self.assertEqual(len(image.data), 2048)
        self.assertEqual(image.read_block(0), b"\xe5" * 512)

    def test_write_block_pads_and_isolates(self):
        image = UcsdImage.new(3, fill=0xE5)
        image.write_block(1, b"\x01\x02\x03", pad=0xFF)
        self.assertEqual(image.read_block(1)[:3], b"\x01\x02\x03")
        self.assertEqual(image.read_block(1)[3], 0xFF)
        self.assertEqual(image.read_block(0), b"\xe5" * 512)
        self.assertEqual(image.read_block(2), b"\xe5" * 512)

    def test_write_blocks_spans_boundary(self):
        image = UcsdImage.new(3, fill=0x00)
        payload = bytes(range(256)) * 3  # 768 bytes -> blocks 1 and 2
        image.write_blocks(1, payload)
        self.assertEqual(image.read_block(1), payload[:512])
        self.assertEqual(image.read_block(2)[:len(payload) - 512], payload[512:])
        self.assertEqual(image.read_block(2)[len(payload) - 512:], b"\x00" * 256)

    def test_rejects_oversize_payload(self):
        image = UcsdImage.new(1)
        with self.assertRaises(ValueError):
            image.write_block(0, b"\x00" * 513)

    def test_rejects_out_of_range_block(self):
        image = UcsdImage.new(1)
        with self.assertRaises(ValueError):
            image.read_block(1)

    def test_hexdump(self):
        text = hexdump(b"\x00\x41\xff", base=0x1000)
        self.assertIn("00001000", text)
        self.assertIn("41", text)
        self.assertIn("|.A.|", text)

    def test_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "disk.img"
            payload_path = Path(tmp) / "payload.bin"
            payload_path.write_bytes(b"\xde\xad\xbe\xef")
            subprocess.run(
                [sys.executable, str(TOOL), "create", str(image_path),
                 "--blocks", "4"],
                check=True, capture_output=True,
            )
            subprocess.run(
                [sys.executable, str(TOOL), "patch", str(image_path),
                 "--at", f"2={payload_path}"],
                check=True, capture_output=True,
            )
            image = UcsdImage.from_file(image_path)
            self.assertEqual(image.read_block(2)[:4], b"\xde\xad\xbe\xef")
            info = subprocess.run(
                [sys.executable, str(TOOL), "info", str(image_path)],
                check=True, capture_output=True, text=True,
            ).stdout
            self.assertIn("4 blocks", info)


if __name__ == "__main__":
    unittest.main()
