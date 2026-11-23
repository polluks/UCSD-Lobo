#!/usr/bin/env python3
"""Minimal host-side tool for manipulating UCSD p-System disk images.

The p-System works in terms of logical 512-byte blocks.  This module keeps
those blocks as a first-class concept so that the boot images assembled by
pasmo can be inserted at exact block offsets without off-by-one errors.

Only the Python standard library is used so the build works on a bare
cross-build host.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BLOCK_SIZE = 512


class UcsdImage:
    """A flat image made up of fixed-size logical blocks."""

    def __init__(self, data: bytearray, block_size: int = BLOCK_SIZE) -> None:
        if block_size <= 0:
            raise ValueError("block_size must be positive")
        if len(data) % block_size:
            raise ValueError(
                f"image size {len(data)} is not a multiple of {block_size}"
            )
        self.data = data
        self.block_size = block_size

    @classmethod
    def new(cls, blocks: int, fill: int = 0xE5,
            block_size: int = BLOCK_SIZE) -> "UcsdImage":
        if blocks <= 0:
            raise ValueError("blocks must be positive")
        return cls(bytearray([fill & 0xFF]) * (blocks * block_size), block_size)

    @classmethod
    def from_file(cls, path: Path, block_size: int = BLOCK_SIZE) -> "UcsdImage":
        return cls(bytearray(path.read_bytes()), block_size)

    @property
    def blocks(self) -> int:
        return len(self.data) // self.block_size

    def read_block(self, number: int) -> bytes:
        self._check_block(number)
        start = number * self.block_size
        return bytes(self.data[start:start + self.block_size])

    def write_block(self, number: int, payload: bytes,
                    pad: int = 0x00) -> None:
        self._check_block(number)
        if len(payload) > self.block_size:
            raise ValueError(
                f"payload of {len(payload)} bytes does not fit in one block"
            )
        start = number * self.block_size
        self.data[start:start + self.block_size] = (
            bytes(payload) + bytes([pad & 0xFF]) * (self.block_size - len(payload))
        )

    def write_blocks(self, start_block: int, payload: bytes,
                     pad: int = 0x00) -> None:
        """Write a payload spanning one or more consecutive blocks."""
        if start_block < 0 or start_block >= self.blocks:
            raise ValueError(f"block {start_block} out of range")
        for offset in range(0, len(payload), self.block_size):
            chunk = payload[offset:offset + self.block_size]
            self.write_block(start_block + offset // self.block_size, chunk, pad)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes(self.data))

    def _check_block(self, number: int) -> None:
        if number < 0 or number >= self.blocks:
            raise ValueError(f"block {number} out of range (0..{self.blocks - 1})")


def hexdump(data: bytes, base: int = 0) -> str:
    lines = []
    for row in range(0, len(data), 16):
        chunk = data[row:row + 16]
        raw = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{base + row:08X}  {raw:<47}  |{ascii_part}|")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create a blank disk image")
    create.add_argument("image", type=Path)
    create.add_argument("--blocks", type=int, required=True)
    create.add_argument("--fill", type=lambda v: int(v, 0), default=0xE5)
    create.add_argument("--block-size", type=int, default=BLOCK_SIZE)

    patch = sub.add_parser("patch", help="write files into a disk image")
    patch.add_argument("image", type=Path)
    patch.add_argument("--block-size", type=int, default=BLOCK_SIZE)
    patch.add_argument(
        "--at", action="append", required=True, metavar="BLOCK=FILE",
        help="write FILE starting at logical BLOCK (repeatable)",
    )
    patch.add_argument("--pad", type=lambda v: int(v, 0), default=0x00,
                       help="byte used to fill the remainder of the last block")

    dump = sub.add_parser("dump", help="hex-dump one logical block")
    dump.add_argument("image", type=Path)
    dump.add_argument("block", type=int)
    dump.add_argument("--block-size", type=int, default=BLOCK_SIZE)

    info = sub.add_parser("info", help="show image geometry")
    info.add_argument("image", type=Path)
    info.add_argument("--block-size", type=int, default=BLOCK_SIZE)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "create":
        image = UcsdImage.new(args.blocks, args.fill, args.block_size)
        image.save(args.image)
        print(f"created {args.image}: {image.blocks} x {image.block_size} byte blocks")

    elif args.command == "patch":
        image = UcsdImage.from_file(args.image, args.block_size)
        for spec in args.at:
            if "=" not in spec:
                raise ValueError(f"invalid --at specification: {spec!r}")
            block_text, path_text = spec.split("=", 1)
            block = int(block_text, 0)
            payload = Path(path_text).read_bytes()
            image.write_blocks(block, payload, args.pad)
            print(f"  wrote {len(payload):5} bytes from {path_text} at block {block}")
        image.save(args.image)

    elif args.command == "dump":
        image = UcsdImage.from_file(args.image, args.block_size)
        print(hexdump(image.read_block(args.block),
                      args.block * args.block_size))

    elif args.command == "info":
        image = UcsdImage.from_file(args.image, args.block_size)
        size = args.block_size * image.blocks
        print(f"{args.image}: {image.blocks} blocks x {args.block_size} bytes "
              f"= {size} bytes ({size // 1024} KiB)")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(f"ucsd_image.py: {exc}", file=sys.stderr)
        sys.exit(1)
