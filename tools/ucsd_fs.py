#!/usr/bin/env python3
"""Read and create minimal UCSD p-System IV volumes with 512-byte blocks.

The directory is one flat table of 78 entries of 26 bytes each, starting at
logical block 2 (configurable).  Entry 0 is the volume label; entries 1..77
describe files.  This tool deliberately implements only what the MAX-80
bootstrap loader needs: locating and reading contiguous files.
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

from ucsd_image import BLOCK_SIZE, UcsdImage

DIR_BLOCK = 2
DIR_BLOCKS = 4
DIR_ENTRIES = 78
ENTRY_SIZE = 26


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def put_u16(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<H", data, offset, value & 0xFFFF)


def decode_name(raw: bytes) -> str:
    if not raw or raw[0] == 0 or raw[0] > 15:
        return ""
    length = raw[0]
    return raw[1:1 + length].decode("ascii", errors="replace")


def encode_name(name: str) -> bytes:
    encoded = name.upper().encode("ascii")[:15]
    return bytes([len(encoded)]) + encoded + bytes(15 - len(encoded))


class Volume:
    def __init__(self, image: UcsdImage, dir_block: int = DIR_BLOCK) -> None:
        self.image = image
        self.dir_block = dir_block
        raw = b"".join(image.read_block(dir_block + i) for i in range(DIR_BLOCKS))
        self.entries = [bytearray(raw[i * ENTRY_SIZE:(i + 1) * ENTRY_SIZE])
                        for i in range(DIR_ENTRIES)]

    def files(self) -> dict[str, dict]:
        result = {}
        for entry in self.entries[1:]:
            name = decode_name(entry[6:22])
            if not name:
                continue
            result[name] = {
                "first": u16(entry, 0),
                "past": u16(entry, 2),
                "kind": entry[4] & 0x0F,
                "last_bytes": u16(entry, 22),
            }
        return result

    def extract(self, name: str) -> bytes:
        info = self.files().get(name.upper())
        if not info:
            raise ValueError(f"file {name!r} not found in directory")
        data = bytearray()
        for block in range(info["first"], info["past"]):
            data += self.image.read_block(block)
        last = info["last_bytes"]
        needed = info["past"] - info["first"]
        keep = (needed - 1) * BLOCK_SIZE + last
        if 0 < last < BLOCK_SIZE and keep < len(data):
            del data[keep:]
        return bytes(data)


def create_volume(components: list[tuple[str, Path, int]], blocks: int,
                  boot_blocks: dict[str, tuple[int, Path]],
                  volume_name: str = "MAX80") -> UcsdImage:
    """Create a volume with the given files packed after reserved blocks."""
    FIRST_FILE_BLOCK = 18
    first_data = FIRST_FILE_BLOCK
    image = UcsdImage.new(blocks, 0xE5)

    # Start with an entirely empty directory so unused entries read as empty.
    for i in range(DIR_BLOCKS):
        image.write_block(DIR_BLOCK + i, bytes(BLOCK_SIZE), pad=0)

    for name, path, kind in components:
        payload = path.read_bytes()
        start = first_data
        needed = (len(payload) + BLOCK_SIZE - 1) // BLOCK_SIZE
        for offset in range(0, needed):
            chunk = payload[offset * BLOCK_SIZE:(offset + 1) * BLOCK_SIZE]
            image.write_block(start + offset, chunk)
        first_data += needed

    # Volume label entry.
    label = bytearray(ENTRY_SIZE)
    put_u16(label, 2, FIRST_FILE_BLOCK)      # first block after directory
    encoded = encode_name(volume_name)
    label[6:22] = encoded
    put_u16(label, 14, blocks)
    put_u16(label, 16, len(components))
    image.write_block(DIR_BLOCK, bytes(label), pad=0)

    # File entries.
    cursor = FIRST_FILE_BLOCK
    for index, (name, path, kind) in enumerate(components, start=1):
        payload = path.read_bytes()
        needed = (len(payload) + BLOCK_SIZE - 1) // BLOCK_SIZE
        entry = bytearray(ENTRY_SIZE)
        put_u16(entry, 0, cursor)
        put_u16(entry, 2, cursor + needed)
        entry[4] = kind & 0x0F
        entry[6:22] = encode_name(name)
        last = len(payload) - (needed - 1) * BLOCK_SIZE if needed else 0
        put_u16(entry, 22, last)
        block = DIR_BLOCK + (index * ENTRY_SIZE) // BLOCK_SIZE
        offset = (index * ENTRY_SIZE) % BLOCK_SIZE
        current = bytearray(image.read_block(block))
        current[offset:offset + ENTRY_SIZE] = entry
        image.write_block(block, bytes(current))
        cursor += needed

    for name, (block, path) in boot_blocks.items():
        image.write_blocks(block, path.read_bytes())

    return image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("list", help="list directory entries")
    listing.add_argument("image", type=Path)
    listing.add_argument("--dir-block", type=int, default=DIR_BLOCK)

    extract = sub.add_parser("extract", help="extract a file from a volume")
    extract.add_argument("image", type=Path)
    extract.add_argument("name")
    extract.add_argument("--out", type=Path, required=True)
    extract.add_argument("--dir-block", type=int, default=DIR_BLOCK)

    create = sub.add_parser("create", help="create a bootable volume")
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--blocks", type=int, default=1309)
    create.add_argument("--volume-name", default="MAX80")
    create.add_argument("--boot1", type=Path, required=True)
    create.add_argument("--boot2", type=Path, required=True)
    create.add_argument("--sbios", type=Path, required=True)
    create.add_argument("--sbios-block", type=int, default=10)
    create.add_argument(
        "--file", action="append", required=True, metavar="NAME=PATH:KIND",
        help="include a p-System file (repeatable), e.g. SYSTEM.INTERP=interp.bin:5",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "list":
        volume = Volume(UcsdImage.from_file(args.image), args.dir_block)
        for name, info in volume.files().items():
            print(f"{name:16} blocks {info['first']:4}-{info['past'] - 1:4} "
                  f"kind={info['kind']}")
        return 0

    if args.command == "extract":
        volume = Volume(UcsdImage.from_file(args.image), args.dir_block)
        payload = volume.extract(args.name)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(payload)
        print(f"extracted {args.name}: {len(payload)} bytes -> {args.out}")
        return 0

    if args.command == "create":
        components = []
        for spec in args.file:
            name, rest = spec.split("=", 1)
            path_text, kind_text = rest.rsplit(":", 1)
            components.append((name, Path(path_text), int(kind_text, 0)))
        boot_blocks = {
            "boot1": (0, args.boot1),
            "boot2": (1, args.boot2),
            "sbios": (args.sbios_block, args.sbios),
        }
        image = create_volume(components, args.blocks, boot_blocks,
                              args.volume_name)
        image.save(args.output)
        print(f"created {args.output} with {len(components)} files")
        return 0

    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"ucsd_fs.py: {exc}")
        raise SystemExit(1)
