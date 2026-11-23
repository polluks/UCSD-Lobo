#!/usr/bin/env python3
"""Assemble a bootable UCSD disk image from the configured component blocks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ucsd_image import UcsdImage

ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text())
    required = {
        "block_size", "blocks", "boot1_block", "boot2_block",
        "sbios_block", "sbios_blocks",
    }
    missing = required - config.keys()
    if missing:
        raise ValueError(f"{path}: missing keys: {', '.join(sorted(missing))}")
    if config["block_size"] != 512:
        raise ValueError(
            "UCSD p-System logical blocks must be 512 bytes; "
            f"got {config['block_size']}"
        )
    if config["boot1_block"] != 0:
        raise ValueError("the primary bootstrap must be at block 0")
    return config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path,
                        default=ROOT / "config" / "image.json")
    parser.add_argument("--base", type=Path,
                        help="existing p-System image to patch in place")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build" / "system.img")
    parser.add_argument("--boot1", type=Path,
                        default=ROOT / "build" / "boot1.bin")
    parser.add_argument("--boot2", type=Path,
                        default=ROOT / "build" / "boot2.bin")
    parser.add_argument("--sbios", type=Path,
                        default=ROOT / "build" / "sbios.bin")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    block_size = config["block_size"]

    if args.base:
        image = UcsdImage.from_file(args.base, block_size)
    else:
        fill = int(config.get("fill", "0xE5"), 0)
        image = UcsdImage.new(config["blocks"], fill, block_size)

    placements = [
        (config["boot1_block"], args.boot1, "primary bootstrap"),
        (config["boot2_block"], args.boot2, "secondary bootstrap"),
        (config["sbios_block"], args.sbios, "SBIOS"),
    ]
    for block, source, label in placements:
        payload = source.read_bytes()
        needed = (len(payload) + block_size - 1) // block_size
        if label == "SBIOS" and needed > config["sbios_blocks"]:
            raise ValueError(
                f"{label} needs {needed} blocks but only "
                f"{config['sbios_blocks']} are configured"
            )
        image.write_blocks(block, payload)
        print(f"{label:18} block {block:4}  {len(payload):5} bytes")

    if image.blocks < config["blocks"]:
        raise ValueError(
            f"base image is too small: {image.blocks} blocks, "
            f"expected at least {config['blocks']}"
        )
    image.save(args.output)
    print(f"wrote {args.output} ({image.blocks} blocks)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"build_image.py: {exc}")
        raise SystemExit(1)
