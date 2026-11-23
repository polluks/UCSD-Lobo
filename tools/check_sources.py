#!/usr/bin/env python3
"""Structural checks on the assembled bootstrap and SBIOS binaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JP = 0xC3

BASIC_VECTORS = [
    "SYSINIT", "SYSHALT", "CONINIT", "CONSTAT", "CONREAD", "CONWRIT",
    "SETDISK", "SETTRK", "SETSEC", "SETBUFR", "DSKREAD", "DSKWRIT",
    "DSKINIT", "DSKSTRT", "DSKSTOP",
]
EXTENDED_VECTORS = [
    "PRNINIT", "PRNSTAT", "PRNREAD", "PRNWRIT", "REMINIT", "REMSTAT",
    "REMREAD", "REMWRIT", "USRINIT", "USRSTAT", "USRREAD", "USRWRIT",
    "CLKREAD",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=ROOT / "build")
    parser.add_argument("--config", type=Path,
                        default=ROOT / "config" / "image.json")
    args = parser.parse_args(argv)

    config = json.loads(args.config.read_text())
    boot1 = (args.build / "boot1.bin").read_bytes()
    boot2 = (args.build / "boot2.bin").read_bytes()
    sbios = (args.build / "sbios.bin").read_bytes()

    assert boot1, "primary bootstrap is empty"
    assert boot2[0] == JP, "secondary bootstrap must start with JP"
    assert len(boot2) <= 4 * 512, "secondary bootstrap exceeds reserved blocks"

    for index, name in enumerate(BASIC_VECTORS + EXTENDED_VECTORS):
        offset = index * 3
        if sbios[offset] != JP:
            raise ValueError(
                f"SBIOS vector {name} at +{offset:02X}H is not a JP "
                f"(got {sbios[offset]:02X})"
            )
    print(f"OK  28 SBIOS vectors present")

    sbios_blocks = (len(sbios) + 511) // 512
    if sbios_blocks > config["sbios_blocks"]:
        raise ValueError(
            f"SBIOS needs {sbios_blocks} blocks, "
            f"configured {config['sbios_blocks']}"
        )
    print(f"OK  SBIOS size {len(sbios)} bytes ({sbios_blocks} blocks)")
    print(f"OK  boot1 {len(boot1)} bytes, boot2 {len(boot2)} bytes")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, AssertionError) as exc:
        print(f"check_sources.py: {exc}")
        raise SystemExit(1)
