#!/usr/bin/env python3
"""Post-build integrity checks for the generated UCSD disk image."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ucsd_image import UcsdImage, hexdump

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path,
                        default=ROOT / "config" / "image.json")
    parser.add_argument("--image", type=Path,
                        default=ROOT / "build" / "system.img")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    config = json.loads(args.config.read_text())
    image = UcsdImage.from_file(args.image, config["block_size"])

    if image.blocks < config["blocks"]:
        raise ValueError(
            f"image has {image.blocks} blocks, expected {config['blocks']}"
        )

    checks = [
        (config["boot1_block"], "primary bootstrap"),
        (config["boot2_block"], "secondary bootstrap"),
        (config["sbios_block"], "SBIOS"),
    ]
    for block, label in checks:
        data = image.read_block(block)
        if data == bytes(config["block_size"]):
            raise ValueError(f"block {block} ({label}) is empty")
        if args.verbose:
            print(f"{label} (block {block}):")
            print(hexdump(data[:64], block * config["block_size"]))
        print(f"OK  {label:18} block {block:4}")

    last_sbios = config["sbios_block"] + config["sbios_blocks"] - 1
    if last_sbios >= image.blocks:
        raise ValueError("SBIOS area extends past end of image")
    print(f"OK  image geometry     {image.blocks} blocks")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f"check_image.py: {exc}")
        raise SystemExit(1)
